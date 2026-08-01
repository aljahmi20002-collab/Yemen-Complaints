frappe.pages['security-monitoring-dashboard'] = frappe.pages['security-monitoring-dashboard'] || {};
frappe.pages['security-monitoring-dashboard'].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __('داشبورد مراقبة الأمن والحماية'),
    single_column: true,
  });

  wrapper.classList.add('yc-security-dashboard-page');
  page.set_primary_action(__('Refresh'), () => loadSecurityDashboard(wrapper));
  loadSecurityDashboard(wrapper);
};

function getSecurityFilters(wrapper) {
  return {
    time_filter: wrapper.querySelector('#sd-time-filter')?.value || '',
    severity_filter: wrapper.querySelector('#sd-severity-filter')?.value || '',
    status_filter: wrapper.querySelector('#sd-status-filter')?.value || '',
  };
}

function loadSecurityDashboard(wrapper) {
  wrapper.innerHTML = `
    <div class="sd-page"><div class="sd-shell">
      <section class="sd-hero"><div class="sd-hero-inner"><div><div class="sd-badge">لوحة أمنية تشغيلية</div><h1>مراقبة الأمن والحماية ومكافحة إساءة الاستخدام</h1><p>لوحة تركز على OTP abuse، تتبع الحالات العام، استهلاك الذكاء الاصطناعي، ومحاولات الحظر أو النشاطات الحرجة حسب الزمن والشدة والحالة.</p></div><div class="sd-side"><h3>جارٍ تحميل البيانات...</h3><p>يتم تجهيز ملخصات الحماية الأمنية ومصادر الإساءة المحتملة.</p></div></div></section>
      <section class="sd-loading-grid"><div class="sd-card sd-skeleton"></div><div class="sd-card sd-skeleton"></div><div class="sd-card sd-skeleton"></div></section>
    </div></div>
  `;
  frappe.call({
    method: 'yemen_complaints.api.get_security_monitoring_summary',
    freeze: false,
    callback: (r) => renderSecurityDashboard(wrapper, r.message),
    error: () => {
      wrapper.querySelector('.sd-shell').innerHTML += '<div class="sd-card sd-error">تعذر تحميل بيانات لوحة الأمن والحماية.</div>';
    },
  });
}

function refreshSecurityDashboard(wrapper) {
  frappe.call({
    method: 'yemen_complaints.api.get_security_monitoring_summary',
    args: getSecurityFilters(wrapper),
    freeze: false,
    callback: (r) => renderSecurityDashboard(wrapper, r.message),
  });
}

