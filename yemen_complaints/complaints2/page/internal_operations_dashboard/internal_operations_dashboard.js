frappe.pages['internal-operations-dashboard'] = frappe.pages['internal-operations-dashboard'] || {};
frappe.pages['internal-operations-dashboard'].on_page_load = function (wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: __('الداشبورد الداخلي للعمليات'),
    single_column: true,
  });

  wrapper.classList.add('yc-internal-dashboard-page');
  page.set_primary_action(__('Refresh'), () => loadInternalDashboard(wrapper));
  loadInternalDashboard(wrapper);
};

function getDashboardFilters(wrapper) {
  return {
    status_filter: wrapper.querySelector('#io-status-filter')?.value || '',
    priority_filter: wrapper.querySelector('#io-priority-filter')?.value || '',
    entity_filter: wrapper.querySelector('#io-entity-filter')?.value || '',
  };
}

function loadInternalDashboard(wrapper) {
  wrapper.innerHTML = `
    <div class="io-page">
      <div class="io-shell">
        <section class="io-hero">
          <div class="io-hero-inner">
            <div>
              <div class="io-badge">لوحة تشغيلية داخلية</div>
              <h1>داشبورد داخلي احترافي للمستشار والموظفين</h1>
              <p>لوحة موحدة لمتابعة مؤشرات الحالات، قوائم العمل، آخر الطلبات، التحليلات السريعة، والوصول السريع إلى التقارير والإعدادات وسجلات الذكاء الاصطناعي والتحقق من الهوية.</p>
            </div>
            <div class="io-side">
              <h3>جارٍ تحميل البيانات...</h3>
              <p>يتم الآن استدعاء المؤشرات المناسبة وفق دور المستخدم وصلاحياته.</p>
            </div>
          </div>
        </section>
        <section class="io-grid io-loading-grid">
          <div class="io-card io-skeleton"></div>
          <div class="io-card io-skeleton"></div>
          <div class="io-card io-skeleton"></div>
          <div class="io-card io-skeleton"></div>
        </section>
      </div>
    </div>
  `;

  frappe.call({
    method: 'yemen_complaints.api.get_internal_dashboard_summary',
    freeze: false,
    callback: (r) => renderInternalDashboard(wrapper, r.message),
    error: () => {
      wrapper.querySelector('.io-shell').innerHTML += '<div class="io-card io-error">تعذر تحميل بيانات الداشبورد الداخلي.</div>';
    },
  });
}

function refreshInternalDashboard(wrapper) {
  frappe.call({
    method: 'yemen_complaints.api.get_internal_dashboard_summary',
    freeze: false,
    args: getDashboardFilters(wrapper),
    callback: (r) => renderInternalDashboard(wrapper, r.message),
  });
}

