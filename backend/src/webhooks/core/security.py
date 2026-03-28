import hashlib
import hmac
import os
import logging
from fastapi import Request, HTTPException, status
from config import config

logger = logging.getLogger("agenticpr.security")

# ─── Production mode detection ──────────────────────────────────
PRODUCTION = os.getenv("PRODUCTION", "").lower() in ("true", "1", "yes")


async def verify_github_signature(request: Request):
    """Verify GitHub webhook signature. 
    In production: MANDATORY — rejects all unsigned requests.
    In development: Optional (warns if missing).
    """
    if not config.WEBHOOK_SECRET:
        if PRODUCTION:
            raise HTTPException(
                status_code=500, 
                detail="WEBHOOK_SECRET is required in production. Set it in environment."
            )
        logger.warning("⚠ WEBHOOK_SECRET not set — skipping signature verification (dev mode only)")
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


# ─── Secret Scanner (pre-LLM firewall) ─────────────────────────
import re

class SecretScanner:
    """
    Scans text for sensitive information (API keys, passwords) and redacts them.
    Acting as a firewall invoked before sending data to LLM.
    """
    def __init__(self):
        self.patterns = [
            # Generic API Key (sk-...)
            (r"(sk-[a-zA-Z0-9]{20,})", "[REDACTED_API_KEY]"),
            # AWS Access Key
            (r"(AKIA[0-9A-Z]{16})", "[REDACTED_AWS_KEY]"),
            # Private Key Header
            (r"-----BEGIN PRIVATE KEY-----", "[REDACTED_PRIVATE_KEY]"),
            # Password in URL (postgres://user:password@host) - simplified regex
            (r":([^:@\s]+)@([a-zA-Z0-9.-]+)", ":[REDACTED_PASSWORD]@\\2"),
            # GitHub tokens
            (r"(ghp_[a-zA-Z0-9]{36,})", "[REDACTED_GITHUB_TOKEN]"),
            (r"(gho_[a-zA-Z0-9]{36,})", "[REDACTED_GITHUB_TOKEN]"),
            # Generic bearer tokens
            (r"(Bearer\s+[a-zA-Z0-9._-]{20,})", "[REDACTED_BEARER]"),
        ]

    def redact(self, text: str) -> str:
        """Redacts secrets from the input text."""
        if not text:
            return ""
            
        redacted_text = text
        for pattern, replacement in self.patterns:
            redacted_text = re.sub(pattern, replacement, redacted_text)
            
        return redacted_text
