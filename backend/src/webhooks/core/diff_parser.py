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
