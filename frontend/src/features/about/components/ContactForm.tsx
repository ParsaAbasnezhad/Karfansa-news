import { useState, type FormEvent } from "react";

import { Icon } from "@/components/ui/Icon";
import { contactErrorMessage } from "@/features/about/api/contact";
import { useContactMutation } from "@/features/about/hooks/use-contact";
import {
  CONTACT_SUBJECTS,
  type ContactErrors,
  type ContactField,
  type ContactPayload,
  type ContactSubject,
} from "@/features/about/types/contact";

const initialValues: ContactPayload = {
  name: "",
  phone: "",
  email: "",
  subject: "",
  message: "",
  website: "",
};

function normalizeMobile(value: string): string {
  const latinDigits = value.replace(/[۰-۹٠-٩]/g, (digit) =>
    String.fromCharCode(digit.charCodeAt(0) - (digit >= "۰" ? 1728 : 1584)),
  );
  const compact = latinDigits.replace(/[\s()-]/g, "");
  if (/^09\d{9}$/.test(compact)) return `+98${compact.slice(1)}`;
  if (/^0098\d{10}$/.test(compact)) return `+${compact.slice(2)}`;
  return compact;
}

function validate(values: ContactPayload): ContactErrors {
  const errors: ContactErrors = {};
  const name = values.name.trim();
  const email = values.email.trim();
  const message = values.message.trim();
  const phone = normalizeMobile(values.phone);

  if (name.length < 2 || name.length > 120) {
    errors.name = "نام و نام خانوادگی باید بین ۲ تا ۱۲۰ نویسه باشد.";
  }
  if (!/^\+?[1-9]\d{7,14}$/.test(phone)) {
    errors.phone = "شماره موبایل معتبر وارد کنید.";
  }
  if (email.length > 254 || !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) {
    errors.email = "نشانی ایمیل معتبر وارد کنید.";
  }
  if (!CONTACT_SUBJECTS.includes(values.subject as ContactSubject)) {
    errors.subject = "یک موضوع از فهرست انتخاب کنید.";
  }
  if (message.length < 10 || message.length > 3000) {
    errors.message = "متن پیام باید بین ۱۰ تا ۳۰۰۰ نویسه باشد.";
  }
  return errors;
}

