frappe.query_reports['Citizen Satisfaction'] = {
  filters: [
    { fieldname: 'group_by', label: __('Group By'), fieldtype: 'Select', options: ['Category','Government Entity'], default: 'Category' },
  ],
};
