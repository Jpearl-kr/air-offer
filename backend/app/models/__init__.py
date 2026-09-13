from app.models.base import Base
from app.models.airport import Airport
from app.models.airline import Airline
from app.models.route import Route
from app.models.provider import Provider
from app.models.flight_search import FlightSearch
from app.models.flight_result import FlightResult
from app.models.provider_price import ProviderPrice
from app.models.card_company import CardCompany
from app.models.payment_method import PaymentMethod
from app.models.promotion import Promotion
from app.models.promotion_rule import PromotionRule
from app.models.user import User
from app.models.user_payment_preference import UserPaymentPreference
from app.models.price_comparison import PriceComparison
from app.models.click import Click
from app.models.booking import Booking
from app.models.price_alert import PriceAlert

__all__ = [
    "Base",
    "Airport",
    "Airline",
    "Route",
    "Provider",
    "FlightSearch",
    "FlightResult",
    "ProviderPrice",
    "CardCompany",
    "PaymentMethod",
    "Promotion",
    "PromotionRule",
    "User",
    "UserPaymentPreference",
    "PriceComparison",
    "Click",
    "Booking",
    "PriceAlert",
]
