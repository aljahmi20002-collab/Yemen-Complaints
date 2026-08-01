# دليل النشر الإنتاجي - Yemen Complaints

## 1) المتطلبات
- Ubuntu 22.04 أو أحدث
- Python متوافق مع إصدار Frappe المستخدم
- Redis / MariaDB / Node.js / Yarn
- Bench CLI
- Nginx + Supervisor
- دومين مخصص وشهادة SSL

## 2) إنشاء بيئة Bench
```bash
bench init frappe-bench --frappe-branch version-15
cd frappe-bench
bench new-site complaints.example.com
```

## 3) إضافة التطبيق
```bash
bench get-app /path/to/yemen_complaints
bench --site complaints.example.com install-app yemen_complaints
bench --site complaints.example.com migrate
bench build
```

## 4) إعداد البريد
من داخل Frappe:
- Email Account
- Default Outgoing
- اختبار الإرسال

هذا مهم لأن التطبيق يعتمد على إشعارات البريد للمواطنين والموظفين.

## 5) تفعيل الجدولة
```bash
bench doctor
bench enable-scheduler
bench --site complaints.example.com scheduler resume
```

## 6) الإنتاج
```bash
sudo bench setup production frappe
```

## 7) SSL واسم النطاق
- اربط الدومين بـ Nginx
- فعّل Let's Encrypt أو استخدم Reverse Proxy مؤمّن
- اختبر الروابط:
  - `/submit-complaint`
  - `/submit-appeal`
  - `/track-complaint`
  - `/my-cases`

## 8) النسخ الاحتياطي
```bash
bench --site complaints.example.com backup
```
ويفضّل جدولة النسخ الاحتياطي اليومي مع تخزين خارجي آمن.

## 9) التوصيات التشغيلية
- إنشاء SMTP موثوق
- تفعيل Audit Trails
- مراجعة الصلاحيات لكل دور قبل الإطلاق
- تفعيل مراقبة الأداء والسجلات
- تجربة سيناريوهات SLA والتنبيهات قبل Go-Live
