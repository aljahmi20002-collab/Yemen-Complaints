# Rollback Notes

## متى نستخدم التراجع؟
- عند وجود عطل حرج يمنع التشغيل
- عند فساد بيانات بعد patch أو migrate
- عند خلل واسع في OTP أو AI أو Workspaces بعد الإطلاق

## طبقات التراجع
### 1) تراجع كود
- العودة لآخر commit مستقر
- إعادة build
- migrate إن لزم

### 2) تراجع قاعدة بيانات
- استعادة backup حديث
- مراجعة سبب المشكلة قبل إعادة الترحيل

## أوامر مفيدة
```bash
bench --site your-site backup
bench --site your-site restore /path/to/backup.sql.gz
bench --site your-site migrate
bench build
```

## تنبيه
يجب توثيق أي rollback:
- السبب
- الوقت
- الشخص المنفذ
- الإجراء التالي
