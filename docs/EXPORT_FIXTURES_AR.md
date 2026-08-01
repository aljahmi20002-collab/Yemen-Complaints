# دليل Export Fixtures

تم إعداد التطبيق لدعم تصدير Fixtures عبر `hooks.py`.

## الأوامر
```bash
bench --site your-site migrate
bench --site your-site export-fixtures
```

## ما الذي سيتم تصديره
- Role
- Workflow
- Web Form
- Workspace
- Number Card
- Dashboard Chart
- Print Format

## لماذا هذا مهم؟
- حفظ الإعدادات القياسية داخل Git
- تسهيل النشر بين البيئات
- تقليل الاعتماد على الإنشاء اليدوي بعد التثبيت
