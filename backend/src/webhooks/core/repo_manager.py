import os
import shutil
import tempfile
import subprocess
import stat

from config import config

# Helper to force delete read-only files on Windows
def remove_readonly(func, path, exc_info):
    # Clear the read-only bit and retry
    os.chmod(path, stat.S_IWRITE)
    func(path)

class RepoManager:
    def __init__(self, repo_url: str, commit_sha: str, token: str):
        # Embed token for auth
        self.repo_url = repo_url.replace("https://", f"https://x-access-token:{token}@")
        self.commit_sha = commit_sha
        
        # Ensure shared workspace exists
        if not os.path.exists(config.WORKSPACE_MOUNT_PATH):
            os.makedirs(config.WORKSPACE_MOUNT_PATH, exist_ok=True)
            
        # Create temp dir INSIDE the shared workspace
        self.temp_dir = tempfile.mkdtemp(prefix="repo-", dir=config.WORKSPACE_MOUNT_PATH)

    def clone_and_checkout(self):
        try:
            print(f"⬇️ Cloning to {self.temp_dir}...")
            # 1. Clone
            subprocess.run(
                ["git", "clone", self.repo_url, "."], 
                cwd=self.temp_dir, 
                check=True,
                capture_output=True
            )
            # 2. Checkout specific SHA
            subprocess.run(
                ["git", "checkout", self.commit_sha], 
                cwd=self.temp_dir, 
                check=True,
                capture_output=True
            )
            return self.temp_dir
        except Exception as e:
            self.cleanup()
            raise e

    def cleanup(self):
        if os.path.exists(self.temp_dir):
            try:
                print(f"🧹 Cleaning up {self.temp_dir}...")
                
                # On Windows, git files might be read-only; clear attributes first
                for root, dirs, files in os.walk(self.temp_dir):
                    for d in dirs:
                        try:
                            os.chmod(os.path.join(root, d), stat.S_IWRITE | stat.S_IREAD)
                        except:
                            pass
                    for f in files:
                        try:
                            os.chmod(os.path.join(root, f), stat.S_IWRITE | stat.S_IREAD)
                        except:
                            pass
                
                # Now try to remove
                shutil.rmtree(self.temp_dir, onerror=remove_readonly)
                print(f"✅ Cleaned up {self.temp_dir}")
            except Exception as e:
                print(f"⚠️ Cleanup failed (non-critical): {e}")
                # On Windows, some processes might still have locks; retry after a short delay
                import time
                time.sleep(0.1)
                try:
                    shutil.rmtree(self.temp_dir, onerror=remove_readonly)
                    print(f"✅ Cleaned up {self.temp_dir} (after retry)")
                except Exception as e2:
                    print(f"⚠️ Second cleanup attempt failed: {e2}")