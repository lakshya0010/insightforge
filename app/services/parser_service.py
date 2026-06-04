import csv
import io
from decimal import Decimal, InvalidOperation
from typing import Optional
from dataclasses import dataclass

@dataclass
class ParsedTransaction:
    date: str
    description: str
    amount: Decimal
    type: str

class CSVParserService:
    DATE_HEADERS = ["date", "transaction date", "txn date", "value date"]
    DESC_HEADERS = ["description", "narration", "particulars", "remarks", "details"]
    DEBIT_HEADERS = ["debit", "withdrawal", "dr", "debit amount"]
    CREDIT_HEADERS = ["credit", "deposit", "credit amount", "cr"]

    def parse(self, file_content: bytes, filename: str) -> list[ParsedTransaction]:
        try:
                try:
                    content = file_content.decode("utf-8")
                except UnicodeDecodeError:
                    content = file_content.decode("latin-1")

                reader = csv.DictReader(io.StringIO(content))

                if not reader.fieldnames:
                    raise ValueError("CSV file has no headers")
                normalized = {
                    str(h).lower().strip(): h
                    for h in reader.fieldnames
                    if h is not None
                }

                date_col = self._find_column(normalized, self.DATE_HEADERS)
                desc_col = self._find_column(normalized, self.DESC_HEADERS)
                debit_col = self._find_column(normalized, self.DEBIT_HEADERS)
                credit_col = self._find_column(normalized, self.CREDIT_HEADERS)
        

                if not all([date_col, desc_col]):
                    raise ValueError("Could not find required columns (date, description). "
                            f"Found columns: {list(normalized.keys())}")
                
                if not debit_col and not credit_col:
                        raise ValueError(
                            "Could not find debit or credit columns. "
                            f"Found columns: {list(normalized.keys())}"
                        )
                
                transactions = []
                for row_num, row in enumerate(reader, start=2):
                    parsed = self._parse_row(
                        row, date_col, desc_col, debit_col, credit_col, row_num
                    )
                    if parsed:
                        transactions.append(parsed)
                    
                if not transactions:
                    raise ValueError("No valid transactions found")
                
                return transactions
        except ValueError:
             raise
        except Exception as e:
            raise ValueError(f"Failed to parse CSV: {str(e)}")
        
    def _find_column(self, normalized:dict, candidates:list[str]) ->Optional[str]:
        for candidate in candidates:
            if candidate in normalized:
                return normalized[candidate]  
        return None
    

    def _parse_row(
            self,
            row: dict,
            date_col: str,
            desc_col: str,
            debit_col: Optional[str],
            credit_col: Optional[str],
            row_num: int) -> Optional[ParsedTransaction]:
        
        
        if not any(row.values()):
            return None

        date = row.get(date_col, "").strip()
        description = row.get(desc_col, "").strip()

        if not date or not description:
            return None

        debit_str = row.get(debit_col, "").strip() if debit_col else ""
        credit_str = row.get(credit_col, "").strip() if credit_col else ""

        debit_amount = self._parse_amount(debit_str)
        credit_amount = self._parse_amount(credit_str)

        if debit_amount and debit_amount > 0:
            return ParsedTransaction(
                date=date,
                description=description,
                amount=debit_amount,
                type="debit"
            )
        elif credit_amount and credit_amount > 0:
            return ParsedTransaction(
                date=date,
                description=description,
                amount=credit_amount,
                type="credit"
            )
        else:
            return None
        
    def _parse_amount(self, amount_str:str) ->Optional[Decimal]:
        if not amount_str:
            return None
        cleaned = ""
        for char in amount_str:
            if char.isdigit() or char==".":
                cleaned+= char
        if not cleaned: 
            return None
        try:
            value = Decimal(cleaned)
            return value if value>0 else None
        except InvalidOperation:
            return None
            
    def extract_month(self, transactions: list[ParsedTransaction]) -> str:
        if not transactions:
            return "unknown"
            
        date_str = transactions[0].date
        for fmt in ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y"]:
            try:
                from datetime import datetime
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m")
            except ValueError:
                continue

        return date_str[:7] if len(date_str) >= 7 else "unknown"
        


         
    