"""A container-ready microservice with background webhook delivery."""

import hmac
import json
from uuid import UUID

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, Request, Response

from rate_limit import limiter
from schemas import DeliveryRead, JobRead, WebhookInput
from worker import (
    create_job,
    deliveries,
    dispatch_webhook,
    jobs,
    public_job,
    sign_body,
    state_lock,
    utc_now,
)

app = FastAPI(
    title="Background Webhook Microservice",
    description="Asynchronous webhook jobs, rate limiting, and a Docker deployment.",
    version="1.0.0",
)


@app.get("/", tags=["Information"])
async def home():
    return {"message": "Background Webhook Microservice", "docs": "/docs"}


@app.get("/health", tags=["Information"])
async def health():
    return {"status": "ok"}


@app.post(
    "/webhooks",
    response_model=JobRead,
    status_code=202,
    dependencies=[Depends(limiter)],
    tags=["Jobs"],
)
async def submit_webhook(
    payload: WebhookInput, background_tasks: BackgroundTasks, response: Response
):
    job = create_job(payload.model_dump())
    background_tasks.add_task(dispatch_webhook, job["id"])
    response.headers["Location"] = f"/jobs/{job['id']}"
    return job


@app.get("/jobs", response_model=list[JobRead], tags=["Jobs"])
async def list_jobs(limit: int = Query(default=20, ge=1, le=100)):
    with state_lock:
        recent = list(reversed(list(jobs.values())))[:limit]
        return [public_job(job) for job in recent]


@app.get("/jobs/{job_id}", response_model=JobRead, tags=["Jobs"])
async def get_job(job_id: UUID):
    with state_lock:
        job = jobs.get(str(job_id))
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return public_job(job)


@app.post("/demo/webhook", tags=["Local demo receiver"])
async def receive_demo_webhook(request: Request):
    # A bounded local receiver verifies the signature and records real HTTP deliveries.
    chunks = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > 65536:
            raise HTTPException(status_code=413, detail="Webhook body is too large")
        chunks.append(chunk)
    body = b"".join(chunks)

    signature = request.headers.get("X-Webhook-Signature", "")
    if not signature.isascii() or not hmac.compare_digest(signature, sign_body(body)):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = json.loads(body)
        job_id = str(UUID(payload["job_id"]))
        validated = WebhookInput(event=payload["event"], message=payload["message"])
    except (ValueError, KeyError, TypeError):
        raise HTTPException(status_code=422, detail="Invalid webhook payload") from None

    with state_lock:
        if any(item["job_id"] == job_id for item in deliveries):
            return {"received": True, "duplicate": True}
        deliveries.append({
            "job_id": job_id,
            **validated.model_dump(),
            "received_at": utc_now(),
        })
    return {"received": True, "duplicate": False}


@app.get("/demo/deliveries", response_model=list[DeliveryRead], tags=["Local demo receiver"])
async def list_deliveries():
    with state_lock:
        return list(reversed(deliveries))
