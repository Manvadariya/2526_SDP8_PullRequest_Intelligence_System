"""
Summary Builder — generates the DeepSource-style PR Report Card block.

This rich HTML block sits ABOVE the Walkthrough dropdown and displays:
  - Overall Grade badge + branding header
  - PR Report Card with grades for Security, Reliability, Complexity, Hygiene
  - Code Review Summary table showing per-language analyzer status
"""

from datetime import datetime, timezone
from typing import Dict, List, Any


# ═══════════════════════════════════════════════════════════════
# GRADE BADGE CONFIG
# ═══════════════════════════════════════════════════════════════

# shields.io badges for grades (works in GitHub dark/light mode)
GRADE_BADGES = {
    "A": "https://img.shields.io/badge/Grade-A-brightgreen?style=flat-square&labelColor=2d333b",
    "B": "https://img.shields.io/badge/Grade-B-green?style=flat-square&labelColor=2d333b",
    "C": "https://img.shields.io/badge/Grade-C-yellow?style=flat-square&labelColor=2d333b",
    "D": "https://img.shields.io/badge/Grade-D-orange?style=flat-square&labelColor=2d333b",
    "F": "https://img.shields.io/badge/Grade-F-red?style=flat-square&labelColor=2d333b",
}

GRADE_BADGE_SMALL = {
    "A": "https://img.shields.io/badge/-A-brightgreen?style=flat-square",
    "B": "https://img.shields.io/badge/-B-green?style=flat-square",
    "C": "https://img.shields.io/badge/-C-yellow?style=flat-square",
    "D": "https://img.shields.io/badge/-D-orange?style=flat-square",
    "F": "https://img.shields.io/badge/-F-red?style=flat-square",
}

STATUS_BADGES = {
    "passed": "https://img.shields.io/badge/-Passed-brightgreen?style=flat-square",
    "failed": "https://img.shields.io/badge/-Issues_Found-red?style=flat-square",
    "warning": "https://img.shields.io/badge/-Warnings-yellow?style=flat-square",
    "skipped": "https://img.shields.io/badge/-Skipped-lightgrey?style=flat-square",
}

# Language name mapping
LANG_NAMES = {
    'py': 'Python', 'js': 'JavaScript', 'ts': 'TypeScript', 'java': 'Java',
    'cpp': 'C++', 'c': 'C', 'go': 'Go', 'rs': 'Rust', 'rb': 'Ruby',
    'php': 'PHP', 'cs': 'C#', 'yml': 'YAML', 'yaml': 'YAML', 'json': 'JSON',
    'sql': 'SQL', 'html': 'HTML', 'css': 'CSS', 'jsx': 'React JSX',
    'tsx': 'React TSX', 'md': 'Markdown', 'sh': 'Shell', 'bash': 'Shell',
    'dockerfile': 'Docker', 'xml': 'XML', 'kt': 'Kotlin', 'swift': 'Swift',
    'r': 'R', 'dart': 'Dart', 'vue': 'Vue', 'svelte': 'Svelte',
}


def compute_grade(score: float) -> str:
    """Convert a 0-100 score to a letter grade."""
    if score >= 90:
        return "A"
    elif score >= 75:
        return "B"
    elif score >= 60:
        return "C"
    elif score >= 40:
        return "D"
    else:
        return "F"


