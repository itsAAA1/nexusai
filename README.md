# NexusAI — Prototype / نموذج أولي

واجهة عربية بسيطة لخمس مهام نصية عبر مزوّد نموذج اختياري. **هذا المستودع نموذج أولي وليس سوق خدمات جاهزًا للبيع.**

## الموجود فعليًا في المستودع

- `index.html`: واجهة HTML/CSS/JavaScript عربية RTL.
- `api/index.py`: معالج HTTP على Python standard library مهيأ كمسار API في Vercel.
- المهام: content، code، marketing، data، وimage. **image يُرجع وصفًا/برومبت نصيًا ولا يُنتج ملف صورة.**
- الاتصال بمزوّد OpenAI أو بمزوّد متوافق معه (مثل Gemini) يتم فقط عند ضبط `OPENAI_API_KEY` في إعدادات الخادم. اتصال API وحده لا يعني أن النموذج يعمل.
- `vercel.json`: إعدادات نشر المشروع.

## Gemini Native API (preferred for NexusAI)

To bypass the OpenAI compatibility layer and call Google's official `models.generateContent` endpoint directly, configure:

```dotenv
AI_PROVIDER=gemini
OPENAI_MODEL=gemini-3.6-flash
OPENAI_MAX_TOKENS=4000
```

Keep `OPENAI_API_KEY` as the **Gemini AI Studio API key** and `NEXUSAI_ACCESS_TOKEN` as the separate application access secret in Vercel encrypted environment variables. The environment variable name `OPENAI_API_KEY` remains for backwards compatibility and does **not** mean an OpenAI key should be used in Gemini mode. `OPENAI_BASE_URL` is ignored in native Gemini mode.

The native adapter uses `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`, sends `x-goog-api-key` server-side, validates model IDs, and never exposes provider response bodies or credentials to the web client. `AI_PROVIDER=openai` (default) preserves the existing OpenAI-compatible chat completion mode.

Google may restrict free-tier access by project/model/region. Never infer the API works merely because a key was saved; verify with an authenticated generation test.

## إعداد مزوّد ذكاء اصطناعي (بدون نشر الأسرار)

الإعداد الافتراضي يستعمل OpenAI. وللاستخدام مع Gemini API بنقطة النهاية المتوافقة مع OpenAI:

- `OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai`
- `OPENAI_MODEL=gemini-3.6-flash`
- `OPENAI_MAX_TOKENS=4000` (اختياري؛ المدى 64–8192؛ الافتراضي 1200)
- `OPENAI_API_KEY` = مفتاح Google AI Studio الخاص بك (يظل سرًا داخل متغيرات Vercel)
- `NEXUSAI_ACCESS_TOKEN` = رمز وصول عشوائي قوي (سر آخر منفصل)

البرنامج يقبل في `OPENAI_BASE_URL` عنوان HTTPS صحيحًا فقط، ويرفض صياغة غير سليمة أو عنوان loopback/private IP أو عنوانًا فيه استعلام؛ لا يرسل طلبًا إذا كانت الإعدادات غير سليمة. الاسم `OPENAI_API_KEY` باقٍ للتوافق مع الكود، لكنه يحمل مفتاح المزوّد المختار، وليس بالضرورة مفتاح OpenAI.

**تنبيه:** نموذج Gemini 3.6 Flash مدرج في طبقة Gemini المجانية رسميًا، لكن الحصص قد تختلف بحسب الحساب والمنطقة، وقد تختلف سياسات البيانات بين المجاني والمدفوع. راجع [أسعار Google الرسمية](https://ai.google.dev/gemini-api/docs/pricing) و[التوافق مع OpenAI](https://ai.google.dev/gemini-api/docs/openai) قبل إضافة بيانات حساسة أو الاستخدام الإنتاجي. التوليد الفعلي لا يمكن إثباته حتى يُضبط المفتاح ويُختبر طلب حقيقي. يجب إعادة نشر المشروع بعد تغيير متغيرات البيئة.

## غير منفذ في هذا الإصدار

لا يوجد في الكود الحالي تسجيل حسابات أو لوحة إدارة أو اشتراكات/فواتير أو بوابات دفع أو قاعدة بيانات أو توليد صور فعلي. لا تعتمد على أي أسعار أو وعد دفع أو تسويق حتى يُنفَّذ ويُختبر.

## التشغيل والنشر

النشر الحالي مبني على ملفات Vercel؛ لا توجد في المستودع ملفات `main.py` أو `requirements.txt`. راجع [Vercel](https://vercel.com/docs) لإعداد Python Functions ثم اضبط `OPENAI_API_KEY` و`NEXUSAI_ACCESS_TOKEN` في متغيرات بيئة الخادم **فقط** عند رغبتك بتفعيل التوليد. يجب أن يكون رمز الوصول عشوائيًا وقويًا. لا تضع مفتاح المزوّد أو رمز الدخول في JavaScript أو GitHub.

- `GET /api`: حالة الخدمة؛ حقلا `inference_configured` و`access_configured` يبيّنان وجود متغيرات البيئة فقط، ولا يثبتان نجاح توليد.
- `POST /api`: JSON يحتوي `agent` و`prompt`، ويستلزم الترويسة `Authorization: Bearer <NEXUSAI_ACCESS_TOKEN>`. إذا لم يُضبط رمز الوصول فالخدمة ترفض الطلبات (fail closed).
- الواجهة تطلب رمز الدخول عند الاستخدام، وترسله في ترويسة الطلب دون حفظه في localStorage.
- اختبارات مستقلة دون مزوّد مدفوع: `python -m unittest discover -s tests -v`.

**قبل تعريض توليد مدفوع للعموم:** رمز الوصول المشترك حماية أولية، وليس تسجيل مستخدمين ولا آلية حصص فردية أو ضبط تكلفة. يلزم تحديد معدلات/حصص ومراقبة تكلفة ومصادقة مناسبة قبل إطلاق خدمة مدفوعة للعامة.

## حالة التحقق

هذه الوثيقة تصف الكود، ولا تدّعي فحص النشر الحي أو الدفع. للمساهمة، قدّم اختبارات للدوال والواجهة وراجع إعدادات النشر قبل دمج أي تغيير.
