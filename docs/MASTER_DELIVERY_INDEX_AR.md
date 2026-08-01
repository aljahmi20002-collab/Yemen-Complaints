# Master Delivery Index
## الفهرس الرئيسي للتسليم
### منصة اليمن للشكاوى والتظلمات

هذا الفهرس هو نقطة الدخول الموحدة لكل مخرجات المشروع، ويجمع:
- الروابط الأساسية
- لوحات القيادة
- صفحات المواطن
- الوثائق التنفيذية والتشغيلية
- ملفات التسليم
- أوامر التشغيل وإعادة البناء

---

## 1) روابط النظام الأساسية
### واجهات المواطن
- الصفحة الرئيسية: `/`
- تقديم شكوى: `/submit-complaint`
- تقديم تظلم: `/submit-appeal`
- تتبع شكوى: `/track-complaint`
- التحقق من الهوية: `/verify-identity`
- طلباتي: `/my-cases`
- الخط الزمني للحالة: `/case-timeline`

### بوابة التوثيق
- فهرس التوثيق: `/docs`
- الوثيقة الشاملة: `/application-docs`
- دليل الاستخدام: `/user-guide`
- دليل المواطن: `/citizen-guide`
- الدليل الإداري: `/admin-guide`
- الملخص التنفيذي: `/executive-brief`
- Executive Brief EN: `/executive-brief-en`
- سياسة الخصوصية: `/privacy-policy`
- شروط الاستخدام: `/terms-of-use`
- دليل API: `/api-guide`
- حزمة التسليم التنفيذية: `/executive-delivery-pack`

### لوحات القيادة
- الداشبورد الداخلي: `/app/internal-operations-dashboard`
- الداشبورد التنفيذي: `/app/executive-leadership-dashboard`
- داشبورد الأمن والحماية: `/app/security-monitoring-dashboard`

---

## 2) أهم الـ Workspaces
- Citizen Complaints Portal
- Advisor Complaint Desk
- Agency Officer Desk
- Follow-up Desk
- Yemen Complaints Manager Desk
- Yemen Complaints Command Center

---

## 3) أهم الـ Reports
- Complaint Summary
- SLA Breaches
- Officer Workload
- Citizen Satisfaction

---

## 4) أهم السجلات المرجعية
- Complaint Case
- Government Entity
- Complaint Category
- Complaint Identity Verification
- Complaint AI Log
- Complaint Security Event
- Yemen Governorate
- Yemen District

---

## 5) ملفات الوثائق الرئيسية
- `docs/APPLICATION_COMPLETE_DOCUMENTATION_AR.md`
- `docs/USER_GUIDE_AR.md`
- `docs/GO_LIVE_FINAL_PACKAGE_AR.md`
- `docs/FINAL_PRODUCTION_AUDIT_AR.md`
- `docs/UAT_CHECKLIST_AR.md`
- `docs/RATE_LIMITING_ABUSE_PROTECTION_AR.md`
- `docs/EXECUTIVE_DELIVERY_PACK_AR.md`
- `docs/RELEASE_NOTES_AR.md`
- `docs/ROLLBACK_NOTES_AR.md`
- `docs/ADMIN_HANDOVER_NOTES_AR.md`
- `docs/SUPPORT_RUNBOOK_SUMMARY_AR.md`

---

## 6) أوامر تشغيل مرجعية
```bash
bench --site your-site migrate
bench build
bench --site your-site clear-cache
bench --site your-site clear-website-cache
bash scripts/rebuild_complaints2_records.sh your-site
```

---

## 7) ملفات ومجلدات بنيوية مهمة
- `complaints2/doctype/`
- `complaints2/report/`
- `complaints2/workspace/`
- `complaints2/dashboard_chart/`
- `complaints2/card/`
- `complaints2/page/`
- `public/css/`
- `public/js/`
- `www/`
- `docs/`
- `fixtures/`
- `scripts/`

---

## 8) الاستخدام المقترح
يستخدم هذا الفهرس كمرجع موحد عند:
- التسليم الرسمي
- التشغيل اليومي
- المراجعة التنفيذية
- الدعم الفني
- الإطلاق الإنتاجي
