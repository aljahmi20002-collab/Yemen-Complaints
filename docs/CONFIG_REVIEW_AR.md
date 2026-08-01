# مراجعة وضبط المكونات الإدارية والتشغيلية

تمت مراجعة وضبط العناصر التالية داخل التطبيق:

## 1) Roles
- تأكيد إنشاء الأدوار الخمسة الأساسية بشكل idempotent
- ضبط `desk_access` بحيث يكون:
  - Citizen: بدون Desk
  - Advisor / Agency Officer / Follow-up Officer / Complaint System Manager: مع Desk
- تحسين منطق التحديث بحيث يتم **تعديل الدور إذا كان موجوداً** وليس فقط إنشاؤه عند أول تثبيت

## 2) Workflow
- مراجعة حالات الدورة التشغيلية وتوزيع `allow_edit` بما يتوافق بشكل أفضل مع الجهة المالكة لكل مرحلة
- توسيع التحولات بحيث تدعم:
  - المستشار
  - موظف الجهة
  - المتابع
  - مدير النظام
- إضافة تحولات إدارية مكررة لمدير النظام كي لا يُحجب عنه زر الإجراء في واجهة Workflow
- تحسين الاتساق بين:
  - Assigned
  - In Progress
  - Waiting Citizen
  - Resolved
  - Overdue

## 3) Web Forms
- إعادة ضبط نموذج الشكوى ونموذج التظلم بشكل أكثر احترافية
- جعل `case_type` مخفياً ومثبتاً تلقائياً حسب نوع النموذج
- إضافة حقول أكثر فائدة للمستخدم العام مثل:
  - اللغة المفضلة
  - مستوى السرية
  - الموظف أو الإدارة محل الشكوى
- تحسين نموذج التظلم بإضافة:
  - رقم المرجع السابق
  - سبب التظلم
- مراجعة الرسائل التعريفية ورسائل النجاح لكل نموذج

## 4) Workspaces
- إعادة تنظيم المحتوى داخل الـ Workspaces
- تقسيم المحتوى إلى:
  - مؤشرات سريعة
  - رسوم وتحليلات
- تخصيص البطاقات والرسوم حسب الدور
- جعل الـ Workspaces **غير عامة** وربطها بالأدوار مباشرة بدل عرضها للجميع

## 5) Number Cards
- الإبقاء على البطاقات الأساسية
- إضافة بطاقات تشغيلية أكثر فائدة مثل:
  - New Intake Cases
  - Under Review Cases
  - Waiting Citizen Cases
  - Appeal Cases
- بذلك أصبحت البطاقات مناسبة أكثر للفرز والمتابعة والتصعيد

## 6) Dashboard Charts
- مراجعة الرسوم الحالية والإبقاء على الأساسية منها
- إضافة رسوم مفيدة للإدارة والتحليل مثل:
  - Cases by Entity
  - Cases by Country
  - Cases by Type
- تحسين التغطية التحليلية للمنصة على مستوى:
  - الحالة
  - الأولوية
  - النوع
  - الدولة
  - الجهة
  - الاتجاه الشهري

## 7) Print Formats
- إعادة إخراج Print Formats بصيغة أكثر رسمية ووضوحاً
- تحسين تنسيق:
  - Complaint Case Professional
  - Government Entity Professional
  - Complaint Category Professional
- إضافة عناصر أكثر فائدة في نسخة الطباعة، مثل:
  - بطاقات معلومات منظمة
  - تلخيص المسار الزمني
  - جدول سجل الإحالات للحالة
  - إبراز خلاصة المعالجة

## الملفات المتأثرة
- `yemen_complaints/yemen_complaints/setup/install.py`
- `yemen_complaints/yemen_complaints/templates/print_formats/complaint_case.html`
- `yemen_complaints/yemen_complaints/templates/print_formats/government_entity.html`
- `yemen_complaints/yemen_complaints/templates/print_formats/complaint_category.html`

## ما يجب تنفيذه بعد التعديل
```bash
bench --site your-site migrate
bench build
```

وإذا أردت تحديث الـ fixtures أيضاً:
```bash
bench --site your-site export-fixtures
```
