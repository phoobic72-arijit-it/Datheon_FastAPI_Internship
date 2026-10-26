"""User registration, JWT authentication, and role-based access control."""

import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import RLock
from typing import Literal

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict, Field, field_validator


# 1. Create the API application

app = FastAPI(
    title="User Authentication API",
    description="Registration, login, JWT authentication, and role-based access control.",
    version="1.0.0",
)


# 2. Load local configuration

load_dotenv(Path(__file__).resolve().parent / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

if len(SECRET_KEY) < 32:
    raise RuntimeError("Missing or short SECRET_KEY. Run: python setup_env.py")


# 3. Validate registration and define public responses

class UserRegister(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    username: str = Field(
        min_length=3,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_]+$",
    )
    password: str = Field(min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def validate_password(cls, password):
        if len(password.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes")

        if "\x00" in password:
            raise ValueError("Password must not contain null characters")

        return password


class UserPublic(BaseModel):
    username: str
    role: Literal["user", "admin"]


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60


# 4. Store users in memory and find a user

users = []
users_lock = RLock()


def find_user(username):
    with users_lock:
        for user in users:
            if user["username"] == username:
                return user.copy()

    return None


# 5. Configure password hashing

password_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__truncate_error=True,
)


# 6. Create and verify password hashes

def hash_password(password):
    hashed_password = password_context.hash(password)
    return hashed_password


def verify_password(password, hashed_password):
    if len(password.encode("utf-8")) > 72 or "\x00" in password:
        return False

    return password_context.verify(password, hashed_password)


# 7. Create the admin from local configuration

admin_password = os.getenv("ADMIN_PASSWORD", "")

if not admin_password:
    raise RuntimeError("Missing ADMIN_PASSWORD. Run: python setup_env.py")

admin_input = UserRegister(
    username=os.getenv("ADMIN_USERNAME", "admin"),
    password=admin_password,
)

users.append({
    "username": admin_input.username,
    "hashed_password": hash_password(admin_input.password),
    "role": "admin",
})

del admin_input, admin_password

# An unknown username still performs a password check.
dummy_password_hash = hash_password(secrets.token_urlsafe(24))


# 8. Create signed JWT access tokens

def create_access_token(user):
    now = datetime.now(timezone.utc)

    payload = {
        "sub": user["username"],
        "role": user["role"],
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# 9. Extract the bearer token and identify the current user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired access token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={
                "require_sub": True,
                "require_exp": True,
                "require_iat": True,
            },
        )
    except JWTError:
        raise credentials_error from None

    username = payload.get("sub")

    if not isinstance(username, str) or not username:
        raise credentials_error

    user = find_user(username)

    if user is None:
        raise credentials_error

    return user


# 10. Allow only admins to access admin routes

def require_admin(current_user: dict = Depends(get_current_user)):
    # Permissions come from the stored user.
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user


# 11. Keep passwords out of validation error responses

@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
):
    errors = [
        {
            "loc": error["loc"],
            "msg": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]

    return JSONResponse(
        status_code=422,
        content={"detail": errors},
    )


# 12. Public information endpoint

@app.get("/", tags=["Information"])
def home():
    return {
        "message": "User Authentication API",
        "docs": "/docs",
    }


# 13. Register a user

@app.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"],
)
def register_user(user_input: UserRegister):
    new_user = {
        "username": user_input.username,
        "hashed_password": hash_password(user_input.password),
        "role": "user",
    }

    with users_lock:
        if find_user(user_input.username) is not None:
            raise HTTPException(
                status_code=409,
                detail="Username already exists",
            )

        users.append(new_user)

    return new_user


# 14. Log in using form data and return a JWT

@app.post(
    "/login",
    response_model=TokenResponse,
    tags=["Authentication"],
)
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = find_user(form_data.username)

    stored_hash = (
        user["hashed_password"]
        if user
        else dummy_password_hash
    )

    password_is_valid = verify_password(
        form_data.password,
        stored_hash,
    )

    if user is None or not password_is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"

    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


# 15. Return the authenticated user's public profile

@app.get(
    "/users/me",
    response_model=UserPublic,
    tags=["Protected"],
)
def get_my_profile(
    current_user: dict = Depends(get_current_user),
):
    return current_user


# 16. Return public user details to admins only

@app.get(
    "/admin/users",
    response_model=list[UserPublic],
    tags=["Admin"],
)
def get_all_users(admin: dict = Depends(require_admin)):
    with users_lock:
        return [
            {
                "username": user["username"],
                "role": user["role"],
            }
            for user in users
        ]