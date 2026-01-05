import subprocess
import json
import sys

class SecurityAgent:
    def run(self, repo_path: str) -> dict:
        print("🛡️ Running Bandit Security Scan...")
        try:
            # Run bandit recursively (-r), output JSON (-f json)
            # -ll means "Report only Medium and High severity issues"
            cmd = [sys.executable, "-m", "bandit", "-r", ".", "-f", "json", "-ll"]
            
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            output = result.stdout.strip()
            
            # Bandit writes to stdout usually, but sometimes stderr if config is missing.
            if not output:
                return {"summary": "No Security Issues Found", "details": []}

            try:
                data = json.loads(output)
            except json.JSONDecodeError:
                return {"summary": "Security Scan Failed", "details": [{"message": "Could not parse bandit output"}]}

            results = data.get("results", [])
            issues = []
            
            for item in results:
                issues.append({
                    "file": item["filename"],
                    "line": item["line_number"],
                    "severity": item["issue_severity"],
                    "message": item["issue_text"],
                    "more_info": item["more_info"]
                })

            return {
                "summary": f"Found {len(issues)} security issues",
                "details": issues
            }

        except Exception as e:
            return {"error": str(e)}