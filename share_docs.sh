#!/bin/bash
# Safe script to share documentation files with mgx.dev

set -e  # Exit on error

echo "🚀 DevOps Brain - Share Documentation Script"
echo "=============================================="
echo ""

# Step 1: Check git status
echo "📋 Step 1: Checking git status..."
if ! git status &>/dev/null; then
    echo "❌ Error: Not in a git repository!"
    echo "   Please run this from your git repository root."
    exit 1
fi

echo "✅ Git repository found"
echo ""

# Step 2: Check for uncommitted changes
echo "📋 Step 2: Checking for uncommitted changes..."
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Warning: You have uncommitted changes"
    echo "   Files to be added:"
    git status --short
    echo ""
    read -p "Continue? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 3: Add documentation files
echo "📋 Step 3: Adding documentation files..."
FILES=(
    "MGX_DEV_RESPONSE.md"
    "ARCHITECTURE.md"
    "ARCHITECTURE_QUICK_REFERENCE.md"
    "DEEP_ANALYSIS.md"
    "ENHANCEMENTS_APPLIED.md"
    "PROJECT_STATUS.md"
    "MGX_DEV_REVIEW_PACKAGE.md"
)

MISSING_FILES=()
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        git add "$file"
        echo "✅ Added: $file"
    else
        MISSING_FILES+=("$file")
        echo "⚠️  Missing: $file"
    fi
done

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    echo ""
    echo "⚠️  Warning: Some files are missing"
    echo "   Missing: ${MISSING_FILES[*]}"
fi

echo ""

# Step 4: Show what will be committed
echo "📋 Step 4: Files ready to commit:"
git status --short
echo ""

# Step 5: Commit
echo "📋 Step 5: Committing files..."
git commit -m "docs: Add mgx.dev review documentation

- MGX_DEV_RESPONSE.md: Answers all 4 questions
- ARCHITECTURE.md: Complete architecture with diagrams
- Supporting documentation files

Ready for mgx.dev review" || {
    echo "⚠️  Nothing to commit (files may already be committed)"
}

echo ""

# Step 6: Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "📋 Step 6: Current branch: $CURRENT_BRANCH"

# Step 7: Get remote URL
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")
if [ -z "$REMOTE_URL" ]; then
    echo "❌ Error: No remote 'origin' found"
    echo "   Please set remote: git remote add origin <your-repo-url>"
    exit 1
fi

echo "📋 Step 7: Remote repository: $REMOTE_URL"
echo ""

# Step 8: Push
echo "📋 Step 8: Pushing to GitHub..."
echo "   Branch: $CURRENT_BRANCH"
echo "   Remote: origin"
echo ""

read -p "Push to GitHub now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git push origin "$CURRENT_BRANCH" || {
        echo ""
        echo "⚠️  Push failed. Trying to pull first..."
        git pull origin "$CURRENT_BRANCH" --rebase
        git push origin "$CURRENT_BRANCH"
    }
    echo ""
    echo "✅ Successfully pushed to GitHub!"
else
    echo "⏭️  Skipped push. Run manually: git push origin $CURRENT_BRANCH"
fi

echo ""
echo "=============================================="
echo "✅ Documentation files are ready!"
echo ""
echo "📧 Next Steps:"
echo "1. Go to: https://github.com/your-username/your-repo"
echo "2. Settings → Collaborators → Add mgx.dev"
echo "3. Share repository link with mgx.dev"
echo ""
echo "Repository URL: $REMOTE_URL"
echo "Branch: $CURRENT_BRANCH"
echo ""
