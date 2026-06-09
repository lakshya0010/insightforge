import logging
from app.repositories.statement_repo import StatementRepository
from app.services.parser_service import CSVParserService
from app.schemas.statement import StatementOut, StatementDetailOut, TransactionOut, ReportOut
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class StatementService:
    def __init__(self, repo: StatementRepository, parser: CSVParserService, llm: LLMService):
        self.repo = repo
        self.parser = parser
        self.llm = llm

    async def upload_statement(
            self,
            user_id: int,
            file_content: bytes,
            filename: str
    ) -> StatementOut:
        parsed_transactions = self.parser.parse(file_content, filename)
        month = self.parser.extract_month(parsed_transactions)

        logger.info(
            f"Parsed {len(parsed_transactions)} Transactions"
            f"from file {filename} for user_id {user_id}"
        )



        statement = await self.repo.create_statement(user_id = user_id, filename=filename, month=month)
        try:
            transactions = await self.repo.save_transactions(
                statement_id=statement.id,
                parsed_transactions=parsed_transactions
            )

            categories = await self.llm.categorize_transactions(transactions)
            print(f"CATEGORIES RESULT: {categories}")

            await self.repo.update_transaction_categories(transactions, categories)

            report_data = await self.llm.generate_report(transactions, month)
            await self.repo.create_report(
                statement_id=statement.id,
                summary=report_data["summary"],
                total_income=report_data["total_income"],
                total_expenses=report_data["total_expenses"],
                category_breakdown=report_data["category_breakdown"]
            )

            await self.repo.update_status(statement.id, "done")
            statement.status = "done"

            logger.info(
                f"Statement {statement.id} saved successfully "
                f"for user {user_id}"
            )

        except Exception as e:
            await self.repo.update_status(statement.id, "failed")
            logger.error(
                f"Failed to process statement {statement.id}: {str(e)}",
                exc_info=True
            )
            raise ValueError("Failed to process statement. Please try again.")
        

        return StatementOut.model_validate(statement)
    

    async def get_statements(self, user_id: int) -> list[StatementOut]:
        statements = await self.repo.get_all_by_user(user_id)
        return [StatementOut.model_validate(s) for s in statements]
    

    async def get_statement_detail(
            self,
            statement_id: int,
            user_id: int,
    )->StatementDetailOut:
        statement = await self.repo.get_by_id(user_id=user_id, statement_id=statement_id)

        if not statement:
            raise ValueError("Statement not found")
        
        transactions = await self.repo.get_transactions(statement_id)
        report = await self.repo.get_report(statement_id)

        return StatementDetailOut(
            id = statement.id,
            filename=statement.filename,
            month=statement.month,
            status=statement.status,
            uploaded_at=statement.uploaded_at,
            transactions=[TransactionOut.model_validate(t) for t in transactions],
            report=ReportOut.model_validate(report) if report else None
        )

