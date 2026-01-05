import os
import shutil
import tempfile
import subprocess
import stat

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
        self.temp_dir = tempfile.mkdtemp(prefix="ai-review-")

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
                # FIX: Use onerror to handle Windows read-only git files
                shutil.rmtree(self.temp_dir, onerror=remove_readonly)
                print(f"🧹 Cleaned up {self.temp_dir}")
            except Exception as e:
                print(f"⚠️ Cleanup failed (non-critical): {e}")