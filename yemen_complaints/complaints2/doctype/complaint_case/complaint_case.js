frappe.ui.form.on('Complaint Case', {
  setup(frm) {
    frm.set_query('citizen_district', () => ({
      filters: frm.doc.citizen_governorate ? { governorate: frm.doc.citizen_governorate } : {},
    }));

    frm.set_query('incident_district', () => ({
      filters: frm.doc.incident_governorate ? { governorate: frm.doc.incident_governorate } : {},
    }));
  },

  refresh(frm) {
    frm.set_intro(__('Manage citizen complaints, appeals, routing, SLA commitments, Yemeni location data, and AI-assisted intake.'), 'blue');

    if (!frm.is_new()) {
      frm.add_custom_button(__('Add Public Update'), () => {
        frappe.prompt([
          { fieldname: 'message', label: __('Message'), fieldtype: 'Small Text', reqd: 1 },
          { fieldname: 'new_status', label: __('New Status'), fieldtype: 'Select', options: ['', 'Under Review', 'Assigned', 'In Progress', 'Waiting Citizen', 'Resolved', 'Rejected', 'Closed'] },
        ], (values) => {
          frappe.call({
            method: 'yemen_complaints.complaints2.doctype.complaint_case.complaint_case.add_public_update',
            args: {
              docname: frm.doc.name,
              message: values.message,
              new_status: values.new_status,
              visibility: 'Public',
              update_type: 'Status Change',
            },
            callback: () => frm.reload_doc(),
          });
        }, __('Add Public Update'), __('Save'));
      });

      frm.add_custom_button(__('Assign Case'), () => {
        frappe.prompt([
          { fieldname: 'assigned_to', label: __('Assigned To'), fieldtype: 'Link', options: 'User', reqd: 1 },
          { fieldname: 'role_type', label: __('Role Type'), fieldtype: 'Select', options: ['Advisor', 'Agency Officer', 'Follow-up Officer'], reqd: 1 },
          { fieldname: 'due_date', label: __('Due Date'), fieldtype: 'Date' },
          { fieldname: 'instructions', label: __('Instructions'), fieldtype: 'Small Text' },
        ], (values) => {
          frappe.call({
            method: 'yemen_complaints.complaints2.doctype.complaint_case.complaint_case.assign_case',
            args: { docname: frm.doc.name, ...values },
            callback: () => frm.reload_doc(),
          });
        }, __('Assign Case'), __('Assign'));
      });

      frm.add_custom_button(__('Open Citizen Portal'), () => {
        window.open('/my-cases', '_blank');
      }, __('Portal'));

      if (window.YemenComplaintsAI) {
        window.YemenComplaintsAI.addTextActionButtons(frm, {
          group: 'AI Tools',
          preferredSourceFields: ['details', 'grievance_reason', 'resolution_summary', 'subject', 'internal_notes'],
          preferredTargetFields: ['internal_notes', 'resolution_summary', 'ai_suggested_reply', 'details'],
        });
        window.YemenComplaintsAI.addIntakeAssistantButton(frm);
        frm.add_custom_button(__('Apply AI Recommendations'), () => {
          frappe.call({
            method: 'yemen_complaints.ai.apply_intake_assistant_recommendations',
            freeze: true,
            freeze_message: __('Applying AI recommendations...'),
            args: { docname: frm.doc.name },
            callback: () => frm.reload_doc(),
          });
        }, __('AI Assistant'));
      }
    }
  },

  citizen_governorate(frm) {
    frm.set_value('citizen_district', null);
  },

  incident_governorate(frm) {
    frm.set_value('incident_district', null);
  },

  category(frm) {
    if (frm.doc.category && !frm.doc.priority) {
      frm.set_value('priority', 'Medium');
    }
  },

  status(frm) {
    if (['Resolved', 'Closed'].includes(frm.doc.status) && !frm.doc.resolution_summary) {
      frm.dashboard.add_comment(__('Please add a resolution summary before final closure.'), 'orange', true);
    }
  },
});
