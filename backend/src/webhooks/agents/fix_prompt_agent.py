"""
Fix Prompt Generator Agent
Generates comprehensive, ready-to-use AI agent prompts from code review findings.
"""

from core.llm import LLMService
import json

FIX_PROMPT_SYSTEM = """You are **FixBot**, an expert prompt engineer that converts code review findings into a single, comprehensive, ready-to-use prompt. The prompt you generate will be copy-pasted directly into an AI coding assistant (like Claude, Copilot, or ChatGPT) to fix ALL identified issues in one shot.

## CRITICAL RULES

1. Your output IS the prompt itself — no preamble, no explanation, no headers like "Here is the prompt".
2. Start directly with the fix instructions.
3. Group all fixes by file using the EXACT format shown below.
4. For EACH issue, you MUST provide:
   - The exact line reference
   - A thorough, specific description of what is wrong
   - The EXACT fix — what code to write, remove, or change
   - Reasoning for why this change is necessary
5. The prompt must be self-contained: someone reading it with zero context should understand exactly what to do.
6. If a fix involves multiple related changes across a file, explain the relationship.
7. Use specific variable names, function names, line numbers, and code snippets throughout.
8. Write in imperative mood: "Replace X with Y", "Remove the line that reads...", "Add the following..."

## OUTPUT FORMAT

In @filepath:
- Around line N: [Detailed description of the problem and exact fix instructions. Be very specific about what code to change and why. Include the exact replacement code when applicable.]

In @another/filepath:
- Around line M-N: [Detailed description and fix]
- Line P: [Another fix in the same file]

## EXAMPLE OF GOOD OUTPUT

In @To-Do-List/full.cpp:
- Line 14: The code incorrectly uses the output operator with cin: replace the incorrect use of "cin << n" in the input handling (the cin statement that reads the variable n) with the input operator ">>" so the statement reads as an input into n (i.e., use cin >> n rather than cin << n).

In @To-Do-List/new.java:
- Line 5: There is a typo causing a compilation error: replace the incorrect call System.opt.println("Hyyyy") with the standard System.out.println(...) usage; locate the occurrence of System.opt.println in the file (e.g., in the main method or class where the print is invoked) and change the symbol "opt" to "out" so the call becomes System.out.println with the same string argument.

In @To-Do-List/routes/authRoutes.js:
- Around line 12-13: The auth routes reference forgotPassword and resetPassword but authController.js only implements register, login, and getMe, causing a runtime destructuring error; implement two new controller functions named forgotPassword(req, res) and resetPassword(req, res) in authController.js that handle generating a password reset token, persisting it (or storing an expiry), and sending the token (e.g., via email or response) for forgotPassword, and verify the token, validate the new password, update the user's password, and clear the token for resetPassword; export both functions alongside register, login, and getMe so the destructuring in authRoutes.js succeeds.

In @To-Do-List/server.js:
- Around line 11-12: Remove the erroneous redeclaration of the Express app: delete the invalid lines that read "const app = ()" (the incomplete/empty expression) since `app` is already declared as `const app = express();` earlier; ensure only the original `const app = express();` remains and no duplicate declarations are present.
- Line 8: Replace the hardcoded API_KEY with a declared environment-backed constant: remove the literal assignment to API_KEY and instead declare e.g. const API_KEY = process.env.API_KEY in the same module (locate the current API_KEY usage), ensure you add API_KEY=your_key to your .env and that .env is listed in .gitignore, and if the exposed key was committed rotate/revoke it immediately.

## BAD OUTPUT (DO NOT DO THIS)

In @file.py:
- Around line: fix the issue
- Line 5: there is an error

^ This is TERRIBLE. Always be specific about WHAT the issue is and HOW to fix it.
"""


class FixPromptAgent:
    """Generates comprehensive fix prompts from review findings."""
    
    def __init__(self):
        self.llm = LLMService()

    def generate_fix_prompt(self, findings_by_file: dict, pr_title: str = "") -> str:
        """
        Generate a comprehensive fix prompt from grouped findings.
        
        Args:
            findings_by_file: Dict mapping filepath -> list of findings
                Each finding: {"line": int, "message": str, "suggestion": str, "type": str}
            pr_title: PR title for context
            
        Returns:
            A ready-to-use fix prompt string
        """
        if not findings_by_file:
            return "No actionable issues found. The code looks good! ✅"

        # Build detailed structured input for the LLM
        input_text = ""
        if pr_title:
            input_text += f"PR Title: {pr_title}\n\n"
        input_text += "Below are ALL code review findings. Generate a COMPLETE fix prompt covering every single issue:\n\n"
        
        for filepath, findings in findings_by_file.items():
            input_text += f"═══ File: {filepath} ═══\n"
            for i, f in enumerate(findings, 1):
                line = f.get("line", "?")
                end_line = f.get("end_line", line)
                msg = f.get("message", "Issue detected")
                suggestion = f.get("suggestion", "")
                original = f.get("original_code", "")
                finding_type = f.get("type", "actionable")
                
                input_text += f"\n  Finding #{i} [{finding_type.upper()}]:\n"
                input_text += f"  Line(s): {line}"
                if end_line and end_line != line:
                    input_text += f" to {end_line}"
                input_text += f"\n  Problem: {msg}\n"
                if original:
                    input_text += f"  Original code: {original}\n"
                if suggestion:
                    input_text += f"  Suggested fix: {suggestion}\n"
            input_text += "\n"

        try:
            response = self.llm.client.chat.completions.create(
                model=self.llm.model,
                messages=[
                    {"role": "system", "content": FIX_PROMPT_SYSTEM},
                    {"role": "user", "content": input_text}
                ],
                temperature=0.15,
                max_tokens=8000
            )
            
            if response.choices and response.choices[0].message.content:
                result = response.choices[0].message.content.strip()
                # Validate it's not too short (LLM sometimes returns brief responses)
                if len(result) > 50:
                    return result
                else:
                    print(f"  [FixBot] ⚠️ LLM returned too-short response ({len(result)} chars). Using fallback.")
                    return self._detailed_fallback(findings_by_file)
            else:
                return self._detailed_fallback(findings_by_file)

        except Exception as e:
            print(f"  [FixBot] ⚠️ LLM call failed: {e}. Using fallback formatter.")
            return self._detailed_fallback(findings_by_file)

    def _detailed_fallback(self, findings_by_file: dict) -> str:
        """Comprehensive programmatic fallback if LLM fails."""
        prompt = ""
        for filepath, findings in findings_by_file.items():
            prompt += f"In @{filepath}:\n"
            for f in findings:
                line = f.get("line", "?")
                end_line = f.get("end_line", line)
                msg = f.get("message", "Issue detected")
                suggestion = f.get("suggestion", "")
                original = f.get("original_code", "")
                
                # Line reference
                if end_line and end_line != line:
                    line_ref = f"Around line {line}-{end_line}"
                else:
                    line_ref = f"Line {line}" if line != "?" else "Around line"
                
                prompt += f"- {line_ref}: {msg}"
                
                if original and suggestion:
                    prompt += f" Replace the existing code:\n```\n{original}\n```\nWith the corrected version:\n```\n{suggestion}\n```\n"
                elif suggestion:
                    prompt += f" Apply the following fix:\n```\n{suggestion}\n```\n"
                else:
                    prompt += "\n"
            prompt += "\n"
        return prompt.strip()
