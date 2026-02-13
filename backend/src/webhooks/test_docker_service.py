import asyncio
import os
import sys

# Ensure backend/src/webhooks is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from config import config
from core.docker_runner import DockerRunner

# if sys.platform == 'win32':
#     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def verify():
    print(f"Docker Exe: {config.DOCKER_EXECUTABLE_PATH}")
    print(f"Worker Name: {config.DOCKER_CONTAINER_NAME}")
    
    # 1. Ensure worker running
    print("Ensuring worker...")
    running = await DockerRunner._ensure_worker_running()
    print(f"Worker running: {running}")
    
    if not running:
        print("❌ Worker failed to start.")
        return

    # 2. Simulate RepoManager: Create a fake repo dir in shared workspace
    repo_name = "test-repo-verify"
    workspace_mount = config.WORKSPACE_MOUNT_PATH
    if not os.path.exists(workspace_mount):
        os.makedirs(workspace_mount)
        
    repo_path = os.path.join(workspace_mount, repo_name)
    os.makedirs(repo_path, exist_ok=True)
    
    # Create a python file with a blatant syntax error
    with open(os.path.join(repo_path, "bad_code.py"), "w") as f:
        f.write("def foo()  # Missing colon\n    pass\n") 
        
    print(f"Running checks on {repo_path}...")
    
    # DEBUG: Check if files are visible
    print("DEBUG: Checking /workspace contents...")
    try:
        proc = await asyncio.create_subprocess_exec(
            config.DOCKER_EXECUTABLE_PATH, "exec", config.DOCKER_CONTAINER_NAME, "ls", "-R", "/workspace",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        out, err = await proc.communicate()
        print(f"ls /workspace:\n{out.decode()}")
        if err: print(f"ls stderr: {err.decode()}")
    except Exception as e:
        print(f"DEBUG ls failed: {e}")

    results = await DockerRunner.run_checks_in_container(repo_path)
    print("Results:", results)
    
    # Check if results contain issues (flake8 should flag unused import or missing newline)
    lint = results.get("lint", {})
    details = lint.get("details", [])
    if details:
        print(f"✅ Lint issues found: {len(details)} (Expected)")
        for d in details:
            print(f"  - {d.get('message')}")
    else:
        print("⚠️ No lint issues found. Verify run_checks.sh output.")

if __name__ == "__main__":
    asyncio.run(verify())
