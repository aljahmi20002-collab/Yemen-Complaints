# حزمة Go-Live النهائية
## منصة اليمن للشكاوى والتظلمات

هذه الوثيقة تجمع العناصر الأساسية التي يحتاجها فريق المشروع والإدارة قبل الإطلاق الفعلي للنظام.

---

## 1) الهدف من الحزمة
تهدف هذه الحزمة إلى:
- توحيد خطوات الإطلاق الإنتاجي
- تقليل المخاطر أثناء التشغيل الأول
- تسهيل التسليم الإداري والفني
- توفير مرجع فوري للدعم والتراجع عند الحاجة

---

## 2) محتويات الحزمة
- قائمة فحص ما قبل الإطلاق
- خطوات الإطلاق
- تحقق ما بعد الإطلاق
- ملاحظات التراجع Rollback
- ملاحظات التسليم الإداري
- ملخص الدعم التشغيلي
- الملاحق والوثائق المرجعية

---

## 3) ما قبل الإطلاق Pre-Go-Live Checklist
### البنية والتثبيت
- [ ] نجح `bench --site your-site migrate`
- [ ] نجح `bench build`
- [ ] نجح `clear-cache`
- [ ] تم تحميل pages/workspaces/charts/cards/reports الصحيحة
- [ ] تم اختبار التطبيق على بيئة staging مشابهة للإنتاج

### القنوات والإشعارات
- [ ] البريد الإلكتروني يعمل
- [ ] OTP عبر البريد يعمل
- [ ] OTP عبر SMS يعمل إن كان مطلوباً
- [ ] OTP عبر WhatsApp يعمل إن كان مطلوباً
- [ ] OTP عبر Telegram يعمل إن كان مطلوباً
- [ ] إشعارات SLA تعمل

### الذكاء الاصطناعي
- [ ] Complaint AI Settings مفعلة فقط إذا كانت المفاتيح صحيحة
- [ ] تم اختبار ChatGPT أو DeepSeek أو Gemini
- [ ] تم اختبار Smart Intake Assistant
- [ ] تم اختبار AI logs

### البيانات المرجعية
- [ ] الجهات الحكومية مراجعة
- [ ] التصنيفات مراجعة
- [ ] المحافظات والمديريات موجودة
- [ ] المستخدمون والأدوار مضبوطة

### الأمن والحماية
- [ ] HTTPS مفعّل
- [ ] النسخ الاحتياطي اليومي مفعل
- [ ] scheduler يعمل
- [ ] rate limiting / abuse monitoring مفعلة برمجياً
- [ ] صلاحيات المدير محصورة بالحسابات المعتمدة

---

## 4) خطوات الإطلاق الفعلي
### الخطوة 1: نسخ احتياطي
```bash
bench --site your-site backup
```

### الخطوة 2: ترحيل وبناء نهائي
```bash
bench --site your-site migrate
bench build
bench --site your-site clear-cache
bench --site your-site clear-website-cache
```

### الخطوة 3: إعادة تحميل السجلات الملفية
```bash
bash scripts/rebuild_complaints2_records.sh your-site
```

### الخطوة 4: اختبار سريع مباشر
- فتح الصفحة الرئيسية
- فتح submit-complaint
- فتح verify-identity
- إرسال OTP تجريبي
- فتح workspaces
- فتح internal dashboard
- فتح executive dashboard
- فتح security dashboard

---

## 5) تحقق ما بعد الإطلاق Post-Go-Live Validation
### المواطن
- [ ] الصفحة الرئيسية تعمل
- [ ] تقديم شكوى يعمل
- [ ] تقديم تظلم يعمل
- [ ] التحقق OTP يعمل
- [ ] التتبع العام يعمل
- [ ] بوابة المواطن تعمل

### الموظفون
- [ ] Advisor Workspace تعمل
- [ ] Agency Workspace تعمل
- [ ] Follow-up Workspace تعمل
- [ ] Manager Workspace تعمل
- [ ] Command Center يعمل

### الداشبوردات
- [ ] Internal Operations Dashboard يعمل
- [ ] Executive Leadership Dashboard يعمل
- [ ] Security Monitoring Dashboard يعمل

### التقارير والطباعة
- [ ] Complaint Summary يعمل
- [ ] SLA Breaches يعمل
- [ ] Officer Workload يعمل
- [ ] Citizen Satisfaction يعمل
- [ ] Print Formats تظهر بشكل صحيح

---

## 6) خطة التراجع Rollback Notes
في حال حدوث مشكلة حرجة بعد الإطلاق:

### سيناريو 1: مشكلة في الكود فقط
- ارجع إلى آخر commit مستقر
- أعد البناء
- نفّذ migrate إن لزم

### سيناريو 2: مشكلة في البيانات بعد الترحيل
- استخدم آخر نسخة backup
- استعد قاعدة البيانات
- راجع patches أو records المضافة قبل التكرار

### أوامر عامة
```bash
git log --oneline
# checkout to stable commit if needed
bench --site your-site restore /path/to/latest-backup.sql.gz
bench --site your-site migrate
bench build
```

### ملاحظة
لا يتم تنفيذ rollback دون قرار صريح من مالك الخدمة أو مدير النظام المسؤول.

---

## 7) ملاحظات التسليم الإداري Administrative Handover
يجب تسليم الجهة المشغلة ما يلي:
- اسم التطبيق ومكوناته
- قائمة الأدوار والصلاحيات
- روابط الصفحات العامة
- روابط الداشبوردات الداخلية والتنفيذية
- مسارات التوثيق الداخلية
- بيانات اعتماد المدراء المعتمدين
- إعدادات القنوات الخارجية (Email/SMS/WhatsApp/Telegram)
- إعدادات AI ومزوداته
- خطة الدعم والتصعيد

---

## 8) ملخص الدعم التشغيلي Support Summary
### عند مشكلة OTP
1. مراجعة Notification Settings
2. مراجعة Security Events
3. مراجعة Identity Verification Records
4. اختبار endpoint للقناة المعنية

### عند مشكلة AI
1. مراجعة AI Settings
2. مراجعة AI Logs
3. مراجعة Security Events
4. اختبار provider مباشرة

### عند مشكلة Workspaces / Dashboards
1. تشغيل rebuild script
2. clear-cache
3. clear-website-cache
4. reload-doc عند الحاجة

---

## 9) المراجع الأساسية
- `docs/FINAL_PRODUCTION_AUDIT_AR.md`
- `docs/UAT_CHECKLIST_AR.md`
- `docs/RATE_LIMITING_ABUSE_PROTECTION_AR.md`
- `docs/PRODUCTION_REVIEW_AR.md`
- `docs/IDENTITY_VERIFICATION_AR.md`
- `docs/AI_INTEGRATION_AR.md`

---

## 10) القرار النهائي قبل الإطلاق
### يوصى بالإطلاق فقط إذا:
- تم استكمال UAT
- تم اختبار القنوات الخارجية
- تم تأكيد النسخ الاحتياطي
- تم تقييد صلاحيات المدراء
- تم التأكد من ظهور الداشبوردات والروابط الصحيحة
- تم قبول النتائج من الجهة المالكة
