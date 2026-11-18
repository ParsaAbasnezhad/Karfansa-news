import { useMutation } from "@tanstack/react-query";
import { useState, type FormEvent, type ReactNode } from "react";
import { Link, useNavigate } from "react-router";

import { queryClient } from "@/app/query-client";
import { Icon, type IconName } from "@/components/ui/Icon";
import { authApi } from "@/features/auth/api";
import { sessionKey, useSession } from "@/features/auth/session";
import { usePageMeta } from "@/hooks/use-page-meta";
import { getErrorMessage } from "@/lib/errors";

type DashboardCardProps = {
  icon: IconName;
  title: string;
  description: string;
  children: ReactNode;
};

function DashboardCard({ icon, title, description, children }: DashboardCardProps) {
  return (
    <section className="profile-card dashboard-card">
      <div className="dashboard-card__heading">
        <span className="profile-icon" aria-hidden="true">
          <Icon name={icon} />
        </span>
        <div>
          <h2>{title}</h2>
          <p>{description}</p>
        </div>
      </div>
      {children}
    </section>
  );
}

function EmptyState({ children }: { children: ReactNode }) {
  return <p className="profile-empty">{children}</p>;
}

export function ProfilePage() {
  usePageMeta("پروفایل من | کارفنسا");
  const { user } = useSession();
  const navigate = useNavigate();
  const [editing, setEditing] = useState(false);
  const [firstName, setFirstName] = useState(user?.first_name ?? "");
  const [lastName, setLastName] = useState(user?.last_name ?? "");
  const [formError, setFormError] = useState("");
  const [saved, setSaved] = useState(false);

  const updateProfile = useMutation({
    mutationFn: () =>
      authApi.updateProfile({ first_name: firstName.trim(), last_name: lastName.trim() }),
    onSuccess: ({ user: updatedUser }) => {
      queryClient.setQueryData(sessionKey, updatedUser);
      setEditing(false);
      setSaved(true);
      window.setTimeout(() => setSaved(false), 3500);
    },
  });

  const logout = useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      queryClient.setQueryData(sessionKey, null);
      void navigate("/login", { replace: true });
    },
  });

  if (!user) return null;

  const fullName = [user.first_name, user.last_name].filter(Boolean).join(" ") || user.username;
  const initials =
    `${user.first_name.at(0) ?? ""}${user.last_name.at(0) ?? ""}` || user.username.at(0);
  const verified = Boolean(user.email_verified || user.mobile_verified);
  const joinedAt = new Intl.DateTimeFormat("fa-IR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(user.date_joined));

  const submitProfile = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaved(false);
    if (!firstName.trim() || !lastName.trim()) {
      setFormError("نام و نام خانوادگی را کامل وارد کنید.");
      return;
    }
    setFormError("");
    updateProfile.mutate();
  };

  return (
    <div className="profile-page" dir="rtl">
      <div className="wrap profile-wrap">
        <header className="profile-card profile-hero">
          <div className="profile-avatar" aria-label={`تصویر نمایه ${fullName}`}>
            {initials?.toUpperCase()}
          </div>
          <div className="profile-identity">
            <div className="profile-title-row">
              <div>
                <p className="profile-eyebrow">حساب کاربری کارفنسا</p>
                <h1>{fullName}</h1>
              </div>
              <span className={verified ? "profile-status is-verified" : "profile-status"}>
                <Icon name={verified ? "check" : "clock"} />
                {verified ? "حساب تأییدشده" : "در انتظار تأیید"}
              </span>
            </div>
            <div className="profile-meta">
              <span>
                <Icon name="mail" />
                <bdi>{user.email || "ایمیل ثبت نشده"}</bdi>
              </span>
              <span>
                <Icon name="phone" />
                <bdi>{user.mobile || "شماره موبایل ثبت نشده"}</bdi>
              </span>
              <span>
                <Icon name="calendar" />
                عضویت از {joinedAt}
              </span>
            </div>
          </div>
          <button
            className="profile-button profile-button--primary"
            type="button"
            onClick={() => setEditing(true)}
          >
            <Icon name="edit" /> ویرایش پروفایل
          </button>
        </header>

        {saved && (
          <div className="profile-alert profile-alert--success" role="status">
            تغییرات پروفایل با موفقیت ذخیره شد.
          </div>
        )}

        <div className="profile-grid">
          <DashboardCard
            icon="user"
            title="اطلاعات شخصی"
            description="مشخصات پایه و راه‌های ارتباطی شما"
          >
            {editing ? (
              <form className="profile-form" onSubmit={submitProfile}>
                <label>
                  نام
                  <input
                    value={firstName}
                    onChange={(event) => setFirstName(event.target.value)}
                    autoComplete="given-name"
                    maxLength={150}
                  />
                </label>
                <label>
                  نام خانوادگی
                  <input
                    value={lastName}
                    onChange={(event) => setLastName(event.target.value)}
                    autoComplete="family-name"
                    maxLength={150}
                  />
                </label>
                {(formError || updateProfile.error) && (
                  <p className="profile-form-error" role="alert">
                    {formError || getErrorMessage(updateProfile.error)}
                  </p>
                )}
                <div className="profile-form-actions">
                  <button
                    className="profile-button profile-button--primary"
                    disabled={updateProfile.isPending}
                    type="submit"
                  >
                    {updateProfile.isPending ? "در حال ذخیره…" : "ذخیره تغییرات"}
                  </button>
                  <button
                    className="profile-button profile-button--ghost"
                    type="button"
                    onClick={() => setEditing(false)}
                  >
                    انصراف
                  </button>
                </div>
              </form>
            ) : (
              <div className="profile-list">
                <div>
                  <span>نام کامل</span>
                  <strong>{fullName}</strong>
                </div>
                <div>
                  <span>ایمیل</span>
                  <strong dir="ltr">{user.email || "—"}</strong>
                </div>
                <div>
                  <span>شماره موبایل</span>
                  <strong dir="ltr">{user.mobile || "—"}</strong>
                </div>
                <div>
                  <span>آدرس‌ها</span>
                  <strong className="profile-muted">هنوز آدرسی ثبت نشده است</strong>
                </div>
              </div>
            )}
          </DashboardCard>

          <DashboardCard
            icon="shield"
            title="امنیت حساب"
            description="تأیید راه‌های ارتباطی و مدیریت رمز عبور"
          >
            <div className="profile-verification">
              <span>
                <i className={user.email_verified ? "is-ok" : ""} />
                ایمیل {user.email_verified ? "تأیید شده" : "تأیید نشده"}
              </span>
              <span>
                <i className={user.mobile_verified ? "is-ok" : ""} />
                موبایل {user.mobile_verified ? "تأیید شده" : "تأیید نشده"}
              </span>
            </div>
            <Link className="profile-text-link" to="/account/security">
              مدیریت امنیت و تغییر رمز <Icon name="chevron-left" />
            </Link>
            <button
              className="profile-logout"
              type="button"
              disabled={logout.isPending}
              onClick={() => logout.mutate()}
            >
              <Icon name="logout" />
              {logout.isPending ? "در حال خروج…" : "خروج امن از حساب"}
            </button>
          </DashboardCard>

          <DashboardCard
            icon="ticket"
            title="پشتیبانی"
            description="پرسش‌ها و درخواست‌های شما از تیم کارفنسا"
          >
            <EmptyState>در حال حاضر تیکتی برای این حساب ثبت نشده است.</EmptyState>
            <Link className="profile-text-link" to="/contact">
              ارتباط با پشتیبانی <Icon name="chevron-left" />
            </Link>
          </DashboardCard>

          <DashboardCard
            icon="briefcase"
            title="فعالیت‌های تجاری"
            description="نمای کلی شرکت‌ها، خدمات و فرصت‌های مرتبط"
          >
            <div className="business-stats" aria-label="آمار فعالیت تجاری">
              <div>
                <strong>۰</strong>
                <span>شرکت ثبت‌شده</span>
              </div>
              <div>
                <strong>۰</strong>
                <span>محصول یا خدمت</span>
              </div>
              <div>
                <strong>۰</strong>
                <span>درخواست فعال</span>
              </div>
            </div>
            <EmptyState>فعالیت تجاری ثبت‌شده‌ای برای نمایش وجود ندارد.</EmptyState>
          </DashboardCard>
        </div>

        <section className="profile-opportunities" aria-labelledby="opportunities-title">
          <div className="opportunities-intro">
            <p className="profile-eyebrow">رشد در شبکه تجاری کارفنسا</p>
            <h2 id="opportunities-title">فرصت‌های بزرگ، از یک ارتباط آغاز می‌شوند</h2>
            <p>
              کارفنسا، بستری برای توسعه ارتباطات تجاری، معرفی توانمندی‌های اقتصادی و کشف فرصت‌های
              تازه در بازارهای داخلی و بین‌المللی است.
            </p>
            <p>
              اگر صاحب کسب‌وکار، تولیدکننده، صادرکننده یا ارائه‌دهنده خدمات هستید، می‌توانید با
              معرفی مجموعه خود در کارفنسا، مسیر تازه‌ای برای دیده‌شدن، ایجاد همکاری‌های تجاری و
              گسترش بازارهای هدف خود آغاز کنید.
            </p>
            <p>
              از ثبت و معرفی شرکت‌ها تا ارائه خدمات تخصصی، شناسایی فرصت‌های سرمایه‌گذاری، تأمین کالا
              و توسعه صادرات، کارفنسا تلاش می‌کند ارتباط میان فعالان اقتصادی را ساده‌تر،
              هوشمندانه‌تر و مؤثرتر کند.
            </p>
          </div>
          <div className="opportunity-grid">
            <article className="opportunity-card">
              <span className="opportunity-icon">
                <Icon name="building" />
              </span>
              <h3>ثبت و معرفی شرکت</h3>
              <p>
                کسب‌وکار خود را به جامعه فعالان اقتصادی معرفی کنید، توانمندی‌ها و محصولاتتان را به
                نمایش بگذارید و زمینه همکاری‌های تجاری جدید را فراهم کنید.
              </p>
              <Link to="/contact?subject=company">
                معرفی شرکت من <Icon name="chevron-left" />
              </Link>
            </article>
            <article className="opportunity-card">
              <span className="opportunity-icon">
                <Icon name="box" />
              </span>
              <h3>معرفی محصولات و خدمات</h3>
              <p>
                محصولات، تخصص‌ها و خدمات خود را در بستری حرفه‌ای معرفی کنید تا مشتریان و شرکای تجاری
                بالقوه راحت‌تر با شما آشنا شوند.
              </p>
              <Link to="/contact?subject=service">
                ثبت محصول یا خدمت <Icon name="chevron-left" />
              </Link>
            </article>
            <article className="opportunity-card">
              <span className="opportunity-icon">
                <Icon name="compass" />
              </span>
              <h3>فرصت‌های اقتصادی و صادراتی</h3>
              <p>
                فرصت‌های مرتبط با صادرات، واردات، تأمین مواد اولیه، سرمایه‌گذاری و همکاری‌های تجاری
                را کشف کنید و افق‌های تازه‌ای برای توسعه فعالیت خود بیابید.
              </p>
              <Link to="/news">
                کشف فرصت‌ها <Icon name="chevron-left" />
              </Link>
            </article>
          </div>
        </section>
      </div>
    </div>
  );
}
