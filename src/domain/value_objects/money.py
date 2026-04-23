from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class Money(BaseModel):

    amount: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    currency: str = Field(default="RUB", max_length=3)

    def __add__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"