export function ContactForm() {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState<ContactErrors>({});
  const mutation = useContactMutation();

  const updateField = (field: ContactField, value: string) => {
    setValues((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
    mutation.reset();
  };

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (mutation.isPending) return;
    const fieldErrors = validate(values);
    setErrors(fieldErrors);
    const firstInvalid = (Object.keys(initialValues) as ContactField[]).find(
      (field) => fieldErrors[field],
    );
    if (firstInvalid) {
      document.getElementById(`contact-${firstInvalid}`)?.focus();
      return;
    }
    const subject = values.subject;
    if (!subject) return;
    mutation.mutate({
      ...values,
      name: values.name.trim(),
      phone: normalizeMobile(values.phone),
      email: values.email.trim(),
      subject,
      message: values.message.trim(),
      website: values.website,
    });
  };

  return (
    <form onSubmit={submit} noValidate>
      <div className="contact-form-grid">
        <Field
          label="نام و نام خانوادگی"
          name="name"
          icon="user"
          value={values.name}
          error={errors.name}
          autoComplete="name"
          maxLength={120}
          onChange={(value) => updateField("name", value)}
        />
        <Field
          label="شماره موبایل"
          name="phone"
          icon="phone"
          value={values.phone}
          error={errors.phone}
          type="tel"
          autoComplete="tel"
          inputMode="tel"
          maxLength={24}
          onChange={(value) => updateField("phone", value)}
        />
        <Field
          label="ایمیل"
          name="email"
          icon="mail"
          value={values.email}
          error={errors.email}
          type="email"
          autoComplete="email"
          maxLength={254}
          onChange={(value) => updateField("email", value)}
        />
        <label className="contact-field">
          <span className="contact-field-label">
            موضوع پیام <i aria-hidden="true">*</i>
          </span>
          <span className="contact-input-wrap">
            <Icon name="file" />
            <select
              id="contact-subject"
              name="subject"
              value={values.subject}
              onChange={(event) => updateField("subject", event.target.value)}
              aria-invalid={Boolean(errors.subject)}
              aria-describedby={errors.subject ? "contact-subject-error" : undefined}
              required
            >
              <option value="" disabled>
                یک موضوع انتخاب کنید
              </option>
              {CONTACT_SUBJECTS.map((topic) => (
                <option key={topic} value={topic}>
                  {topic}
                </option>
              ))}
            </select>
          </span>
          {errors.subject ? (
            <span className="contact-field-error" id="contact-subject-error">
              {errors.subject}
            </span>
          ) : null}
        </label>
        <label className="contact-field contact-form-wide">
          <span className="contact-field-label">
            متن پیام <i aria-hidden="true">*</i>
          </span>
          <textarea
            id="contact-message"
            name="message"
            rows={6}
            minLength={10}
            maxLength={3000}
            value={values.message}
            onChange={(event) => updateField("message", event.target.value)}
            aria-invalid={Boolean(errors.message)}
            aria-describedby={errors.message ? "contact-message-error" : undefined}
            required
          />
          <span className="contact-message-meta">
            <span>جزئیات پیام به بررسی دقیق‌تر کمک می‌کند.</span>
            <span>{values.message.length}/۳۰۰۰</span>
          </span>
          {errors.message ? (
            <span className="contact-field-error" id="contact-message-error">
              {errors.message}
            </span>
          ) : null}
        </label>
        <label className="contact-honeypot" aria-hidden="true">
          وب‌سایت
          <input
            name="website"
            value={values.website}
            tabIndex={-1}
            autoComplete="off"
            onChange={(event) =>
              setValues((current) => ({ ...current, website: event.target.value }))
            }
          />
        </label>
      </div>
      {mutation.isError ? (
        <p className="contact-error" role="alert">
          {contactErrorMessage(mutation.error)}
        </p>
      ) : null}
      {mutation.isSuccess ? (
        <p className="contact-success" role="status">
          {mutation.data.message}
        </p>
      ) : null}
      <button type="submit" className="contact-submit" disabled={mutation.isPending}>
        {mutation.isPending ? "در حال ارسال…" : "ارسال پیام"}
        {mutation.isPending ? null : <Icon name="arrow" />}
      </button>
      <p className="contact-privacy-note">
        پیام فقط برای بررسی تحریریه ذخیره می‌شود و در همین سرویس می‌ماند.
      </p>
    </form>
  );
}

interface FieldProps {
  label: string;
  name: "name" | "phone" | "email";
  icon: "user" | "phone" | "mail";
  value: string;
  error?: string | undefined;
  type?: "text" | "tel" | "email";
  autoComplete: string;
  inputMode?: "tel";
  maxLength: number;
  onChange: (value: string) => void;
}

function Field({
  label,
  name,
  icon,
  value,
  error,
  type = "text",
  autoComplete,
  inputMode,
  maxLength,
  onChange,
}: FieldProps) {
  const id = `contact-${name}`;
  const errorId = `${id}-error`;
  return (
    <label className="contact-field" htmlFor={id}>
      <span className="contact-field-label">
        {label} <i aria-hidden="true">*</i>
      </span>
      <span className="contact-input-wrap">
        <Icon name={icon} />
        <input
          id={id}
          name={name}
          type={type}
          autoComplete={autoComplete}
          inputMode={inputMode}
          maxLength={maxLength}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? errorId : undefined}
          required
        />
      </span>
      {error ? (
        <span className="contact-field-error" id={errorId}>
          {error}
        </span>
      ) : null}
    </label>
  );
}
