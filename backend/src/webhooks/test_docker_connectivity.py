import asyncio
import sys
import os

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def test_docker():
    print(f"PATH: {os.environ.get('PATH')}")
    print("Attempting to run 'docker version' via asyncio...")
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        print(f"Return Code: {proc.returncode}")
        print(f"STDOUT: {stdout.decode().strip()}")
        print(f"STDERR: {stderr.decode().strip()}")
    except FileNotFoundError:
        print("❌ FileNotFoundError: 'docker' executable not found in PATH.")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_docker())
