# AI Next + Fixtures Snapshot

## ما تم ضمن هذه المرحلة
### Fixtures
تمت إضافة ملفات fixtures مرئية داخل:
- `fixtures/role.json`
- `fixtures/workflow.json`
- `fixtures/web_form.json`
- `fixtures/workspace.json`
- `fixtures/number_card.json`
- `fixtures/dashboard_chart.json`
- `fixtures/print_format.json`
- `fixtures/complaint_ai_settings.json`
- `fixtures/complaint_notification_settings.json`

### AI Next
تمت إضافة:
- `Complaint AI Log` لتتبع عمليات الذكاء الاصطناعي
- تسجيل كل عملية AI نصية أو تشغيل للمساعد الذكي
- زر `Apply AI Recommendations` في Complaint Case
- دوال backend لتطبيق اقتراحات التصنيف/الجهة/الأولوية

### شاشة مستقلة للتحقق OTP
تمت إضافة صفحة:
- `/verify-identity`

وتتضمن:
- إرسال الرمز
- تأكيد الرمز
- إعادة الإرسال
- عداد زمني cooldown
- سجل محاولات/أحداث أوضح
- تخزين محلي لنتيجة التحقق للعودة إلى Web Form
