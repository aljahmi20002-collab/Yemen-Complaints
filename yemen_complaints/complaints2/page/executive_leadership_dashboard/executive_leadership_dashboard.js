frappe.pages['executive-leadership-dashboard'] = frappe.pages['executive-leadership-dashboard'] || {};
frappe.pages['executive-leadership-dashboard'].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __('داشبورد القيادة العليا'),
    single_column: true,
  });

  wrapper.classList.add('yc-executive-dashboard-page');
  page.set_primary_action(__('Refresh'), () => loadExecutiveDashboard(wrapper));
  page.set_secondary_action(__('Print Snapshot'), () => window.print());
  page.add_menu_item(__('Export Snapshot JSON'), () => exportExecutiveSnapshotJson(wrapper));
  loadExecutiveDashboard(wrapper);
};

function getExecutiveFilters(wrapper) {
  return {
    time_filter: wrapper.querySelector('#ex-time-filter')?.value || '',
    entity_filter: wrapper.querySelector('#ex-entity-filter')?.value || '',
    governorate_filter: wrapper.querySelector('#ex-governorate-filter')?.value || '',
    category_filter: wrapper.querySelector('#ex-category-filter')?.value || '',
  };
}

function loadExecutiveDashboard(wrapper) {
  wrapper.innerHTML = `
    <div class="ex-page">
      <div class="ex-shell">
        <section class="ex-hero">
          <div class="ex-hero-inner">
            <div>
              <div class="ex-badge">لوحة قيادية عليا</div>
              <h1>داشبورد القيادة العليا لاتخاذ القرار ومراقبة الأداء</h1>
              <p>لوحة آنية وآلية وشاملة لعرض المؤشرات القيادية، صحة SLA، جودة التحقق من الهوية، النشاط التحليلي، الاتجاهات الزمنية، والجهات أو الفئات التي تتطلب قراراً أو تدخلاً سريعاً.</p>
            </div>
            <div class="ex-side">
              <h3>تحميل المؤشرات الاستراتيجية...</h3>
              <p>يتم تجهيز لوحة القيادة التنفيذية بالتحليلات الملائمة للمديرين وصناع القرار.</p>
            </div>
          </div>
        </section>
        <section class="ex-loading-grid">
          <div class="ex-card ex-skeleton"></div>
          <div class="ex-card ex-skeleton"></div>
          <div class="ex-card ex-skeleton"></div>
          <div class="ex-card ex-skeleton"></div>
        </section>
      </div>
    </div>
  `;

  frappe.call({
    method: 'yemen_complaints.api.get_executive_dashboard_summary',
    freeze: false,
    callback: (r) => renderExecutiveDashboard(wrapper, r.message),
    error: () => {
      wrapper.querySelector('.ex-shell').innerHTML += '<div class="ex-card ex-error">تعذر تحميل بيانات الداشبورد التنفيذي.</div>';
    },
  });
}

function refreshExecutiveDashboard(wrapper) {
  frappe.call({
    method: 'yemen_complaints.api.get_executive_dashboard_summary',
    freeze: false,
    args: getExecutiveFilters(wrapper),
    callback: (r) => renderExecutiveDashboard(wrapper, r.message),
  });
}

