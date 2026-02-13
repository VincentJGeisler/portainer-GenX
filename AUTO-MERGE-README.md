# Portainer GenX Auto-Merge

Two ways to keep Portainer-GenX up-to-date with upstream:

## Option 1: Python Script (Manual)

Run the Python script whenever you want to merge upstream changes.

### Usage

```bash
# Basic usage - will prompt for confirmation
python3 auto-merge.py

# Dry run - see what would happen without pushing
python3 auto-merge.py --dry-run

# Automatic - no prompts, auto-push
python3 auto-merge.py --auto-push

# Force push (use with caution!)
python3 auto-merge.py --auto-push --force
```

### What It Does

1. ✅ Fetches latest upstream changes
2. ✅ Checks how many commits behind
3. ✅ Creates new branch from upstream/develop
4. ✅ Applies GenX password modification (12 → 1)
5. ✅ Commits the change
6. ✅ Creates version tag (e.g., `2.39.0-genx`)
7. ✅ Pushes to GitHub (triggers Docker build)

### Requirements

- Python 3.7+
- Git
- Clean working tree

### Example Output

```
============================================================
Portainer GenX Auto-Merge
============================================================

✓ Fetched upstream/develop
⚠ Currently 127 commits behind upstream

Current version: 2.38.1
Upstream version: 2.39.0

Merge 127 commits from upstream? (y/N): y

============================================================
Creating Merge Branch
============================================================

✓ Created branch: genx-auto-merge-20260213

============================================================
Applying GenX Password Modification
============================================================

✓ Applied password modification: 12 → 1

============================================================
Committing Changes
============================================================

✓ Committed changes

============================================================
Creating Tag
============================================================

✓ Created tag: 2.39.0-genx

============================================================
Success!
============================================================

✓ Merged 127 commits from upstream
✓ Version: 2.39.0-genx
✓ Docker image will build automatically via GitHub Actions

Release URL: https://github.com/VincentJGeisler/portainer-GenX/releases/tag/2.39.0-genx
```

---

## Option 2: GitHub Actions (Automatic)

The workflow runs automatically every Monday at 9 AM UTC.

### Configuration

File: `.github/workflows/auto-merge.yml`

**Schedule**: Every Monday at 9 AM UTC

```yaml
schedule:
  - cron: '0 9 * * 1'  # Weekly on Monday
```

### Manual Trigger

You can also run it manually:

1. Go to **Actions** tab on GitHub
2. Select **"Auto-Merge Upstream"** workflow
3. Click **"Run workflow"**
4. Optional: Enable "Dry run" to test without pushing

### What It Does

1. ✅ Checks if updates available
2. ✅ If yes: Runs auto-merge script
3. ✅ Pushes changes automatically
4. ✅ Triggers Docker build workflow
5. ✅ Creates summary report

### Workflow Summary

After running, you'll see a summary like:

```
## Auto-Merge Complete! 🎉

- **Commits merged**: 127
- **Status**: Merged and pushed
- **Docker build**: Will trigger automatically

The Docker image will be built and pushed automatically by the build workflow.
```

---

## Changing the Schedule

Edit `.github/workflows/auto-merge.yml`:

```yaml
# Daily at 2 AM UTC
- cron: '0 2 * * *'

# Every Monday and Thursday at 9 AM UTC
- cron: '0 9 * * 1,4'

# First day of every month at 10 AM UTC
- cron: '0 10 1 * *'

# Every 6 hours
- cron: '0 */6 * * *'
```

---

## How It Works

### The GenX Modification

Both methods preserve this single line change:

```diff
# File: api/datastore/init.go
- RequiredPasswordLength: 12,
+ RequiredPasswordLength: 1,
```

### The Process

```
1. Fetch upstream/develop
         ↓
2. Create branch from upstream
         ↓
3. Apply password change (12 → 1)
         ↓
4. Commit + Tag
         ↓
5. Push to GitHub
         ↓
6. GitHub Actions builds Docker image
         ↓
7. Docker image pushed to Docker Hub
```

