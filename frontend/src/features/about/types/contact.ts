export const CONTACT_SUBJECTS = [
  "پیشنهاد سوژه",
  "اصلاح خبر",
  "همکاری رسانه‌ای",
  "تبلیغات",
  "پشتیبانی فنی",
  "سایر موارد",
] as const;

export type ContactSubject = (typeof CONTACT_SUBJECTS)[number];

export interface ContactPayload {
  name: string;
  phone: string;
  email: string;
  subject: ContactSubject | "";
  message: string;
  website: string;
}

export interface ContactResponse {
  message: string;
}

export type ContactField = keyof Omit<ContactPayload, "website">;
export type ContactErrors = {
  [Key in ContactField]?: string | undefined;
};