function renderInternalDashboard(wrapper, data) {
  const counts = data.counts || {};
  const queue = data.my_queue || [];
  const recentCases = data.recent_cases || [];
  const urgentCases = data.urgent_cases || [];
  const links = data.quick_links || [];
  const statusBreakdown = data.status_breakdown || [];
  const priorityBreakdown = data.priority_breakdown || [];
  const entityBreakdown = data.entity_breakdown || [];
  const monthlyTrend = data.monthly_trend || [];
  const verificationBreakdown = data.verification_breakdown || [];
  const aiActivity = data.ai_activity || [];
  const topOfficers = data.top_officers || [];
  const slaHealth = data.sla_health || {};
  const filterOptions = data.filter_options || {};
  const appliedFilters = data.applied_filters || {};

  const queueHtml = queue.length
    ? queue.map((row) => `
        <button class="io-queue-item io-action-btn" data-status="" data-priority="" data-entity="">
          <span>${frappe.utils.escape_html(row.label || '')}</span>
          <strong>${row.count || 0}</strong>
        </button>
      `).join('')
    : '<div class="io-empty">لا توجد قوائم عمل مخصصة لهذا الدور حالياً.</div>';

  const recentHtml = renderCaseRows(recentCases, 'لا توجد حالات حديثة ضمن نطاق صلاحياتك.');
  const urgentHtml = renderCaseRows(urgentCases, 'لا توجد حالات عاجلة مفتوحة حالياً.', true);

  const linksHtml = links.map((row) => `
    <a class="io-link-card" href="${frappe.utils.escape_html(row.route || '#')}">
      <b>${frappe.utils.escape_html(row.label || '')}</b>
      <span>انتقال سريع</span>
    </a>
  `).join('');

  const aiHtml = aiActivity.length
    ? aiActivity.map((row) => `
        <div class="io-ai-row">
          <div>
            <b>${frappe.utils.escape_html(row.action_label || row.provider || '')}</b>
            <small>${frappe.utils.escape_html(row.reference_name || '')}</small>
          </div>
          <div class="io-case-meta">
            <span class="io-chip io-chip-status">${frappe.utils.escape_html(row.provider || '')}</span>
            <span class="io-chip ${row.status === 'Error' ? 'io-chip-priority' : 'io-chip-success'}">${frappe.utils.escape_html(row.status || '')}</span>
          </div>
        </div>
      `).join('')
    : '<div class="io-empty">لا توجد أنشطة ذكاء اصطناعي حديثة.</div>';

  const officersHtml = topOfficers.length
    ? topOfficers.map((row) => `
        <div class="io-officer-row">
          <div>
            <b>${frappe.utils.escape_html(row.user || '')}</b>
            <small>${frappe.utils.escape_html(row.role_label || '')}</small>
          </div>
          <strong>${row.count || 0}</strong>
        </div>
      `).join('')
    : '<div class="io-empty">لا توجد بيانات كافية لاحتساب أكثر المستخدمين نشاطاً.</div>';

  wrapper.innerHTML = `
    <div class="io-page">
      <div class="io-shell">
        <section class="io-hero">
          <div class="io-hero-inner">
            <div>
              <div class="io-badge">لوحة تشغيلية داخلية</div>
              <h1>الداشبورد الداخلي — ${frappe.utils.escape_html(data.role_label || '')}</h1>
              <p>تجميعة تشغيلية تركز على الحالات المرئية للمستخدم الحالي، وقوائم العمل ذات الصلة، وآخر الحالات، والاختصارات التحليلية والتنفيذية.</p>
            </div>
            <div class="io-side">
              <h3>ملخص الدور الحالي</h3>
              <div class="io-side-metric"><span>إجمالي الحالات المرئية</span><strong>${counts.total_visible || 0}</strong></div>
              <div class="io-side-metric"><span>الحالات المفتوحة</span><strong>${counts.open_cases || 0}</strong></div>
              <div class="io-side-metric"><span>الحالات المتأخرة</span><strong>${counts.overdue || 0}</strong></div>
              <div class="io-side-metric"><span>عالية الأولوية</span><strong>${counts.high_priority || 0}</strong></div>
            </div>
          </div>
        </section>

        <section class="io-card">
          <div class="io-card-head">
            <div>
              <h3>فلاتر الداشبورد</h3>
              <p>تصفية التحليلات والقوائم حسب الحالة أو الأولوية أو الجهة.</p>
            </div>
          </div>
          <div class="io-filter-grid">
            <div class="io-filter-field">
              <label>الحالة</label>
              <select id="io-status-filter" class="form-control">
                ${(filterOptions.statuses || []).map((value) => `<option value="${frappe.utils.escape_html(value)}" ${appliedFilters.status_filter === value ? 'selected' : ''}>${frappe.utils.escape_html(value || 'الكل')}</option>`).join('')}
              </select>
            </div>
            <div class="io-filter-field">
              <label>الأولوية</label>
              <select id="io-priority-filter" class="form-control">
                ${(filterOptions.priorities || []).map((value) => `<option value="${frappe.utils.escape_html(value)}" ${appliedFilters.priority_filter === value ? 'selected' : ''}>${frappe.utils.escape_html(value || 'الكل')}</option>`).join('')}
              </select>
            </div>
            <div class="io-filter-field">
              <label>الجهة</label>
              <select id="io-entity-filter" class="form-control">
                ${(filterOptions.entities || []).map((value) => `<option value="${frappe.utils.escape_html(value)}" ${appliedFilters.entity_filter === value ? 'selected' : ''}>${frappe.utils.escape_html(value || 'الكل')}</option>`).join('')}
              </select>
            </div>
            <div class="io-filter-actions">
              <button class="io-btn io-btn-primary" onclick="refreshInternalDashboard(document.querySelector('.yc-internal-dashboard-page'))">تطبيق الفلاتر</button>
              <button class="io-btn io-btn-outline" onclick="resetInternalDashboardFilters(document.querySelector('.yc-internal-dashboard-page'))">إعادة ضبط</button>
            </div>
          </div>
        </section>

        <section class="io-grid io-stats-grid">
          ${makeStatCard('إجمالي الحالات المرئية', counts.total_visible || 0, 'كل الحالات المتاحة حسب صلاحياتك.', 'neutral', {label: 'الكل', status: '', priority: '', entity: ''})}
          ${makeStatCard('الحالات المفتوحة', counts.open_cases || 0, 'تشمل الحالات قيد العمل أو المتابعة.', 'blue', {label: 'الحالات المفتوحة', status: 'In Progress'})}
          ${makeStatCard('الحالات الجديدة', counts.new_cases || 0, 'طلبات جديدة تحتاج فرزًا أو بدء معالجة.', 'gold', {label: 'الحالات الجديدة', status: 'New'})}
          ${makeStatCard('قيد المراجعة', counts.under_review || 0, 'حالات ما زالت في مرحلة المراجعة الأولية.', 'purple', {label: 'قيد المراجعة', status: 'Under Review'})}
          ${makeStatCard('بانتظار المواطن', counts.waiting_citizen || 0, 'حالات تنتظر استكمالًا أو ردًا من المواطن.', 'orange', {label: 'بانتظار المواطن', status: 'Waiting Citizen'})}
          ${makeStatCard('المتأخرة', counts.overdue || 0, 'حالات تجاوزت المدة المستهدفة.', 'red', {label: 'الحالات المتأخرة', status: 'Overdue'})}
          ${makeStatCard('المحسومة / المغلقة', counts.resolved || 0, 'حالات تم إنهاؤها أو إغلاقها.', 'green', {label: 'الحالات المحسومة', status: 'Resolved'})}
          ${makeStatCard('عالية الأولوية', counts.high_priority || 0, 'طلبات حرجة أو ذات أولوية مرتفعة.', 'red', {label: 'عالية الأولوية', priority: 'High'})}
        </section>

        <section class="io-split-grid">
          <article class="io-card">
            <div class="io-card-head">
              <div>
                <h3>قوائم العمل حسب الدور</h3>
                <p>مؤشرات مباشرة توضح حجم الأعمال المطلوب التعامل معها الآن.</p>
              </div>
            </div>
            <div class="io-queue-grid">${queueHtml}</div>
          </article>

          <article class="io-card">
            <div class="io-card-head">
              <div>
                <h3>وصول سريع للتقارير والإجراءات</h3>
                <p>اختصارات داخلية للانتقال إلى القوائم والتقارير والسجلات الأكثر استخدامًا.</p>
              </div>
            </div>
            <div class="io-links-grid">${linksHtml}</div>
          </article>
        </section>

        <section class="io-analytics-grid">
          ${makeMetricPanel('الحالات حسب الحالة', statusBreakdown, 'status')}
          ${makeMetricPanel('الحالات حسب الأولوية', priorityBreakdown, 'priority')}
          ${makeMetricPanel('أكثر الجهات ورودًا', entityBreakdown, 'entity')}
          ${makeMetricPanel('قنوات التحقق من الهوية', verificationBreakdown, 'verification')}
        </section>

        <section class="io-split-grid">
          <article class="io-card">
            <div class="io-card-head">
              <div>
                <h3>الاتجاه الشهري للحالات</h3>
                <p>قراءة سريعة للمنحنى العام خلال آخر الأشهر.</p>
              </div>
            </div>
            ${makeTrendChart(monthlyTrend)}
          </article>

          <article class="io-card">
            <div class="io-card-head">
              <div>
                <h3>صحة التشغيل وSLA</h3>
                <p>نظرة سريعة على مستوى الخطر التشغيلي ومخرجات الذكاء الاصطناعي.</p>
              </div>
            </div>
            <div class="io-health-grid">
              <div class="io-health-box"><small>نسبة الخطر SLA</small><strong>${slaHealth.sla_risk_ratio || 0}%</strong></div>
              <div class="io-health-box"><small>الحالات المفتوحة</small><strong>${slaHealth.open_cases || 0}</strong></div>
              <div class="io-health-box"><small>الحالات المتأخرة</small><strong>${slaHealth.overdue_cases || 0}</strong></div>
              <div class="io-health-box"><small>AI Success</small><strong>${slaHealth.ai_success || 0}</strong></div>
              <div class="io-health-box"><small>AI Error</small><strong>${slaHealth.ai_error || 0}</strong></div>
              <div class="io-health-box"><small>الحالات المحسومة</small><strong>${slaHealth.resolved_cases || 0}</strong></div>
            </div>
          </article>
        </section>

        <section class="io-split-grid">
          <article class="io-card">
            <div class="io-card-head">
              <div>
                <h3>أنشطة الذكاء الاصطناعي الحديثة</h3>
                <p>آخر العمليات المطبقة عبر أدوات الذكاء الاصطناعي أو المساعد الذكي.</p>
              </div>
              <a class="io-inline-link" href="/app/complaint-ai-log">عرض السجل الكامل</a>
            </div>
            <div class="io-ai-list">${aiHtml}</div>
          </article>

          <article class="io-card">
            <div class="io-card-head">
              <div>
                <h3>أكثر المستخدمين نشاطاً</h3>
                <p>عرض مبسط للمستخدمين المرتبطين بأكبر عدد من الحالات المفتوحة حالياً.</p>
              </div>
            </div>
            <div class="io-officer-list">${officersHtml}</div>
          </article>
        </section>

        <section class="io-split-grid">
          <article class="io-card">
            <div class="io-card-head">
              <div>
                <h3>الحالات العاجلة والمفتوحة</h3>
                <p>قائمة مختصرة بأهم الحالات عالية الأولوية التي لا تزال مفتوحة.</p>
              </div>
            </div>
            <div class="io-cases-list">${urgentHtml}</div>
          </article>

          <article class="io-card">
            <div class="io-card-head">
              <div>
                <h3>آخر الحالات ضمن نطاقك</h3>
                <p>آخر الحالات المحدثة لمتابعتها بسرعة أو الدخول إلى شاشة الحالة مباشرة.</p>
              </div>
              <a class="io-inline-link" href="/app/complaint-case">عرض كل الحالات</a>
            </div>
            <div class="io-cases-list">${recentHtml}</div>
          </article>
        </section>
      </div>
    </div>
  `;

  bindInternalDashboardEvents(wrapper);
}

