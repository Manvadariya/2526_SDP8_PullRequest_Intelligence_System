import subprocess
import json
import sys
import os
from pathlib import Path

class LinterAgent:
    def __init__(self):
        self.linters = {
            'python': self._run_flake8,
            'javascript': self._run_eslint,
            'typescript': self._run_eslint,
            'java': self._run_checkstyle,
            'cpp': self._run_cppcheck,
            'c': self._run_cppcheck,
        }
    
    def run(self, repo_path: str, changed_files: list = None) -> dict:
        """
        Run linters for all detected languages.
        Returns combined results from all linters.
        """
        print("🔍 Running Multi-Language Linting...")
        
        # Detect languages from file extensions
        languages = self._detect_languages(repo_path, changed_files)
        
        all_results = {
            "summary": "",
            "details": [],
            "by_language": {}
        }
        
        total_issues = 0
        
        for lang in languages:
            if lang in self.linters:
                print(f"  📝 Linting {lang}...")
                result = self.linters[lang](repo_path)
                all_results["by_language"][lang] = result
                
                if "details" in result:
                    total_issues += len(result["details"])
                    all_results["details"].extend(result["details"])
        
        all_results["summary"] = f"Found {total_issues} lint issues across {len(languages)} language(s)"
        
        return all_results
    
    def _detect_languages(self, repo_path: str, changed_files: list = None) -> set:
        """Detect programming languages in the repo."""
        ext_to_lang = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.c': 'c',
            '.h': 'cpp',
            '.hpp': 'cpp',
        }
        
        languages = set()
        
        if changed_files:
            # Only check changed files
            for f in changed_files:
                ext = Path(f).suffix.lower()
                if ext in ext_to_lang:
                    languages.add(ext_to_lang[ext])
        else:
            # Scan entire repo
            for root, dirs, files in os.walk(repo_path):
                # Skip common non-source directories
                dirs[:] = [d for d in dirs if d not in {'.git', 'node_modules', 'venv', '__pycache__', 'build', 'dist'}]
                
                for f in files:
                    ext = Path(f).suffix.lower()
                    if ext in ext_to_lang:
                        languages.add(ext_to_lang[ext])
        
        return languages
    
    def _run_flake8(self, repo_path: str) -> dict:
        """Run Flake8 for Python files."""
        try:
            cmd = [sys.executable, "-m", "flake8", ".", "--format=json", "--max-line-length=120"]
            result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, timeout=60)
            
            output = result.stdout.strip()
            if not output:
                return {"summary": "No Python lint issues", "details": []}
            
            try:
                data = json.loads(output)
            except json.JSONDecodeError:
                # Try to find JSON in output
                start_idx = output.find('{')
                if start_idx != -1:
                    try:
                        data = json.loads(output[start_idx:])
                    except:
                        return {"summary": "Flake8 parse error", "details": []}
                else:
                    return {"summary": "No JSON output", "details": []}
            
            issues = []
            for filename, violations in data.items():
                for v in violations:
                    issues.append({
                        "file": filename,
                        "line": v.get("line", 0),
                        "code": v.get("code", ""),
                        "message": v.get("text", ""),
                        "language": "python"
                    })
            
            return {"summary": f"Found {len(issues)} Python issues", "details": issues[:20]}
            
        except subprocess.TimeoutExpired:
            return {"error": "Flake8 timeout"}
        except Exception as e:
            return {"error": str(e)}
    
    def _run_eslint(self, repo_path: str) -> dict:
        """Run ESLint for JavaScript/TypeScript files."""
        try:
            # Check if eslint exists
            eslint_path = os.path.join(repo_path, "node_modules", ".bin", "eslint")
            if os.name == 'nt':  # Windows
                eslint_path = os.path.join(repo_path, "node_modules", ".bin", "eslint.cmd")
            
            if os.path.exists(eslint_path):
                cmd = [eslint_path, ".", "--format=json", "--ext", ".js,.jsx,.ts,.tsx"]
            else:
                # Try global npx
                cmd = ["npx", "eslint", ".", "--format=json", "--ext", ".js,.jsx,.ts,.tsx"]
            
            result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, timeout=120)
            
            output = result.stdout.strip()
            if not output:
                return {"summary": "No JS/TS lint issues", "details": []}
            
            try:
                data = json.loads(output)
            except json.JSONDecodeError:
                return {"summary": "ESLint parse error", "details": []}
            
            issues = []
            for file_result in data:
                filepath = file_result.get("filePath", "")
                for msg in file_result.get("messages", []):
                    issues.append({
                        "file": filepath,
                        "line": msg.get("line", 0),
                        "code": msg.get("ruleId", ""),
                        "message": msg.get("message", ""),
                        "severity": "error" if msg.get("severity") == 2 else "warning",
                        "language": "javascript"
                    })
            
            return {"summary": f"Found {len(issues)} JS/TS issues", "details": issues[:20]}
            
        except subprocess.TimeoutExpired:
            return {"error": "ESLint timeout"}
        except FileNotFoundError:
            return {"summary": "ESLint not installed", "details": []}
        except Exception as e:
            return {"error": str(e)}
    
    def _run_checkstyle(self, repo_path: str) -> dict:
        """Run Checkstyle for Java files."""
        try:
            # Look for checkstyle jar or use Maven/Gradle
            cmd = ["mvn", "checkstyle:check", "-Dcheckstyle.output.format=json"]
            
            result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, timeout=180)
            
            # Parse Maven Checkstyle output (usually XML, convert to our format)
            issues = []
            
            # Fallback: Try using checkstyle directly if available
            if result.returncode != 0:
                # Try direct checkstyle
                try:
                    cmd = ["checkstyle", "-c", "/google_checks.xml", "-f", "json", "."]
                    result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, timeout=120)
                    
                    if result.stdout:
                        data = json.loads(result.stdout)
                        for file_result in data:
                            for error in file_result.get("errors", []):
                                issues.append({
                                    "file": file_result.get("filename", ""),
                                    "line": error.get("line", 0),
                                    "code": error.get("source", "").split(".")[-1],
                                    "message": error.get("message", ""),
                                    "language": "java"
                                })
                except:
                    pass
            
            return {"summary": f"Found {len(issues)} Java issues", "details": issues[:20]}
            
        except subprocess.TimeoutExpired:
            return {"error": "Checkstyle timeout"}
        except FileNotFoundError:
            return {"summary": "Checkstyle/Maven not available", "details": []}
        except Exception as e:
            return {"error": str(e)}
    
    def _run_cppcheck(self, repo_path: str) -> dict:
        """Run cppcheck for C/C++ files."""
        try:
            cmd = [
                "cppcheck",
                "--enable=all",
                "--template={file}:{line}:{severity}:{message}",
                "."
            ]
            
            result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, timeout=180)
            
            issues = []
            
            # cppcheck outputs to stderr in template format
            output = result.stderr if result.stderr else result.stdout
            
            if output:
                # Parse cppcheck output (line by line for template output)
                import re
                for line in output.split('\n'):
                    if line.strip():
                        # Parse text format: file:line:severity:message
                        match = re.match(r'(.+):(\d+):(\w+):(.+)', line)
                        if match:
                            issues.append({
                                "file": match.group(1),
                                "line": int(match.group(2)),
                                "code": match.group(3),
                                "message": match.group(4),
                                "language": "cpp"
                            })
            
            return {"summary": f"Found {len(issues)} C/C++ issues", "details": issues[:20]}
            
        except subprocess.TimeoutExpired:
            return {"error": "cppcheck timeout"}
        except FileNotFoundError:
            return {"summary": "cppcheck not installed", "details": []}
        except Exception as e:
            return {"error": str(e)}