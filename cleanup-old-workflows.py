#!/usr/bin/env python3
"""
Clean up old GitHub Actions workflow runs

This script deletes workflow runs for workflows that no longer exist.
"""

import subprocess
import json
import sys

def run_command(cmd):
    """Run command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def get_old_workflow_runs():
    """Get runs for old workflows"""
    print("Fetching workflow runs...")
    
    # Get all workflow runs
    cmd = 'gh run list -R VincentJGeisler/portainer-GenX --limit 100 --json databaseId,workflowName,conclusion,createdAt'
    output = run_command(cmd)
    
    if not output:
        print("No runs found or error fetching runs")
        return []
    
    runs = json.loads(output)
    
    # Filter for old workflows (not our new ones)
    old_workflow_names = [
        "Portainer-GenX CI",
        "Docker Image CI",
        "Build and Test"
    ]
    
    old_runs = [
        run for run in runs 
        if run['workflowName'] in old_workflow_names
    ]
    
    return old_runs

def delete_run(run_id):
    """Delete a specific workflow run"""
    cmd = f'gh run delete {run_id} -R VincentJGeisler/portainer-GenX'
    try:
        subprocess.run(cmd, shell=True, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    print("GitHub Actions Cleanup Tool")
    print("=" * 60)
    
    # Get old runs
    old_runs = get_old_workflow_runs()
    
    if not old_runs:
        print("\n✓ No old workflow runs found!")
        print("Your Actions tab is already clean.")
        return
    
    print(f"\nFound {len(old_runs)} old workflow runs:")
    print()
    
    # Group by workflow name
    by_workflow = {}
    for run in old_runs:
        name = run['workflowName']
        if name not in by_workflow:
            by_workflow[name] = []
        by_workflow[name].append(run)
    
    for workflow_name, runs in by_workflow.items():
        print(f"  - {workflow_name}: {len(runs)} runs")
    
    print()
    response = input(f"Delete all {len(old_runs)} old workflow runs? (y/N): ")
    
    if response.lower() != 'y':
        print("Cancelled. No runs deleted.")
        return
    
    print("\nDeleting runs...")
    deleted = 0
    failed = 0
    
    for run in old_runs:
        print(f"  Deleting run {run['databaseId']} ({run['workflowName']})...", end=" ")
        if delete_run(run['databaseId']):
            print("✓")
            deleted += 1
        else:
            print("✗")
            failed += 1
    
    print()
    print(f"✓ Deleted {deleted} runs")
    if failed > 0:
        print(f"✗ Failed to delete {failed} runs")
    
    print("\n✓ Cleanup complete!")
    print("Your Actions tab should now only show the working workflows.")

if __name__ == "__main__":
    try:
        # Check if gh CLI is available
        subprocess.run("gh --version", shell=True, check=True, capture_output=True)
        main()
    except subprocess.CalledProcessError:
        print("Error: GitHub CLI (gh) not found!")
        print("Install it from: https://cli.github.com/")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