function renderSecurityDashboard(wrapper, data) {
  const counts = data.counts || {};
  const alerts = data.alerts || [];
  const filterOptions = data.filter_options || {};
  const applied = data.applied_filters || {};
  const eventTypes = data.event_type_breakdown || [];
  const severities = data.severity_breakdown || [];
  const statuses = data.status_breakdown || [];
  const endpoints = data.endpoint_breakdown || [];
  const ips = data.ip_breakdown || [];
  const trend = data.event_trend || [];
  const identifiers = data.top_identifiers || [];
  const users = data.top_users || [];
  const recent = data.recent_events || [];
  const links = data.quick_links || [];

  const alertsHtml = alerts.map((row) => `
    <a class="sd-alert sd-alert-${frappe.utils.escape_html(row.severity || 'neutral')}" href="${frappe.utils.escape_html(row.route || '#')}">
      <div><b>${frappe.utils.escape_html(row.title || '')}</b><span>${frappe.utils.escape_html(row.description || '')}</span></div>
      <i>↗</i>
    </a>`).join('');

  const recentHtml = recent.length ? recent.map((row) => `
    <div class="sd-event-row">
      <div>
        <b>${frappe.utils.escape_html(row.event_type || '')}</b>
        <small>${frappe.utils.escape_html(row.endpoint || '')} — ${frappe.utils.escape_html(row.identifier || '')}</small>
        <div class="sd-event-message">${frappe.utils.escape_html(row.message || '')}</div>
      </div>
      <div class="sd-event-meta">
        <span class="sd-chip sd-chip-${(row.severity || 'low').toLowerCase()}">${frappe.utils.escape_html(row.severity || '')}</span>
        <span class="sd-chip sd-chip-status">${frappe.utils.escape_html(row.status || '')}</span>
      </div>
    </div>`).join('') : '<div class="sd-empty">لا توجد أحداث حديثة.</div>';

  const linksHtml = links.map((row) => `<a class="sd-link-card" href="${frappe.utils.escape_html(row.route || '#')}"><b>${frappe.utils.escape_html(row.label || '')}</b><span>انتقال مباشر</span></a>`).join('');

  wrapper.innerHTML = `
    <div class="sd-page"><div class="sd-shell">
      <section class="sd-hero">
        <div class="sd-hero-inner">
          <div><div class="sd-badge">لوحة أمنية تشغيلية</div><h1>داشبورد الأمن والحماية</h1><p>مركز رقابي لمتابعة الأنشطة المحظورة، التهديدات التشغيلية، استهلاك OTP وAI، وحركة الأحداث الأمنية حسب الزمن والنطاق.</p></div>
          <div class="sd-side">
            <div class="sd-side-box"><span>إجمالي الأحداث</span><strong>${counts.total_events || 0}</strong></div>
            <div class="sd-side-box"><span>أحداث محظورة</span><strong>${counts.blocked_events || 0}</strong></div>
            <div class="sd-side-box"><span>حرجة</span><strong>${counts.critical_events || 0}</strong></div>
            <div class="sd-side-box"><span>عالية الشدة</span><strong>${counts.high_events || 0}</strong></div>
          </div>
        </div>
      </section>

      <section class="sd-card">
        <div class="sd-card-head"><div><h3>فلاتر الأمن والحماية</h3><p>فلترة حسب الزمن أو الشدة أو الحالة.</p></div></div>
        <div class="sd-filter-grid">
          <div class="sd-filter-field"><label>الفترة الزمنية</label><select id="sd-time-filter" class="form-control">${(filterOptions.time_ranges || []).map((row) => `<option value="${frappe.utils.escape_html(row.value)}" ${applied.time_filter === row.value ? 'selected' : ''}>${frappe.utils.escape_html(row.label)}</option>`).join('')}</select></div>
          <div class="sd-filter-field"><label>الشدة</label><select id="sd-severity-filter" class="form-control">${(filterOptions.severities || []).map((value) => `<option value="${frappe.utils.escape_html(value)}" ${applied.severity_filter === value ? 'selected' : ''}>${frappe.utils.escape_html(value || 'الكل')}</option>`).join('')}</select></div>
          <div class="sd-filter-field"><label>الحالة</label><select id="sd-status-filter" class="form-control">${(filterOptions.statuses || []).map((value) => `<option value="${frappe.utils.escape_html(value)}" ${applied.status_filter === value ? 'selected' : ''}>${frappe.utils.escape_html(value || 'الكل')}</option>`).join('')}</select></div>
          <div class="sd-filter-actions"><button class="sd-btn sd-btn-primary" onclick="refreshSecurityDashboard(document.querySelector('.yc-security-dashboard-page'))">تطبيق</button><button class="sd-btn sd-btn-outline" onclick="resetSecurityDashboardFilters(document.querySelector('.yc-security-dashboard-page'))">إعادة ضبط</button></div>
        </div>
      </section>

      <section class="sd-alerts-grid">${alertsHtml}</section>

      <section class="sd-stats-grid">
        ${makeSecurityTile('إجمالي الأحداث', counts.total_events || 0, 'neutral')}
        ${makeSecurityTile('محظورة', counts.blocked_events || 0, 'red')}
        ${makeSecurityTile('مرصودة', counts.observed_events || 0, 'orange')}
        ${makeSecurityTile('مسموح بها', counts.allowed_events || 0, 'green')}
        ${makeSecurityTile('حرجة', counts.critical_events || 0, 'red')}
        ${makeSecurityTile('عالية الشدة', counts.high_events || 0, 'purple')}
      </section>

      <section class="sd-widget-grid">
        ${makeSecurityMetricPanel('أنواع الأحداث', eventTypes, 'event')}
        ${makeSecurityMetricPanel('التوزيع حسب الشدة', severities, 'severity')}
        ${makeSecurityMetricPanel('التوزيع حسب الحالة', statuses, 'status')}
        ${makeSecurityMetricPanel('أكثر الـ endpoints نشاطاً', endpoints, 'endpoint')}
      </section>

      <section class="sd-split-grid">
        <article class="sd-card"><div class="sd-card-head"><div><h3>أكثر عناوين IP تكراراً</h3></div></div>${makeSecurityMetricPanelBody(ips, 'ip')}</article>
        <article class="sd-card"><div class="sd-card-head"><div><h3>أكثر المعرفات تكراراً</h3></div></div>${makeSecurityMetricPanelBody(identifiers, 'identifier')}</article>
      </section>

      <section class="sd-split-grid">
        <article class="sd-card"><div class="sd-card-head"><div><h3>أكثر المستخدمين نشاطاً</h3></div></div>${makeSecurityMetricPanelBody(users, 'user')}</article>
        <article class="sd-card"><div class="sd-card-head"><div><h3>الاتجاه الزمني للأحداث</h3></div></div>${makeSecurityTrend(trend)}</article>
      </section>

      <section class="sd-split-grid">
        <article class="sd-card"><div class="sd-card-head"><div><h3>الوصول السريع</h3><p>انتقل مباشرة إلى سجلات الأمن أو OTP أو AI.</p></div></div><div class="sd-links-grid">${linksHtml}</div></article>
        <article class="sd-card"><div class="sd-card-head"><div><h3>آخر الأحداث</h3><p>آخر الأحداث الأمنية المسجلة في النظام.</p></div></div><div class="sd-events-list">${recentHtml}</div></article>
      </section>
    </div></div>
  `;
}

