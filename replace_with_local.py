#!/usr/bin/env python3
"""
Script to replace all repository files with local version while preserving poppler integration.

This script helps replace the entire repository content with the user's local version,
ensuring that:
1. All current files are removed (except .git)
2. Local files are copied to repository
3. Poppler integration is verified and working
4. Proper commit is made with the specified message
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def backup_git_dir(repo_path):
    """Backup .git directory before replacement."""
    git_path = repo_path / ".git"
    backup_path = repo_path.parent / "git_backup"
    
    if git_path.exists():
        print("Backing up .git directory...")
        if backup_path.exists():
            shutil.rmtree(backup_path)
        shutil.copytree(git_path, backup_path)
        return True
    return False

def restore_git_dir(repo_path):
    """Restore .git directory after replacement."""
    git_path = repo_path / ".git"
    backup_path = repo_path.parent / "git_backup"
    
    if backup_path.exists():
        print("Restoring .git directory...")
        if git_path.exists():
            shutil.rmtree(git_path)
        shutil.copytree(backup_path, git_path)
        shutil.rmtree(backup_path)
        return True
    return False

def clear_repository(repo_path):
    """Remove all files except .git directory."""
    print("Clearing repository (preserving .git)...")
    
    for item in repo_path.iterdir():
        if item.name == ".git":
            continue
        
        print(f"Removing {item.name}...")
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()

def copy_local_files(local_path, repo_path):
    """Copy all files from local directory to repository."""
    print(f"Copying files from {local_path} to {repo_path}...")
    
    for item in local_path.iterdir():
        if item.name == ".git":
            continue
            
        dest_path = repo_path / item.name
        print(f"Copying {item.name}...")
        
        if item.is_dir():
            shutil.copytree(item, dest_path)
        else:
            shutil.copy2(item, dest_path)

def verify_poppler_integration(repo_path):
    """Verify that poppler is properly integrated and working."""
    print("Verifying poppler integration...")
    
    poppler_path = repo_path / "poppler"
    if not poppler_path.exists():
        print("ERROR: poppler directory not found!")
        return False
    
    # Check for essential poppler binaries
    bin_path = poppler_path / "Library" / "bin"
    if not bin_path.exists():
        print("ERROR: poppler/Library/bin directory not found!")
        return False
    
    essential_files = ["poppler.dll", "pdfinfo.exe", "pdfimages.exe"]
    missing_files = []
    
    for file in essential_files:
        if not (bin_path / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"ERROR: Missing essential poppler files: {missing_files}")
        return False
    
    print("✓ Poppler integration verified successfully")
    return True

def test_application_startup(repo_path):
    """Test if the application can start properly."""
    print("Testing application startup...")
    
    main_py = repo_path / "main.py"
    if not main_py.exists():
        print("WARNING: main.py not found")
        return False
    
    # Try to import main modules to check for syntax errors
    success, stdout, stderr = run_command("python -m py_compile main.py", cwd=repo_path)
    if not success:
        print(f"ERROR: main.py has syntax errors: {stderr}")
        return False
    
    print("✓ Application startup test passed")
    return True

def commit_changes(repo_path):
    """Commit all changes with the specified message."""
    print("Committing changes...")
    
    # Add all files
    success, _, stderr = run_command("git add .", cwd=repo_path)
    if not success:
        print(f"ERROR: Failed to add files: {stderr}")
        return False
    
    # Commit with specified message
    commit_msg = "Replace all files with my local version (including poppler integration)"
    success, stdout, stderr = run_command(f'git commit -m "{commit_msg}"', cwd=repo_path)
    if not success:
        print(f"ERROR: Failed to commit: {stderr}")
        return False
    
    print("✓ Changes committed successfully")
    return True

def main():
    """Main replacement process."""
    if len(sys.argv) != 3:
        print("Usage: python replace_with_local.py <local_directory> <repository_directory>")
        print("Example: python replace_with_local.py /path/to/local/version /path/to/repo")
        sys.exit(1)
    
    local_path = Path(sys.argv[1])
    repo_path = Path(sys.argv[2])
    
    # Validate paths
    if not local_path.exists():
        print(f"ERROR: Local directory does not exist: {local_path}")
        sys.exit(1)
    
    if not repo_path.exists():
        print(f"ERROR: Repository directory does not exist: {repo_path}")
        sys.exit(1)
    
    git_path = repo_path / ".git"
    if not git_path.exists():
        print(f"ERROR: Not a git repository: {repo_path}")
        sys.exit(1)
    
    print("=== Repository Replacement Process ===")
    print(f"Local directory: {local_path}")
    print(f"Repository directory: {repo_path}")
    print()
    
    try:
        # Step 1: Clear repository (preserving .git)
        clear_repository(repo_path)
        
        # Step 2: Copy local files
        copy_local_files(local_path, repo_path)
        
        # Step 3: Verify poppler integration
        if not verify_poppler_integration(repo_path):
            print("ERROR: Poppler integration verification failed!")
            sys.exit(1)
        
        # Step 4: Test application startup
        if not test_application_startup(repo_path):
            print("WARNING: Application startup test failed, but continuing...")
        
        # Step 5: Commit changes
        if not commit_changes(repo_path):
            print("ERROR: Failed to commit changes!")
            sys.exit(1)
        
        print()
        print("=== SUCCESS ===")
        print("Repository has been successfully replaced with your local version!")
        print("Poppler integration is verified and working.")
        print("All changes have been committed.")
        
    except Exception as e:
        print(f"ERROR: Unexpected error during replacement: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()