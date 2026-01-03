import hashlib
import hmac
from fastapi import Request, HTTPException, status
from config import config

async def verify_github_signature(request: Request):
    # Skip verification if no secret is set (for testing)
    if not config.WEBHOOK_SECRET:
        return

    signature_header = request.headers.get("X-Hub-Signature-256")
    if not signature_header:
        raise HTTPException(status_code=403, detail="Missing signature header")

    # Read the raw body (we need the exact bytes GitHub sent)
    payload_body = await request.body()
    
    # Calculate HMAC
    hash_object = hmac.new(
        config.WEBHOOK_SECRET.encode("utf-8"),
        msg=payload_body,
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()

    if not hmac.compare_digest(expected_signature, signature_header):
        raise HTTPException(status_code=403, detail="Invalid signature")