function renderExecutiveDashboard(wrapper, data) {
  const counts = data.counts || {};
  const kpis = data.kpis || {};
  const alerts = data.executive_alerts || [];
  const decisionSupport = data.decision_support || [];
  const quickLinks = data.quick_links || [];
  const criticalCases = data.recent_critical_cases || [];
  const topOverdueEntities = data.top_overdue_entities || [];
  const statusBreakdown = data.status_breakdown || [];
  const priorityBreakdown = data.priority_breakdown || [];
  const entityBreakdown = data.entity_breakdown || [];
  const governorateBreakdown = data.governorate_breakdown || [];
  const categoryBreakdown = data.category_breakdown || [];
  const countryBreakdown = data.country_breakdown || [];
  const channelBreakdown = data.channel_breakdown || [];
  const monthlyIntake = data.monthly_intake_trend || [];
  const monthlyClosure = data.monthly_closure_trend || [];
  const verificationHealth = data.verification_health || [];
  const verificationChannels = data.verification_channels || [];
  const aiHealth = data.ai_health || {};
  const filterOptions = data.filter_options || {};
  const appliedFilters = data.applied_filters || {};

  wrapper.__executive_dashboard_data = data;

  const alertsHtml = alerts.map((row) => `
    <a class="ex-alert ex-alert-${frappe.utils.escape_html(row.severity || 'neutral')}" href="${frappe.utils.escape_html(row.route || '#')}">
      <div>
        <b>${frappe.utils.escape_html(row.title || '')}</b>
        <span>${frappe.utils.escape_html(row.description || '')}</span>
      </div>
      <i>↗</i>
    </a>
  `).join('');

  const quickLinksHtml = quickLinks.map((row) => `
    <a class="ex-link-card" href="${frappe.utils.escape_html(row.route || '#')}">
      <b>${frappe.utils.escape_html(row.label || '')}</b>
      <span>انتقال مباشر</span>
    </a>
  `).join('');

  const criticalHtml = criticalCases.length
    ? criticalCases.map((row) => `
        <a class="ex-case-row ex-case-row-critical" href="/app/complaint-case/${encodeURIComponent(row.name)}">
          <div>
            <b>${frappe.utils.escape_html(row.subject || row.name || '')}</b>
            <small>${frappe.utils.escape_html(row.name || '')}</small>
          </div>
          <div class="ex-case-meta">
            <span class="ex-chip ex-chip-priority">${frappe.utils.escape_html(row.priority || '')}</span>
            <span class="ex-chip ex-chip-status">${frappe.utils.escape_html(row.status || '')}</span>
          </div>
        </a>
      `).join('')
    : '<div class="ex-empty">لا توجد حالات حرجة ضمن الفلاتر الحالية.</div>';

  const overdueEntitiesHtml = topOverdueEntities.length
    ? topOverdueEntities.map((row) => `
        <button class="ex-metric-row ex-action-btn" data-entity="${frappe.utils.escape_html(row.label || '')}">
          <div class="ex-metric-head"><span>${frappe.utils.escape_html(row.label || '')}</span><strong>${row.count || 0}</strong></div>
          <div class="ex-meter"><div class="ex-meter-fill ex-meter-red" style="width:${Math.max(8, Math.round(((row.count || 0) / Math.max(...topOverdueEntities.map((r) => r.count || 0), 1)) * 100))}%"></div></div>
        </button>
      `).join('')
    : '<div class="ex-empty">لا توجد جهات متأخرة حالياً.</div>';

  const insightHtml = decisionSupport.length
    ? decisionSupport.map((row) => `<div class="ex-insight-item">${frappe.utils.escape_html(row)}</div>`).join('')
    : '<div class="ex-empty">لا توجد توصيات قيادية إضافية حالياً.</div>';

  wrapper.innerHTML = `
    <div class="ex-page">
      <div class="ex-shell">
        <section class="ex-hero">
          <div class="ex-hero-inner">
            <div>
              <div class="ex-badge">لوحة قيادية عليا</div>
              <h1>الداشبورد التنفيذي — مؤشرات فورية لدعم القرار</h1>
              <p>تجميعة قيادية تعرض الأحجام العامة، المخاطر، الأداء، الاتجاهات، وأكثر الجهات والفئات استهلاكاً أو تأخراً، مع قدرة على الفلترة والانتقال السريع إلى القوائم والتقارير.</p>
            </div>
            <div class="ex-side">
              <div class="ex-side-box"><span>إجمالي الحالات</span><strong>${counts.total_cases || 0}</strong></div>
              <div class="ex-side-box"><span>الحالات المتأخرة</span><strong>${counts.overdue_cases || 0}</strong></div>
              <div class="ex-side-box"><span>نسبة SLA للحسم</span><strong>${kpis.resolution_sla_rate || 0}%</strong></div>
              <div class="ex-side-box"><span>نسبة نجاح AI</span><strong>${aiHealth.success_rate || 0}%</strong></div>
            </div>
          </div>
        </section>

        <section class="ex-card">
          <div class="ex-card-head">
            <div>
              <h3>فلاتر الداشبورد التنفيذي</h3>
              <p>فلترة القياس حسب الفترة الزمنية أو الجهة أو المحافظة أو التصنيف.</p>
            </div>
          </div>
          <div class="ex-filter-grid">
            <div class="ex-filter-field">
              <label>الفترة الزمنية</label>
              <select id="ex-time-filter" class="form-control">
                ${(filterOptions.time_ranges || []).map((row) => `<option value="${frappe.utils.escape_html(row.value)}" ${appliedFilters.time_filter === row.value ? 'selected' : ''}>${frappe.utils.escape_html(row.label)}</option>`).join('')}
              </select>
            </div>
            <div class="ex-filter-field">
              <label>الجهة</label>
              <select id="ex-entity-filter" class="form-control">
                ${(filterOptions.entities || []).map((value) => `<option value="${frappe.utils.escape_html(value)}" ${appliedFilters.entity_filter === value ? 'selected' : ''}>${frappe.utils.escape_html(value || 'الكل')}</option>`).join('')}
              </select>
            </div>
            <div class="ex-filter-field">
              <label>المحافظة</label>
              <select id="ex-governorate-filter" class="form-control">
                ${(filterOptions.governorates || []).map((value) => `<option value="${frappe.utils.escape_html(value)}" ${appliedFilters.governorate_filter === value ? 'selected' : ''}>${frappe.utils.escape_html(value || 'الكل')}</option>`).join('')}
              </select>
            </div>
            <div class="ex-filter-field">
              <label>التصنيف</label>
              <select id="ex-category-filter" class="form-control">
                ${(filterOptions.categories || []).map((value) => `<option value="${frappe.utils.escape_html(value)}" ${appliedFilters.category_filter === value ? 'selected' : ''}>${frappe.utils.escape_html(value || 'الكل')}</option>`).join('')}
              </select>
            </div>
            <div class="ex-filter-actions">
              <button class="ex-btn ex-btn-primary" onclick="refreshExecutiveDashboard(document.querySelector('.yc-executive-dashboard-page'))">تطبيق الفلاتر</button>
              <button class="ex-btn ex-btn-outline" onclick="resetExecutiveDashboardFilters(document.querySelector('.yc-executive-dashboard-page'))">إعادة ضبط</button>
            </div>
          </div>
        </section>

        <section class="ex-alerts-grid">${alertsHtml}</section>

        <section class="ex-executive-strip">
          ${makeExecutiveTile('إجمالي الحالات', counts.total_cases || 0, 'neutral')}
          ${makeExecutiveTile('الحالات المفتوحة', counts.open_cases || 0, 'blue')}
          ${makeExecutiveTile('المتأخرة', counts.overdue_cases || 0, 'red')}
          ${makeExecutiveTile('عالية الأولوية', counts.high_priority_cases || 0, 'orange')}
          ${makeExecutiveTile('نسبة أول استجابة ضمن SLA', `${kpis.first_response_sla_rate || 0}%`, 'purple')}
          ${makeExecutiveTile('نسبة الحسم ضمن SLA', `${kpis.resolution_sla_rate || 0}%`, 'green')}
          ${makeExecutiveTile('متوسط الرضا', kpis.avg_satisfaction || 0, 'green')}
          ${makeExecutiveTile('عدد الجهات النشطة', kpis.distinct_entities || 0, 'neutral')}
        </section>

        <section class="ex-action-center-card ex-card">
          <div class="ex-card-head">
            <div>
              <h3>مؤشرات دعم القرار</h3>
              <p>توصيات تنفيذية تساعد القيادة العليا في تحديد أولويات التدخل والمتابعة.</p>
            </div>
          </div>
          <div class="ex-insight-list">${insightHtml}</div>
        </section>

        <section class="ex-split-grid">
          <article class="ex-card">
            <div class="ex-card-head"><div><h3>الوصول السريع</h3><p>نقاط انتقال مباشرة للتقارير والقوائم التنفيذية.</p></div></div>
            <div class="ex-links-grid">${quickLinksHtml}</div>
          </article>
          <article class="ex-card">
            <div class="ex-card-head"><div><h3>الحالات الحرجة المفتوحة</h3><p>طلبات تحتاج رؤية ومتابعة على المستوى القيادي.</p></div></div>
            <div class="ex-cases-list">${criticalHtml}</div>
          </article>
        </section>

        <section class="ex-widget-grid">
          <article class="ex-card"><div class="ex-card-head"><div><h3>الحالات حسب الحالة</h3></div></div><div class="ex-chart-widget" id="ex-chart-status"></div></article>
          <article class="ex-card"><div class="ex-card-head"><div><h3>الحالات حسب الأولوية</h3></div></div><div class="ex-chart-widget" id="ex-chart-priority"></div></article>
          <article class="ex-card"><div class="ex-card-head"><div><h3>الحالات حسب الجهة</h3></div></div><div class="ex-chart-widget" id="ex-chart-entity"></div></article>
          <article class="ex-card"><div class="ex-card-head"><div><h3>الحالات حسب التصنيف</h3></div></div><div class="ex-chart-widget" id="ex-chart-category"></div></article>
        </section>

        <section class="ex-widget-grid">
          <article class="ex-card"><div class="ex-card-head"><div><h3>الحالات حسب المحافظة</h3></div></div><div class="ex-chart-widget" id="ex-chart-governorate"></div></article>
          <article class="ex-card"><div class="ex-card-head"><div><h3>الحالات حسب الدولة</h3></div></div><div class="ex-chart-widget" id="ex-chart-country"></div></article>
          <article class="ex-card"><div class="ex-card-head"><div><h3>قنوات الاستقبال</h3></div></div><div class="ex-chart-widget" id="ex-chart-channel"></div></article>
          <article class="ex-card"><div class="ex-card-head"><div><h3>قنوات التحقق OTP</h3></div></div><div class="ex-chart-widget" id="ex-chart-verification-channel"></div></article>
        </section>

        <section class="ex-split-grid">
          <article class="ex-card">
            <div class="ex-card-head"><div><h3>الاتجاه الشهري للحالات الواردة</h3></div></div>
            ${makeExecutiveTrend(monthlyIntake, '#9b1c1c', '#f59e0b')}
          </article>
          <article class="ex-card">
            <div class="ex-card-head"><div><h3>الاتجاه الشهري للحالات المحسومة</h3></div></div>
            ${makeExecutiveTrend(monthlyClosure, '#166534', '#4ade80')}
          </article>
        </section>

        <section class="ex-split-grid">
          <article class="ex-card">
            <div class="ex-card-head"><div><h3>أكثر الجهات تأخراً</h3><p>الجهات التي تتكرر فيها الحالات المتأخرة.</p></div></div>
            <div class="ex-metric-list">${overdueEntitiesHtml}</div>
          </article>
          <article class="ex-card">
            <div class="ex-card-head"><div><h3>صحة التحقق والذكاء الاصطناعي</h3><p>مزيج رقابي على سجل OTP وصحة AI.</p></div></div>
            <div class="ex-health-grid">
              <div class="ex-health-box"><small>نجاحات AI</small><strong>${aiHealth.success || 0}</strong></div>
              <div class="ex-health-box"><small>أخطاء AI</small><strong>${aiHealth.error || 0}</strong></div>
              <div class="ex-health-box"><small>نسبة نجاح AI</small><strong>${aiHealth.success_rate || 0}%</strong></div>
              <div class="ex-health-box"><small>قنوات تحقق OTP</small><strong>${verificationChannels.length || 0}</strong></div>
              <div class="ex-health-box"><small>حالات OTP مميزة</small><strong>${verificationHealth.length || 0}</strong></div>
              <div class="ex-health-box"><small>متوسط الرضا</small><strong>${kpis.avg_satisfaction || 0}</strong></div>
            </div>
          </article>
        </section>
      </div>
    </div>
  `;

  bindExecutiveDashboardEvents(wrapper);
  initExecutiveCharts({
    statusBreakdown,
    priorityBreakdown,
    entityBreakdown,
    categoryBreakdown,
    governorateBreakdown,
    countryBreakdown,
    channelBreakdown,
    verificationChannels,
  });
}

