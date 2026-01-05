import subprocess
import json
import sys

class LinterAgent:
    def __init__(self):
        pass

    def run(self, repo_path: str) -> dict:
        print("🔍 Running Flake8...")
        try:
            cmd = [sys.executable, "-m", "flake8", ".", "--format=json"]
            result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True)
            
            output = result.stdout
            if not output:
                return {"summary": "No Lint Issues", "details": []}

            # FIX: Flake8 might output text warnings mixed with JSON.
            # We look for the start of the JSON structure (usually a dictionary or list)
            try:
                # Attempt direct parse first
                data = json.loads(output)
            except json.JSONDecodeError:
                # Fallback: Find the first '{' and try to parse from there
                start_idx = output.find('{')
                if start_idx != -1:
                    try:
                        data = json.loads(output[start_idx:])
                    except:
                        return {"summary": "Linter Parse Error", "details": [{"message": "Could not parse Flake8 JSON output"}]}
                else:
                    return {"summary": "Linter Parse Error", "details": [{"message": "No JSON found in output"}]}
            
            issues = []
            # Flake8 JSON is a dict: {"filename": [{"code": "E123", ...}]}
            for filename, violations in data.items():
                for v in violations:
                    issues.append({
                        "file": filename,
                        "line": v["line"],
                        "code": v["code"],
                        "message": v["text"]
                    })

            return {
                "summary": f"Found {len(issues)} lint issues",
                "details": issues[:10]
            }

        except Exception as e:
            return {"error": str(e)}