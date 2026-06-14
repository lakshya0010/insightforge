from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.models.statement import Statement, Transaction, Report
from decimal import Decimal


class StatementRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_report(self, statement_id: int) -> Optional[Report]:
        result = await self.db.execute(
            select(Report).where(Report.statement_id == statement_id)
        )
        return result.scalar_one_or_none()
    
    async def update_transaction_categories(
            self,
            trasactions: list[Transaction],
            categories: list[str]
    )->None:
        for transaction,category in zip(trasactions, categories):
            transaction.category = category
        await self.db.commit()
        
    
    async def create_report(
            self,
            statement_id:int,
            summary:str,
            total_income:float,
            total_expenses: float,
            category_breakdown: dict,
            top_transfers:dict
    ) -> Report:
        report = Report(
            statement_id = statement_id,
            summary = summary,
            total_expenses = Decimal(str(total_expenses)),
            total_income = Decimal(str(total_income)),
            category_breakdown = category_breakdown,
            top_transfers=top_transfers
        )
        self.db.add(report)
        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def create_statement(
            self,
            user_id: int,
            filename: str,
            month: str
    ) -> Statement:
        statement = Statement(
            user_id = user_id,
            filename = filename,
            month = month,
            status = "processing"
        )
        self.db.add(statement)
        await self.db.commit()
        await self.db.refresh(statement)
        return statement
    
    async def save_transactions(
            self,
            statement_id:int,
            parsed_transactions:list
    )->list[Transaction]:
        transactions = [
            Transaction(
                statement_id = statement_id,
                date = pt.date,
                description = pt.description,
                amount = pt.amount,
                type = pt.type,
                category = None
            )
            for pt in parsed_transactions
        ]

        self.db.add_all(transactions)
        await self.db.commit()
        return transactions
    

    async def update_status(self, statement_id:int, status:str) ->None:
        statement = await self.get_by_id(statement_id)
        if statement:
            statement.status = status
            await self.db.commit()
    
    async def get_by_id(self, statement_id:int, user_id: Optional[int] = None) -> Optional[Statement]:
        query = select(Statement).where(Statement.id == statement_id)
        if user_id:
            query = query.where(Statement.user_id == user_id)
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all_by_user(self, user_id:int) -> list[Statement]:
        result = await self.db.execute(select(Statement).where(Statement.user_id == user_id).order_by(Statement.uploaded_at.desc()))
        return list(result.scalars().all())
    
    async def get_transactions(self, statement_id:int)->list[Transaction]:
        result = await self.db.execute(
            select(Transaction).where(Transaction.statement_id == statement_id).order_by(Transaction.id)
        )
        return list(result.scalars().all())
    

        
        
        

