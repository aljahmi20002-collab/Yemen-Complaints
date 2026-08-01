# إضافة الخط الرسمي وبيانات المحافظات والمديريات

## الخط الرسمي للتطبيق
تم اعتماد الخط التالي كخط رسمي للتطبيق:
- Droid Arabic Kufi Regular
- Droid Arabic Kufi Bold

وتمت إضافته داخل:
- `yemen_complaints/yemen_complaints/public/fonts/`

مع ربطه في:
- `yemen_complaints/yemen_complaints/public/css/yemen_complaints.css`

ويستخدم الآن في:
- الواجهات العامة
- صفحات البوابة
- نماذج الويب
- صيغ الطباعة

## بيانات اليمن المرجعية
تمت إضافة بيانات المحافظات والمديريات اليمنية بالاعتماد على ملف حدود إدارية لليمن من HDX/OCHA (22 محافظة و335 مديرية).

### العناصر المضافة
- Doctype: `Yemen Governorate`
- Doctype: `Yemen District`
- ملف بيانات: `yemen_complaints/yemen_complaints/data/yemen_admin_units.json`

## الحقول المضافة
### في Complaint Case
- `citizen_governorate`
- `citizen_district`
- `incident_governorate`
- `incident_district`

### في Government Entity
- `governorate`
- `district`

## التحسينات المنفذة
- ربط المديرية بالمحافظة عبر فلاتر ديناميكية
- التحقق برمجياً من أن المديرية تتبع المحافظة المختارة
- تحسين Web Forms لإظهار نفس البيانات المرجعية
- تحسين قوالب الطباعة لإظهار بيانات الموقع
- إضافة رسم تحليلي حسب المحافظة داخل Dashboard Charts
