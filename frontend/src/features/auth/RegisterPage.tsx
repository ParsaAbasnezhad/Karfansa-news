import { useMutation } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";

import { authApi } from "@/features/auth/api";
import {
  AuthFeedback,
  AuthField,
  AuthShell,
  AuthSubmitLabel,
  PasswordField,
} from "@/features/auth/components";
import {
  normalizeIdentifier,
  validEmail,
  validMobile,
  validatePasswordPair,
} from "@/features/auth/validation";
import { usePageMeta } from "@/hooks/use-page-meta";

export function RegisterPage() {
  usePageMeta("ثبت‌نام | کارفنسا");
  const navigate = useNavigate();
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [mobile, setMobile] = useState("");
  const [method, setMethod] = useState<"email" | "sms">("email");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [validationError, setValidationError] = useState("");
  const register = useMutation({
    mutationFn: () =>
      authApi.register({
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        ...(email.trim() && { email: normalizeIdentifier(email) }),
        ...(mobile.trim() && { mobile: normalizeIdentifier(mobile) }),
        password,
        password_confirmation: confirmation,
        verification_method: method,
      }),
    onSuccess: ({ challenge_id }) => {
      void navigate(
        `/verify?${new URLSearchParams({ purpose: "registration", challenge: challenge_id }).toString()}`,
      );
    },
  });

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (register.isPending) return;
    let message: string;
    if (!firstName.trim() || !lastName.trim()) message = "نام و نام خانوادگی الزامی است.";
    else if (!email.trim() && !mobile.trim()) message = "ایمیل یا شماره موبایل را وارد کنید.";
    else if (email.trim() && !validEmail(normalizeIdentifier(email)))
      message = "ایمیل معتبر وارد کنید.";
    else if (mobile.trim() && !validMobile(mobile))
      message = "شماره موبایل ایرانی معتبر وارد کنید.";
    else if (method === "email" && !email.trim())
      message = "برای تأیید ایمیلی، نشانی ایمیل را وارد کنید.";
    else if (method === "sms" && !mobile.trim())
      message = "برای تأیید پیامکی، شماره موبایل را وارد کنید.";
    else message = validatePasswordPair(password, confirmation) ?? "";
    setValidationError(message);
    if (!message) register.mutate();
  };

  return (
    <AuthShell
      title="ایجاد حساب کاربری"
      description="اطلاعات خود را وارد کنید و راه تأیید حساب را انتخاب کنید."
      footer={
        <span>
          حساب دارید؟ <Link to="/login">وارد شوید</Link>
        </span>
      }
    >
      <form className="auth-form" onSubmit={submit} noValidate>
        <div className="auth-grid">
          <AuthField
            label="نام"
            name="first_name"
            autoComplete="given-name"
            value={firstName}
            onChange={(event) => setFirstName(event.target.value)}
            maxLength={150}
            required
          />
          <AuthField
            label="نام خانوادگی"
            name="last_name"
            autoComplete="family-name"
            value={lastName}
            onChange={(event) => setLastName(event.target.value)}
            maxLength={150}
            required
          />
        </div>
        <AuthField
          label="ایمیل"
          name="email"
          type="email"
          autoComplete="email"
          dir="ltr"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          maxLength={254}
          hint="ایمیل یا موبایل الزامی است؛ می‌توانید هر دو را وارد کنید."
        />
        <AuthField
          label="شماره موبایل ایرانی"
          name="mobile"
          type="tel"
          inputMode="tel"
          autoComplete="tel"
          dir="ltr"
          value={mobile}
          onChange={(event) => setMobile(event.target.value)}
          placeholder="۰۹۱۲…"
          maxLength={24}
        />
        <fieldset className="auth-choice">
          <legend>روش تأیید حساب</legend>
          <label>
            <input
              type="radio"
              name="verification_method"
              value="email"
              checked={method === "email"}
              onChange={() => setMethod("email")}
            />{" "}
            ایمیل
          </label>
          <label>
            <input
              type="radio"
              name="verification_method"
              value="sms"
              checked={method === "sms"}
              onChange={() => setMethod("sms")}
            />{" "}
            پیامک
          </label>
        </fieldset>
        <PasswordField
          label="رمز عبور"
          name="password"
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
        <p className="auth-hint">رمز عبور باید معیارهای امنیتی سامانه را داشته باشد.</p>
        <AuthFeedback error={validationError || register.error} />
        <button className="auth-submit" type="submit" disabled={register.isPending}>
          <AuthSubmitLabel
            pending={register.isPending}
            idle="ثبت‌نام و دریافت کد"
            pendingLabel="در حال ثبت…"
          />
        </button>
      </form>
    </AuthShell>
  );
}
