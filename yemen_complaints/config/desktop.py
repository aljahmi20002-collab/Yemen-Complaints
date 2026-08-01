from frappe import _


def get_data():
    return [
        {
            "module_name": "Complaints2",
            "label": _("Complaints2"),
            "color": "red",
            "icon": "octicon octicon-comment-discussion",
            "type": "module",
            "description": _("Citizen complaints and appeals management"),
        }
    ]
