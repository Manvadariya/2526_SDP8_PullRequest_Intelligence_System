#!/usr/bin/env bash
# ───────────────────────────────────────────────────────────
# run_checks.sh  –  Entrypoint for the PR analysis container
#
# Mount points expected by the caller:
#   /workspace   –  cloned repo (read-only)
#   /results     –  output directory (read-write)
#
# Outputs:
#   /results/lint.json      –  combined linting results
#   /results/security.json  –  bandit security scan results
# ───────────────────────────────────────────────────────────
set -uo pipefail

WORKSPACE="${1:-/workspace}"
RESULTS="${2:-/results}"

mkdir -p "$RESULTS"

# Delegate all heavy lifting to a Python script for reliable JSON handling
python3 - "$WORKSPACE" "$RESULTS" <<'PYTHON_SCRIPT'
import sys, os, json, subprocess, re
from pathlib import Path

WORKSPACE = sys.argv[1]
RESULTS   = sys.argv[2]

# ── Helper: detect languages ─────────────────────────────
EXT_MAP = {
    '.py': 'python',
    '.js': 'javascript', '.jsx': 'javascript',
    '.ts': 'typescript', '.tsx': 'typescript',
    '.c': 'cpp', '.cpp': 'cpp', '.cc': 'cpp',
    '.cxx': 'cpp', '.h': 'cpp', '.hpp': 'cpp',
    '.java': 'java',
}
SKIP_DIRS = {'.git', 'node_modules', 'venv', '__pycache__', 'build', 'dist'}

def detect_languages():
    langs = set()
    for root, dirs, files in os.walk(WORKSPACE):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            ext = Path(f).suffix.lower()
            if ext in EXT_MAP:
                langs.add(EXT_MAP[ext])
    return langs

languages = detect_languages()
print(f"🔍 Detected languages: {languages or 'none'}")

# ── 1. Linting ────────────────────────────────────────────
all_lint_issues = []

# ── Python (flake8) ──
if 'python' in languages:
    print("  📝 Running flake8...")
    try:
        r = subprocess.run(
            [sys.executable, "-m", "flake8", ".", "--format=json",
             "--max-line-length=120",
             "--exclude=.git,node_modules,venv,__pycache__,build,dist"],
            cwd=WORKSPACE, capture_output=True, text=True, timeout=60
        )
        if r.stdout.strip():
            try:
                data = json.loads(r.stdout)
                for fname, violations in data.items():
                    for v in violations:
                        all_lint_issues.append({
                            "file": fname,
                            "line": v.get("line_number", v.get("line", 0)),
                            "code": v.get("code", ""),
                            "message": v.get("text", v.get("message", "")),
                            "language": "python"
                        })
                print(f"    Found {len(all_lint_issues)} Python issues")
            except json.JSONDecodeError:
                print("    ⚠️ flake8 JSON parse error")
        else:
            print("    No Python issues")
    except subprocess.TimeoutExpired:
        print("    ⏰ flake8 timed out")
    except Exception as e:
        print(f"    ⚠️ flake8 error: {e}")

# ── JavaScript / TypeScript (eslint) ──
if 'javascript' in languages or 'typescript' in languages:
    print("  📝 Running eslint...")
    try:
        r = subprocess.run(
            ["eslint", ".", "--format=json",
             "--ext", ".js,.jsx,.ts,.tsx",
             "--no-eslintrc",
             "--rule", '{"no-unused-vars":"warn","no-undef":"error","semi":"warn"}'],
            cwd=WORKSPACE, capture_output=True, text=True, timeout=120
        )
        if r.stdout.strip():
            try:
                data = json.loads(r.stdout)
                js_count = 0
                for f_result in data:
                    for msg in f_result.get("messages", []):
                        all_lint_issues.append({
                            "file": f_result.get("filePath", ""),
                            "line": msg.get("line", 0),
                            "code": msg.get("ruleId", ""),
                            "message": msg.get("message", ""),
                            "severity": "error" if msg.get("severity") == 2 else "warning",
                            "language": "javascript"
                        })
                        js_count += 1
                print(f"    Found {js_count} JS/TS issues")
            except json.JSONDecodeError:
                print("    ⚠️ eslint JSON parse error")
        else:
            print("    No JS/TS issues")
    except FileNotFoundError:
        print("    ⚠️ eslint not found")
    except subprocess.TimeoutExpired:
        print("    ⏰ eslint timed out")
    except Exception as e:
        print(f"    ⚠️ eslint error: {e}")

