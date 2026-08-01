frappe.ui.form.on('Complaint Category', {
  refresh(frm) {
    frm.set_intro(__('Configure SLA, routing defaults, priority behavior, and AI-assisted classification notes for complaints.'), 'green');

    if (!frm.is_new() && window.YemenComplaintsAI) {
      window.YemenComplaintsAI.addTextActionButtons(frm, {
        group: 'AI Tools',
        preferredSourceFields: ['description', 'category_name_ar', 'category_name_en'],
        preferredTargetFields: ['description'],
      });
    }
  },
});
