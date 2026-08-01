# Fixtures

هذا المجلد مخصص لملفات fixtures التي يمكن تصديرها من Frappe عبر:

```bash
bench --site your-site export-fixtures
```

تم إعداد `hooks.py` ليشمل تصدير العناصر التالية:
- Roles
- Workflow
- Web Forms
- Workspaces
- Number Cards
- Dashboard Charts
- Print Formats

بعد التصدير ستظهر ملفات JSON في هذا المجلد ويمكن حفظها ضمن المستودع.