# ── C/C++ (cppcheck) ──
if 'cpp' in languages:
    print("  📝 Running cppcheck...")
    try:
        r = subprocess.run(
            ["cppcheck", "--enable=all",
             "--template={file}:{line}:{severity}:{message}",
             "--suppress=missingIncludeSystem", "."],
            cwd=WORKSPACE, capture_output=True, text=True, timeout=180
        )
        output = r.stderr or r.stdout  # cppcheck writes to stderr
        if output:
            cpp_count = 0
            for line in output.split('\n'):
                line = line.strip()
                m = re.match(r'(.+):(\d+):(\w+):(.+)', line)
                if m:
                    all_lint_issues.append({
                        "file": m.group(1),
                        "line": int(m.group(2)),
                        "code": m.group(3),
                        "message": m.group(4),
                        "language": "cpp"
                    })
                    cpp_count += 1
            print(f"    Found {cpp_count} C/C++ issues")
    except FileNotFoundError:
        print("    ⚠️ cppcheck not found")
    except subprocess.TimeoutExpired:
        print("    ⏰ cppcheck timed out")
    except Exception as e:
        print(f"    ⚠️ cppcheck error: {e}")

# Truncate to top 20 issues and write
lint_result = {
    "summary": f"Found {len(all_lint_issues)} lint issues",
    "details": all_lint_issues[:20]
}
with open(os.path.join(RESULTS, "lint.json"), "w") as f:
    json.dump(lint_result, f, indent=2)
print(f"📄 Lint results: {lint_result['summary']}")


# ── 2. Security scan (bandit) ─────────────────────────────
sec_result = {"summary": "No Security Issues Found", "details": []}

if 'python' in languages:
    print("🛡️ Running bandit security scan...")
    try:
        r = subprocess.run(
            [sys.executable, "-m", "bandit", "-r", ".", "-f", "json", "-ll",
             "--exclude", ".git,node_modules,venv,__pycache__"],
            cwd=WORKSPACE, capture_output=True, text=True, timeout=120
        )
        if r.stdout.strip():
            try:
                data = json.loads(r.stdout)
                issues = []
                for item in data.get("results", []):
                    issues.append({
                        "file": item["filename"],
                        "line": item["line_number"],
                        "severity": item["issue_severity"],
                        "message": item["issue_text"],
                        "more_info": item["more_info"]
                    })
                sec_result = {
                    "summary": f"Found {len(issues)} security issues" if issues else "No Security Issues Found",
                    "details": issues
                }
                print(f"    {sec_result['summary']}")
            except (json.JSONDecodeError, KeyError) as e:
                print(f"    ⚠️ bandit parse error: {e}")
    except FileNotFoundError:
        print("    ⚠️ bandit not found")
    except subprocess.TimeoutExpired:
        print("    ⏰ bandit timed out")
    except Exception as e:
        print(f"    ⚠️ bandit error: {e}")
else:
    print("🛡️ Skipping bandit (no Python files)")

with open(os.path.join(RESULTS, "security.json"), "w") as f:
    json.dump(sec_result, f, indent=2)

print(f"\n✅ All checks complete. Results written to {RESULTS}/")
PYTHON_SCRIPT

echo ""
echo "📁 Results directory:"
ls -la "$RESULTS/"
