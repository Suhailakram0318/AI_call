from pydantic import BaseModel

class CallRequest(BaseModel):
    name: str
    phone: str
    bank_name: str
    due_amount: str
    due_date: str