function renderCaseRows(rows, emptyText, urgent = false) {
  return rows.length
    ? rows.map((row) => `
        <a class="io-case-row ${urgent ? 'io-case-row-urgent' : ''}" href="/app/complaint-case/${encodeURIComponent(row.name)}">
          <div>
            <b>${frappe.utils.escape_html(row.subject || row.name || '')}</b>
            <small>${frappe.utils.escape_html(row.name || '')}</small>
          </div>
          <div class="io-case-meta">
            <span class="io-chip io-chip-priority">${frappe.utils.escape_html(row.priority || '')}</span>
            <span class="io-chip io-chip-status">${frappe.utils.escape_html(row.status || '')}</span>
          </div>
        </a>
      `).join('')
    : `<div class="io-empty">${frappe.utils.escape_html(emptyText)}</div>`;
}

function makeStatCard(label, value, hint, tone, drilldown = {}) {
  return `
    <button class="io-stat io-stat-${tone} io-action-btn" data-status="${frappe.utils.escape_html(drilldown.status || '')}" data-priority="${frappe.utils.escape_html(drilldown.priority || '')}" data-entity="${frappe.utils.escape_html(drilldown.entity || '')}">
      <div class="io-stat-label">${frappe.utils.escape_html(label)}</div>
      <div class="io-stat-value">${value}</div>
      <div class="io-stat-hint">${frappe.utils.escape_html(hint)}</div>
    </button>
  `;
}

