from pydantic import BaseModel


class PaymentMethodOut(BaseModel):
    id: int
    type: str
    name: str
