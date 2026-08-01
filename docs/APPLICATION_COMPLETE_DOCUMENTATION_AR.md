# الوثيقة الشاملة للتطبيق
## منصة اليمن للشكاوى والتظلمات

**اسم التطبيق:** `yemen_complaints`  
**الإطار:** Frappe Framework  
**لغة الوثيقة:** العربية  
**الإصدار المرجعي:** النسخة الحالية داخل مساحة العمل  

---

## 1. مقدمة
منصة اليمن للشكاوى والتظلمات هي نظام إلكتروني متكامل لاستقبال الشكاوى والتظلمات من المواطنين اليمنيين داخل اليمن وخارجه، مع إمكانيات التحقق من الهوية، الإحالة، المتابعة، التقارير، المؤشرات، الطباعة، والإشعارات، إضافة إلى قدرات ذكاء اصطناعي مساعدة لموظفي الاستقبال والمعالجة.

المنصة مبنية على **Frappe Framework**، ومصممة لتكون قابلة للتوسع، ومناسبة للعمل المؤسسي الحكومي أو شبه الحكومي، مع دعم صلاحيات متعددة الأدوار، وواجهات عربية احترافية، وخط رسمي موحد.

---

## 2. أهداف النظام
### 2.1 الهدف الرئيسي
تمكين المواطن اليمني من تقديم شكوى أو تظلم ومتابعته إلكترونياً من أي مكان في العالم.

### 2.2 الأهداف الفرعية
- رقمنة عملية استقبال الشكاوى والتظلمات.
- ضمان التحقق من هوية مقدم الشكوى قبل الإرسال.
- تمكين الجهات المختصة من الفرز والإحالة والمتابعة.
- توفير تقارير تشغيلية وتنفيذية ومؤشرات أداء.
- تسريع اتخاذ القرار عبر مساعد ذكاء اصطناعي.
- تحسين تجربة المواطن في التقديم والمتابعة.

---

## 3. نطاق التطبيق
يشمل التطبيق حالياً:
- تقديم الشكاوى والتظلمات عبر Web Forms.
- التحقق من الهوية عبر Email / SMS / WhatsApp / Telegram.
- إدارة ملفات الشكاوى والتظلمات.
- نظام إحالة ومتابعة داخلي.
- Workspaces حسب الدور.
- Number Cards وDashboard Charts.
- تقارير Script Reports.
- Print Formats احترافية.
- تكامل AI مع ChatGPT وDeepSeek وGemini.
- شاشة مستقلة للتحقق OTP.
- بيانات مرجعية للمحافظات والمديريات اليمنية.

---

## 4. المستخدمون والأدوار
### 4.1 Citizen
المواطن مقدم الشكوى أو التظلم.

**الصلاحيات الأساسية:**
- تقديم شكوى أو تظلم.
- التحقق من الهوية.
- متابعة الحالة.
- عرض التحديثات العامة.
- إضافة ملاحظة عامة على الحالة.

### 4.2 Advisor
مستشار استقبال الشكاوى.

**الصلاحيات الأساسية:**
- مراجعة الحالات الجديدة.
- فرز الشكاوى والتظلمات.
- تحديد التصنيف.
- تشغيل المساعد الذكي للاستقبال.
- الإحالة إلى موظف الجهة أو المتابع.
- رفض أو إعادة فتح بعض الحالات حسب المسار.

### 4.3 Agency Officer
موظف الجهة المختصة.

**الصلاحيات الأساسية:**
- معالجة الحالة.
- طلب استكمال من المواطن.
- تحديث الحالة.
- اقتراح أو تنفيذ الإغلاق التشغيلي.

### 4.4 Follow-up Officer
موظف المتابعة والرقابة.

**الصلاحيات الأساسية:**
- متابعة الحالات المتأخرة.
- مراقبة SLA.
- المساهمة في التحريك أو الإغلاق.
- متابعة حالات الانتظار والتصعيد.

### 4.5 Complaint System Manager
مدير النظام.

**الصلاحيات الأساسية:**
- إدارة الإعدادات العامة.
- إدارة AI وNotifications.
- الاطلاع الكامل على التقارير واللوحات.
- إدارة البيانات المرجعية.
- الإشراف على workflow والأمان والتشغيل.

---

## 5. الوحدات الوظيفية الرئيسية
### 5.1 إدارة الشكاوى والتظلمات
DocType رئيسي:
- `Complaint Case`

### 5.2 الإحالات
Child Table:
- `Complaint Assignment`

### 5.3 التحديثات
Child Table:
- `Complaint Update`

### 5.4 الجهات الحكومية
DocType:
- `Government Entity`

### 5.5 التصنيفات
DocType:
- `Complaint Category`

### 5.6 التحقق من الهوية
DocType:
- `Complaint Identity Verification`

### 5.7 إعدادات الإشعارات
Single DocType:
- `Complaint Notification Settings`

### 5.8 إعدادات الذكاء الاصطناعي
Single DocType:
- `Complaint AI Settings`

