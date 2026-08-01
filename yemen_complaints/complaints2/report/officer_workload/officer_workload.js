frappe.query_reports['Officer Workload'] = {
  filters: [
    { fieldname: 'role_dimension', label: __('Dimension'), fieldtype: 'Select', options: ['Advisor','Agency Officer','Follow-up Officer'], default: 'Advisor' },
  ],
};
