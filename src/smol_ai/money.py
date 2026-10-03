"""Currency amounts as decimal cents, never binary floats."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "USD"

    def __post_init__(self) -> None:
        if isinstance(self.amount, float):
            raise TypeError("Money rejects float. Pass a Decimal or a numeric string.")
        if isinstance(self.amount, bool) or not isinstance(self.amount, (Decimal, int, str)):
            raise TypeError("Money amount must be Decimal, int, or a numeric string.")
        if not self.currency or not str(self.currency).isalpha():
            raise ValueError("Currency must be an alphabetic code.")

        amount = self.amount if isinstance(self.amount, Decimal) else Decimal(str(self.amount))
        quantized = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        object.__setattr__(self, "amount", quantized)
        object.__setattr__(self, "currency", self.currency.upper())

    def _same_currency(self, other: "Money") -> None:
        if not isinstance(other, Money):
            raise TypeError("Money can only combine with Money.")
        if self.currency != other.currency:
            raise ValueError(
                "Cannot combine {0} with {1}.".format(self.currency, other.currency)
            )

    def __add__(self, other: "Money") -> "Money":
        self._same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        self._same_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, quantity: int) -> "Money":
        if isinstance(quantity, bool) or not isinstance(quantity, int):
            raise TypeError("Multiply Money by an int quantity, not a float.")
        return Money(self.amount * quantity, self.currency)

    def __lt__(self, other: "Money") -> bool:
        self._same_currency(other)
        return self.amount < other.amount

    def __le__(self, other: "Money") -> bool:
        self._same_currency(other)
        return self.amount <= other.amount

    def __gt__(self, other: "Money") -> bool:
        self._same_currency(other)
        return self.amount > other.amount

    def __ge__(self, other: "Money") -> bool:
        self._same_currency(other)
        return self.amount >= other.amount

    def __str__(self) -> str:
        return "{0} {1}".format(self.amount, self.currency)


def transaction_total(unit_price: Money, quantity: int, fees: Money) -> Money:
    """Landed total for one purchase. Callers must not trust a model-supplied total."""
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
        raise ValueError("Quantity must be a positive integer.")
    return (unit_price * quantity) + fees
