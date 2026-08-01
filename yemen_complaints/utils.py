from __future__ import annotations

OPEN_STATUSES = {
    "New",
    "Under Review",
    "Assigned",
    "In Progress",
    "Waiting Citizen",
    "Overdue",
}

CLOSED_STATUSES = {"Resolved", "Rejected", "Closed"}

CASE_PREFIX = {
    "Complaint": "CMP",
    "Appeal": "APL",
    "Inquiry": "INQ",
}

ROLE_MAP = {
    "citizen": "Citizen",
    "advisor": "Advisor",
    "agency": "Agency Officer",
    "follow_up": "Follow-up Officer",
    "manager": "Complaint System Manager",
}
