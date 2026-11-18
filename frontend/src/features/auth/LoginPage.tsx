import { useMutation } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router";

import { queryClient } from "@/app/query-client";
import { authApi } from "@/features/auth/api";
import {
  AuthFeedback,
  AuthField,
  AuthShell,
  AuthSubmitLabel,
  PasswordField,
} from "@/features/auth/components";
import { sessionKey } from "@/features/auth/session";
import { normalizeIdentifier, safeRedirect } from "@/features/auth/validation";
import { usePageMeta } from "@/hooks/use-page-meta";

export function LoginPage() {
  usePageMeta("ورود به حساب | کارفنسا");
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const next = safeRedirect(params.get("next"));
  const [mode, setMode] = useState<"password" | "otp">("password");
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [validationError, setValidationError] = useState("");

  const login = useMutation({
    mutationFn: () => authApi.login(normalizeIdentifier(identifier), password),
    onSuccess: ({ user }) => {
      queryClient.setQueryData(sessionKey, user);
      void navigate(next, { replace: true });
    },
  });
  const requestOtp = useMutation({
    mutationFn: () => authApi.requestLoginOtp(normalizeIdentifier(identifier)),
    onSuccess: ({ challenge_id }) => {
      const query = new URLSearchParams({ purpose: "login", challenge: challenge_id, next });
      void navigate(`/verify?${query.toString()}`);
    },
  });

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (login.isPending || requestOtp.isPending) return;
    if (!identifier.trim()) {
      setValidationError("ایمیل یا شماره موبایل را وارد کنید.");
      return;
    }
    if (mode === "password") {
      if (!password) {
        setValidationError("رمز عبور را وارد کنید.");
        return;
      }
      login.mutate();
    } else requestOtp.mutate();
  };

  return (
    <AuthShell
      title="ورود به حساب"
      description="برای ادامه، روش ورود دلخواهتان را انتخاب کنید."
      footer={
        <span>
          حساب ندارید؟ <Link to="/register">ثبت‌نام کنید</Link>
        </span>
      }
    >
      <div
        className="auth-tabs"
        role="group"
        aria-label="روش ورود"
        data-active={mode === "password" ? "0" : "1"}
      >
        <button
          type="button"
          className={mode === "password" ? "active" : ""}
          aria-pressed={mode === "password"}
          onClick={() => {
            setMode("password");
            setValidationError("");
          }}
        >
          رمز عبور
        </button>
        <button
          type="button"
          className={mode === "otp" ? "active" : ""}
          aria-pressed={mode === "otp"}
          onClick={() => {
            setMode("otp");
            setValidationError("");
          }}
        >
          کد یک‌بارمصرف
        </button>
      </div>
      {params.get("reset") === "success" ? (
        <AuthFeedback message="رمز عبور با موفقیت تغییر کرد. اکنون وارد شوید." />
      ) : null}
      <form className="auth-form" onSubmit={submit} noValidate>
        <AuthField
          label="ایمیل یا شماره موبایل"
          name="identifier"
          autoComplete="username"
          inputMode="email"
          value={identifier}
          onChange={(event) => {
            setIdentifier(event.target.value);
            setValidationError("");
          }}
          required
        />
        {mode === "password" ? (
          <>
            <PasswordField
              label="رمز عبور"
              name="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => {
                setPassword(event.target.value);
                setValidationError("");
              }}
              required
            />
            <Link className="auth-secondary-link" to="/forgot-password">
              رمز عبور را فراموش کرده‌اید؟
            </Link>
          </>
        ) : (
          <p className="auth-hint">کد ورود به راه ارتباطی تأییدشده شما فرستاده می‌شود.</p>
        )}
        <AuthFeedback error={validationError || login.error || requestOtp.error} />
        <button
          className="auth-submit"
          type="submit"
          disabled={login.isPending || requestOtp.isPending}
        >
          <AuthSubmitLabel
            pending={login.isPending || requestOtp.isPending}
            idle={mode === "password" ? "ورود" : "دریافت کد ورود"}
          />
        </button>
      </form>
    </AuthShell>
  );
}
