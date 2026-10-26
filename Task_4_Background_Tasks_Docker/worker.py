"""Asynchronous webhook dispatch with bounded history and retry handling."""

import asyncio
import hashlib
import hmac
import json
import os
import secrets
from collections import deque
from datetime import datetime, timezone
from threading import RLock
from urllib.parse import urlsplit
from uuid import uuid4

import httpx
from fastapi import HTTPException

APP_PORT = int(os.getenv("APP_PORT", "8004"))
WEBHOOK_URL = os.getenv(
    "WEBHOOK_URL", f"http://127.0.0.1:{APP_PORT}/demo/webhook"
)
SIGNING_SECRET = os.getenv("WEBHOOK_SIGNING_SECRET") or secrets.token_hex(32)

parsed_url = urlsplit(WEBHOOK_URL)
if (
    parsed_url.scheme not in {"http", "https"}
    or not parsed_url.hostname
    or parsed_url.username
    or parsed_url.password
    or parsed_url.fragment
):
    raise ValueError("WEBHOOK_URL must be an HTTP(S) URL without credentials or a fragment")

jobs = {}
deliveries = deque(maxlen=100)
state_lock = RLock()
MAX_JOBS = 500
MAX_ATTEMPTS = 3


def utc_now():
    return datetime.now(timezone.utc)


def sign_body(body):
    digest = hmac.new(SIGNING_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def public_job(job):
    return {key: value for key, value in job.items() if key != "payload"}


def create_job(payload):
    now = utc_now()
    with state_lock:
        if len(jobs) >= MAX_JOBS:
            removable = next(
                (key for key, job in jobs.items() if job["status"] in {"succeeded", "failed"}),
                None,
            )
            if removable is None:
                raise HTTPException(status_code=503, detail="Job queue is full")
            del jobs[removable]

        job_id = str(uuid4())
        jobs[job_id] = {
            "id": job_id,
            "status": "queued",
            "attempts": 0,
            "created_at": now,
            "updated_at": now,
            "response_status": None,
            "error": None,
            "payload": payload,
        }
        return public_job(jobs[job_id])


def update_job(job_id, **changes):
    with state_lock:
        jobs[job_id].update(changes, updated_at=utc_now())


async def dispatch_webhook(job_id):
    with state_lock:
        job = jobs[job_id]
        payload = {
            "job_id": job_id,
            **job["payload"],
            "created_at": job["created_at"].isoformat(),
        }

    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": sign_body(body),
        "Idempotency-Key": job_id,
    }

    try:
        async with httpx.AsyncClient(
            timeout=5.0, follow_redirects=False, trust_env=False
        ) as client:
            for attempt in range(1, MAX_ATTEMPTS + 1):
                update_job(job_id, status="processing", attempts=attempt)
                try:
                    response = await client.post(WEBHOOK_URL, content=body, headers=headers)
                    update_job(job_id, response_status=response.status_code)
                    response.raise_for_status()
                except httpx.HTTPStatusError as exc:
                    code = exc.response.status_code
                    error = f"Webhook returned HTTP {code}"
                    retryable = code == 429 or code >= 500
                except httpx.RequestError:
                    error = "Webhook could not be reached or timed out"
                    retryable = True
                else:
                    update_job(job_id, status="succeeded", error=None)
                    return

                if not retryable or attempt == MAX_ATTEMPTS:
                    update_job(job_id, status="failed", error=error)
                    return

                await asyncio.sleep(attempt)
    except Exception:
        # Background exceptions are recorded instead of leaving a job processing forever.
        update_job(job_id, status="failed", error="Unexpected webhook dispatch failure")
