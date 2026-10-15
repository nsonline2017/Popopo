from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserOut(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    role: str
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class OptionIn(BaseModel):
    id: Optional[int] = None
    text: str
    is_correct: bool = False
    order_index: int = 0

class OptionOut(BaseModel):
    id: int
    text: str
    is_correct: bool
    order_index: int
    class Config:
        from_attributes = True

class NodeIn(BaseModel):
    id: Optional[int] = None
    prompt: str
    order_index: int = 0
    is_root: bool = False
    parent_option_id: Optional[int] = None
    options: List[OptionIn] = []

class NodeOut(BaseModel):
    id: int
    prompt: str
    order_index: int
    is_root: bool
    parent_option_id: Optional[int]
    options: List[OptionOut] = []
    class Config:
        from_attributes = True

class StudyOut(BaseModel):
    id: int
    name: str
    study_type: str
    file_paths: List[str]
    class Config:
        from_attributes = True

class QuizIn(BaseModel):
    title: str
    description: Optional[str] = None
    study_id: Optional[int] = None
    nodes: List[NodeIn] = []

class QuizOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    study_id: Optional[int]
    study: Optional[StudyOut] = None
    created_at: datetime
    nodes: List[NodeOut] = []
    class Config:
        from_attributes = True

class QuizListItem(BaseModel):
    id: int
    title: str
    description: Optional[str]
    study_id: Optional[int]
    created_at: datetime
    class Config:
        from_attributes = True

class SubmitAnswer(BaseModel):
    node_id: int
    option_id: int

class SubmitIn(BaseModel):
    selections: List[SubmitAnswer]

class SubmitResult(BaseModel):
    correct: bool
    errors: List[dict]  # {node_id, option_id, message}
    message: str
