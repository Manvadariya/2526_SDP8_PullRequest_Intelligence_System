"""
docker_runner.py – Run linting & security checks using a persistent Docker worker.

The worker container runs in the background, mounting the shared workspace.
Use `docker exec` to run checks instantly without startup overhead.
"""

import os
import json
import sys
import asyncio
from config import config as app_config

# Ensure stdout can handle emoji/unicode on Windows (cp1252 terminals)
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


class DockerRunner:
    """Manages the persistent Docker worker service for PR analysis."""

    IMAGE_NAME = getattr(app_config, "DOCKER_IMAGE", "pr-checks:latest")
    TIMEOUT = getattr(app_config, "DOCKER_TIMEOUT", 300)
    WORKER_NAME = getattr(app_config, "DOCKER_CONTAINER_NAME", "sapient-pr-checks-worker")
    DOCKER_EXE = getattr(app_config, "DOCKER_EXECUTABLE_PATH", "docker")
    _docker_available = None  # Cache result to avoid repeated checks

    @staticmethod
    async def run_checks_in_container(repo_path: str, changed_files: list = None) -> dict:
        """
        Run checks inside the persistent worker container via `docker exec`.
        """
        repo_dirname = os.path.basename(repo_path)
        # Path inside container (assuming workspace is mounted at /workspace)
        container_workdir = f"/workspace/{repo_dirname}"
        
        # Results are written to the repo dir itself to avoid permission issues with a separate mount
        results_file_lint = os.path.join(repo_path, "lint.json")
        results_file_sec = os.path.join(repo_path, "security.json")

        print(f"🐳 Running checks for {repo_dirname} in worker '{DockerRunner.WORKER_NAME}'...")

        # 1. Ensure Worker is Running
        if not await DockerRunner._ensure_worker_running():
             return DockerRunner._default_results("Docker worker unavailable")

        try:
            # 2. Exec Command
            # We run the script inside the container's view of the repo
            cmd_args = [
                "exec",
                "-w", container_workdir,
                DockerRunner.WORKER_NAME,
                "/usr/local/bin/run_checks.sh",
                ".",
                "."
            ]

            process = await asyncio.create_subprocess_exec(
                DockerRunner.DOCKER_EXE, *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=DockerRunner.TIMEOUT
                )
            except asyncio.TimeoutError:
                print(f"⏰ Checks timed out after {DockerRunner.TIMEOUT}s")
                try:
                    process.kill()
                    # We can't kill the exec easily without killing the container or finding the PID.
                    # For now, just warn. The script inside might still be running.
                except:
                    pass
                return DockerRunner._default_results("Review timed out")

            if stdout:
                print(stdout.decode(errors="replace")[:1000]) # Log first 1000 chars
            if stderr:
                err_text = stderr.decode(errors="replace")
                if err_text.strip():
                    print(f"⚠️ Exec stderr: {err_text[:500]}")

            print(f"✅ Checks finished (exit code {process.returncode})")

            # 3. Read Results from Repo Dir (Host side)
            # The script writes lint.json and security.json to the current directory (container_workdir)
            # which maps to repo_path on host.
            
            lint_results = DockerRunner._read_json(results_file_lint)
            sec_results = DockerRunner._read_json(results_file_sec)

            return {
                "lint": lint_results or {"summary": "No lint output", "details": []},
                "security": sec_results or {"summary": "No security output", "details": []},
            }

        except Exception as e:
            print(f"❌ Docker execution error: {e}")
            return DockerRunner._default_results(str(e))

    # ── Service Management ─────────────────────────────────────

    @staticmethod
    async def check_docker_available() -> bool:
        """Verify that the Docker daemon is reachable by running `docker info`.
        Result is cached for the lifetime of the process."""
        if DockerRunner._docker_available is not None:
            return DockerRunner._docker_available

        try:
            proc = await asyncio.create_subprocess_exec(
                DockerRunner.DOCKER_EXE, "info",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)
            if proc.returncode == 0:
                DockerRunner._docker_available = True
                print("🐳 Docker daemon is reachable.")
                return True
            else:
                err = stderr.decode(errors="replace").strip()
                print(f"❌ Docker daemon not reachable (exit {proc.returncode}):")
                print(f"   {err[:200]}")
                print("   💡 Ensure Docker Desktop is running, or start the Docker service.")
                DockerRunner._docker_available = False
                return False
        except FileNotFoundError:
            print(f"❌ Docker executable not found at: {DockerRunner.DOCKER_EXE}")
            print("   💡 Install Docker or set DOCKER_EXECUTABLE_PATH in your .env file.")
            DockerRunner._docker_available = False
            return False
        except asyncio.TimeoutError:
            print("❌ Docker daemon check timed out (15s). Is Docker Desktop starting up?")
            DockerRunner._docker_available = False
            return False
        except Exception as e:
            print(f"❌ Docker availability check failed: {e}")
            DockerRunner._docker_available = False
            return False

    @staticmethod
    async def _ensure_worker_running() -> bool:
        """Ensure the long-running worker container is up."""
        # Pre-flight: is Docker daemon even reachable?
        if not await DockerRunner.check_docker_available():
            return False

        # Check if running
        is_running = await DockerRunner._is_container_running(DockerRunner.WORKER_NAME)
        if is_running:
            return True
        
        print(f"🔧 Worker '{DockerRunner.WORKER_NAME}' not running. Starting...")
        
        # Remove if exists but stopped
        await DockerRunner._remove_container(DockerRunner.WORKER_NAME)
        
        # Start new
        # Mount host workspace to /workspace in container
        workspace_mount = getattr(app_config, "WORKSPACE_MOUNT_PATH", "")
        if not workspace_mount:
            print("❌ WORKSPACE_MOUNT_PATH not set in config.")
            return False
            
        # Ensure dir exists on host
        if not os.path.exists(workspace_mount):
            print(f"🔧 Creating workspace dir: {workspace_mount}")
            os.makedirs(workspace_mount, exist_ok=True)

        # Normalize drive letter to uppercase for Docker Desktop Windows compatibility
        workspace_mount = os.path.abspath(workspace_mount)
        if len(workspace_mount) > 1 and workspace_mount[1] == ':':
            workspace_mount = workspace_mount[0].upper() + workspace_mount[1:]

        print(f"🔍 Mounting: {workspace_mount} -> /workspace")
        print(f"D drive contents local: {os.listdir(workspace_mount) if os.path.exists(workspace_mount) else 'DIR NOT FOUND'}")

        cmd_args = [
            "run", "-d",
            "--name", DockerRunner.WORKER_NAME,
            "--restart", "unless-stopped",
            "-v", f"{workspace_mount}:/workspace",
            DockerRunner.IMAGE_NAME,
            "sleep", "infinity"
        ]
        print(f"🚀 Running Docker command: {cmd_args}")
        
        try:
             proc = await asyncio.create_subprocess_exec(
                DockerRunner.DOCKER_EXE, *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
             )
             stdout, stderr = await proc.communicate()
             if proc.returncode != 0:
                 print(f"❌ Failed to start worker: {stderr.decode()}")
                 return False
             
             print(f"✅ Worker started: {stdout.decode().strip()[:12]}")
             # Wait for status=running
             for _ in range(10):
                 if await DockerRunner._is_container_running(DockerRunner.WORKER_NAME):
                     return True
                 await asyncio.sleep(1)
             print("❌ Worker stuck in starting state.")
             return False
        except Exception as e:
             print(f"❌ Exception starting worker: {e!r}")
             import traceback
             traceback.print_exc()
             return False

    @staticmethod
    async def _is_container_running(name: str) -> bool:
        try:
            proc = await asyncio.create_subprocess_exec(
                DockerRunner.DOCKER_EXE, "ps", "-q", "-f", f"name={name}", "-f", "status=running",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            return bool(stdout.strip())
        except Exception:
            return False

    @staticmethod
    async def _remove_container(name: str):
        try:
            proc = await asyncio.create_subprocess_exec(
                DockerRunner.DOCKER_EXE, "rm", "-f", name,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await proc.wait()
        except:
            pass

    @staticmethod
    def _read_json(path: str) -> dict:
        """Read and parse a JSON results file."""
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Could not read {path}: {e}")
        return None

    @staticmethod
    def _default_results(error_msg: str) -> dict:
        """Return a default result structure when Docker fails."""
        return {
            "lint": {"summary": "Lint check unavailable", "details": [], "error": error_msg},
            "security": {"summary": "Security check unavailable", "details": [], "error": error_msg},
        }
