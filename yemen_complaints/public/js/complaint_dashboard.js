frappe.listview_settings['Complaint Case'] = {
  add_fields: ['status', 'priority', 'is_overdue', 'government_entity'],
  get_indicator(doc) {
    if (doc.status === 'Overdue' || doc.is_overdue) {
      return [__('Overdue'), 'red', 'status,=,Overdue'];
    }
    if (['Resolved', 'Closed'].includes(doc.status)) {
      return [__(doc.status), 'green', `status,=,${doc.status}`];
    }
    if (doc.priority === 'Critical') {
      return [__('Critical'), 'orange', 'priority,=,Critical'];
    }
    return [__(doc.status || 'New'), 'blue', `status,=,${doc.status || 'New'}`];
  },
};