function makeSecurityTile(label, value, tone) {
  return `<div class="sd-tile sd-tile-${tone}"><small>${frappe.utils.escape_html(label)}</small><strong>${value}</strong></div>`;
}

function makeSecurityMetricPanel(title, rows, tone) {
  return `<article class="sd-card"><div class="sd-card-head"><div><h3>${frappe.utils.escape_html(title)}</h3></div></div>${makeSecurityMetricPanelBody(rows, tone)}</article>`;
}

function makeSecurityMetricPanelBody(rows, tone) {
  const values = rows || [];
  const max = Math.max(...values.map((r) => r.count || 0), 1);
  if (!values.length) return '<div class="sd-empty">لا توجد بيانات متاحة.</div>';
  return `<div class="sd-metric-list">${values.map((row) => {
    const width = Math.max(8, Math.round(((row.count || 0) / max) * 100));
    return `<div class="sd-metric-row"><div class="sd-metric-head"><span>${frappe.utils.escape_html(row.label || '')}</span><strong>${row.count || 0}</strong></div><div class="sd-meter"><div class="sd-meter-fill sd-meter-${tone}" style="width:${width}%"></div></div></div>`;
  }).join('')}</div>`;
}

function makeSecurityTrend(rows) {
  const values = rows || [];
  const max = Math.max(...values.map((r) => r.count || 0), 1);
  if (!values.length) return '<div class="sd-empty">لا توجد بيانات زمنية متاحة.</div>';
  return `<div class="sd-trend-chart">${values.map((row) => {
    const height = Math.max(16, Math.round(((row.count || 0) / max) * 150));
    return `<div class="sd-trend-col"><div class="sd-trend-bar"><span style="height:${height}px"></span></div><strong>${row.count || 0}</strong><small>${frappe.utils.escape_html(row.label || '')}</small></div>`;
  }).join('')}</div>`;
}

function resetSecurityDashboardFilters(wrapper) {
  wrapper.querySelector('#sd-time-filter').value = '';
  wrapper.querySelector('#sd-severity-filter').value = '';
  wrapper.querySelector('#sd-status-filter').value = '';
  refreshSecurityDashboard(wrapper);
}
