frappe.query_reports['Complaint Summary'] = {
  filters: [
    { fieldname: 'from_date', label: __('From Date'), fieldtype: 'Date' },
    { fieldname: 'to_date', label: __('To Date'), fieldtype: 'Date' },
    { fieldname: 'case_type', label: __('Case Type'), fieldtype: 'Select', options: ['','Complaint','Appeal','Inquiry'] },
    { fieldname: 'government_entity', label: __('Government Entity'), fieldtype: 'Link', options: 'Government Entity' },
  ],
};
