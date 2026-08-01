frappe.ui.form.on('Complaint Identity Verification', {
  refresh(frm) {
    frm.set_intro(__('Stores citizen identity verification requests for complaint submission channels.'), 'orange');
  },
});
