
import json
import os

class FeedbackManager:
    """
    Manages user feedback loops to improve the agent over time.
    Logs "false positives" and provides negative constraints to the LLM.
    """
    def __init__(self, log_file: str = "feedback_log.json"):
        # Store in the same directory as this file for simplicity in this project
        self.log_path = os.path.join(os.path.dirname(__file__), log_file)
        self._ensure_log_exists()

    def _ensure_log_exists(self):
        if not os.path.exists(self.log_path):
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def log_feedback(self, file_path: str, line: int, comment_body: str, user_feedback: str):
        """
        Logs negative feedback (False Positive).
        """
        if "false positive" in user_feedback.lower() or "wrong" in user_feedback.lower():
            entry = {
                "file": file_path,
                "line": line,
                "original_comment": comment_body,
                "user_feedback": user_feedback,
                "type": "false_positive"
            }
            
            try:
                with open(self.log_path, "r+", encoding="utf-8") as f:
                    data = json.load(f)
                    data.append(entry)
                    f.seek(0)
                    json.dump(data, f, indent=2)
            except Exception as e:
                print(f"⚠️ Failed to log feedback: {e}")

    def get_negative_constraints(self) -> str:
        """
        Returns a prompt string summarizing previous mistakes.
        """
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if not data:
                return ""
                
            # Naive summary: just count or list specific files. 
            # In a real system, we'd use semantic search or clustering.
            # For now, let's just say "Be careful with these files..."
            
            false_positives = [e for e in data if e.get("type") == "false_positive"]
            if not false_positives:
                return ""
                
            # Construct a simple constraint message
            # "Users have flagged 3 false positives in 'auth.py'. Be extra conservative."
            files = set(e["file"] for e in false_positives)
            return f"\n\n> ⚠️ **FEEDBACK HISTORY**: Users have previously flagged valid code as errors in these files: {', '.join(files)}. Be extremely conservative when reviewing them."
            
        except Exception:
            return ""
