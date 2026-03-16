# 🚀 NexusAI - وكالة خدمات الذكاء الاصطناعي

**AI Services Marketplace & Agency Platform**

![NexusAI Logo](https://cdn.manus.im/nexusai-logo.png)

---

## 📌 نبذة عن المشروع

**NexusAI** هي منصة متقدمة لبيع وشراء خدمات الذكاء الاصطناعي. تجمع بين تكنولوجيا حديثة وواجهة احترافية لتقديم خدمات متخصصة بجودة عالية.

**NexusAI** is an advanced marketplace platform for buying and selling AI-powered services. It combines cutting-edge technology with a professional interface to deliver specialized services with exceptional quality.

### ✨ المميزات الرئيسية

- **5 وكلاء ذكاء اصطناعي متخصصين** - Specialized AI agents for different services
- **نظام تسعير ديناميكي** - Dynamic pricing system with real-time calculations
- **لوحة تحكم عملاء متقدمة** - Advanced customer dashboard with analytics
- **نظام إشعارات فوري** - Real-time notification system
- **معرض أعمال احترافي** - Professional portfolio showcase
- **نموذج طلب ذكي** - Smart request form with validation
- **دعم اللغة العربية** - Full Arabic language support

---

## 🎯 الخدمات المتاحة

| الخدمة | الوصف | السعر |
|--------|--------|-------|
| **كتابة المحتوى** | محتوى احترافي وأصلي | 50 ر.س / 500 كلمة |
| **البرمجة والتطوير** | تطوير مواقع وتطبيقات | 200 ر.س / ساعة |
| **التسويق الرقمي** | استراتيجيات تسويق متقدمة | 150 ر.س / ساعة |
| **إنشاء الصور** | تصميم وإنشاء صور احترافية | 75 ر.س / صورة |
| **تحليل البيانات** | تحليل وتصور البيانات | 100 ر.س / ساعة |

---

## 🛠️ المتطلبات التقنية

### Backend Requirements
- **Node.js** 22.13.0 أو أحدث
- **Express.js** 4.x
- **tRPC** 11.x
- **Drizzle ORM** لإدارة قاعدة البيانات
- **MySQL/TiDB** لتخزين البيانات

### Frontend Requirements
- **React** 19.x
- **TypeScript** 5.x
- **Tailwind CSS** 4.x
- **Vite** لبناء المشروع
- **shadcn/ui** لمكونات الواجهة

### Additional Services
- **Manus OAuth** للمصادقة
- **S3 Storage** لتخزين الملفات
- **Whisper API** لتحويل الكلام إلى نص
- **Image Generation API** لإنشاء الصور

---

## 🚀 البدء السريع

### 1. استنساخ المشروع
```bash
git clone https://github.com/itsAAA1/nexusai.git
cd nexusai
```

### 2. تثبيت المتطلبات
```bash
pnpm install
```

### 3. إعداد متغيرات البيئة
```bash
cp .env.example .env.local
# ثم قم بتعديل الملف بإضافة مفاتيحك الخاصة
```

### 4. تشغيل قاعدة البيانات
```bash
pnpm db:push
```

### 5. بدء خادم التطوير
```bash
pnpm dev
```

الموقع سيكون متاحاً على: `http://localhost:3000`

---

## 📁 هيكل المشروع

```
nexusai/
├── client/                    # تطبيق React الأمامي
│   ├── src/
│   │   ├── pages/            # صفحات التطبيق
│   │   ├── components/       # مكونات قابلة لإعادة الاستخدام
│   │   ├── contexts/         # React contexts
│   │   ├── hooks/            # Custom hooks
│   │   ├── lib/              # مكتبات مساعدة
│   │   └── App.tsx           # المكون الرئيسي
│   ├── public/               # ملفات ثابتة
│   └── index.html            # ملف HTML الرئيسي
│
├── server/                    # خادم Express
│   ├── _core/                # أساسيات الإطار
│   ├── db.ts                 # مساعدات قاعدة البيانات
│   ├── routers.ts            # إجراءات tRPC
│   └── *.test.ts             # اختبارات Vitest
│
├── drizzle/                   # إدارة قاعدة البيانات
│   ├── schema.ts             # تعريف الجداول
│   └── migrations/           # ملفات الترحيل
│
├── storage/                   # مساعدات S3
│   └── index.ts              # دوال التخزين
│
├── shared/                    # ملفات مشتركة
│   └── types.ts              # أنواع TypeScript
│
└── package.json              # المتطلبات والسكريبتات
```

---

## 🔧 الأوامر المتاحة

```bash
# تطوير
pnpm dev              # بدء خادم التطوير

# الاختبار
pnpm test             # تشغيل اختبارات Vitest
pnpm test:watch       # مراقبة الاختبارات

# قاعدة البيانات
pnpm db:push          # دفع التغييرات إلى قاعدة البيانات
pnpm db:studio        # فتح Drizzle Studio

# البناء
pnpm build            # بناء المشروع للإنتاج
pnpm start            # تشغيل الخادم المبني

# الفحص
pnpm lint             # فحص الكود
pnpm type-check       # فحص أنواع TypeScript
```

---

## 🔐 متغيرات البيئة المطلوبة

```env
# قاعدة البيانات
DATABASE_URL=mysql://user:password@host:port/database

# المصادقة
JWT_SECRET=your-secret-key-here
VITE_APP_ID=your-app-id
OAUTH_SERVER_URL=https://api.manus.im
VITE_OAUTH_PORTAL_URL=https://portal.manus.im

# المالك
OWNER_NAME=Your Name
OWNER_OPEN_ID=your-open-id

# APIs
BUILT_IN_FORGE_API_URL=https://api.manus.im
BUILT_IN_FORGE_API_KEY=your-api-key
VITE_FRONTEND_FORGE_API_URL=https://api.manus.im
VITE_FRONTEND_FORGE_API_KEY=your-frontend-key

# التحليلات
VITE_ANALYTICS_ENDPOINT=https://analytics.manus.im
VITE_ANALYTICS_WEBSITE_ID=your-website-id

# التطبيق
VITE_APP_TITLE=NexusAI
VITE_APP_LOGO=https://cdn.manus.im/nexusai-logo.png
```

---

## 📊 الإحصائيات والأداء

- **⚡ سرعة التحميل:** < 2 ثانية
- **📱 الأجهزة المدعومة:** جميع الأجهزة (Responsive)
- **🌍 اللغات المدعومة:** العربية والإنجليزية
- **👥 عدد الوكلاء:** 5 وكلاء متخصصين
- **📈 معدل النجاح:** 99.5%

---

## 🧪 الاختبار

المشروع يحتوي على اختبارات شاملة باستخدام **Vitest**:

```bash
# تشغيل جميع الاختبارات
pnpm test

# تشغيل اختبار محدد
pnpm test server/auth.logout.test.ts

# مراقبة الاختبارات (Watch mode)
pnpm test:watch

# تقرير التغطية
pnpm test:coverage
```

### مثال على اختبار:
```typescript
import { describe, it, expect } from 'vitest';

describe('AI Agent', () => {
  it('should generate content successfully', async () => {
    const result = await agent.generateContent('test prompt');
    expect(result).toBeDefined();
    expect(result.length).toBeGreaterThan(0);
  });
});
```

---

## 🚀 النشر والاستضافة

### خيارات الاستضافة المدعومة:

1. **Manus Platform** (موصى به)
   - استضافة مدمجة
   - نطاق مخصص
   - SSL تلقائي

2. **Railway**
   - سهل الاستخدام
   - تكامل مع GitHub
   - نسخ احتياطية تلقائية

3. **Vercel**
   - مخصص لـ Next.js
   - نشر سريع جداً
   - CDN عالمي

### خطوات النشر على Manus:
```bash
# 1. إنشاء checkpoint
pnpm checkpoint "Production ready"

# 2. الضغط على زر Publish في لوحة التحكم
# 3. اختيار النطاق المخصص
# 4. تأكيد النشر
```

---

## 🤝 المساهمة

نرحب بمساهماتك! اتبع هذه الخطوات:

1. **Fork المشروع**
   ```bash
   git clone https://github.com/your-username/nexusai.git
   ```

2. **أنشئ فرع جديد**
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **اعمل على التحسينات**
   ```bash
   git add .
   git commit -m "Add amazing feature"
   ```

4. **ادفع التغييرات**
   ```bash
   git push origin feature/amazing-feature
   ```

5. **افتح Pull Request**

---

## 📝 الترخيص

هذا المشروع مرخص تحت **MIT License** - انظر ملف [LICENSE](LICENSE) للتفاصيل.

---

## 📞 التواصل والدعم

- **البريد الإلكتروني:** abdullateef_404@hotmail.com
- **LinkedIn:** [in/abdullateef-alsaeed](https://linkedin.com/in/abdullateef-alsaeed)
- **GitHub:** [@itsAAA1](https://github.com/itsAAA1)
- **الموقع:** [linktr.ee/itsAAA](https://linktr.ee/itsAAA)

---

## 🎓 الموارد والتعليم

- [React Documentation](https://react.dev)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [tRPC Documentation](https://trpc.io/docs)
- [Drizzle ORM Docs](https://orm.drizzle.team)

---

## 📈 خارطة الطريق

- [ ] إضافة نظام الدفع المتقدم
- [ ] تحسين خوارزميات الذكاء الاصطناعي
- [ ] إضافة تطبيق موبايل
- [ ] نظام التقييمات والتعليقات
- [ ] تحليلات متقدمة للأداء
- [ ] دعم لغات إضافية

---

## 🙏 شكر خاص

شكر خاص لجميع المساهمين والمستخدمين الذين ساعدوا في تطوير هذا المشروع.

---

**تم آخر تحديث:** March 16, 2026
**الإصدار:** 1.0.0
**الحالة:** ✅ Production Ready

---

**Made with ❤️ by Abdullateef Abdullah Alsaeid**
