# Rate Limiting + Abuse Protection Design
## منصة اليمن للشكاوى والتظلمات

## الهدف
حماية الواجهات العامة والوظائف الحساسة من سوء الاستخدام، وخاصة:
- OTP Verification
- Public Tracking
- AI Endpoints
- Web Forms العامة

---

## 1) الأسطح الأكثر حساسية

### 1.1 OTP APIs
- `send_identity_verification_code`
- `confirm_identity_verification_code`
- `resend_identity_verification_code`
- `get_identity_verification_status`

### 1.2 التتبع العام
- `track_case`

### 1.3 الذكاء الاصطناعي
- `perform_text_action`
- `run_intake_assistant`
- `apply_intake_assistant_recommendations`

### 1.4 نماذج الويب العامة
- `/submit-complaint`
- `/submit-appeal`

---

## 2) الضوابط المقترحة

### 2.1 OTP Send Limit
لكل:
- IP
- contact_value
- channel

مقترح:
- 3 محاولات إرسال خلال 15 دقيقة
- حد يومي: 10 محاولات

### 2.2 OTP Verify Limit
لكل طلب تحقق:
- `verification_max_attempts` موجود بالفعل

مقترح إضافي:
- 5 محاولات خلال عمر الرمز
- lock لمدة 15 دقيقة بعد تجاوز الحد

### 2.3 Public Tracking Limit
لكل IP:
- 20 طلب تتبع خلال 10 دقائق

### 2.4 AI Limit
لكل مستخدم داخلي:
- 60 عملية نصية في الساعة
- 20 تشغيل Smart Intake Assistant في الساعة

### 2.5 Web Form Submit Limit
لكل IP أو email/phone:
- 5 submissions خلال ساعة
- تنبيه عند تجاوز 3 submissions قصيرة جداً لنفس الهوية

---

## 3) نموذج التنفيذ الفني المقترح

### خيار 1 — Rate Limit باستخدام Cache / Redis
احفظ counters في cache مثل:
- `otp:send:<channel>:<contact>`
- `otp:send:ip:<ip>`
- `track:ip:<ip>`
- `ai:user:<user>`

مع TTL مناسب.

### خيار 2 — Logging Doctype
إنشاء Doctype مثل:
- `Request Throttle Log`

لحفظ:
- user / ip / endpoint / timestamp / allowed / reason

### خيار 3 — مختلط
- Redis للسرعة
- Log للرقابة والتحليل

---

## 4) حماية إضافية مقترحة

### 4.1 CAPTCHA / hCaptcha / Cloudflare Turnstile
يُنصح بتفعيلها على:
- OTP send
- Web Forms العامة
- Public tracking after repeated failures

### 4.2 Device / Browser Fingerprint خفيف
يمكن تسجيل:
- user agent
- ip
- accept-language
- timezone

ليس للتوثيق النهائي، ولكن لاكتشاف النمط غير الطبيعي.

### 4.3 Suspicious Patterns
أنشئ قواعد تنبيه عند:
- محاولات كثيرة على عدة contacts من IP واحد
- OTP failures كثيرة
- تتبع عام على أرقام حالات كثيرة متتابعة
- AI usage unusually high

---

## 5) سياسات استجابة

### Low Severity
- تأخير زمني بسيط
- رسالة انتظار

### Medium Severity
- تعطيل endpoint مؤقتاً للمستخدم/IP
- طلب CAPTCHA إضافي

### High Severity
- block مؤقت
- تنبيه إداري
- تسجيل أمني

---

## 6) رسائل المستخدم المقترحة
- "تم تجاوز الحد المسموح مؤقتاً، يرجى المحاولة لاحقاً."
- "عدد محاولات التحقق كبير، يرجى الانتظار قبل إعادة المحاولة."
- "تم إيقاف الإرسال مؤقتاً لحماية الخدمة من سوء الاستخدام."

---

## 7) توصيات قابلة للتنفيذ لاحقاً
1. إضافة util موحد مثل:
   - `security.py`
2. إضافة helper:
   - `check_rate_limit(key, limit, window_seconds)`
3. استدعاؤه في:
   - verification APIs
   - tracking API
   - AI APIs
4. إضافة لوحات رقابية للإساءات:
   - OTP failures by IP
   - AI usage by user
   - Tracking abuse attempts

---

## 8) الحد الأدنى الذي أوصي بتطبيقه فوراً
- OTP send limit
- OTP verify limit
- public tracking IP limit
- AI per-user hourly limit
- alert log للإساءة

---

## 9) ملاحظة مهمة
هذه الوثيقة تصمم طبقة الحماية. يمكنني في خطوة لاحقة أن أنفذها فعلياً في الكود، مع:
- cache-based throttling
- logs
- admin review page
- alert counters
