# Security & Authentication

AutoRubric implements a real JWT-based authentication system backed by PostgreSQL.

## Environment Variables
The following environment variables control authentication:
- `JWT_SECRET`: Secret key used to sign JWT tokens. **Must** be changed in production.
- `JWT_ALGORITHM`: The algorithm used to sign JWTs (default: `HS256`).
- `ACCESS_TOKEN_EXPIRE_MINUTES`: The expiration time for JWTs (default: 30 minutes).
- `REGISTRATION_CODE`: An optional invite code required to register new accounts. If left empty, registration is open.
- `APP_ENV`: If set to `prod`, the application will refuse to start if `JWT_SECRET` is left as `supersecret`.

## Admin Bootstrapping
There are no longer hardcoded default accounts in the codebase. To create an initial admin account, use the provided script:
```bash
python backend/scripts/create_admin.py
```
You can set `ADMIN_EMAIL` and `ADMIN_PASSWORD` in your environment to skip the interactive prompts.

## Known Limitations
This is a basic implementation of authentication. It has the following known limitations:
- **No Email Verification**: Users are not required to verify their email address upon registration.
- **No Token Revocation**: JWTs cannot be revoked before their expiration time. If a user logs out, the token is simply removed from the client side.
- **Shared Data Access (No Per-User Ownership)**: All users currently share data (rubrics, submissions, jobs) regardless of ownership. A5 features for per-user visibility have not been fully enabled or enforced.
