from sqlalchemy import Integer, String, Numeric, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship 
from sqlalchemy.sql import func
from app.core.database import Base
from decimal import Decimal
from typing import Optional

class Statement(Base):
    __tablename__ = "statements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    month: Mapped[str] = mapped_column(String(7), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="processing")
    uploaded_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    transactions: Mapped[list["Transaction"]] = relationship("Transaction", back_populates="statement", cascade="all, delete-orphan")
    report: Mapped[Optional["Report"]] = relationship("Report", back_populates="statement", uselist=False, cascade="all, delete-orphan")

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    statement_id: Mapped[int] = mapped_column(Integer, ForeignKey("statements.id"), nullable=False, index=True)
    date: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10,2), nullable=False)
    type: Mapped[str] = mapped_column(String(10), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    statement: Mapped["Statement"] = relationship("Statement", back_populates="transactions")

class Report(Base):
    __tablename__ = "Report"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    statement_id: Mapped[int] = mapped_column(Integer, ForeignKey("statements.id"),nullable=False, unique=True)
    summary: Mapped[Optional[str]] = mapped_column(String(5000), nullable=True)
    total_income: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    total_expenses: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    category_breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    top_transfers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    statement: Mapped["Statement"] = relationship(
        "Statement", back_populates="report"
    )




