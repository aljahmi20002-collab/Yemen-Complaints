#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <site-name>"
  exit 1
fi

SITE="$1"

echo "== Live Verification Checklist =="
echo "Site: $SITE"
echo

echo "1) Run migration and asset build"
echo "   bench --site $SITE migrate"
echo "   bench build"
echo

echo "2) Reload core file-based records"
echo "   bash scripts/sync_reload_all_records.sh $SITE"
echo

echo "3) Verify key pages manually"
echo "   /"
echo "   /submit-complaint"
echo "   /submit-appeal"
echo "   /track-complaint"
echo "   /verify-identity"
echo "   /my-cases"
echo "   /docs"
echo "   /executive-delivery-pack"
echo

echo "4) Verify dashboards"
echo "   /app/internal-operations-dashboard"
echo "   /app/executive-leadership-dashboard"
echo "   /app/security-monitoring-dashboard"
echo

echo "5) Verify core record counts from bench console"
echo "   frappe.db.count('Yemen Governorate')  # expected 22"
echo "   frappe.db.count('Yemen District')     # expected 335"
echo

echo "6) Verify channels"
echo "   - Email OTP"
echo "   - SMS OTP (if enabled)"
echo "   - WhatsApp OTP (if enabled)"
echo "   - Telegram OTP (if enabled)"
echo

echo "7) Verify AI"
echo "   - AI text actions"
echo "   - Smart Intake Assistant"
echo "   - Complaint AI Log"
echo

echo "8) Verify security logging"
echo "   - Complaint Security Event"
echo "   - blocked / observed / allowed events visible"
echo

echo "Checklist prepared. Execute manual validation and sign off."