function makeExecutiveTile(label, value, tone) {
  return `<div class="ex-tile ex-tile-${tone}"><small>${frappe.utils.escape_html(label)}</small><strong>${value}</strong></div>`;
}

function makeExecutiveTrend(rows, color1, color2) {
  const values = rows || [];
  const max = Math.max(...values.map((r) => r.count || 0), 1);
  if (!values.length) return '<div class="ex-empty">لا توجد بيانات زمنية متاحة.</div>';
  return `
    <div class="ex-trend-chart">
      ${values.map((row) => {
        const height = Math.max(16, Math.round(((row.count || 0) / max) * 160));
        return `<div class="ex-trend-col"><div class="ex-trend-bar"><span style="height:${height}px;background:linear-gradient(180deg, ${color1}, ${color2});"></span></div><strong>${row.count || 0}</strong><small>${frappe.utils.escape_html(row.label || '')}</small></div>`;
      }).join('')}
    </div>
  `;
}

function bindExecutiveDashboardEvents(wrapper) {
  wrapper.querySelectorAll('.ex-action-btn').forEach((button) => {
    button.addEventListener('click', () => {
      const filters = {
        entity: button.dataset.entity || '',
        category: button.dataset.category || '',
      };
      openExecutiveCaseList(filters);
    });
  });
}

