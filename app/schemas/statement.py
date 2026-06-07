from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from typing import Optional
from datetime import datetime

class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: str
    description: str
    amount: Decimal
    type: str
    category: Optional[str] = None

class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    summary: Optional[str] = None
    total_income: Optional[Decimal] = None
    total_expenses: Optional[Decimal] = None
    category_breakdown: Optional[dict] = None
    created_at: datetime

class StatementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    filename: str
    month: str
    status: str
    uploaded_at: datetime

class StatementDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    month: str
    status: str
    uploaded_at: datetime
    transactions: list[TransactionOut] = []
    report: Optional[ReportOut] = None