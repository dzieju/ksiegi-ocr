"""
Version and PR information utilities for the application.
"""
import os
import subprocess
import re


def get_git_commit_hash(short=True):
    """Get the current git commit hash."""
    try:
        cmd = ["git", "rev-parse"]
        if short:
            cmd.append("--short")
        cmd.append("HEAD")
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"


def get_pr_number():
    """
    Get PR number from current branch name or latest commit message.
    Looks for patterns like 'pull request #123' or branch names containing PR info.
    """
    try:
        # First try to get PR number from branch name
        result = subprocess.run(["git", "branch", "--show-current"], 
                              capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            branch_name = result.stdout.strip()
            # Look for PR patterns in branch name (e.g., copilot/fix-405ec0f1-...)
            # Extract numbers from branch name that might indicate PR
            numbers = re.findall(r'\d+', branch_name)
            if numbers and len(numbers[0]) > 2:  # Likely a PR number if > 2 digits
                # For now, we'll use a simple heuristic - look for meaningful numbers
                pass
        
        # Try to get PR number from recent commit messages
        result = subprocess.run(["git", "log", "--oneline", "-10"], 
                              capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            commits = result.stdout
            # Look for "pull request #123" or "#123" patterns
            pr_match = re.search(r'(?:pull request #|#)(\d+)', commits, re.IGNORECASE)
            if pr_match:
                return pr_match.group(1)
            
            # Look for "Merge pull request #123"
            merge_match = re.search(r'Merge pull request #(\d+)', commits, re.IGNORECASE)
            if merge_match:
                return merge_match.group(1)
    except Exception:
        pass
    
    return None


def get_program_name():
    """Get the program name."""
    return "Księgi-OCR"


def get_version_info():
    """Get complete version information including program name, PR, and commit."""
    program_name = get_program_name()
    commit_hash = get_git_commit_hash(short=True)
    pr_number = get_pr_number()
    
    info = {
        'program_name': program_name,
        'commit_hash': commit_hash,
        'pr_number': pr_number
    }
    
    return info


def format_title_bar():
    """Format title bar text with program name, PR, and version."""
    info = get_version_info()
    
    title_parts = [info['program_name']]
    
    if info['pr_number']:
        title_parts.append(f"PR#{info['pr_number']}")
    
    if info['commit_hash'] and info['commit_hash'] != "unknown":
        title_parts.append(f"v{info['commit_hash']}")
    
    return " - ".join(title_parts)


def format_system_info():
    """Format system information display text."""
    info = get_version_info()
    
    lines = [
        f"Program: {info['program_name']}",
        f"Commit: {info['commit_hash']}"
    ]
    
    if info['pr_number']:
        lines.insert(1, f"PR Number: #{info['pr_number']}")
    
    # Add GPU/Framework information
    try:
        from tools.gpu_utils import format_gpu_status_text
        gpu_status = format_gpu_status_text()
        lines.append("")  # Empty line separator
        lines.append("=== GPU/AI Framework Status ===")
        lines.extend(gpu_status.split('\n'))
    except Exception as e:
        lines.append("")
        lines.append("=== GPU/AI Framework Status ===")
        lines.append(f"❌ Error getting GPU info: {e}")
    
    return "\n".join(lines)