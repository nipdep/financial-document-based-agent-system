from datetime import datetime
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, constr, Field
from typing import Optional, List

class AddDocumentSchema(BaseModel):
    filename: constr(strip_whitespace=True, min_length=1)
    content_type: Optional[str] = Field(None, description="MIME type of the file, e.g., 'application/pdf'")
    class Config:
        schema_extra = {
            "example": {
                "filename": "report.pdf",
                "content_type": "application/pdf",
            }
        }