import json
import logging
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from app.core.config import settings
from app.models.statement import Transaction


logger = logging.getLogger(__name__)

CATEGORIES = ["Food", "Transport", "Entertainment", "Utilities", "Shopping", "Healthcare", "Income", "Transfer", "Other"]

class LLMService:
    def __init__(self):
        self.fast_llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model ="llama-3.3-70b-versatile",
            temperature=0
        )
        self.smart_llm = ChatGroq(
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

        prompt = f"""Categorize these {len(transactions)} bank transactions.

Valid categories: {", ".join(CATEGORIES)}

Rules:
- UPI payments TO individual person names (not businesses) → Transfer
- Received FROM individual person names → Transfer  
- Metro recharges, Uber, Ola, bus, petrol → Transport
- Swiggy, Zomato, restaurants, food delivery → Food
- Salary, stipend, pocket money from family → Income
- Netflix, movies, games, subscriptions → Entertainment
- Electricity, water, internet, phone bills → Utilities
- Amazon, Flipkart, shopping apps → Shopping
- Hospital, medicine, pharmacy → Healthcare
- Anything else → Other

Transactions:
{transaction_text}

Reply with ONLY a JSON array of exactly {len(transactions)} category strings.
First character must be [ and last must be ]
Do not include any other text.

Output:"""
            
        logger.info(f"Categorizing {len(transactions)} transactions")
            
        response = await self.fast_llm.ainvoke(
            [HumanMessage(content=prompt)]
        )
        raw  = response.content.strip()

        return self._parse_categories(raw, len(transactions))
        
    def _parse_categories(
            self,
            raw,
            expected_count: int
            )->list[str]:
        try:
            cleaned = raw.strip()
            if cleaned.startswith("'''"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(lines[1:-1])

            parsed = json.loads(cleaned)

            if not isinstance(parsed, list):
                raise ValueError("Response is not a list")
            
            result = []

            for cat in parsed:
                if cat in CATEGORIES:
                    result.append(cat)
                else:
                    logger.warning("Invalid category '{cat} - defaulting to Other")
                    result.append("Other")

            while len(result)<expected_count:
                result.append("Other")
                
            return result[:expected_count]
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse categories: {e}. Raw: {raw}")
            return ["Other"] * expected_count
        
    
    async def generate_report(
            self,
            transactions: list[Transaction],
            month:str
    )->dict:
        total_income = sum(
            float(t.amount) for t in transactions if t.type == "credit"
        )
        total_expenses = sum(
            float(t.amount) for t in transactions if t.type == "debit"
        )

        category_breakdown = {}
        for t in transactions:
            if t.type == "debit" and t.category:
                category_breakdown[t.category] = (category_breakdown.get(t.category,0) + float(t.amount))
        transfers = [t for t in transactions if t.category == "Transfer"]
        transfer_summary = {}
        for t in transfers:
            name = t.description.strip()
            transfer_summary[name] = (
                transfer_summary.get(name, 0) + float(t.amount)
            )
        top_transfers = sorted(
            transfer_summary.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]

        if top_transfers:
            transfer_lines = "\n".join([
                f"- {name}: ₹{amount:,.0f}"
                for name, amount in top_transfers
            ])
            transfer_text = f"\nTop people you transacted with:\n{transfer_lines}"
        else:
            transfer_text = ""
        debit_transactions = [t for t in transactions if t.type =="debit"]
        biggest = max(
            debit_transactions, key = lambda t: t.amount
        ) if debit_transactions else None

        breakdown_lines = [
            f"- {cat}: ₹{amount:,.2f}"
            for cat, amount in sorted(
                category_breakdown.items(),
                key = lambda x:x[1],
                reverse=True
            )
        ]
        breakdown_text = "\n".join(breakdown_lines)

        biggest_text = (
            f"{biggest.description}: ₹{biggest.amount}"
            if biggest else "N/A"
        )

        prompt =f"""You are a personal finance advisor. Write a friendly,
helpful spending report for {month} based on this data.

Financial Summary:
- Total Income: ₹{total_income:,.2f}
- Total Expenses: ₹{total_expenses:,.2f}
- Net Savings: ₹{total_income - total_expenses:,.2f}
- Biggest Single Expense: {biggest_text}

Spending by Category:
{breakdown_text}
{transfer_text}

Write a 3-4 paragraph report that:
1. Summarizes overall spending vs income
2. Highlights the top spending categories  
3. Points out anything notable (high spending, good savings, etc.)
4. Gives 1-2 specific, actionable tips

Keep it conversational, specific to the numbers, and under 300 words.
Address the user as "you"."""
        logger.info(f"Generating report for month {month}")

        response = await self.smart_llm.ainvoke(
            [HumanMessage(content=prompt)]
        )

        summary = response.content.strip()

        return {
        "summary": summary,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "category_breakdown": category_breakdown,
        "top_transfers": dict(top_transfers)
        }

                