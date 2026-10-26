# Task 2: User Authentication and RBAC with JWT

A FastAPI backend for user registration, password hashing, JWT login,
protected profiles, and role-based access control (RBAC).
The API can be used through Swagger UI; no frontend is required.

## Features

- Registration with Pydantic validation and duplicate-username protection.
- Password hashing and verification using Passlib and bcrypt.
- Signed HS256 JWT access tokens with a 30-minute lifetime.
- OAuth2PasswordBearer and Depends(get_current_user) for protected routes.
- Separate user and admin permissions.
- An admin account created from private local configuration at startup.
- Public response models that exclude passwords and password hashes.
- Validation errors that do not echo submitted passwords.
- Auto-generated OpenAPI, Swagger UI, and ReDoc documentation.

## Requirements

Python 3.10 or newer, pip, and Terminal.

## Files

| File | Purpose |
|---|---|
| main.py | API, schemas, password helpers, JWT helpers, and access control |
| requirements.txt | Python dependencies |
| setup_env.py | Generate missing local secrets and admin credentials |
| .env.example | Environment-variable names without secrets |
| .gitignore | Exclude local secrets and generated files |
| README.md | Setup, operation, and project documentation |

## Setup on macOS

Run inside the project folder:

```bash
cd ~/Desktop/Task_2_User_Authentication
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python setup_env.py
python -m uvicorn main:app --reload
```

The setup script fills missing settings in .env and preserves existing values.
It generates a random signing secret and a random admin password.
Open .env in your editor to view ADMIN_USERNAME and ADMIN_PASSWORD.
Existing process environment variables take precedence over .env values.

Open [Swagger UI](http://127.0.0.1:8000/docs).
[ReDoc](http://127.0.0.1:8000/redoc) and
[OpenAPI JSON](http://127.0.0.1:8000/openapi.json) are also available.
Stop the server with Control + C.

## Endpoints

| Method | Path | Access | Successful response |
|---|---|---|---|
| GET | / | Public | 200: API information |
| POST | /register | Public | 201: username and assigned user role |
| POST | /login | Public, valid credentials required | 200: access token |
| GET | /users/me | Valid bearer token | 200: current user's profile |
| GET | /admin/users | Valid admin token | 200: public user details |

## Register an account

Use POST /register in Swagger with this example JSON:

```json
{
  "username": "arijit",
  "password": "Hello123!"
}
```

Usernames are case-sensitive, contain 3-30 characters, and allow only
letters, numbers, and underscores. Passwords require at least 8 characters,
must not exceed 72 UTF-8 bytes, and cannot contain a null character.
The example password is for demonstration; choose your own password.
New accounts always receive the user role. Extra fields, including role,
are rejected. The original password is not added to the user record.

## Log in and use protected routes

POST /login accepts form fields username and password, rather than JSON.
It returns access_token, token_type, and expires_in (1800 seconds).

For Swagger, click Authorize, enter your username and password,
then click Authorize and Close. Swagger obtains a token from /login and
adds it to protected requests. Leave client_id and client_secret blank.

Use GET /users/me to view your public profile. For other API clients,
send the token in this header:

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

## Admin access

The admin account is created at startup from ADMIN_USERNAME and
ADMIN_PASSWORD in your local configuration. There are no shared default
admin credentials and no public endpoint that grants the admin role.

To use GET /admin/users in Swagger, log out in Authorize and authorize again
using the admin credentials from .env. A regular user receives 403 on this
route. Permission checks use the stored user's role.

## Error responses

| Status | Meaning |
|---|---|
| 401 | Missing, invalid, or expired token; incorrect login; or unknown token subject |
| 403 | Authenticated user does not have the required admin role |
| 409 | Username already exists |
| 422 | Invalid or missing input, invalid password length, or unexpected registration fields |

## Architecture and scope

Registration validates input, hashes the password, and stores a user record.
Login verifies the saved hash and issues a signed token.
get_current_user verifies the token's signature and required claims,
including expiry, then finds the stored user. require_admin additionally
checks the user's stored role. Response models expose public fields only.

This is a local internship demonstration with an in-memory user list.
Regular accounts disappear when the server restarts or reloads; the admin
is recreated from local configuration. Run one application process because
multiple workers do not share the user list. It is not a production deployment.

## Dependency compatibility

Passlib 1.7.4 and bcrypt 4.3.0 are pinned together because bcrypt 5 causes
a known Passlib compatibility failure. Passlib may log a nonfatal
"(trapped) error reading bcrypt version" warning with bcrypt 4.3.0.
This known warning does not by itself mean hashing failed.

## GitHub submission

Keep this folder as Task_2_User_Authentication beside Task_1_BookStore
in the Datheon_FastAPI_Internship repository. Include the six source and
documentation files listed above. Never upload .env or .venv.
The .env file contains the JWT signing secret and bootstrap admin credentials.

## References

- [FastAPI security documentation](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
- [Passlib CryptContext tutorial](https://passlib.readthedocs.io/en/stable/narr/context-tutorial.html)
- [Passlib/bcrypt compatibility report](https://github.com/pyca/bcrypt/issues/1079)