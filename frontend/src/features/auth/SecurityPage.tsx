import { useMutation } from "@tanstack/react-query";
import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router";

import { queryClient } from "@/app/query-client";
import { authApi } from "@/features/auth/api";
import {
  AuthFeedback,
  AuthShell,
  AuthSubmitLabel,
  OtpInput,
  PasswordField,
} from "@/features/auth/components";
import { sessionKey, useSession } from "@/features/auth/session";
import { validatePasswordPair } from "@/features/auth/validation";
import { usePageMeta } from "@/hooks/use-page-meta";

export function SecurityPage() {
  usePageMeta("امنیت حساب | کارفنسا");
  const { user } = useSession();
  const navigate = useNavigate();
  const [challenge, setChallenge] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [validationError, setValidationError] = useState("");
  const [success, setSuccess] = useState("");
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    if (seconds <= 0) return;
    const timer = window.setTimeout(() => setSeconds((value) => Math.max(0, value - 1)), 1000);
    return () => window.clearTimeout(timer);
  }, [seconds]);

  const requestChange = useMutation({
    mutationFn: authApi.requestChangePasswordOtp,
    onSuccess: ({ challenge_id }) => {
      setChallenge(challenge_id);
      setSeconds(60);
      setSuccess("کد تأیید برای راه ارتباطی تأییدشده شما فرستاده شد.");
    },
  });
  const resendChange = useMutation({
    mutationFn: () => authApi.resendOtp(challenge),
    onSuccess: ({ challenge_id }) => {
      setChallenge(challenge_id);
      setCode("");
      setSeconds(60);
      setSuccess("کد تازه فرستاده شد.");
    },
  });
  const change = useMutation({
    mutationFn: () => authApi.changePassword(challenge, code, password, confirmation),
    onSuccess: () => {
      setCode("");
      setPassword("");
      setConfirmation("");
      setChallenge("");
      setSuccess("رمز عبور تغییر کرد. نشست‌های دیگر شما خارج شدند.");
      void queryClient.invalidateQueries({ queryKey: sessionKey });
    },
  });
  const contact = useMutation({
    mutationFn: (method: "email" | "sms") => authApi.requestContactVerification(method),
    onSuccess: ({ challenge_id }) => {
      void navigate(
        `/verify?${new URLSearchParams({ purpose: "contact", challenge: challenge_id }).toString()}`,
      );
    },
  });
  const logout = useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      queryClient.setQueryData(sessionKey, null);
      void navigate("/login", { replace: true });
    },
  });

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (change.isPending) return;
    const error = !/^\d{6}$/.test(code)
      ? "کد شش‌رقمی را کامل وارد کنید."
      : validatePasswordPair(password, confirmation);
    setValidationError(error ?? "");
    setSuccess("");
    if (!error) change.mutate();
  };

  return (
    <AuthShell
      title="امنیت حساب"
      description={
        user
          ? `سلام ${user.first_name || user.username}، راه‌های ارتباطی و رمز عبور خود را اینجا مدیریت کنید.`
          : "مدیریت حساب کاربری"
      }
    >
      <div className="auth-security-section">
        <h2>راه‌های ارتباطی</h2>
        <div className="auth-contact-row">
          <div>
            <b>ایمیل</b>
            <span dir="ltr">{user?.email || "ثبت نشده"}</span>
          </div>
          {user?.email ? (
            user.email_verified ? (
              <span className="auth-badge verified">تأیید شده</span>
            ) : (
              <button
                type="button"
                disabled={contact.isPending}
                onClick={() => contact.mutate("email")}
              >
                تأیید ایمیل
              </button>
            )
          ) : null}
        </div>
        <div className="auth-contact-row">
          <div>
            <b>موبایل</b>
            <span dir="ltr">{user?.mobile || "ثبت نشده"}</span>
          </div>
          {user?.mobile ? (
            user.mobile_verified ? (
              <span className="auth-badge verified">تأیید شده</span>
            ) : (
              <button
                type="button"
                disabled={contact.isPending}
                onClick={() => contact.mutate("sms")}
              >
                تأیید موبایل
              </button>
            )
          ) : null}
        </div>
        <AuthFeedback error={contact.error} />
      </div>
      <div className="auth-security-section">
        <h2>تغییر رمز عبور</h2>
        <p className="auth-hint">
          برای تغییر رمز عبور، ابتدا کد تأیید را از راه ارتباطی تأییدشده دریافت کنید.
        </p>
        {!challenge ? (
          <button
            className="auth-outline-button"
            type="button"
            disabled={requestChange.isPending}
            onClick={() => {
              setSuccess("");
              requestChange.mutate();
            }}
          >
            <AuthSubmitLabel
              pending={requestChange.isPending}
              idle="دریافت کد تغییر رمز"
              pendingLabel="در حال ارسال…"
            />
          </button>
        ) : (
          <form className="auth-form" onSubmit={submit} noValidate>
            <OtpInput
              value={code}
              onChange={(value) => {
                setCode(value);
                setValidationError("");
              }}
              disabled={change.isPending}
            />
            <PasswordField
              label="رمز عبور جدید"
              name="new_password"
              autoComplete="new-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
            <PasswordField
              label="تکرار رمز عبور"
              name="password_confirmation"
              autoComplete="new-password"
              value={confirmation}
              onChange={(event) => setConfirmation(event.target.value)}
              required
            />
            <button className="auth-submit" type="submit" disabled={change.isPending}>
              <AuthSubmitLabel
                pending={change.isPending}
                idle="تغییر رمز عبور"
                pendingLabel="در حال ذخیره…"
              />
            </button>
            <button
              className="auth-text-button"
              type="button"
              disabled={seconds > 0 || resendChange.isPending}
              onClick={() => resendChange.mutate()}
            >
              {seconds > 0
                ? `ارسال دوباره پس از ${seconds} ثانیه`
                : resendChange.isPending
                  ? "در حال ارسال…"
                  : "ارسال دوباره کد"}
            </button>
          </form>
        )}
        <AuthFeedback
          error={validationError || requestChange.error || resendChange.error || change.error}
          message={success}
        />
      </div>
      <div className="auth-security-section auth-signout">
        <h2>خروج از حساب</h2>
        <button
          className="auth-outline-button"
          type="button"
          onClick={() => logout.mutate()}
          disabled={logout.isPending}
        >
          <AuthSubmitLabel pending={logout.isPending} idle="خروج" pendingLabel="در حال خروج…" />
        </button>
        <AuthFeedback error={logout.error} />
      </div>
    </AuthShell>
  );
}
