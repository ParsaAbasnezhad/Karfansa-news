import { Link } from "react-router";

import { Icon } from "@/components/ui/Icon";
import { ContactForm } from "@/features/about/components/ContactForm";
import { useContactPage } from "@/features/about/hooks/use-pages";
import { usePageMeta } from "@/hooks/use-page-meta";
import { isSafeHref, sanitizePlainText } from "@/lib/safe-text";

import "../about.css";

function ExternalOrText({
  href,
  children,
}: {
  href: string;
  children: string;
}) {
  const text = sanitizePlainText(children);
  if (!text) return null;
  if (href && isSafeHref(href)) {
    return (
      <a href={href} target={href.startsWith("http") ? "_blank" : undefined} rel="noopener noreferrer">
        {text}
      </a>
    );
  }
  return <p>{text}</p>;
}

export function ContactPage() {
  const pageQuery = useContactPage();
  const page = pageQuery.data;

  usePageMeta(
    page?.seo_title || "تماس با کارفنسا نیوز",
    page?.seo_description ||
      "پیام خود را برای تحریریه کارفنسا نیوز بفرستید؛ پیشنهاد سوژه، اصلاح خبر یا همکاری رسانه‌ای.",
  );

  if (pageQuery.isPending) {
    return (
      <div className="contact-page" dir="rtl" aria-busy="true">
        <div className="about-loading" role="status">
          در حال بارگذاری صفحه تماس…
        </div>
      </div>
    );
  }

  if (pageQuery.isError || !page) {
    return (
      <div className="contact-page" dir="rtl">
        <div className="about-error" role="alert">
          <p>محتوای صفحه تماس بارگذاری نشد.</p>
          <button
            type="button"
            className="about-button about-button-primary"
            onClick={() => void pageQuery.refetch()}
          >
            تلاش دوباره
          </button>
        </div>
      </div>
    );
  }

  const infoCards = [
    page.support_email
      ? {
          icon: "mail" as const,
          title: "ایمیل پشتیبانی",
          body: page.support_email,
          href: `mailto:${page.support_email}`,
        }
      : null,
    page.business_email
      ? {
          icon: "mail" as const,
          title: "ایمیل تجاری",
          body: page.business_email,
          href: `mailto:${page.business_email}`,
        }
      : null,
    page.phone
      ? {
          icon: "phone" as const,
          title: "شماره تماس",
          body: page.phone,
          href: `tel:${page.phone.replace(/\s+/g, "")}`,
        }
      : null,
    page.whatsapp
      ? {
          icon: "phone" as const,
          title: "واتساپ",
          body: page.whatsapp,
          href: isSafeHref(page.whatsapp)
            ? page.whatsapp
            : `https://wa.me/${page.whatsapp.replace(/\D/g, "")}`,
        }
      : null,
    page.office_address
      ? {
          icon: "building" as const,
          title: "آدرس دفتر",
          body: page.office_address,
          href: page.map_url && isSafeHref(page.map_url) ? page.map_url : "",
        }
      : null,
    page.response_hours
      ? {
          icon: "clock" as const,
          title: "ساعات پاسخ‌گویی",
          body: page.response_hours,
          href: "",
        }
      : null,
  ].filter(Boolean) as Array<{
    icon: "mail" | "phone" | "building" | "clock";
    title: string;
    body: string;
    href: string;
  }>;

  const socialLinks = [
    page.instagram_url ? { label: "اینستاگرام", href: page.instagram_url } : null,
    page.linkedin_url ? { label: "لینکدین", href: page.linkedin_url } : null,
    page.telegram_url ? { label: "تلگرام", href: page.telegram_url } : null,
  ].filter((item): item is { label: string; href: string } => Boolean(item && isSafeHref(item.href)));

  return (
    <div className="contact-page" dir="rtl">
      <header className="contact-hero">
        <div className="contact-hero-copy">
          <span className="about-kicker">
            <i />
            ارتباط با تحریریه
          </span>
          <h1>{sanitizePlainText(page.title)}</h1>
          {page.description ? <p>{sanitizePlainText(page.description)}</p> : null}
        </div>
      </header>

      {infoCards.length > 0 ? (
        <section className="contact-info-grid" aria-label="اطلاعات ارتباط">
          {infoCards.map((card) => (
            <article className="contact-info-card" key={card.title}>
              <span className="contact-info-icon">
                <Icon name={card.icon} />
              </span>
              <div>
                <h2>{card.title}</h2>
                <ExternalOrText href={card.href}>{card.body}</ExternalOrText>
              </div>
            </article>
          ))}
        </section>
      ) : (
        <section className="contact-info-grid" aria-label="اطلاعات ارتباط">
          <article className="contact-info-card">
            <span className="contact-info-icon">
              <Icon name="mail" />
            </span>
            <div>
              <h2>فرم تحریریه</h2>
              <p>پیام از همین صفحه ذخیره می‌شود تا تحریریه آن را بررسی کند.</p>
            </div>
          </article>
          <article className="contact-info-card">
            <span className="contact-info-icon">
              <Icon name="file" />
            </span>
            <div>
              <h2>موضوع‌های پیام</h2>
              <p>سوژه، اصلاح خبر، همکاری، تبلیغات، پشتیبانی فنی یا سایر موارد.</p>
            </div>
          </article>
          <article className="contact-info-card">
            <span className="contact-info-icon">
              <Icon name="clock" />
            </span>
            <div>
              <h2>پاسخ‌گویی</h2>
              <p>
                {sanitizePlainText(page.support_text) ||
                  "پیگیری جداگانه در این نسخه نیست؛ پس از بررسی در صورت نیاز تماس گرفته می‌شود."}
              </p>
            </div>
          </article>
        </section>
      )}

      <div className="contact-layout">
        <section className="contact-form-panel" aria-labelledby="contact-form-title">
          <span className="about-eyebrow">فرم ارتباط</span>
          <h2 id="contact-form-title">پیام خود را بنویسید</h2>
          <p className="contact-form-intro">
            {sanitizePlainText(page.form_intro) || "همهٔ فیلدها الزامی هستند."}
          </p>
          <ContactForm privacyNote={page.support_text} />
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
          {socialLinks.length > 0 ? (
            <div className="contact-social-links">
              {socialLinks.map((item) => (
                <a key={item.label} href={item.href} target="_blank" rel="noopener noreferrer">
                  <Icon name="arrow" />
                  <span>{item.label}</span>
                  <Icon name="chevron-left" />
                </a>
              ))}
            </div>
          ) : null}
        </aside>
      </div>

      {page.faqs.length > 0 ? (
        <section className="contact-faq" aria-labelledby="contact-faq-title">
          <span className="about-eyebrow">پیش از ارسال</span>
          <h2 id="contact-faq-title">پرسش‌های متداول</h2>
          <div className="contact-faq-list">
            {page.faqs.map((faq) => (
              <details key={faq.id}>
                <summary>{sanitizePlainText(faq.question)}</summary>
                <p>{sanitizePlainText(faq.answer)}</p>
              </details>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
