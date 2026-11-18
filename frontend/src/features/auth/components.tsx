import {
  useRef,
  useState,
  type ClipboardEvent,
  type InputHTMLAttributes,
  type KeyboardEvent,
  type ReactNode,
} from "react";
import { Link } from "react-router";

import { Icon } from "@/components/ui/Icon";
import { latinDigits } from "@/features/auth/validation";
import { getErrorMessage } from "@/lib/errors";

export function AuthShell({
  title,
  description,
  children,
  footer,
}: {
  title: string;
  description: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <section className="auth-page wrap" dir="rtl">
      <div className="auth-card">
        <div className="auth-heading">
          <span className="auth-eyebrow">حساب کاربری کارفنسا</span>
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
        {children}
        {footer ? <div className="auth-footer">{footer}</div> : null}
      </div>
      <aside className="auth-aside" aria-label="درباره حساب کاربری">
        <span className="auth-aside-mark" aria-hidden="true">
          ک
        </span>
        <h2>همراه خبر، با خیال آسوده</h2>
        <p>حساب کاربری شما با تأیید راه ارتباطی و ورود امن محافظت می‌شود.</p>
        <ul className="auth-aside-list">
          <li>ورود با رمز یا کد یک‌بارمصرف</li>
          <li>تأیید ایمیل یا موبایل</li>
          <li>بازیابی امن رمز عبور</li>
        </ul>
        <Link to="/">بازگشت به صفحه اصلی</Link>
      </aside>
    </section>
  );
}

export function AuthField({
  label,
  error,
  hint,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { label: string; error?: string; hint?: string }) {
  const id = props.id ?? props.name ?? label;
  return (
    <label className="auth-field" htmlFor={id}>
      <span className="auth-label">{label}</span>
      <input
        {...props}
        id={id}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined}
      />
      {error ? (
        <span className="auth-field-error" id={`${id}-error`}>
          {error}
        </span>
      ) : null}
      {!error && hint ? (
        <span className="auth-hint" id={`${id}-hint`}>
          {hint}
        </span>
      ) : null}
    </label>
  );
}

export function PasswordField({
  label,
  ...props
}: Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & { label: string }) {
  const [visible, setVisible] = useState(false);
  const id = props.id ?? props.name ?? label;
  return (
    <div className="auth-password-row">
      <AuthField {...props} id={id} label={label} type={visible ? "text" : "password"} />
      <button
        type="button"
        className="auth-visibility"
        aria-label={visible ? `پنهان کردن ${label}` : `نمایش ${label}`}
        aria-pressed={visible}
        onClick={() => setVisible((current) => !current)}
      >
        <Icon name={visible ? "eye-off" : "eye"} />
        <span>{visible ? "پنهان" : "نمایش"}</span>
      </button>
    </div>
  );
}

export function OtpInput({
  value,
  onChange,
  disabled = false,
}: {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}) {
  const refs = useRef<Array<HTMLInputElement | null>>([]);
  const digits = value.padEnd(6, " ").slice(0, 6).split("");

  const assign = (index: number, input: string) => {
    const next = digits.map((digit) => digit.trim());
    const parsed = latinDigits(input).replace(/\D/g, "");
    if (!parsed) return;
    for (let offset = 0; offset < parsed.length && index + offset < 6; offset += 1) {
      next[index + offset] = parsed[offset] ?? "";
    }
    onChange(next.join(""));
    refs.current[Math.min(index + parsed.length, 5)]?.focus();
  };

  const paste = (event: ClipboardEvent<HTMLInputElement>, index: number) => {
    event.preventDefault();
    assign(index, event.clipboardData.getData("text"));
  };

  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>, index: number) => {
    if (event.key === "Backspace") {
      const next = digits.map((item) => item.trim());
      if (next[index]) next[index] = "";
      else if (index > 0) {
        next[index - 1] = "";
        refs.current[index - 1]?.focus();
      }
      onChange(next.join(""));
      event.preventDefault();
      return;
    }
    if (event.key === "ArrowLeft" && index > 0) {
      refs.current[index - 1]?.focus();
      event.preventDefault();
      return;
    }
    if (event.key === "ArrowRight" && index < 5) {
      refs.current[index + 1]?.focus();
      event.preventDefault();
      return;
    }
    if (event.key === "Home") {
      refs.current[0]?.focus();
      event.preventDefault();
      return;
    }
    if (event.key === "End") {
      refs.current[5]?.focus();
      event.preventDefault();
    }
  };

  return (
    <div className="auth-otp-field">
      <span className="auth-label" id="auth-otp-label">
        کد شش‌رقمی
      </span>
      <div
        className="auth-otp"
        dir="ltr"
        role="group"
        aria-labelledby="auth-otp-label"
      >
        {digits.map((digit, index) => (
          <input
            key={index}
            ref={(element) => {
              refs.current[index] = element;
            }}
            className={digit.trim() ? "is-filled" : undefined}
            type="text"
            inputMode="numeric"
            pattern="[0-9]*"
            autoComplete={index === 0 ? "one-time-code" : "off"}
            enterKeyHint={index === 5 ? "done" : "next"}
            aria-label={`رقم ${index + 1} از ۶`}
            maxLength={6}
            value={digit.trim()}
            disabled={disabled}
            onChange={(event) => assign(index, event.target.value)}
            onPaste={(event) => paste(event, index)}
            onFocus={(event) => event.currentTarget.select()}
            onKeyDown={(event) => onKeyDown(event, index)}
          />
        ))}
      </div>
    </div>
  );
}

export function AuthFeedback({ error, message }: { error?: unknown; message?: string }) {
  if (error) {
    const text = typeof error === "string" ? error : getErrorMessage(error);
    return (
      <p className="auth-feedback auth-error" role="alert">
        {text}
      </p>
    );
  }
  if (message)
    return (
      <p className="auth-feedback auth-success" role="status">
        {message}
      </p>
    );
  return null;
}

export function AuthSubmitLabel({
  pending,
  idle,
  pendingLabel = "لطفاً صبر کنید…",
}: {
  pending: boolean;
  idle: string;
  pendingLabel?: string;
}) {
  if (!pending) return <>{idle}</>;
  return (
    <>
      <span className="auth-spinner" aria-hidden="true" />
      {pendingLabel}
    </>
  );
}
