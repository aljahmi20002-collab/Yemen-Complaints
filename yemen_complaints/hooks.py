app_name = "yemen_complaints"
app_title = "Yemen Complaints"
app_publisher = "Arena.ai"
app_description = "Complaints and appeals intake, tracking, dashboards, and SLA management"
app_email = "support@example.com"
app_license = "MIT"

add_to_apps_screen = [
    {
        "name": "yemen_complaints",
        "logo": "/assets/yemen_complaints/images/official_emblem.png",
        "title": "Yemen Complaints",
        "route": "/app/yemen-complaints-command-center",
        "has_permission": "yemen_complaints.permissions.app_has_access",
    }
]

after_install = "yemen_complaints.setup.install.after_install"
after_migrate = "yemen_complaints.setup.install.after_migrate"

app_include_css = ["/assets/yemen_complaints/css/yemen_complaints.css"]
app_include_js = [
    "/assets/yemen_complaints/js/complaint_dashboard.js",
    "/assets/yemen_complaints/js/ai_tools.js",
]
web_include_css = ["/assets/yemen_complaints/css/yemen_complaints.css"]

# Keep fixture auto-import minimal during install to avoid dependency-order issues.
# Roles are safe to import; other administrative objects are created programmatically
# in after_install / after_migrate and can still be exported manually to fixtures/.
fixtures = [
    {"dt": "Role", "filters": [["role_name", "in", ["Citizen", "Advisor", "Agency Officer", "Follow-up Officer", "Complaint System Manager"]]]},
]

permission_query_conditions = {
    "Complaint Case": "yemen_complaints.permissions.complaint_case_query_conditions",
}

has_permission = {
    "Complaint Case": "yemen_complaints.permissions.complaint_case_has_permission",
}

scheduler_events = {
    "hourly": [
        "yemen_complaints.tasks.send_sla_reminders",
    ],
    "daily": [
        "yemen_complaints.tasks.update_overdue_cases",
    ],
}

doc_events = {
    "Complaint Case": {
        "validate": "yemen_complaints.complaints2.doctype.complaint_case.complaint_case.apply_sla_and_defaults",
        "after_insert": "yemen_complaints.notifications.after_insert_complaint_case",
        "on_update": "yemen_complaints.notifications.on_update_complaint_case",
    }
}
