#!/bin/bash
# Helper script to push code to GitHub (AIForBharat repository)

set -e

echo "🔍 Checking Git status..."

# Check if git is initialized
if [ ! -d .git ]; then
    echo "📦 Initializing Git repository..."
    git init
    git branch -M main
fi

# Check if remote exists
if ! git remote get-url origin &> /dev/null; then
    echo "🔗 Adding remote origin: AIForBharat"
    git remote add origin https://github.com/priyanshu6729/AIForBharat.git
else
    CURRENT_ORIGIN=$(git remote get-url origin)
    if [ "$CURRENT_ORIGIN" != "https://github.com/priyanshu6729/AIForBharat.git" ]; then
        echo "⚠️  Current origin: $CURRENT_ORIGIN"
        echo "🔄 Updating to AIForBharat repository..."
        git remote set-url origin https://github.com/priyanshu6729/AIForBharat.git
    fi
fi

echo "✅ Remote origin: https://github.com/priyanshu6729/AIForBharat.git"
echo ""

# Check current branch
current_branch=$(git branch --show-current 2>/dev/null || echo "")

if [ -z "$current_branch" ]; then
    echo "🌿 Creating main branch..."
    git checkout -b main
    current_branch="main"
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    echo "📝 You have uncommitted changes:"
    echo ""
    git status --short
    echo ""
    read -p "Commit these changes? (y/n) " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "Enter commit message (or press Enter for default):"
        read commit_message
        
        if [ -z "$commit_message" ]; then
            commit_message="feat: Add Codexa backend to AIForBharat

- FastAPI application with AWS Cognito authentication
- PostgreSQL database with Alembic migrations
- AWS Bedrock AI integration for code guidance
- Code analysis, execution, and visualization
- Learning paths and progress tracking
- Docker containerization
- CI/CD pipeline with GitHub Actions
- Production-ready deployment configuration"
        fi
        
        git add -A
        git commit -m "$commit_message"
        echo "✅ Changes committed"
    else
        echo "❌ Push cancelled. Commit your changes first."
        exit 1
    fi
elif ! git log -1 &> /dev/null; then
    echo "📝 No commits yet. Creating initial commit..."
    git add .
    git commit -m "feat: Initial commit - Codexa Backend

- FastAPI application with AWS Cognito authentication
- PostgreSQL database with Alembic migrations
- AWS Bedrock AI integration for code guidance
- Code analysis, execution, and visualization
- Learning paths and progress tracking
- Docker containerization
- CI/CD pipeline with GitHub Actions
- Production-ready deployment configuration"
    echo "✅ Initial commit created"
else
    echo "✅ No uncommitted changes"
fi

echo ""
echo "🚀 Pushing to GitHub (AIForBharat)..."
echo "   Repository: priyanshu6729/AIForBharat"
echo "   Branch: $current_branch"
echo ""

# Push to GitHub
if git push origin "$current_branch" 2>&1; then
    echo ""
    echo "✅ Code pushed successfully!"
    echo ""
    echo "🔗 View on GitHub:"
    echo "   https://github.com/priyanshu6729/AIForBharat"
    echo ""
else
    echo ""
    echo "⚠️  First time push? Run:"
    echo "   git push -u origin $current_branch"
    echo ""
    read -p "Push with -u flag? (y/n) " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git push -u origin "$current_branch"
        echo ""
        echo "✅ Code pushed successfully!"
    else
        exit 1
    fi
fi

echo ""
echo "📋 Next steps:"
echo "  1. View repository: https://github.com/priyanshu6729/AIForBharat"
echo "  2. Check GitHub Actions: https://github.com/priyanshu6729/AIForBharat/actions"
echo "  3. Deploy to production: ./scripts/deploy.sh production"
echo "  4. Or deploy to Railway: railway up"
echo ""