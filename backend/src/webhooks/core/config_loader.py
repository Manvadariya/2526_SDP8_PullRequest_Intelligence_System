import yaml
from core.github_client import GitHubClient

DEFAULT_CONFIG = {
    "enable_review": True,
    "severity_threshold": "low",
    "custom_instructions": "Focus on bugs and security. Be concise."
}

async def load_repo_config(gh: GitHubClient, repo: str, sha: str) -> dict:
    print(f"🔍 Checking for .pr-reviewer.yml in {repo} at {sha[:7]}...")
    
    try:
        content = await gh.get_file_content(repo, ".pr-reviewer.yml", sha)
        if content:
            user_config = yaml.safe_load(content)
            print("✅ Found custom config!")
            # Merge with defaults
            return {**DEFAULT_CONFIG, **user_config}
    except Exception as e:
        print(f"⚠️ Error loading config: {e}")

    print("ℹ️ Using default config.")
    return DEFAULT_CONFIG