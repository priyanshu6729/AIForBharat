#!/bin/bash

set -e

echo "🔍 Verifying GitHub readiness..."
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Check 1: .env not in git
echo "1️⃣  Checking .env is not tracked..."
if git ls-files --error-unmatch .env 2>/dev/null; then
    echo -e "${RED}❌ .env is tracked by git! This is a security risk!${NC}"
    echo "   Run: git rm --cached .env"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✅ .env is not tracked${NC}"
fi

# Check 2: .env.example exists
echo "2️⃣  Checking .env.example exists..."
if [ -f .env.example ]; then
    echo -e "${GREEN}✅ .env.example exists${NC}"
else
    echo -e "${RED}❌ .env.example is missing${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check 3: Secrets not in .env.example
echo "3️⃣  Checking .env.example has no secrets..."
if grep -q "your_password\|your_key\|example\|changeme\|your-" .env.example; then
    echo -e "${GREEN}✅ .env.example has placeholder values${NC}"
else
    echo -e "${YELLOW}⚠️  .env.example might contain real values${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 4: README.md exists
echo "4️⃣  Checking README.md..."
if [ -f README.md ]; then
    if [ $(wc -l < README.md) -gt 50 ]; then
        echo -e "${GREEN}✅ README.md is comprehensive${NC}"
    else
        echo -e "${YELLOW}⚠️  README.md seems short${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${RED}❌ README.md is missing${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check 5: .gitignore exists
echo "5️⃣  Checking .gitignore..."
if [ -f .gitignore ]; then
    if grep -q "__pycache__\|.env\|.venv" .gitignore; then
        echo -e "${GREEN}✅ .gitignore is properly configured${NC}"
    else
        echo -e "${YELLOW}⚠️  .gitignore might be incomplete${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${RED}❌ .gitignore is missing${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check 6: LICENSE exists
echo "6️⃣  Checking LICENSE..."
if [ -f LICENSE ]; then
    echo -e "${GREEN}✅ LICENSE exists${NC}"
else
    echo -e "${YELLOW}⚠️  LICENSE is missing (recommended)${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 7: requirements.txt exists
echo "7️⃣  Checking requirements.txt..."
if [ -f requirements.txt ]; then
    if [ $(wc -l < requirements.txt) -gt 5 ]; then
        echo -e "${GREEN}✅ requirements.txt exists with dependencies${NC}"
    else
        echo -e "${YELLOW}⚠️  requirements.txt seems empty${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${RED}❌ requirements.txt is missing${NC}"
    ERRORS=$((ERRORS + 1))
fi

# Check 8: Dockerfile exists
echo "8️⃣  Checking Dockerfile..."
if [ -f Dockerfile ]; then
    echo -e "${GREEN}✅ Dockerfile exists${NC}"
else
    echo -e "${YELLOW}⚠️  Dockerfile is missing (optional)${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 9: GitHub Actions
echo "9️⃣  Checking GitHub Actions..."
if [ -d .github/workflows ]; then
    echo -e "${GREEN}✅ GitHub Actions configured${NC}"
else
    echo -e "${YELLOW}⚠️  No GitHub Actions (optional)${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 10: No large files
echo "🔟 Checking for large files..."
LARGE_FILES=$(find . -type f -size +10M -not -path "./.git/*" -not -path "./.venv/*" 2>/dev/null)
if [ -z "$LARGE_FILES" ]; then
    echo -e "${GREEN}✅ No large files found${NC}"
else
    echo -e "${YELLOW}⚠️  Large files found (consider Git LFS):${NC}"
    echo "$LARGE_FILES"
    WARNINGS=$((WARNINGS + 1))
fi

# Check 11: No REAL hardcoded secrets (improved check)
echo "1️⃣1️⃣  Scanning for hardcoded secrets..."
# Look for actual secret patterns, not just the word "password"
POTENTIAL_SECRETS=$(grep -r -E "(password|secret|api_key|aws_access)(\s*=\s*['\"][^'\"]{8,}['\"])" --include="*.py" app/ 2>/dev/null | grep -v "getenv\|os.environ\|config\|BaseModel\|str\|def " || true)
if [ -z "$POTENTIAL_SECRETS" ]; then
    echo -e "${GREEN}✅ No hardcoded secrets found${NC}"
else
    echo -e "${RED}❌ Potential hardcoded secrets found:${NC}"
    echo "$POTENTIAL_SECRETS"
    ERRORS=$((ERRORS + 1))
fi

# Check 12: Python cache files not tracked
echo "1️⃣2️⃣  Checking Python cache..."
if git ls-files | grep -q "__pycache__\|\.pyc"; then
    echo -e "${RED}❌ Python cache files are tracked!${NC}"
    echo "   Run: git rm -r --cached **/__pycache__ **/*.pyc"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✅ No Python cache in git${NC}"
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED! Ready for GitHub!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review your changes: git status"
    echo "  2. Run: ./scripts/git_push.sh"
    echo "  3. Or manually: git add . && git commit -m 'Your message' && git push"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  $WARNINGS warnings found (review recommended)${NC}"
    echo ""
    echo "You can proceed, but consider fixing warnings first."
    exit 0
else
    echo -e "${RED}❌ $ERRORS critical errors found!${NC}"
    echo -e "${YELLOW}⚠️  $WARNINGS warnings found${NC}"
    echo ""
    echo "Please fix errors before pushing to GitHub!"
    exit 1
fi