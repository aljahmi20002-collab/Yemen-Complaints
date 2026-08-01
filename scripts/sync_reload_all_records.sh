#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <site-name>"
  exit 1
fi

SITE="$1"
APP="yemen_complaints"
MODULE="Complaints2"

bench --site "$SITE" migrate
bench build

# Pages
for page in \
  docs_center application_docs user_guide_portal citizen_guide_portal admin_guide_portal \
  executive_brief_portal executive_brief_en_portal executive_leadership_dashboard \
  privacy_policy_portal terms_of_use_portal api_guide_portal submit_complaint_portal \
  submit_appeal_portal track_complaint_portal verify_identity_portal my_cases_portal \
  internal_operations_dashboard security_monitoring_dashboard
  do
    bench --site "$SITE" reload-doc "$APP" "$MODULE" page "$page"
  done

# Dashboard Charts
for chart in \
  cases_by_status cases_by_priority monthly_complaint_trend cases_by_country \
  cases_by_governorate cases_by_type cases_by_entity
  do
    bench --site "$SITE" reload-doc "$APP" "$MODULE" dashboard_chart "$chart"
  done

# Cards
for card in \
  العمليات_والكيانات_الأساسية التقارير_التنفيذية الإعدادات_والضبط الواجهات_والبوابات
  do
    bench --site "$SITE" reload-doc "$APP" "$MODULE" card "$card"
  done

# Workspaces
for workspace in \
  citizen_complaints_portal advisor_complaint_desk agency_officer_desk \
  follow_up_desk yemen_complaints_manager_desk yemen_complaints_command_center
  do
    bench --site "$SITE" reload-doc "$APP" "$MODULE" workspace "$workspace"
  done

# Reports
for report in complaint_summary sla_breaches officer_workload citizen_satisfaction
  do
    bench --site "$SITE" reload-doc "$APP" "$MODULE" report "$report"
  done

# Doctypes frequently touched
for dt in \
  complaint_case complaint_category government_entity complaint_identity_verification \
  complaint_ai_log complaint_ai_settings complaint_notification_settings \
  complaint_security_event yemen_governorate yemen_district
  do
    bench --site "$SITE" reload-doc "$APP" "$MODULE" doctype "$dt"
  done

bench --site "$SITE" clear-cache
bench --site "$SITE" clear-website-cache

echo "Full sync/reload complete for site: $SITE"
