from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Any
from datetime import datetime

# -------- Public DTOs --------
class DocOut(BaseModel):
    id: str = Field(alias="_id")
    filename: str
    created_at: datetime

class FolderOut(BaseModel):
    name: str
    count: int

class SearchOut(BaseModel):
    count: int
    results: List[DocOut]

class ActionScope(BaseModel):
    type: Literal["folder","files"]
    name: Optional[str] = None
    ids: Optional[List[str]] = None

class ActionRunIn(BaseModel):
    scope: ActionScope
    messages: List[dict]
    actions: List[Literal["make_document","make_csv"]]

class ActionRunOut(BaseModel):
    created: List[dict]
    credits_charged: int

class OCRIn(BaseModel):
    source: str
    imageId: str
    text: str
    meta: Optional[dict] = None

class OCRResp(BaseModel):
    classification: Literal["official","ad","unknown"]
    task_created: bool
    task: Optional[dict]

class UsageMonthOut(BaseModel):
    month: str
    credits: int

class MetricsOut(BaseModel):
    docs_total: int
    folders_total: int
    actions_month: int
    tasks_today: int

class AuditOut(BaseModel):
    id: str = Field(alias="_id")
    at: datetime
    userId: Optional[str]
    action: str
    entityType: str
    entityId: Optional[str]
    metadata: Optional[Any]

class CurrentUser(BaseModel):
    id: str
    email: str
    role: Literal["admin","support","moderator","user"]