### 5.9 سجلات الذكاء الاصطناعي
DocType:
- `Complaint AI Log`

### 5.10 البيانات المرجعية اليمنية
- `Yemen Governorate`
- `Yemen District`

---

## 6. تدفق العمل التشغيلي
### 6.1 السيناريو العام
1. المواطن يفتح نموذج الشكوى أو التظلم.
2. يملأ البيانات الأساسية.
3. يختار قناة التحقق من الهوية.
4. يستلم OTP ويؤكد الهوية.
5. يرسل الشكوى.
6. تُنشأ الحالة في النظام.
7. المستشار يراجع ويصنف ويشغّل المساعد الذكي إذا لزم.
8. يتم تعيين الجهة أو الموظف المختص.
9. تتم المعالجة والتحديثات.
10. تتم المتابعة أو الإغلاق.
11. يمكن للمواطن متابعة الحالة من البوابة أو صفحة التتبع.

---

## 7. Workflow الرسمي
### الحالات
- New
- Under Review
- Assigned
- In Progress
- Waiting Citizen
- Resolved
- Rejected
- Closed
- Overdue

### ملاحظات
- لا يسمح بالحسم أو الإغلاق بدون `Resolution Summary`.
- لا يسمح بالانتقال إلى `Assigned` دون إسناد أو مسؤول واضح.
- الانتقالات مضبوطة حسب الدور.

---

## 8. التحقق من الهوية قبل الإرسال
### القنوات المدعومة
- Email
- SMS
- WhatsApp
- Telegram

### عناصر التحكم
- طول رمز التحقق
- مدة الصلاحية
- عدد المحاولات
- فاصل إعادة الإرسال
- تفعيل/تعطيل كل قناة

### الشاشة المستقلة
المسار:
- `/verify-identity`

### الوظائف المتاحة
- إرسال الرمز
- تأكيد الرمز
- إعادة الإرسال
- عداد زمني
- سجل المحاولات والأحداث

---

## 9. الذكاء الاصطناعي
### 9.1 المزوّدات المدعومة
- ChatGPT / OpenAI
- DeepSeek
- Gemini

### 9.2 الأدوات النصية
تمت إضافة أزرار ذكاء اصطناعي على الدوكتايبات المناسبة لتنفيذ:
- ترجمة نص
- تلخيص نص
- تحسين الكتابة
- إصلاح الإملاء والنحو
- تحليل نص
- اقترح رد
- صياغة رسالة
- تصنيف الموضوع
- ابحث عن عناصر النص
- اختصر
- اكتب بالتفصيل
- تبسيط اللغة
- اجعل النص رسمي
- خلاصة نص

### 9.3 المساعد الذكي لاستقبال الشكاوى
زر:
- `Smart Intake Assistant`

ينتج:
- ملخص الحالة
- تصنيف مقترح
- أولوية مقترحة
- جهة مقترحة
- عناصر مهمة
- مؤشرات خطورة
- توصيات متابعة
- رد مقترح
- رسالة مناسبة للمواطن

### 9.4 تطبيق توصيات AI
زر:
- `Apply AI Recommendations`

يقوم بتطبيق ما يمكن مطابقته على:
- `priority`
- `category`
- `government_entity`

### 9.5 AI Log
يتم تسجيل كل عملية AI في:
- `Complaint AI Log`

---

## 10. الإشعارات والتواصل
### إشعارات المواطن
- استلام الطلب
- تحديث الحالة
- تحديث عام
- OTP للتحقق من الهوية

### إشعارات الموظفين
- الإحالة
- تنبيهات SLA

### القنوات
- Email
- SMS
- WhatsApp
- Telegram

---

## 11. Web Forms
### النماذج الحالية
- `submit-complaint`
- `submit-appeal`

### مميزات النماذج
- دعم RTL
- خط Droid Arabic Kufi
- حقول المحافظات والمديريات
- التحقق من الهوية قبل الإرسال
- دعم المرفقات

---

## 12. الواجهات العامة والبوابات
### 12.1 صفحة تتبع عامة
- `/track-complaint`

### 12.2 بوابة المواطن
- `/my-cases`

### 12.3 الخط الزمني للحالة
- `/case-timeline`

### 12.4 شاشة التحقق OTP
- `/verify-identity`

---

## 13. Workspaces
### الحالية
- Citizen Complaints Portal
- Advisor Complaint Desk
- Agency Officer Desk
- Follow-up Desk
- Yemen Complaints Manager Desk

كل Workspace يحتوي على:
- مؤشرات سريعة
- رسوم وتحليلات
- تخصيص حسب الدور

---

## 14. Number Cards
أمثلة:
- Open Complaint Cases
- New Intake Cases
- Under Review Cases
- Waiting Citizen Cases
- Overdue Complaint Cases
- Resolved Complaint Cases
- High Priority Complaint Cases
- Appeal Cases

---

