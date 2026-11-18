# Authentication notification delivery

Public registration, passwordless login, recovery, and resend requests queue a
challenge UUID. The Celery worker creates the OTP, submits it through
`apps.users.notifications.send_otp`, and stores its one-way verifier only after
the provider confirms acceptance. Public API responses acknowledge the request,
not successful delivery. OTP values are never placed in Celery messages.
Authenticated password-change and contact-verification code requests dispatch
synchronously and succeed only after the provider confirms acceptance. OTP
dispatch tasks do not retry after an uncertain provider response; users may
request a fresh challenge after an unsuccessful attempt.
The password-change notice is a Celery task carrying only a user ID; when the broker
is unavailable, it attempts direct delivery. It uses a verified email address when
present and otherwise a verified mobile number through the SMS adapter. Celery
publishing has retries disabled for this notice, with short Redis socket timeouts.

## Email

The application uses Django's configured email backend. Local development defaults
to the console backend. Production should configure `DJANGO_EMAIL_BACKEND` as
`django.core.mail.backends.smtp.EmailBackend`, a real
`DJANGO_DEFAULT_FROM_EMAIL`, and the `DJANGO_EMAIL_HOST`, `DJANGO_EMAIL_PORT`,
`DJANGO_EMAIL_HOST_USER`, `DJANGO_EMAIL_HOST_PASSWORD`,
`DJANGO_EMAIL_USE_TLS` or `DJANGO_EMAIL_USE_SSL` values required by the mail
service. The OTP email contains Persian right-to-left HTML and text alternatives.
The sender must verify SPF/DKIM/DMARC for production deliverability.

## SMS

`SMS_PROVIDER_CLASS` may name a dotted Python class implementing
`send_sms(*, destination: str, message: str) -> bool`. Adapters may also expose
`send_verification_code(*, destination, code, purpose) -> bool` for template OTP
APIs. The adapter must return `True` only after its provider confirms acceptance;
`False` or an exception rejects the OTP delivery. Provider credentials should
be read from secret environment variables inside that adapter.

### Kavenegar (VerifyLookup)

A ready adapter is shipped at
`apps.users.providers.kavenegar.KavenegarSmsProvider`. It follows the official
Kavenegar VerifyLookup API:

`POST https://api.kavenegar.com/v1/{API-KEY}/verify/lookup.json`

with `receptor`, `token` (the six-digit OTP), `template`, and `type=sms`.
Free-form password-change notices use `sms/send.json`. Enable it only after an
OTP template containing `%token` is approved in the Kavenegar panel:

```
SMS_PROVIDER_CLASS=apps.users.providers.kavenegar.KavenegarSmsProvider
KAVENEGAR_API_KEY=...
KAVENEGAR_VERIFY_TEMPLATE=your_approved_template
KAVENEGAR_SENDER=   # optional line number for free-form notices
```

Without a configured provider class, production SMS delivery fails closed.
Do not claim real SMS delivery works until credentials and a successful
provider response are verified in the deployment environment.

For local development only, `SMS_DEV_INBOX` may be set to a developer email
address. With `DEBUG=True` and no provider class, an SMS preview is sent to
that inbox via Django email. The preview does not send a real text message.
The preview adapter is disabled in production regardless of the inbox value.

Email and SMS submission acceptance does not guarantee eventual delivery to
the recipient. A provider failure invalidates its challenge. Queued public
requests retain generic responses to avoid exposing account eligibility.
