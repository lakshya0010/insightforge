import json
import logging
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from app.core.config import settings
from app.models.statement import Transaction


logger = logging.getLogger(__name__)

CATEGORIES = ["Food", "Transport", "Entertainment", "Utilities", "Shopping", "Healthcare", "Income", "Other"]

class LLMService:
    def __init__(self):
        self.fast_llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model ="llama-3.1-8b-instant",
            temperature=0
        )
        self.smart_time = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model= "llama-3.3-70b-versatile",
            temperature=0.7
        )
    
    async def categorize_transactions(
            self,
            transactions: list[Transaction]
    ) -> list[str]:
        if not transactions: return []
        
        transaction_lines = []
        for i,t in enumerate(transactions, start=1):
            transaction_lines.append(
                f"{i}. {t.description} - {t.amount} - {t.type}"
            )
            transaction_text = "\n".join(transaction_lines)

            prompt = f"""Categorize each transaction below into exactly one category.

Valid categories: {", ".join(CATEGORIES)}

Rules:
- Salary, wages, freelance payments → Income
- Restaurants, food delivery, groceries → Food
- Uber, Ola, petrol, metro, bus → Transport
- Movies, streaming, games, sports → Entertainment
- Electricity, water, internet, phone bills → Utilities
- Online shopping, retail stores → Shopping
- Hospitals, medicines, pharmacy → Healthcare
- Anything else → Other

Transactions:
{transaction_text}

Reply with ONLY a JSON array of category strings, one per transaction, in the same order.
Example format: ["Food", "Income", "Transport"]
No explanation, no markdown, just the JSON array."""
            
            logger.info(f"Categorizing {len(transactions)} transactions")
            
            response = await self.fast_llm.ainvoke(
                [HumanMessage(content=prompt)]
            )
            raw  = response.content.strip()
            logger.info("Categorization info: {raw}")

            return self.parse_categories(raw, len(transactions))
        
        