function openExecutiveCaseList(filters) {
  const routeFilters = {};
  if (filters.entity) routeFilters.government_entity = filters.entity;
  if (filters.category) routeFilters.category = filters.category;
  frappe.set_route('List', 'Complaint Case', 'List', routeFilters);
}

function resetExecutiveDashboardFilters(wrapper) {
  wrapper.querySelector('#ex-time-filter').value = '';
  wrapper.querySelector('#ex-entity-filter').value = '';
  wrapper.querySelector('#ex-governorate-filter').value = '';
  wrapper.querySelector('#ex-category-filter').value = '';
  refreshExecutiveDashboard(wrapper);
}

function exportExecutiveSnapshotJson(wrapper) {
  const data = wrapper.__executive_dashboard_data;
  if (!data) {
    frappe.msgprint(__('No executive snapshot data available yet.'));
    return;
  }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `executive-dashboard-snapshot-${frappe.datetime.nowdate()}.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function initExecutiveCharts({ statusBreakdown = [], priorityBreakdown = [], entityBreakdown = [], categoryBreakdown = [], governorateBreakdown = [], countryBreakdown = [], channelBreakdown = [], verificationChannels = [] }) {
  renderExecutiveChart('ex-chart-status', 'donut', statusBreakdown, '#1d4ed8');
  renderExecutiveChart('ex-chart-priority', 'bar', priorityBreakdown, '#9b1c1c');
  renderExecutiveChart('ex-chart-entity', 'bar', entityBreakdown, '#7c3aed');
  renderExecutiveChart('ex-chart-category', 'bar', categoryBreakdown, '#0f766e');
  renderExecutiveChart('ex-chart-governorate', 'bar', governorateBreakdown, '#d97706');
  renderExecutiveChart('ex-chart-country', 'bar', countryBreakdown, '#0ea5e9');
  renderExecutiveChart('ex-chart-channel', 'donut', channelBreakdown, '#f59e0b');
  renderExecutiveChart('ex-chart-verification-channel', 'donut', verificationChannels, '#10b981');
}

function renderExecutiveChart(containerId, chartType, rows, color) {
  const container = document.getElementById(containerId);
  if (!container) return;
  if (!rows.length) {
    container.innerHTML = '<div class="ex-empty">لا توجد بيانات كافية لعرض الرسم.</div>';
    return;
  }
  if (window.frappe && frappe.Chart) {
    container.innerHTML = '';
    new frappe.Chart(container, {
      data: {
        labels: rows.map((row) => row.label || '—'),
        datasets: [{ name: __('Cases'), values: rows.map((row) => row.count || 0) }],
      },
      type: chartType,
      colors: [color],
      height: 260,
    });
    return;
  }
  const max = Math.max(...rows.map((row) => row.count || 0), 1);
  container.innerHTML = rows.map((row) => {
    const width = Math.max(8, Math.round(((row.count || 0) / max) * 100));
    return `
      <div class="ex-fallback-chart-row">
        <div class="ex-metric-head"><span>${frappe.utils.escape_html(row.label || '')}</span><strong>${row.count || 0}</strong></div>
        <div class="ex-meter"><div class="ex-meter-fill" style="width:${width}%;background:${color};"></div></div>
      </div>
    `;
  }).join('');
}
