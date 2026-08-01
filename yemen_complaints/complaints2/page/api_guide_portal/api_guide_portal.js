frappe.pages['api_guide_portal'].on_page_load = function(wrapper) {
  const page = frappe.ui.make_app_page({
    parent: wrapper,
    title: 'API Guide',
    single_column: true,
  });
  wrapper.innerHTML = `
    <div style="padding:2rem;direction:rtl;font-family:DroidArabicKufi,Tahoma,Arial,sans-serif;">
      <div style="max-width:760px;margin:0 auto;background:#fff;border:1px solid #e5e7eb;border-radius:20px;padding:1.5rem;box-shadow:0 12px 30px rgba(15,23,42,.05);">
        <h3 style="margin-top:0;color:#9b1c1c">جارٍ التحويل...</h3>
        <p>سيتم نقلك إلى الصفحة المطلوبة خلال لحظات.</p>
        <p><a href="/api-guide" style="display:inline-block;padding:.65rem 1rem;border-radius:999px;background:#9b1c1c;color:#fff;text-decoration:none;">افتح الصفحة الآن</a></p>
      </div>
    </div>`;
  setTimeout(() => { window.location.href = '/api-guide'; }, 50);
};