def compute_grades_from_review(
    inline_comments: list,
    nitpicks: dict,
    clean_files: list,
    all_files: list,
    all_raw_findings: dict,
    lint_results: dict = None,
    sec_results: dict = None,
    verdict: str = "COMMENT",
) -> Dict[str, str]:
    """
    Compute letter grades for each category from review data.
    Returns: {"overall": "B", "security": "A", "reliability": "C", "complexity": "B", "hygiene": "C"}
    """
    total_files = max(len(all_files), 1)
    total_actionable = len(inline_comments)
    total_nitpicks = sum(len(v) for v in nitpicks.values())

    # -- Security grade --
    security_issues = 0
    for fp, findings in all_raw_findings.items():
        for f in findings:
            if isinstance(f, dict):
                cat = str(f.get("category", "")).upper()
                if cat == "SECURITY":
                    security_issues += 1
    if sec_results and sec_results.get("details"):
        security_issues += len(sec_results["details"])

    if security_issues == 0:
        security_grade = "A"
    elif security_issues <= 1:
        security_grade = "B"
    elif security_issues <= 3:
        security_grade = "C"
    elif security_issues <= 5:
        security_grade = "D"
    else:
        security_grade = "F"

    # -- Reliability grade (based on actionable issues ratio) --
    if total_actionable == 0:
        reliability_score = 100
    else:
        reliability_score = max(0, 100 - (total_actionable / total_files) * 30)
    reliability_grade = compute_grade(reliability_score)

    # Penalize for critical findings
    critical_count = 0
    for fp, findings in all_raw_findings.items():
        for f in findings:
            if isinstance(f, dict) and str(f.get("severity", "")).upper() == "CRITICAL":
                critical_count += 1
    if critical_count > 0:
        # Drop at least one grade for criticals
        grade_order = ["A", "B", "C", "D", "F"]
        idx = grade_order.index(reliability_grade) if reliability_grade in grade_order else 0
        reliability_grade = grade_order[min(idx + critical_count, 4)]

    # -- Complexity grade (based on file count and finding density) --
    if total_files <= 3:
        complexity_score = 90
    elif total_files <= 8:
        complexity_score = 75
    elif total_files <= 15:
        complexity_score = 60
    else:
        complexity_score = 45
    complexity_grade = compute_grade(complexity_score)

    # -- Hygiene grade (based on nitpicks and lint) --
    lint_count = 0
    if lint_results and lint_results.get("details"):
        lint_count = len(lint_results["details"])

    hygiene_issues = total_nitpicks + lint_count
    if hygiene_issues == 0:
        hygiene_score = 100
    elif hygiene_issues <= 3:
        hygiene_score = 80
    elif hygiene_issues <= 8:
        hygiene_score = 60
    elif hygiene_issues <= 15:
        hygiene_score = 40
    else:
        hygiene_score = 25
    hygiene_grade = compute_grade(hygiene_score)

    # -- Overall grade (weighted average) --
    grade_to_score = {"A": 95, "B": 80, "C": 65, "D": 45, "F": 25}
    overall_score = (
        grade_to_score.get(security_grade, 50) * 0.35
        + grade_to_score.get(reliability_grade, 50) * 0.30
        + grade_to_score.get(complexity_grade, 50) * 0.15
        + grade_to_score.get(hygiene_grade, 50) * 0.20
    )
    overall_grade = compute_grade(overall_score)

    # Determine focus area (lowest grade)
    grades = {
        "Security": security_grade,
        "Reliability": reliability_grade,
        "Complexity": complexity_grade,
        "Hygiene": hygiene_grade,
    }
    focus_area = min(grades, key=lambda k: grade_to_score.get(grades[k], 50))

    return {
        "overall": overall_grade,
        "security": security_grade,
        "reliability": reliability_grade,
        "complexity": complexity_grade,
        "hygiene": hygiene_grade,
        "focus_area": focus_area,
    }


def detect_languages(all_files: list) -> List[str]:
    """Detect unique languages from file list."""
    seen = set()
    languages = []
    for fp in all_files:
        ext = fp.rsplit('.', 1)[-1].lower() if '.' in fp else ''
        # Special case for Dockerfile
        if 'dockerfile' in fp.lower():
            ext = 'dockerfile'
        lang = LANG_NAMES.get(ext, '')
        if lang and lang not in seen:
            seen.add(lang)
            languages.append(lang)
    return languages