function makeMetricPanel(title, rows, tone) {
  const values = rows || [];
  const max = Math.max(...values.map((r) => r.count || 0), 1);
  const body = values.length
    ? values.map((row) => {
        const width = Math.max(8, Math.round(((row.count || 0) / max) * 100));
        return `
          <button class="io-metric-row io-action-btn" data-status="${tone === 'status' ? frappe.utils.escape_html(row.label || '') : ''}" data-priority="${tone === 'priority' ? frappe.utils.escape_html(row.label || '') : ''}" data-entity="${tone === 'entity' ? frappe.utils.escape_html(row.label || '') : ''}">
            <div class="io-metric-head">
              <span>${frappe.utils.escape_html(row.label || '')}</span>
              <strong>${row.count || 0}</strong>
            </div>
            <div class="io-meter"><div class="io-meter-fill io-meter-${tone}" style="width:${width}%"></div></div>
          </button>
        `;
      }).join('')
    : '<div class="io-empty">لا توجد بيانات متاحة.</div>';

  return `
    <article class="io-card">
      <div class="io-card-head"><div><h3>${frappe.utils.escape_html(title)}</h3></div></div>
      <div class="io-metric-list">${body}</div>
    </article>
  `;
}

function makeTrendChart(rows) {
  const values = rows || [];
  const max = Math.max(...values.map((r) => r.count || 0), 1);
  const body = values.length
    ? values.map((row) => {
        const height = Math.max(16, Math.round(((row.count || 0) / max) * 140));
        return `
          <div class="io-trend-col">
            <div class="io-trend-bar"><span style="height:${height}px"></span></div>
            <strong>${row.count || 0}</strong>
            <small>${frappe.utils.escape_html(row.label || '')}</small>
          </div>
        `;
      }).join('')
    : '<div class="io-empty">لا توجد بيانات اتجاه شهري متاحة.</div>';

  return `<div class="io-trend-chart">${body}</div>`;
}

function bindInternalDashboardEvents(wrapper) {
  wrapper.querySelectorAll('.io-action-btn').forEach((button) => {
    button.addEventListener('click', () => {
      const filters = {
        status: button.dataset.status || '',
        priority: button.dataset.priority || '',
        entity: button.dataset.entity || '',
      };
      openComplaintCaseList(filters);
    });
  });
}

function openComplaintCaseList(filters) {
  const routeFilters = {};
  if (filters.status) routeFilters.status = filters.status;
  if (filters.priority) routeFilters.priority = filters.priority;
  if (filters.entity) routeFilters.government_entity = filters.entity;
  frappe.set_route('List', 'Complaint Case', 'List', routeFilters);
}

function resetInternalDashboardFilters(wrapper) {
  wrapper.querySelector('#io-status-filter').value = '';
  wrapper.querySelector('#io-priority-filter').value = '';
  wrapper.querySelector('#io-entity-filter').value = '';
  refreshInternalDashboard(wrapper);
}
