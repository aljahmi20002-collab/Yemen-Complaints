frappe.ui.form.on('Government Entity', {
  setup(frm) {
    frm.set_query('district', () => ({
      filters: frm.doc.governorate ? { governorate: frm.doc.governorate } : {},
    }));
  },

  refresh(frm) {
    frm.set_intro(__('Maintain routing defaults, ownership, Yemeni location details, and description quality for complaint assignments.'), 'blue');

    if (!frm.is_new() && window.YemenComplaintsAI) {
      window.YemenComplaintsAI.addTextActionButtons(frm, {
        group: 'AI Tools',
        preferredSourceFields: ['description', 'address', 'entity_name_ar', 'entity_name_en'],
        preferredTargetFields: ['description', 'address'],
      });
    }
  },

  governorate(frm) {
    frm.set_value('district', null);
  },
});
