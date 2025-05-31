from pydantic import BaseModel

class CallRequest(BaseModel):
    name: str
    phone: str
    due_amount: str
    due_date: str
