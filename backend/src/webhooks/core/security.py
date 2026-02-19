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

import re

class SecretScanner:
    """
    Scans text for sensitive information (API keys, passwords) and redacts them.
    Acting as a firewall involved before sending data to LLM.
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
            (r":([^:@\s]+)@([a-zA-Z0-9.-]+)", ":[REDACTED_PASSWORD]@\\2")
        ]

    def redact(self, text: str) -> str:
        """
        Redacts secrets from the input text.
        """
        if not text:
            return ""
            
        redacted_text = text
        for pattern, replacement in self.patterns:
            redacted_text = re.sub(pattern, replacement, redacted_text)
            
        return redacted_text
