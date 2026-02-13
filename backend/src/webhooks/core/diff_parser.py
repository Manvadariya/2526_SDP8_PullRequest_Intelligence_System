import re
from typing import Dict

class DiffParser:
    """Parses unified diff format and extracts per-file changes."""
    
    @staticmethod
    def parse_diff(raw_diff: str) -> Dict[str, str]:
        """
        Splits a unified diff into individual file diffs.
        Returns: {"path/to/file.py": "diff content..."}
        """
        file_diffs = {}
        current_file = None
        current_diff_lines = []
        
        for line in raw_diff.split('\n'):
            # Detect new file header
            if line.startswith('diff --git'):
                # Save previous file
                if current_file:
                    file_diffs[current_file] = '\n'.join(current_diff_lines)
                
                # Extract new filename (e.g., "a/src/app.py b/src/app.py")
                match = re.search(r'b/(.+)$', line)
                if match:
                    current_file = match.group(1)
                    current_diff_lines = [line]
            elif current_file:
                current_diff_lines.append(line)
        
        # Save last file
        if current_file:
            file_diffs[current_file] = '\n'.join(current_diff_lines)
        
        return file_diffs
    
    @staticmethod
    def format_diff_block(diff_content: str, max_context_lines: int = 5) -> str:
        """
        Formats diff into a pretty code block with +/- lines.
        Collapses large deletion blocks with ellipsis.
        """
        lines = diff_content.split('\n')
        formatted_lines = []
        deletion_buffer = []
        
        for line in lines:
            # Skip diff metadata
            if line.startswith('diff --git') or line.startswith('index '):
                continue
            
            # File headers
            if line.startswith('---') or line.startswith('+++'):
                formatted_lines.append(line)
                continue
            
            # Hunk headers
            if line.startswith('@@'):
                # Flush any pending deletions
                if deletion_buffer:
                    if len(deletion_buffer) > max_context_lines:
                        formatted_lines.extend(deletion_buffer[:2])
                        formatted_lines.append(f"... [{len(deletion_buffer)} lines removed] ...")
                        formatted_lines.extend(deletion_buffer[-2:])
                    else:
                        formatted_lines.extend(deletion_buffer)
                    deletion_buffer = []
                
                formatted_lines.append(line)
                continue
            
            # Handle deletions (buffer them)
            if line.startswith('-') and not line.startswith('---'):
                deletion_buffer.append(line)
                continue
            
            # Handle additions and context
            if deletion_buffer:
                # Flush deletion buffer
                if len(deletion_buffer) > max_context_lines:
                    formatted_lines.extend(deletion_buffer[:2])
                    formatted_lines.append(f"... [{len(deletion_buffer)} lines removed] ...")
                    formatted_lines.extend(deletion_buffer[-2:])
                else:
                    formatted_lines.extend(deletion_buffer)
                deletion_buffer = []
            
            formatted_lines.append(line)
        
        # Final flush
        if deletion_buffer:
            if len(deletion_buffer) > max_context_lines:
                formatted_lines.extend(deletion_buffer[:2])
                formatted_lines.append(f"... [{len(deletion_buffer)} lines removed] ...")
                formatted_lines.extend(deletion_buffer[-2:])
            else:
                formatted_lines.extend(deletion_buffer)
        
        return '\n'.join(formatted_lines)

    @staticmethod
    def annotate_diff_with_line_numbers(file_diff: str) -> str:
        """
        Annotates a single file's diff with new-side line numbers (Lxx).
        This helps the LLM reference exact line numbers for inline comments.
        """
        lines = file_diff.split('\n')
        annotated = []
        new_line = 0

        for line in lines:
            if line.startswith('@@'):
                match = re.search(r'\+(\d+)', line)
                if match:
                    new_line = int(match.group(1))
                annotated.append(line)
            elif line.startswith('+++') or line.startswith('---') or line.startswith('diff --git') or line.startswith('index '):
                annotated.append(line)
            elif line.startswith('+'):
                annotated.append(f"L{new_line:>4} {line}")
                new_line += 1
            elif line.startswith('-'):
                annotated.append(f"      {line}")  # No new-side line number for deletions
            else:
                # Context line
                if new_line > 0:
                    annotated.append(f"L{new_line:>4} {line}")
                    new_line += 1
                else:
                    annotated.append(line)

        return '\n'.join(annotated)

    @staticmethod
    def get_valid_right_lines(file_diff: str) -> set:
        """
        Returns all line numbers visible on the RIGHT side of the diff.
        These are the only valid positions for inline review comments.
        """
        lines = file_diff.split('\n')
        valid = set()
        new_line = 0

        for line in lines:
            if line.startswith('@@'):
                match = re.search(r'\+(\d+)', line)
                if match:
                    new_line = int(match.group(1))
            elif line.startswith('+++') or line.startswith('---') or line.startswith('diff --git') or line.startswith('index '):
                continue
            elif line.startswith('+'):
                valid.add(new_line)
                new_line += 1
            elif line.startswith('-'):
                pass  # Deletions don't consume new-side line numbers
            else:
                if new_line > 0:
                    valid.add(new_line)
                    new_line += 1

        return valid
