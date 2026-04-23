# Git Cheatsheet for Solo Development

## Daily Workflow

```bash
git status                          # See what's changed
git add .                           # Stage all changes
git add filename.txt                # Stage specific file
git commit -m "Your message here"   # Commit with message
git push                            # Send to GitHub
git pull                            # Get updates from GitHub
```

## Viewing History & Changes

```bash
git log --oneline                   # Compact history view
git log --oneline -10               # Last 10 commits
git diff                            # See unstaged changes
git diff filename.txt               # Changes in specific file
git show                            # See last commit details
```

## Undo Operations (Before Committing)

```bash
git restore filename.txt            # Discard changes to a file
git restore .                       # Discard ALL changes (careful!)
git restore --staged filename.txt   # Unstage a file (keep changes)
```

## Undo Operations (After Committing)

```bash
git commit --amend -m "New message" # Fix last commit message
git reset HEAD~1                    # Undo last commit, keep changes
git reset --hard HEAD~1             # Undo last commit, LOSE changes (careful!)
```

## First-Time Setup (One-time only)

```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
git config --global core.editor "nano"  # Or your preferred editor
```

## Starting a New Project

```bash
git init                            # Create new repo in current folder
git remote add origin <github-url>  # Connect to GitHub
git branch -M main                  # Rename default branch to main
git push -u origin main             # First push to GitHub
```

## Clone Existing Project

```bash
git clone <github-url>              # Download repo from GitHub
```

## Useful Aliases (Optional - makes commands shorter)

```bash
# Set these up once, then use forever:
git config --global alias.st status
git config --global alias.co commit
git config --global alias.br branch
git config --global alias.last 'log -1 HEAD'

# Now you can use:
git st          # instead of git status
git co -m "msg" # instead of git commit -m "msg"
```

## Common Scenarios

### "I want to save my work"
```bash
git add .
git commit -m "Description of what you did"
git push
```

### "I want to see what I changed"
```bash
git status      # Files changed
git diff        # Line-by-line changes
```

### "I messed up a file, start over"
```bash
git restore filename.txt
```

### "I made a typo in my commit message"
```bash
git commit --amend -m "Corrected message"
git push --force  # Only if you already pushed
```

### "I committed too early, want to add more"
```bash
# Make your additional changes, then:
git add .
git commit --amend --no-edit  # Adds to previous commit
```

## Important Notes

- `git add .` stages ALL changes (careful with unintended files!)
- `git restore` and `git reset --hard` are DESTRUCTIVE - changes are gone
- Always `git pull` before `git push` if working from multiple machines
- Commit messages should be brief but descriptive
- Push regularly so you have backups on GitHub
