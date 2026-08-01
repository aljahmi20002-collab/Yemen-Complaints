# دليل تكامل SMS و WhatsApp

## الفكرة
التطبيق يرسل الطلبات إلى مزود خارجي باستخدام POST JSON.

## SMS Payload المتوقع
```json
{
  "to": "+9677xxxxxxx",
  "message": "...",
  "event": "citizen_receipt",
  "source": "yemen_complaints"
}
```

## WhatsApp Payload المتوقع
```json
{
  "to": "+9677xxxxxxx",
  "message": "...",
  "event": "citizen_status_update",
  "source": "yemen_complaints",
  "template_name": "optional-template"
}
```

## الإعداد من داخل النظام
افتح:
`Complaint Notification Settings`

ثم أدخل:
- Endpoint
- Token / API Key
- اسم Header إذا كان مختلفاً عن `Authorization`
- Timeout
- تفعيل القناة المناسبة

## أمثلة لمزوّدات يمكن ربطها
- Twilio
- Meta WhatsApp Cloud API عبر وسيط داخلي
- مزود SMS محلي أو إقليمي
- بوابة حكومية داخلية

## ملاحظة
إذا كان المزود يتطلب Payload مختلفاً، يمكن تعديل `messaging.py` بسهولة ليتوافق مع المواصفات المطلوبة.
