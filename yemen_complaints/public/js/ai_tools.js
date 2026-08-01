window.YemenComplaintsAI = (() => {
  const ACTIONS = [
    { key: 'translate', label: 'ترجمة نص' },
    { key: 'summarize', label: 'تلخيص نص' },
    { key: 'improve_writing', label: 'تحسين الكتابة' },
    { key: 'fix_grammar', label: 'إصلاح الإملاء والنحو' },
    { key: 'analyze', label: 'تحليل نص' },
    { key: 'suggest_reply', label: 'اقترح رد' },
    { key: 'draft_message', label: 'صياغة رسالة' },
    { key: 'classify_subject', label: 'تصنيف الموضوع' },
    { key: 'extract_elements', label: 'ابحث عن عناصر النص' },
    { key: 'shorten', label: 'اختصر' },
    { key: 'expand', label: 'اكتب بالتفصيل' },
    { key: 'simplify', label: 'تبسيط اللغة' },
    { key: 'make_formal', label: 'اجعل النص رسمي' },
    { key: 'text_conclusion', label: 'خلاصة نص' },
  ];

  const TEXT_FIELD_TYPES = ['Data', 'Small Text', 'Text', 'Text Editor', 'Code', 'Long Text'];

  function getTextFields(frm, options = {}) {
    const exclude = new Set(options.exclude || []);
    return (frm.meta.fields || [])
      .filter((df) => df.fieldname && !exclude.has(df.fieldname) && TEXT_FIELD_TYPES.includes(df.fieldtype) && !df.hidden)
      .map((df) => ({
        value: df.fieldname,
        label: `${__(df.label || df.fieldname)} (${df.fieldname})`,
      }));
  }

  function getOptionString(items, includeBlank = true) {
    const rows = [];
    if (includeBlank) rows.push('');
    items.forEach((item) => rows.push(item.value));
    return rows.join('\n');
  }

  function findBestDefaultField(fields, preferred = []) {
    for (const candidate of preferred) {
      if (fields.find((f) => f.value === candidate)) return candidate;
    }
    return fields[0]?.value || '';
  }

  function runTextAction(frm, action, options = {}) {
    const sourceFields = getTextFields(frm, { exclude: options.excludeSource || [] });
    if (!sourceFields.length) {
      frappe.msgprint(__('No supported text fields found on this form.'));
      return;
    }

    const defaultSource = findBestDefaultField(sourceFields, options.preferredSourceFields || ['details', 'description', 'subject']);
    const targetFields = getTextFields(frm, { exclude: options.excludeTarget || [] });
    const defaultTarget = findBestDefaultField(targetFields, options.preferredTargetFields || []);

    frappe.prompt([
      {
        fieldname: 'source_field',
        label: __('Source Field'),
        fieldtype: 'Select',
        options: getOptionString(sourceFields, false),
        default: defaultSource,
        reqd: 1,
      },
      {
        fieldname: 'target_field',
        label: __('Target Field'),
        fieldtype: 'Select',
        options: getOptionString(targetFields, true),
        default: defaultTarget,
      },
      {
        fieldname: 'extra_instruction',
        label: __('Additional Instruction'),
        fieldtype: 'Small Text',
        description: __('Optional custom instruction for the AI result.'),
      },
    ], (values) => {
      frappe.call({
        method: 'yemen_complaints.ai.perform_text_action',
        freeze: true,
        freeze_message: __('Running AI action...'),
        args: {
          doctype: frm.doctype,
          docname: frm.doc.name,
          source_field: values.source_field,
          target_field: values.target_field || null,
          action_key: action.key,
          extra_instruction: values.extra_instruction || null,
        },
        callback: (r) => showResultDialog(frm, action, values, r.message),
      });
    }, action.label, __('Run'));
  }

  function showResultDialog(frm, action, values, payload) {
    const dialog = new frappe.ui.Dialog({
      title: `${action.label} - ${payload.provider}`,
      size: 'large',
      fields: [
        {
          fieldname: 'result',
          label: __('Result'),
          fieldtype: 'Code',
          options: 'Text',
          read_only: 1,
          default: payload.result,
        },
      ],
      primary_action_label: values.target_field ? __('Apply to Target Field') : __('Apply to Source Field'),
      primary_action: () => {
        const fieldname = values.target_field || values.source_field;
        frm.set_value(fieldname, payload.result);
        dialog.hide();
        frappe.show_alert({ message: __('AI result applied to {0}', [fieldname]), indicator: 'green' });
      },
    });
    dialog.show();
    const copyButton = $('<button class="btn btn-default btn-sm" style="margin-inline-end:8px;">' + __('Copy') + '</button>');
    copyButton.on('click', async () => {
      try {
        await navigator.clipboard.writeText(payload.result || '');
        frappe.show_alert({ message: __('Copied to clipboard'), indicator: 'green' });
      } catch (e) {
        frappe.msgprint(__('Copy to clipboard failed.'));
      }
    });
    dialog.$wrapper.find('.modal-footer .standard-actions').prepend(copyButton);
  }

  function addTextActionButtons(frm, options = {}) {
    if (frm.is_new()) return;
    const group = options.group || 'AI Tools';
    ACTIONS.forEach((action) => {
      frm.add_custom_button(action.label, () => runTextAction(frm, action, options), group);
    });
  }

  function runIntakeAssistant(frm) {
    frappe.call({
      method: 'yemen_complaints.ai.run_intake_assistant',
      freeze: true,
      freeze_message: __('Running Smart Intake Assistant...'),
      args: { docname: frm.doc.name },
      callback: (r) => showIntakeAssistantDialog(frm, r.message),
    });
  }

  function showIntakeAssistantDialog(frm, payload) {
    const dialog = new frappe.ui.Dialog({
      title: __('Smart Intake Assistant') + ` - ${payload.provider}`,
      size: 'large',
      fields: [
        { fieldname: 'summary', label: __('Summary'), fieldtype: 'Small Text', read_only: 1, default: payload.summary },
        { fieldname: 'classification', label: __('Classification'), fieldtype: 'Data', read_only: 1, default: payload.classification },
        { fieldname: 'suggested_priority', label: __('Suggested Priority'), fieldtype: 'Data', read_only: 1, default: payload.suggested_priority },
        { fieldname: 'suggested_category', label: __('Suggested Category'), fieldtype: 'Data', read_only: 1, default: payload.suggested_category },
        { fieldname: 'suggested_entity', label: __('Suggested Entity'), fieldtype: 'Data', read_only: 1, default: payload.suggested_entity },
        { fieldname: 'key_elements', label: __('Key Elements'), fieldtype: 'Small Text', read_only: 1, default: payload.key_elements },
        { fieldname: 'risk_flags', label: __('Risk Flags'), fieldtype: 'Small Text', read_only: 1, default: payload.risk_flags },
        { fieldname: 'recommended_actions', label: __('Recommended Actions'), fieldtype: 'Small Text', read_only: 1, default: payload.recommended_actions },
        { fieldname: 'suggested_reply', label: __('Suggested Reply'), fieldtype: 'Text Editor', read_only: 1, default: payload.suggested_reply },
        { fieldname: 'citizen_message', label: __('Citizen Message'), fieldtype: 'Text Editor', read_only: 1, default: payload.citizen_message },
        { fieldname: 'reasoning', label: __('Reasoning'), fieldtype: 'Small Text', read_only: 1, default: payload.reasoning },
        { fieldname: 'raw_result', label: __('Raw JSON'), fieldtype: 'Code', options: 'JSON', read_only: 1, default: payload.raw_result },
      ],
      primary_action_label: __('Apply Assistant Fields'),
      primary_action: () => {
        frm.set_value('ai_case_summary', payload.summary || '');
        frm.set_value('ai_subject_classification', payload.classification || '');
        frm.set_value('ai_suggested_priority', payload.suggested_priority || '');
        frm.set_value('ai_suggested_category', payload.suggested_category || '');
        frm.set_value('ai_suggested_entity', payload.suggested_entity || '');
        frm.set_value('ai_key_elements', payload.key_elements || '');
        frm.set_value('ai_risk_flags', payload.risk_flags || '');
        frm.set_value('ai_recommended_actions', payload.recommended_actions || '');
        frm.set_value('ai_suggested_reply', payload.suggested_reply || '');
        frm.set_value('ai_citizen_message', payload.citizen_message || '');
        frm.set_value('ai_reasoning', payload.reasoning || '');
        frm.set_value('ai_analysis_json', payload.raw_result || '');
        frm.set_value('ai_last_provider', payload.provider || '');
        frm.set_value('ai_last_run_on', frappe.datetime.now_datetime());
        dialog.hide();
        frappe.show_alert({ message: __('Assistant results applied to AI fields'), indicator: 'green' });
      },
    });
    dialog.show();
  }

  function addIntakeAssistantButton(frm) {
    if (frm.is_new()) return;
    frm.add_custom_button(__('Smart Intake Assistant'), () => runIntakeAssistant(frm), __('AI Assistant'));
  }

  return {
    actions: ACTIONS,
    addTextActionButtons,
    addIntakeAssistantButton,
    runTextAction,
    runIntakeAssistant,
  };
})();
