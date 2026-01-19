import yaml
import json
from typing import List, Dict, Optional

class CustomCheckLoader:
    """
    Loads custom checks from various sources:
    - .pr-reviewer.yml in repo
    - User-provided document files
    - API-provided checks
    """
    
    DEFAULT_CHECKS = [
        "No hardcoded API keys or secrets",
        "Error handling must log errors (no empty catch blocks)",
        "Functions should have docstrings/comments explaining purpose",
        "Avoid nested loops where possible (O(n^2))"
    ]
    
    @staticmethod
    async def load_from_repo(gh, repo: str, sha: str) -> Dict:
        """Load custom checks from .pr-reviewer.yml in the repository."""
        print(f"🔍 Loading custom checks from {repo}...")
        
        config = {
            "enable_review": True,
            "severity_threshold": "low",
            "custom_instructions": "",
            "custom_checks": CustomCheckLoader.DEFAULT_CHECKS.copy(),
            "language_rules": {}
        }
        
        try:
            # Try .pr-reviewer.yml
            content = await gh.get_file_content(repo, ".pr-reviewer.yml", sha)
            if content:
                user_config = yaml.safe_load(content)
                config = CustomCheckLoader._merge_config(config, user_config)
                print("✅ Loaded .pr-reviewer.yml")
        except Exception as e:
            print(f"⚠️ No .pr-reviewer.yml found: {e}")
        
        # Try best_practices.md or similar
        try:
            for doc_name in ["best_practices.md", "CODING_STANDARDS.md", "CODE_REVIEW.md"]:
                content = await gh.get_file_content(repo, doc_name, sha)
                if content:
                    checks = CustomCheckLoader._parse_markdown_checks(content)
                    if checks:
                        config["custom_checks"].extend(checks)
                        print(f"✅ Loaded checks from {doc_name}")
                        break
        except Exception as e:
            print(f"⚠️ No custom docs found: {e}")
        
        return config
    
    @staticmethod
    def _merge_config(default: Dict, user: Dict) -> Dict:
        """Merge user config with defaults."""
        merged = default.copy()
        
        for key, value in user.items():
            if key == "custom_checks" and isinstance(value, list):
                # Extend checks, don't replace
                merged["custom_checks"] = merged.get("custom_checks", []) + value
            elif key == "language_rules" and isinstance(value, dict):
                # Merge language-specific rules
                merged["language_rules"] = {**merged.get("language_rules", {}), **value}
            else:
                merged[key] = value
        
        return merged
    
    @staticmethod
    def _parse_markdown_checks(content: str) -> List[str]:
        """Extract check items from a markdown document."""
        checks = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            # Match numbered or bulleted list items
            if line.startswith(('- ', '* ', '• ')):
                check = line[2:].strip()
                if check and len(check) > 10:  # Minimum meaningful length
                    # Remove markdown formatting
                    check = check.replace('**', '').replace('*', '').replace('`', '')
                    checks.append(check)
            elif line and line[0].isdigit() and '.' in line[:3]:
                # Numbered list: "1. Check item"
                check = line.split('.', 1)[1].strip() if '.' in line else line
                if check and len(check) > 10:
                    check = check.replace('**', '').replace('*', '').replace('`', '')
                    checks.append(check)
        
        return checks[:20]  # Limit to 20 custom checks
    
    @staticmethod
    def parse_user_document(content: str, format: str = "auto") -> List[str]:
        """
        Parse a user-provided document to extract custom checks.
        Supports: markdown, yaml, json, plain text
        """
        if format == "auto":
            # Detect format
            if content.strip().startswith('{') or content.strip().startswith('['):
                format = "json"
            elif content.strip().startswith('---') or ':' in content.split('\n')[0]:
                format = "yaml"
            else:
                format = "markdown"
        
        if format == "json":
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    return [str(item) for item in data]
                elif isinstance(data, dict) and "checks" in data:
                    return [str(item) for item in data["checks"]]
            except:
                pass
        
        elif format == "yaml":
            try:
                data = yaml.safe_load(content)
                if isinstance(data, list):
                    return [str(item) for item in data]
                elif isinstance(data, dict) and "checks" in data:
                    return [str(item) for item in data["checks"]]
            except:
                pass
        
        # Fallback to markdown parsing
        return CustomCheckLoader._parse_markdown_checks(content)
