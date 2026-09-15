from pydantic import BaseModel


class ClickCreateRequest(BaseModel):
    price_comparison_id: int


class ClickCreateResponse(BaseModel):
    redirect_url: str
