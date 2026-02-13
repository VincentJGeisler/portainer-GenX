#!/usr/bin/env python3
"""
Portainer GenX Auto-Merge Script

This script automates merging upstream Portainer changes while preserving
the GenX password modification.

Usage:
    python auto-merge.py [--dry-run] [--auto-push]
"""

import subprocess
import sys
import re
import argparse
from datetime import datetime
from pathlib import Path


class Colors:
    """Terminal colors for pretty output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def run_command(cmd, capture=True, check=True):
    """Run a shell command and return output"""
    print(f"{Colors.BLUE}Running: {cmd}{Colors.END}")
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=capture,
        text=True,
        check=check
    )
    if capture:
        return result.stdout.strip()
    return result.returncode == 0


def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")


def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")


def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")


def print_header(msg):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{msg}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")


def check_git_repo():
    """Verify we're in a git repository"""
    try:
        run_command("git rev-parse --git-dir", capture=True)
        return True
    except subprocess.CalledProcessError:
        print_error("Not a git repository!")
        return False


def check_clean_working_tree():
    """Check if working tree is clean"""
    status = run_command("git status --porcelain", capture=True)
    if status:
        print_error("Working tree is not clean. Commit or stash changes first.")
        return False
    return True


def fetch_upstream():
    """Fetch latest changes from upstream"""
    print_header("Fetching Upstream")
    
    # Check if upstream remote exists
    remotes = run_command("git remote", capture=True)
    if 'upstream' not in remotes:
        print_warning("Upstream remote not found. Adding it...")
        run_command("git remote add upstream https://github.com/portainer/portainer.git")
    
    # Fetch upstream
    run_command("git fetch upstream develop")
    print_success("Fetched upstream/develop")
    
    return True


def get_commits_behind():
    """Get number of commits behind upstream"""
    count = run_command("git rev-list --count HEAD..upstream/develop", capture=True)
    return int(count)


def get_current_version():
    """Get current version from tags"""
    try:
        # Get latest tag
        tag = run_command("git describe --tags --abbrev=0", capture=True)
        # Extract version number (e.g., "2.38.1-genx" -> "2.38.1")
        match = re.match(r'(\d+\.\d+\.\d+)', tag)
        if match:
            return match.group(1)
    except:
        pass
    return "2.38.1"  # Default


def get_upstream_version():
    """Get upstream version from their tags"""
    try:
        # Get upstream tags
        tags = run_command("git tag -l --sort=-version:refname --merged upstream/develop", capture=True)
        for tag in tags.split('\n'):
            # Look for version tags (e.g., "2.38.1", "2.39.0")
            match = re.match(r'(\d+\.\d+\.\d+)$', tag.strip())
            if match:
                return match.group(1)
    except:
        pass
    
    # Fallback: check package.json
    try:
        run_command("git show upstream/develop:package.json > /tmp/package.json.tmp")
        with open('/tmp/package.json.tmp', 'r') as f:
            content = f.read()
            match = re.search(r'"version":\s*"(\d+\.\d+\.\d+)"', content)
            if match:
                return match.group(1)
    except:
        pass
    
    return None


def create_merge_branch(version):
    """Create new branch from upstream"""
    print_header("Creating Merge Branch")
    
    branch_name = f"genx-auto-merge-{datetime.now().strftime('%Y%m%d')}"
    
    # Check if branch already exists
    branches = run_command("git branch -a", capture=True)
    if branch_name in branches:
        print_warning(f"Branch {branch_name} already exists. Deleting it...")
        run_command(f"git branch -D {branch_name}", check=False)
    
    # Create new branch from upstream
    run_command(f"git checkout -b {branch_name} upstream/develop")
    print_success(f"Created branch: {branch_name}")
    
    return branch_name


def apply_password_modification():
    """Apply the GenX password modification"""
    print_header("Applying GenX Password Modification")
    
    init_file = Path("api/datastore/init.go")
    
    if not init_file.exists():
        print_error(f"File not found: {init_file}")
        return False
    
    # Read file
    content = init_file.read_text()
    
    # Replace password length
    original = "RequiredPasswordLength: 12,"
    modified = "RequiredPasswordLength: 1,"
    
    if original not in content:
        print_warning("Password length not found at expected value (12). Checking current value...")
        # Try to find any RequiredPasswordLength setting
        match = re.search(r'RequiredPasswordLength:\s*(\d+)', content)
        if match:
            current_value = match.group(1)
            if current_value == "1":
                print_warning("Password length already set to 1!")
                return True
            else:
                print_warning(f"Found RequiredPasswordLength: {current_value}. Changing to 1...")
                content = re.sub(
                    r'RequiredPasswordLength:\s*\d+',
                    'RequiredPasswordLength: 1',
                    content
                )
        else:
            print_error("Could not find RequiredPasswordLength in file!")
            return False
    else:
        content = content.replace(original, modified)
    
    # Write back
    init_file.write_text(content)
    print_success("Applied password modification: 12 → 1")
    
    return True


