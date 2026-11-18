import { useMutation } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";

import { authApi } from "@/features/auth/api";
import { queryClient } from "@/app/query-client";
import {
  AuthFeedback,
  AuthField,
  AuthShell,
  AuthSubmitLabel,
  PasswordField,
} from "@/features/auth/components";
import { useResetToken } from "@/features/auth/reset-token-context";
import { sessionKey } from "@/features/auth/session";
import { normalizeIdentifier, validatePasswordPair } from "@/features/auth/validation";
import { usePageMeta } from "@/hooks/use-page-meta";

export function ForgotPasswordPage() {
  usePageMeta("فراموشی رمز عبور | کارفنسا");
  const navigate = useNavigate();
  const { setToken } = useResetToken();
  const [identifier, setIdentifier] = useState("");
  const [validationError, setValidationError] = useState("");
  const request = useMutation({
    mutationFn: () => authApi.forgotPassword(normalizeIdentifier(identifier)),
    onSuccess: ({ challenge_id }) => {
      setToken(null);
      void navigate(
        `/verify?${new URLSearchParams({ purpose: "reset", challenge: challenge_id }).toString()}`,
      );
    },
  });
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (request.isPending) return;
    if (!identifier.trim()) {
      setValidationError("ایمیل یا شماره موبایل را وارد کنید.");
      return;
    }
    setValidationError("");
    request.mutate();
  };
  return (
    <AuthShell
      title="بازیابی رمز عبور"
      description="اگر حسابی با این راه ارتباطی فعال باشد، کد بازیابی برایتان فرستاده می‌شود."
      footer={<Link to="/login">بازگشت به ورود</Link>}
    >
      <form className="auth-form" onSubmit={submit} noValidate>
        <AuthField
          label="ایمیل یا شماره موبایل"
          name="identifier"
          autoComplete="username"
          value={identifier}
          onChange={(event) => {
            setIdentifier(event.target.value);
            setValidationError("");
          }}
          required
        />
        <AuthFeedback error={validationError || request.error} />
        <button className="auth-submit" type="submit" disabled={request.isPending}>
          <AuthSubmitLabel
            pending={request.isPending}
            idle="دریافت کد بازیابی"
            pendingLabel="در حال بررسی…"
          />
        </button>
      </form>
    </AuthShell>
  );
}

export function ResetPasswordPage() {
  usePageMeta("رمز عبور جدید | کارفنسا");
  const navigate = useNavigate();
  const { token, setToken } = useResetToken();
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [validationError, setValidationError] = useState("");
  const reset = useMutation({
    mutationFn: () => authApi.resetPassword(token!, password, confirmation),
    onSuccess: () => {
      setToken(null);
      queryClient.setQueryData(sessionKey, null);
      void navigate("/login?reset=success", { replace: true });
    },
  });
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (reset.isPending) return;
    const error = validatePasswordPair(password, confirmation);
    setValidationError(error ?? "");
    if (!error) reset.mutate();
  };
  if (!token) {
    return (
      <AuthShell
        title="کد بازیابی لازم است"
        description="ابتدا کد ارسال‌شده را تأیید کنید."
        footer={<Link to="/forgot-password">شروع بازیابی</Link>}
      >
        <p className="auth-hint">مجوز تغییر رمز عبور در این صفحه یافت نشد.</p>
      </AuthShell>
    );
  }
  return (
    <AuthShell
      title="انتخاب رمز عبور جدید"
      description="برای حساب خود رمز عبور تازه و قوی انتخاب کنید."
      footer={<Link to="/login">بازگشت به ورود</Link>}
    >
      <form className="auth-form" onSubmit={submit} noValidate>
        <PasswordField
          label="رمز عبور جدید"
          name="new_password"
          autoComplete="new-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          minLength={8}
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
        <AuthFeedback error={validationError || reset.error} />
        <button className="auth-submit" type="submit" disabled={reset.isPending}>
          <AuthSubmitLabel
            pending={reset.isPending}
            idle="ذخیره رمز عبور"
            pendingLabel="در حال ذخیره…"
          />
        </button>
      </form>
    </AuthShell>
  );
}
