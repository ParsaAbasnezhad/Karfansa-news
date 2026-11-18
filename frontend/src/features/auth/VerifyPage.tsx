import { useMutation } from "@tanstack/react-query";
import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router";

import { queryClient } from "@/app/query-client";
import { authApi } from "@/features/auth/api";
import { AuthFeedback, AuthShell, AuthSubmitLabel, OtpInput } from "@/features/auth/components";
import { useResetToken } from "@/features/auth/reset-token-context";
import { sessionKey } from "@/features/auth/session";
import { safeRedirect } from "@/features/auth/validation";
import { usePageMeta } from "@/hooks/use-page-meta";

type Purpose = "registration" | "login" | "reset" | "contact";
const labels: Record<Purpose, string> = {
  registration: "تأیید حساب",
  login: "تأیید ورود",
  reset: "بازیابی رمز عبور",
  contact: "تأیید راه ارتباطی",
};

export function VerifyPage() {
  usePageMeta("تأیید کد | کارفنسا");
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { setToken } = useResetToken();
  const rawPurpose = params.get("purpose");
  const purpose: Purpose | null =
    rawPurpose && rawPurpose in labels ? (rawPurpose as Purpose) : null;
  const challenge = params.get("challenge") ?? "";
  const next = safeRedirect(params.get("next"));
  const [code, setCode] = useState("");
  const [seconds, setSeconds] = useState(60);
  const [validationError, setValidationError] = useState("");

  useEffect(() => {
    if (seconds <= 0) return;
    const timer = window.setTimeout(() => setSeconds((value) => Math.max(0, value - 1)), 1000);
    return () => window.clearTimeout(timer);
  }, [seconds]);

  const verify = useMutation({
    mutationFn: async () => {
      if (purpose === "registration")
        return { kind: purpose, value: await authApi.verifyRegistration(challenge, code) } as const;
      if (purpose === "login")
        return { kind: purpose, value: await authApi.verifyLoginOtp(challenge, code) } as const;
      if (purpose === "contact")
        return { kind: purpose, value: await authApi.verifyContact(challenge, code) } as const;
      if (purpose === "reset")
        return { kind: purpose, value: await authApi.verifyResetOtp(challenge, code) } as const;
      throw new Error("درخواست تأیید معتبر نیست.");
    },
    onSuccess: (result) => {
      if (result.kind === "reset") {
        setToken(result.value.reset_token);
        void navigate("/reset-password", { replace: true });
        return;
      }
      queryClient.setQueryData(sessionKey, result.value.user);
      void navigate(
        result.kind === "contact"
          ? "/account/security"
          : result.kind === "login"
            ? next
            : "/account/security",
        { replace: true },
      );
    },
  });
  const resend = useMutation({
    mutationFn: () => authApi.resendOtp(challenge),
    onSuccess: ({ challenge_id }) => {
      const updated = new URLSearchParams(params);
      updated.set("challenge", challenge_id);
      setCode("");
      setSeconds(60);
      void navigate(`/verify?${updated.toString()}`, { replace: true });
    },
  });

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (verify.isPending || !purpose || !challenge) return;
    if (!/^\d{6}$/.test(code)) {
      setValidationError("کد شش‌رقمی را کامل وارد کنید.");
      return;
    }
    setValidationError("");
    verify.mutate();
  };

  if (!purpose || !challenge) {
    return (
      <AuthShell
        title="درخواست نامعتبر"
        description="برای دریافت کد تازه، از مرحله قبل شروع کنید."
        footer={<Link to="/login">بازگشت به ورود</Link>}
      >
        <p className="auth-feedback auth-error">اطلاعات تأیید یافت نشد.</p>
      </AuthShell>
    );
  }

  return (
    <AuthShell
      title={labels[purpose]}
      description="کد شش‌رقمی ارسال‌شده را وارد کنید. اعتبار کد ۵ دقیقه است."
      footer={
        <Link
          to={
            purpose === "reset"
              ? "/forgot-password"
              : purpose === "registration"
                ? "/register"
                : purpose === "contact"
                  ? "/account/security"
                  : "/login"
          }
        >
          بازگشت به مرحله قبل
        </Link>
      }
    >
      <form className="auth-form" onSubmit={submit} noValidate>
        <OtpInput
          value={code}
          onChange={(value) => {
            setCode(value);
            setValidationError("");
          }}
          disabled={verify.isPending}
        />
        <AuthFeedback error={validationError || verify.error || resend.error} />
        <button
          className="auth-submit"
          type="submit"
          disabled={verify.isPending || resend.isPending}
        >
          <AuthSubmitLabel
            pending={verify.isPending}
            idle="تأیید کد"
            pendingLabel="در حال بررسی…"
          />
        </button>
      </form>
      <div className="auth-resend" aria-live="polite">
        {seconds > 0 ? (
          <span>ارسال دوباره تا {seconds} ثانیه دیگر</span>
        ) : (
          <button type="button" onClick={() => resend.mutate()} disabled={resend.isPending}>
            <AuthSubmitLabel
              pending={resend.isPending}
              idle="ارسال دوباره کد"
              pendingLabel="در حال ارسال…"
            />
          </button>
        )}
      </div>
    </AuthShell>
  );
}