## 15. Dashboard Charts
أمثلة:
- Cases by Status
- Cases by Priority
- Monthly Complaint Trend
- Cases by Country
- Cases by Governorate
- Cases by Type
- Cases by Entity

---

## 16. التقارير
### التقارير الحالية
- Complaint Summary
- SLA Breaches
- Officer Workload
- Citizen Satisfaction

---

## 17. Print Formats
### الحالية
- Complaint Case Professional
- Government Entity Professional
- Complaint Category Professional

### خصائصها
- إخراج رسمي
- دعم اللغة العربية
- عرض منظم للبيانات
- ملائمة للطباعة أو PDF

---

## 18. البيانات المرجعية اليمنية
### المحافظات
22 محافظة

### المديريات
335 مديرية

### الاستخدام
تُستخدم في:
- Complaint Case
- Government Entity
- Web Forms
- التحليلات

---

## 19. الخط الرسمي للتطبيق
تم اعتماد:
- Droid Arabic Kufi Regular
- Droid Arabic Kufi Bold

ويستخدم في:
- الواجهات
- النماذج
- البوابة
- الطباعة

---

## 20. بنية المشروع
المجلدات المهمة:
- `fixtures/`
- `docs/`
- `deployment/`
- `yemen_complaints/`
- `yemen_complaints/public/`
- `yemen_complaints/www/`
- `yemen_complaints/templates/`

---

## 21. ملفات التهيئة الأساسية
- `hooks.py`
- `setup/install.py`
- `permissions.py`
- `tasks.py`
- `messaging.py`
- `verification.py`
- `ai.py`

---

## 22. الـ Fixtures المتاحة
يوجد داخل:
- `fixtures/role.json`
- `fixtures/workflow.json`
- `fixtures/web_form.json`
- `fixtures/workspace.json`
- `fixtures/number_card.json`
- `fixtures/dashboard_chart.json`
- `fixtures/print_format.json`
- `fixtures/complaint_ai_settings.json`
- `fixtures/complaint_notification_settings.json`

---

## 23. التثبيت والتشغيل
### أوامر أساسية
```bash
bench --site your-site install-app yemen_complaints
bench --site your-site migrate
bench build
```

### تصدير Fixtures
```bash
bench --site your-site export-fixtures
```

---

## 24. التهيئة بعد التثبيت
### 24.1 إعداد الإشعارات
افتح:
- `Complaint Notification Settings`

وقم بضبط:
- البريد الإلكتروني
- SMS
- WhatsApp
- Telegram
- قنوات التحقق OTP

### 24.2 إعداد الذكاء الاصطناعي
افتح:
- `Complaint AI Settings`

وقم بضبط:
- Enable AI
- Default Provider
- API Keys
- Model
- Endpoint

---

## 25. الأمان والضبط المؤسسي
### عناصر مهمة
- تقييد الوصول بالأدوار.
- منع المواطن من تغيير الحالة مباشرة.
- منع استخدام OTP أكثر من مرة.
- تقييد AI للمستشار/مدير النظام في المساعد الذكي.
- تسجيل AI actions وOTP events.

---

## 26. المراقبة والتشغيل
يوصى بمراقبة:
- Error Log
- Scheduler
- Email Queue
- AI Log
- Identity Verification records
- الحالات المتأخرة SLA

---

## 27. القيود الحالية
- Telegram وWhatsApp وSMS تعمل عبر Generic Endpoint وتحتاج ربط مزود فعلي.
- بعض الـ fixtures الحالية تم توليدها مرجعياً داخل المشروع، ويُفضّل إعادة تصديرها من بيئة Frappe النهائية عند الاعتماد الكامل.
- AI يحتاج مفاتيح صحيحة ومراقبة تكلفة الاستخدام.

---

## 28. التوصيات المستقبلية
- إضافة rate limiting وabuse protection لواجهة OTP.
- إضافة مراقبة تكلفة AI واستهلاك المزود.
- إضافة تنبيهات إدارية عند كثرة محاولات OTP الفاشلة.
- إضافة بوابة إدارية لمراجعة سجلات الذكاء الاصطناعي.
- دعم تكاملات حكومية إضافية.

---

## 29. مراجع داخلية في المشروع
- `docs/AI_INTEGRATION_AR.md`
- `docs/IDENTITY_VERIFICATION_AR.md`
- `docs/FONT_AND_YEMEN_LOCATION_AR.md`
- `docs/PRODUCTION_REVIEW_AR.md`
- `docs/AI_NEXT_AND_FIXTURES_AR.md`
- `docs/DEPLOYMENT_PRODUCTION_AR.md`

---

## 30. خلاصة
التطبيق في وضعه الحالي يمثل منصة متكاملة ومتقدمة لاستقبال ومتابعة الشكاوى والتظلمات، مع دعم قوي للتحقق من الهوية، التحليلات، الأدوار، الطباعة، والتكاملات الذكية، ويمكن اعتباره أساساً قوياً لبيئة إنتاجية بعد إكمال الضبط النهائي للمزودات والإعدادات التشغيلية.