def commit_changes(version):
    """Commit the password modification"""
    print_header("Committing Changes")
    
    run_command("git add api/datastore/init.go")
    
    commit_msg = f"""feat(genx): apply password relaxation to upstream v{version}

Reduces RequiredPasswordLength from 12 to 1 to support simple passwords
in development, home lab, and personal environments where complex
password requirements are not necessary.

This automated merge syncs with upstream Portainer v{version}.

SECURITY NOTE: Use strong passwords in production environments.

Changes:
- api/datastore/init.go: RequiredPasswordLength 12 -> 1"""
    
    run_command(f'git commit -m "{commit_msg}"')
    print_success("Committed changes")
    
    return True


def create_tag(version):
    """Create a version tag"""
    print_header("Creating Tag")
    
    tag_name = f"{version}-genx"
    
    # Check if tag exists
    tags = run_command("git tag -l", capture=True)
    if tag_name in tags:
        print_warning(f"Tag {tag_name} already exists!")
        response = input("Delete and recreate? (y/N): ")
        if response.lower() == 'y':
            run_command(f"git tag -d {tag_name}")
        else:
            return tag_name
    
    tag_msg = f"""Portainer GenX v{version}

Synced with upstream Portainer v{version}.

GenX Changes:
- Minimum password length: 1 character (vs 12 in upstream)
- Perfect for home labs, dev environments, and personal use

Automated merge on {datetime.now().strftime('%Y-%m-%d')}."""
    
    run_command(f'git tag -a {tag_name} -m "{tag_msg}"')
    print_success(f"Created tag: {tag_name}")
    
    return tag_name


def push_changes(branch_name, tag_name, force=False):
    """Push branch and tag to origin"""
    print_header("Pushing to GitHub")
    
    force_flag = "--force-with-lease" if force else ""
    
    # Push branch
    run_command(f"git push origin {branch_name}:develop {force_flag}")
    print_success("Pushed branch to develop")
    
    # Push tag
    run_command(f"git push origin {tag_name}")
    print_success(f"Pushed tag: {tag_name}")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Auto-merge upstream Portainer with GenX modifications"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Run without pushing changes"
    )
    parser.add_argument(
        '--auto-push',
        action='store_true',
        help="Automatically push without confirmation"
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help="Force push (use with caution!)"
    )
    
    args = parser.parse_args()
    
    print_header("Portainer GenX Auto-Merge")
    print("This script will merge upstream Portainer with GenX modifications")
    
    # Pre-flight checks
    if not check_git_repo():
        sys.exit(1)
    
    if not check_clean_working_tree():
        sys.exit(1)
    
    # Fetch upstream
    if not fetch_upstream():
        sys.exit(1)
    
    # Check if we're behind
    commits_behind = get_commits_behind()
    if commits_behind == 0:
        print_success("Already up-to-date with upstream!")
        sys.exit(0)
    
    print_warning(f"Currently {commits_behind} commits behind upstream")
    
    # Get versions
    current_version = get_current_version()
    upstream_version = get_upstream_version()
    
    if upstream_version:
        print(f"Current version: {current_version}")
        print(f"Upstream version: {upstream_version}")
        version = upstream_version
    else:
        print_warning("Could not determine upstream version, using current")
        version = current_version
    
    # Confirm
    if not args.auto_push and not args.dry_run:
        response = input(f"\nMerge {commits_behind} commits from upstream? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)
    
    # Create merge branch
    branch_name = create_merge_branch(version)
    
    # Apply password modification
    if not apply_password_modification():
        print_error("Failed to apply password modification!")
        sys.exit(1)
    
    # Commit
    if not commit_changes(version):
        print_error("Failed to commit changes!")
        sys.exit(1)
    
    # Create tag
    tag_name = create_tag(version)
    
    # Show diff
    print_header("Changes Summary")
    run_command("git diff upstream/develop HEAD -- api/datastore/init.go", capture=False)
    
    if args.dry_run:
        print_warning("\nDry run mode - not pushing changes")
        print(f"Branch: {branch_name}")
        print(f"Tag: {tag_name}")
        print("\nTo push manually:")
        print(f"  git push origin {branch_name}:develop --force-with-lease")
        print(f"  git push origin {tag_name}")
        sys.exit(0)
    
    # Push
    if args.auto_push:
        push_changes(branch_name, tag_name, force=args.force)
    else:
        response = input("\nPush changes to GitHub? (y/N): ")
        if response.lower() == 'y':
            push_changes(branch_name, tag_name, force=args.force)
        else:
            print("Not pushed. You can push manually with:")
            print(f"  git push origin {branch_name}:develop --force-with-lease")
            print(f"  git push origin {tag_name}")
    
    print_header("Success!")
    print_success(f"Merged {commits_behind} commits from upstream")
    print_success(f"Version: {version}-genx")
    print_success("Docker image will build automatically via GitHub Actions")
    print(f"\nRelease URL: https://github.com/VincentJGeisler/portainer-GenX/releases/tag/{tag_name}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAborted by user.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {e}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
