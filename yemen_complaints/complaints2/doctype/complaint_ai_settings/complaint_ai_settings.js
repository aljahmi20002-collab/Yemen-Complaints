frappe.ui.form.on('Complaint AI Settings', {
  refresh(frm) {
    frm.set_intro(__('Configure AI providers, models, and intake assistant behavior for complaint operations.'), 'blue');
  },
});
