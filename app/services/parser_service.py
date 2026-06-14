import io
import json
import logging
import pdfplumber
from decimal import Decimal, InvalidOperation
from dataclasses import dataclass
from typing import Optional
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ParsedTransaction:
    date: str
    description: str
    amount: Decimal
    type: str  # "debit" or "credit"


class CSVParserService:

    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model="llama-3.3-70b-versatile",
            temperature=0
        )

    def parse(self, file_content: bytes, filename: str) -> list[ParsedTransaction]:
        """
        Main entry point. Detects file type and routes accordingly.
        Always returns list[ParsedTransaction].
        """
        filename_lower = filename.lower()

        if filename_lower.endswith(".pdf"):
            raw_text = self._extract_pdf_text(file_content)
        elif filename_lower.endswith(".csv"):
            raw_text = self._extract_csv_text(file_content)
        else:
            raise ValueError(f"Unsupported file type. Please upload a CSV or PDF.")

        if not raw_text or len(raw_text.strip()) < 50:
            raise ValueError("Could not extract readable text from the file.")

        logger.info(f"Extracted {len(raw_text)} characters from {filename}")

        # Send to LLM for parsing
        transactions = self._llm_parse(raw_text, filename)

        if not transactions:
            raise ValueError("No valid transactions found in the file.")

        logger.info(f"Successfully parsed {len(transactions)} transactions")
        return transactions

    def _extract_pdf_text(self, file_content: bytes) -> str:
        """Extract text from PDF using pdfplumber."""
        try:
            text_parts = []
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            return "\n".join(text_parts)
        except Exception as e:
            raise ValueError(f"Could not read PDF file: {str(e)}")

    def _extract_csv_text(self, file_content: bytes) -> str:
        """Read CSV as plain text — let LLM handle the structure."""
        try:
            try:
                return file_content.decode("utf-8-sig")  # handles BOM character
            except UnicodeDecodeError:
                return file_content.decode("latin-1")
        except Exception as e:
            raise ValueError(f"Could not read CSV file: {str(e)}")

    def _llm_parse(self, raw_text: str, filename: str) -> list[ParsedTransaction]:
        """
        Send raw text to LLM and get structured transactions back.
        The LLM handles all format variations — we just validate the output.
        """
        # Trim text if too long — keep first 6000 chars which covers most statements
        # For very long statements we'd chunk, but most monthly statements fit here
        trimmed_text = raw_text[:12000] if len(raw_text) > 6000 else raw_text

        prompt = f"""You are a bank statement parser. Extract all financial transactions from this bank statement text.

For each transaction, extract:
- date: the transaction date (keep original format)
- description: merchant name or payment description (keep it concise, max 100 chars)
- amount: the transaction amount as a positive number (no currency symbols, no commas)
- type: "debit" if money went out, "credit" if money came in

Rules:
- Opening Balance and Closing Balance are NOT transactions — skip them
- Page numbers, disclaimers, and headers are NOT transactions — skip them
- If a row has both deposit and withdrawal columns, use whichever has a value
- UPI/DR = debit, UPI/CR = credit
- Return ONLY a JSON array, nothing else
- description: extract the merchant or person name, NOT the UPI reference number. 
  For UPI transactions, look for the name after UPI/DR/ or UPI/CR/ 
  (e.g. from "UPI/DR/612551130262/DELHI MET/..." extract "DELHI MET").
  For cheque transactions, use the payee name if available.
  Never use raw reference numbers as description.
- Extract ALL transactions, do not stop early
- The statement may span multiple pages — process everything

Bank statement text:
{trimmed_text}

Return format (JSON array only, no markdown, no explanation):
[{{"date": "02-05-2026", "description": "ZOMATO UPI", "amount": "450.00", "type": "debit"}}]"""

        logger.info("Sending statement to LLM for parsing")

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            raw = response.content.strip()
            logger.info(f"LLM parser response length: {len(raw)} chars")

            return self._parse_llm_response(raw)

        except Exception as e:
            logger.error(f"LLM parsing failed: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to parse statement with AI: {str(e)}")

    def _parse_llm_response(self, raw: str) -> list[ParsedTransaction]:
        """
        Extract and validate the JSON array from LLM response.
        Same robust extraction as categorization.
        """
        # Find JSON array boundaries
        start = raw.find("[")
        end = raw.rfind("]")

        if start == -1 or end == -1:
            logger.error(f"No JSON array in LLM response: {raw[:200]}")
            raise ValueError("AI could not parse the statement format.")

        json_str = raw[start:end + 1]

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}. Raw: {json_str[:200]}")
            raise ValueError("AI returned malformed data. Please try again.")

        transactions = []
        for i, item in enumerate(data):
            try:
                transaction = self._validate_transaction(item, i)
                if transaction:
                    transactions.append(transaction)
            except Exception as e:
                logger.warning(f"Skipping transaction {i}: {e}")
                continue

        return transactions

    def _validate_transaction(
        self, item: dict, index: int
    ) -> Optional[ParsedTransaction]:
        """
        Validate one transaction from LLM output.
        Returns None for invalid items rather than crashing.
        """
        if not isinstance(item, dict):
            return None

        date = str(item.get("date", "")).strip()
        description = str(item.get("description", "")).strip()
        amount_raw = str(item.get("amount", "")).strip()
        type_raw = str(item.get("type", "")).strip().lower()

        # Must have date and description
        if not date or not description:
            return None

        # Parse amount
        amount = self._parse_amount(amount_raw)
        if amount is None or amount <= 0:
            return None

        # Normalize type
        if type_raw not in ("debit", "credit"):
            # Try to infer from common patterns
            if any(x in type_raw for x in ["dr", "debit", "withdrawal", "out"]):
                type_raw = "debit"
            elif any(x in type_raw for x in ["cr", "credit", "deposit", "in"]):
                type_raw = "credit"
            else:
                logger.warning(f"Unknown transaction type '{type_raw}' — defaulting to debit")
                type_raw = "debit"

        return ParsedTransaction(
            date=date,
            description=description[:200],  # cap length
            amount=amount,
            type=type_raw
        )

    def _parse_amount(self, amount_str: str) -> Optional[Decimal]:
        """Convert amount string to Decimal. Handles commas, currency symbols."""
        if not amount_str:
            return None
        # Remove everything except digits and decimal point
        cleaned = ""
        for char in amount_str:
            if char.isdigit() or char == ".":
                cleaned += char
        if not cleaned:
            return None
        try:
            value = Decimal(cleaned)
            return value if value > 0 else None
        except InvalidOperation:
            return None

    def extract_month(self, transactions: list[ParsedTransaction]) -> str:
        """Extract month from first transaction date."""
        if not transactions:
            return "unknown"
        date_str = transactions[0].date
        for fmt in ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%y", "%d/%m/%y"]:
            try:
                from datetime import datetime
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m")
            except ValueError:
                continue
        return date_str[:7] if len(date_str) >= 7 else "unknown"