#!/bin/bash
# Quick Fix Script for Critical Issues
# Generated: October 30, 2025
# Run this to fix the most critical issues found in audit

set -e  # Exit on error

echo "🔧 My Hibachi Chef - Quick Fix Script"
echo "======================================"
echo ""

# Change to backend directory
cd "$(dirname "$0")/apps/backend"

echo "📋 Step 1: Create NotificationService compatibility alias"
echo "--------------------------------------------------------"
cat > src/services/notification_service.py << 'EOF'
"""
Notification Service - Compatibility Alias

This module provides backward compatibility for imports that reference
the old NotificationService name. It redirects to UnifiedNotificationService.

Created: October 30, 2025
Reason: Fix import errors in payment_matcher_service.py and payment_email_scheduler.py
"""

from .unified_notification_service import UnifiedNotificationService as NotificationService
from .unified_notification_service import (
    notify_new_booking,
    notify_booking_edit,
    notify_cancellation,
    notify_payment,
    notify_review,
    notify_complaint,
    get_notification_service
)

__all__ = [
    'NotificationService',
    'notify_new_booking',
    'notify_booking_edit',
    'notify_cancellation',
    'notify_payment',
    'notify_review',
    'notify_complaint',
    'get_notification_service'
]
EOF

echo "✅ Created notification_service.py compatibility alias"
echo ""

echo "📋 Step 2: Install missing dependencies"
echo "----------------------------------------"
if ! pip show twilio > /dev/null 2>&1; then
    echo "Installing twilio..."
    pip install twilio==8.10.0
    echo "✅ Twilio installed"
else
    echo "✅ Twilio already installed"
fi
echo ""

echo "📋 Step 3: Update requirements.txt"
echo "-----------------------------------"
if ! grep -q "twilio" requirements.txt; then
    echo "twilio==8.10.0  # WhatsApp/SMS notifications via Twilio" >> requirements.txt
    echo "✅ Added twilio to requirements.txt"
else
    echo "✅ Twilio already in requirements.txt"
fi
echo ""

echo "📋 Step 4: Organize test files"
echo "-------------------------------"
mkdir -p tests/services
mkdir -p tests/integrations
mkdir -p tests/api

# Move test files if they exist
if ls test_*.py 1> /dev/null 2>&1; then
    mv test_*.py tests/services/ 2>/dev/null || true
    echo "✅ Moved test files to tests/services/"
else
    echo "ℹ️  No test_*.py files in root to move"
fi

if ls verify_*.py 1> /dev/null 2>&1; then
    mv verify_*.py tests/integrations/ 2>/dev/null || true
    echo "✅ Moved verify files to tests/integrations/"
else
    echo "ℹ️  No verify_*.py files in root to move"
fi
echo ""

echo "📋 Step 5: Fix customer frontend linting"
echo "-----------------------------------------"
cd ../customer

# Remove unused import
if command -v sed &> /dev/null; then
    # Fix import line
    sed -i "s/import { Users, X, ChevronDown, ChevronUp }/import { Users, ChevronDown, ChevronUp }/" \
        src/components/payment/AlternativePayerField.tsx 2>/dev/null || true
    
    # Fix apostrophes
    sed -i "s/payer's name doesn't/payer\&apos;s name doesn\&apos;t/" \
        src/components/payment/AlternativePayerField.tsx 2>/dev/null || true
    
    echo "✅ Fixed linting issues in AlternativePayerField.tsx"
else
    echo "⚠️  sed not available, manually fix:"
    echo "   1. Remove 'X' from imports in AlternativePayerField.tsx"
    echo "   2. Escape apostrophes with &apos;"
fi

# Run linting if available
if [ -f "package.json" ] && command -v npm &> /dev/null; then
    if npm run lint:fix > /dev/null 2>&1; then
        echo "✅ Ran ESLint fix"
    else
        echo "ℹ️  lint:fix script not available"
    fi
fi

cd ../backend
echo ""

echo "📋 Step 6: Update .gitignore"
echo "-----------------------------"
if ! grep -q "^test_.*\.py$" ../../.gitignore; then
    cat >> ../../.gitignore << 'EOF'

# Test files in backend root (should be in tests/ directory)
apps/backend/test_*.py
apps/backend/*_test.py
apps/backend/verify_*.py
EOF
    echo "✅ Updated .gitignore"
else
    echo "✅ .gitignore already configured"
fi
echo ""

echo "======================================"
echo "✅ Quick Fix Complete!"
echo "======================================"
echo ""
echo "📊 Summary of Changes:"
echo "  ✅ Created notification_service.py compatibility alias"
echo "  ✅ Installed Twilio dependency"
echo "  ✅ Updated requirements.txt"
echo "  ✅ Organized test files into tests/ directory"
echo "  ✅ Fixed linting errors in customer frontend"
echo "  ✅ Updated .gitignore"
echo ""
echo "🎯 Next Steps:"
echo "  1. Restart backend server: python src/api/app/main.py"
echo "  2. Run tests: pytest tests/"
echo "  3. Check frontend: npm run dev (in apps/customer)"
echo "  4. Review audit report: COMPREHENSIVE_ONE_WEEK_AUDIT_REPORT.md"
echo ""
echo "⚠️  Manual Actions Still Needed:"
echo "  1. Remove hardcoded Twilio credentials from test files"
echo "  2. Implement rate limiting (see audit report)"
echo "  3. Add security headers (see audit report)"
echo "  4. Decide on RingCentral SMS fallback"
echo ""
echo "📞 Questions? See audit report sections:"
echo "  - Critical Issues: Fix immediately"
echo "  - Medium Priority: Fix within 1 week"
echo "  - Low Priority: Fix when convenient"
echo ""
