from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any

Verdict = Literal['OK','NEEDS_APPROVAL','REJECTED']

class ChatIn(BaseModel):
    message: str
    attachments: Optional[Dict[str, Any]] = None

class ChatOut(BaseModel):
    verdict: Verdict
    reason: str
    record: Optional[Dict[str, Any]] = None