### Version Detection

The script automatically detects the upstream version by:
1. Checking upstream git tags
2. Reading package.json
3. Falling back to current version

---

## Comparison

| Feature | Python Script | GitHub Actions |
|---------|---------------|----------------|
| **Trigger** | Manual | Automatic (weekly) |
| **Control** | Full control | Automated |
| **Visibility** | Terminal output | GitHub UI |
| **Dry run** | ✅ Yes | ✅ Yes |
| **Testing** | Run locally | Run in cloud |
| **Notifications** | Terminal only | GitHub notifications |
| **Best for** | On-demand updates | Hands-off automation |

---

## Recommended Workflow

### For Regular Updates
Use **GitHub Actions** (automatic weekly).

### For Testing or Custom Updates  
Use **Python script** with `--dry-run` first.

### For Urgent Updates
Use **Python script** with `--auto-push`.

---

## Troubleshooting

### Script says "Working tree not clean"
```bash
git status
git stash  # or commit your changes
python3 auto-merge.py
```

### Script can't find upstream version
The script will use the current version and continue.

### Want to change the password length?
Edit `auto-merge.py` and change this line:
```python
modified = "RequiredPasswordLength: 1,"  # Change 1 to desired value
```

### Workflow not running automatically?
- Check Actions are enabled in repository settings
- Verify the cron schedule
- Check recent workflow runs for errors

### Merge conflicts
The script will fail if there are conflicts. Manually:
1. Run script with `--dry-run`
2. Check the branch it creates
3. Resolve conflicts
4. Push manually

---

## Safety Features

### Both Methods
- ✅ Check working tree is clean
- ✅ Create backup (branch persists)
- ✅ Verify changes before pushing
- ✅ Use `--force-with-lease` (safer than `--force`)

### Python Script
- ✅ Interactive confirmation prompts
- ✅ Dry-run mode
- ✅ Shows diff before pushing

### GitHub Actions
- ✅ Only runs if updates available
- ✅ Can be disabled
- ✅ Manual approval option
- ✅ Visible logs and summaries

---

## Advanced Usage

### Test Locally Before Automation
```bash
# 1. Test with dry-run
python3 auto-merge.py --dry-run

# 2. If looks good, run for real
python3 auto-merge.py --auto-push

# 3. After success, enable GitHub Actions
```

### Customize for Your Fork
Edit the Python script to:
- Change commit message format
- Add additional modifications
- Change tag naming convention
- Add post-merge steps

### Monitor Automated Merges
- Enable GitHub notifications for Actions
- Check Actions tab weekly
- Review merge commits
- Watch Docker Hub for new images

---

## Future Enhancements

Possible additions:
- [ ] Slack/Discord notifications
- [ ] Automatic GitHub release creation
- [ ] Changelog generation
- [ ] Email notifications on merge
- [ ] Rollback capability
- [ ] Multiple modification support
- [ ] Pre/post-merge hooks

---

## FAQ

**Q: Will this overwrite my changes?**  
A: No, the script creates a new branch from upstream and only modifies the password line.

**Q: What if I have other customizations?**  
A: Add them to the Python script after the password modification.

**Q: Can I run this more frequently?**  
A: Yes, edit the cron schedule. Daily is reasonable.

**Q: What if upstream breaks something?**  
A: The backup branch is preserved. You can rollback or fix manually.

**Q: Do I need both?**  
A: No, pick one. GitHub Actions for automation, Python script for manual control.

---

## Getting Started

### Option 1: Automated (Recommended)
1. Commit the workflow file
2. Push to GitHub
3. Enable Actions if disabled
4. Wait for Monday (or trigger manually)
5. Done! Updates happen automatically

### Option 2: Manual
1. Make `auto-merge.py` executable
2. Run when you want updates
3. Script does everything else

---

**Qapla'!** Now you'll never be more than a week behind upstream! 🚀
