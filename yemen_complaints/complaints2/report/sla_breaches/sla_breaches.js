frappe.query_reports['SLA Breaches'] = {
  filters: [
    { fieldname: 'government_entity', label: __('Government Entity'), fieldtype: 'Link', options: 'Government Entity' },
    { fieldname: 'priority', label: __('Priority'), fieldtype: 'Select', options: ['','Low','Medium','High','Critical'] },
    { fieldname: 'status', label: __('Status'), fieldtype: 'Select', options: ['','New','Under Review','Assigned','In Progress','Waiting Citizen','Overdue'] },
  ],
};