def build_report_card_block(
    repo_full_name: str,
    pr_number: int,
    commit_sha: str,
    inline_comments: list,
    nitpicks: dict,
    clean_files: list,
    all_files: list,
    all_raw_findings: dict,
    lint_results: dict = None,
    sec_results: dict = None,
    verdict: str = "COMMENT",
) -> str:
    """
    Build the DeepSource-style PR Report Card HTML block.
    This goes ABOVE the Walkthrough dropdown.
    """
    # Compute grades
    grades = compute_grades_from_review(
        inline_comments=inline_comments,
        nitpicks=nitpicks,
        clean_files=clean_files,
        all_files=all_files,
        all_raw_findings=all_raw_findings,
        lint_results=lint_results,
        sec_results=sec_results,
        verdict=verdict,
    )

    overall_grade = grades["overall"]
    pr_url = f"https://github.com/{repo_full_name}/pull/{pr_number}"
    now_utc = datetime.now(timezone.utc).strftime("%b %d, %Y %I:%M %p")

    # ── Header ──
    block = f'<h2><img src="{GRADE_BADGES[overall_grade]}" height="20" align="right"/>'
    block += '<span>AgenticPR Code Review</span></h2>\n\n'

    # ── Summary paragraph ──
    block += f'<p>We reviewed changes in <code>{commit_sha[:7]}</code> on this pull request. '
    block += 'Below is the summary for the review, and you can see the individual issues we found as inline review comments.</p>\n\n'
    block += f'<p><a href="{pr_url}">View pull request</a>&nbsp;↗</p>\n\n'

    # ── Important note ──
    total_actionable = len(inline_comments)
    total_nitpick = sum(len(v) for v in nitpicks.values())
    if total_nitpick > 0:
        block += '> [!IMPORTANT]\n'
        block += f'> {total_nitpick} nitpick comment(s) are included in the review body below and are not shown as inline comments.\n\n'

    # ── PR Report Card ──
    block += '<h3>PR Report Card</h3>\n'
    block += '<table>\n<tr>\n'

    # Left column: Overall Grade + Focus Area
    block += '<td width="375px" valign="top">\n'
    block += f'<strong>Overall Grade</strong>&nbsp;&nbsp;'
    block += f'<img src="{GRADE_BADGE_SMALL[overall_grade]}" height="16" align="right"/>\n'
    block += f'<br/><br/><strong>Focus Area:</strong> {grades["focus_area"]}\n'
    block += '</td>\n'

    # Right column: Category grades
    block += '<td width="375px" valign="top">\n'
    for category in ["Security", "Reliability", "Complexity", "Hygiene"]:
        g = grades[category.lower()]
        block += f'<strong>{category}</strong>&nbsp;&nbsp;'
        block += f'<img src="{GRADE_BADGE_SMALL[g]}" height="16" align="right"/>\n'
        block += '<br/><br/>'
    block += '\n</td>\n'
    block += '</tr>\n</table>\n\n'

    # ── Code Review Summary Table ──
    languages = detect_languages(all_files)

    # Build per-language status from findings
    lang_status = {}
    for fp, findings in all_raw_findings.items():
        ext = fp.rsplit('.', 1)[-1].lower() if '.' in fp else ''
        if 'dockerfile' in fp.lower():
            ext = 'dockerfile'
        lang = LANG_NAMES.get(ext, '')
        if lang:
            actionable = [f for f in findings if isinstance(f, dict) and f.get("type") != "nitpick"]
            if actionable:
                lang_status[lang] = "failed"
            elif lang not in lang_status:
                lang_status[lang] = "passed"

    # Mark clean languages
    for lang in languages:
        if lang not in lang_status:
            lang_status[lang] = "passed"

    # Add security scanner row
    if sec_results:
        if sec_results.get("details"):
            lang_status["Secrets Scanner"] = "failed"
        elif sec_results.get("error"):
            lang_status["Secrets Scanner"] = "skipped"
        else:
            lang_status["Secrets Scanner"] = "passed"
        if "Secrets Scanner" not in languages:
            languages.append("Secrets Scanner")

    block += '<h3>Code Review Summary</h3>\n'
    block += '<table width="100%">\n'
    block += '<thead>\n<tr>\n'
    block += '<th width="200px" align="left">Analyzer</th>\n'
    block += '<th width="150px">Status</th>\n'
    block += '<th width="250px">Updated (UTC)</th>\n'
    block += '<th width="150px" align="center">Details</th>\n'
    block += '</tr>\n</thead>\n'
    block += '<tbody>\n'

    for lang in languages:
        status = lang_status.get(lang, "passed")
        badge_url = STATUS_BADGES.get(status, STATUS_BADGES["passed"])
        block += '<tr>\n'
        block += f'<td><strong>{lang}</strong></td>\n'
        block += f'<td align="center"><img src="{badge_url}" height="20"/></td>\n'
        block += f'<td align="center">{now_utc}</td>\n'
        block += f'<td align="center"><a href="{pr_url}">Review</a>&nbsp;↗</td>\n'
        block += '</tr>'

    block += '\n</tbody>\n</table>\n\n'

    return block
