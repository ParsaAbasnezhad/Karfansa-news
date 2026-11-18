# Authentication architecture and rollout

## Existing system and compatibility

Karfansa News already uses `users.User`, a subclass of Django's `AbstractUser`.
Existing rows use a unique username and may have a non-unique, unverified email.
The project already configures Argon2 for new password hashes, retains PBKDF2
verification, and provides PostgreSQL, Redis, Celery, Django sessions, and a
versioned Django Ninja API. Before this work there were no public authentication
endpoints or frontend authentication pages in this repository.

The additive user migration preserves IDs, usernames, password hashes, admin
permissions, and existing sessions. Legacy email values need special care because
they have no verification evidence and are not unique. An existing account remains
usable through username/password or an unambiguous email/password path, but a
legacy email alone cannot authorize passwordless login or recovery. New signups
reserve only the selected verification contact. An unverified second contact is
claimed only after its own OTP succeeds, so one account cannot permanently reserve
another person's unverified address or phone number. Abandoned inactive signup
claims are released by the scheduled cleanup task.

## Implementation sequence

1. Extend the user table with optional normalized contacts and verification state;
   add a purpose-bound OTP challenge with a one-way verifier.
2. Add registration, login, verification, recovery, and password-change services
   behind the existing `/api/v1/` Ninja API and error envelope.
3. Deliver codes through Django email or a configured SMS adapter, with Redis
   throttling and PostgreSQL transactions for one-time verification.
4. Add Persian RTL forms using the existing API client, React Query, router, and
   design tokens. Keep authentication in HttpOnly Django session cookies.
5. Verify migrations, API and frontend tests, static checks, and deployment
   settings before rollout.

## API and browser flows

The router is mounted at `/api/v1/auth/`. It provides `csrf`, `register`,
`verify-registration`, `login`, `request-login-otp`, `verify-login-otp`,
`resend-otp`, `forgot-password`, `verify-reset-otp`, `reset-password`,
`request-change-password-otp`, `change-password`,
`request-contact-verification`, `verify-contact`, `logout`, and `me` operations.
Every operation uses a trailing slash. Errors retain the project's standard
`{"error": {"code", "message", "details?"}}` envelope.

The browser obtains a CSRF cookie first and sends `X-CSRFToken` on writes. Django
keeps the session ID in an HttpOnly cookie; no session or refresh token is stored
in localStorage. Production sets Secure and SameSite cookie attributes. The reset
authorization is single purpose, expires quickly, and is kept in browser memory
until the password form is submitted. Password updates invalidate other sessions
through Django's session authentication hash.

OTP values are generated with a cryptographically secure random generator,
verified against a keyed digest, expire after five minutes, and allow at most
five wrong attempts. Database row locks serialize consumption across workers;
Redis counters limit requests by action, IP, identifier, and account. Public
registration and recovery responses are generic to reduce account enumeration.

## Deployment notes

Serve the frontend and `/api/` on the same HTTPS origin through the existing
reverse proxy so session and CSRF cookies remain first party. Configure a real
SMTP backend and verified sender before enabling email registration. Configure an
SMS provider adapter from its official documentation before enabling production
mobile delivery. Start the existing PostgreSQL, Redis, backend, and Celery worker
services; apply the additive migration before serving the new frontend. Preserve
the named database and Redis volumes. See [auth-delivery.md](auth-delivery.md) for
notification settings.
