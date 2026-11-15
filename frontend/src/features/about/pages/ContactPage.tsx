import { Link } from "react-router";

import { Icon } from "@/components/ui/Icon";
import { ContactForm } from "@/features/about/components/ContactForm";
import { usePageMeta } from "@/hooks/use-page-meta";

import "../about.css";

const faqs = [
  {
    question: "پیام من کجا می‌رود؟",
    answer: "متن فرم در سرویس تماس ذخیره می‌شود تا تحریریه آن را ببیند. پیگیری جداگانه‌ای در این نسخه وجود ندارد.",
  },
  {
    question: "برای اصلاح یک خبر چه موضوعی را انتخاب کنم؟",
    answer: "موضوع «اصلاح خبر» را انتخاب کنید و عنوان خبر و توضیح اصلاح را در متن بنویسید.",
  },
  {
    question: "اگر ارسال نشد چه کنم؟",
    answer: "فیلدها را با پیام خطا تطبیق دهید. اگر تعداد ارسال‌ها در یک ساعت زیاد باشد، سرویس کمی بعد دوباره پذیرای پیام است.",
  },
];

export function ContactPage() {
  usePageMeta(
    "تماس با کارفنسا نیوز",
    "پیام خود را برای تحریریه کارفنسا نیوز بفرستید؛ پیشنهاد سوژه، اصلاح خبر یا همکاری رسانه‌ای.",
  );

  return (
    <div className="contact-page" dir="rtl">
      <header className="contact-hero">
        <div className="contact-hero-copy">
          <span className="about-kicker">
            <i />
            ارتباط با تحریریه
          </span>
          <h1>برای سوژه، اصلاح یا همکاری بنویسید</h1>
          <p>پیام از همین صفحه به سرویس تماس می‌رود و برای بررسی ذخیره می‌شود.</p>
        </div>
      </header>

      <div className="contact-layout">
        <section className="contact-form-panel" aria-labelledby="contact-form-title">
          <span className="about-eyebrow">فرم ارتباط</span>
          <h2 id="contact-form-title">پیام خود را بنویسید</h2>
          <p className="contact-form-intro">همهٔ فیلدها الزامی هستند.</p>
          <ContactForm />
        </section>
        <aside className="contact-aside" aria-labelledby="contact-shortcuts-title">
          <div className="contact-aside-top">
            <span className="about-eyebrow">مسیرهای سریع</span>
            <h2 id="contact-shortcuts-title">اگر به دنبال خبر هستید، مستقیم بروید.</h2>
          </div>
          <Link className="contact-shortcut" to="/news">
            <span className="contact-shortcut-icon">
              <Icon name="news" />
            </span>
            <span>
              <strong>فهرست اخبار</strong>
              <small>جست‌وجو، موضوع و زمان انتشار</small>
            </span>
            <Icon name="arrow" />
          </Link>
          <Link className="contact-shortcut" to="/about">
            <span className="contact-shortcut-icon">
              <Icon name="building" />
            </span>
            <span>
              <strong>دربارهٔ کارفنسا نیوز</strong>
              <small>روش انتخاب و نمایش خبرها</small>
            </span>
            <Icon name="arrow" />
          </Link>
        </aside>
      </div>

      <section className="contact-faq" aria-labelledby="contact-faq-title">
        <span className="about-eyebrow">پیش از ارسال</span>
        <h2 id="contact-faq-title">پرسش‌های متداول</h2>
        <div className="contact-faq-list">
          {faqs.map((faq) => (
            <details key={faq.question}>
              <summary>{faq.question}</summary>
              <p>{faq.answer}</p>
            </details>
          ))}
        </div>
      </section>
    </div>
  );
}
