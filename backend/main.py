import json
import os

from src.pr_service import PullRequestService
from src.diff_parser import DiffService, parse_diff
from src.repo_context import RepositoryContextService

OWNER = "shubham-vaishnav-13"     
REPO = "GitDemo" 

pr_service = PullRequestService(OWNER, REPO)
diff_service = DiffService(OWNER, REPO)

repo_context_service = RepositoryContextService(OWNER, REPO)
context = repo_context_service.fetch_repository_context()

if os.getenv("EXPORT_REPO_CONTEXT_JSON", "0") == "1":
    ai_payload = repo_context_service.build_ai_context_json(
        include_file_contents=True,
        max_total_chars=int(os.getenv("REPO_CONTEXT_MAX_TOTAL_CHARS", "120000")),
        max_file_chars=int(os.getenv("REPO_CONTEXT_MAX_FILE_CHARS", "8000")),
        max_files_with_content=int(os.getenv("REPO_CONTEXT_MAX_FILES", "60")),
        include_tree_entries=int(os.getenv("REPO_CONTEXT_TREE_ENTRIES", "2000")),
    )
    out_path = os.getenv("REPO_CONTEXT_OUT", "repo_context_ai.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(ai_payload, f, indent=2, ensure_ascii=False)
    print(f"\nWrote AI repo context JSON to: {out_path}")

print("\n=== REPOSITORY CONTEXT ===")
print("Repo:", context.get("full_name"))
print("Default branch:", context.get("default_branch"))
print("Topics:", context.get("topics"))
print("Languages:", context.get("languages"))
print("README (preview):")
print((context.get("readme") or "")[:500])
print("File paths (sample):", (context.get("file_paths") or [])[:25])

prs = pr_service.fetch_pull_requests()

print("DEBUG: Number of PRs fetched =", len(prs))

for pr in prs:
    print(f"\nPR #{pr['number']} - {pr['title']}")

    files = diff_service.fetch_pr_files(pr["number"])

    for file in files:
        print(f"\nFile: {file['filename']}")
        added, removed = parse_diff(file.get("patch"))

        print("➕ Added lines:")
        for a in added:
            print(a)

        print("➖ Removed lines:")
        for r in removed:
            print(r)
