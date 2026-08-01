# المرحلة الثانية - التحسينات الاحترافية

## ما تمت إضافته
- Workflow رسمي للحالات باستخدام حقل `status`
- إشعارات بريدية للمواطن وفرق العمل
- رسائل استلام الطلب وتحديثات الحالة والتحديثات العامة
- تنبيهات وتصعيد SLA للجهات المعنية ومدير النظام
- تشغيل مزامنة الإعدادات بعد `migrate`
- اختبارات أولية للنواة الأساسية

## مسار Workflow المقترح
1. New
2. Under Review
3. Assigned
4. In Progress
5. Waiting Citizen
6. Resolved
7. Closed

مع حالات خاصة:
- Rejected
- Overdue

## رسائل البريد الحالية
- إشعار استلام طلب للمواطن
- إشعار إحالة للمستشار/الموظف/المتابع
- إشعار تحديث الحالة للمواطن
- إشعار تحديث عام للمواطن
- إشعار تصعيد SLA

## التحسينات المقترحة التالية
- SMS Gateway
- WhatsApp Cloud API
- Portal authenticated citizen dashboard
- Geo analytics by country/city
- AI-assisted triage and category suggestion
- Full Arabic translation CSV fixtures
