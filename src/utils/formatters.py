"""Formatters for financial output."""

from decimal import Decimal
from typing import Union


def format_brl(value: Union[Decimal, float, int]) -> str:
    """
    Format value as Brazilian currency (R$).

    Format: R$ 1.234,56 (thousands separator = period, decimal separator = comma)
    """
    if not isinstance(value, Decimal):
        value = Decimal(str(value))

    negative = value < 0
    value = abs(value)

    # Format with 2 decimal places using US locale then swap separators
    formatted = f"{value:,.2f}"
    # Convert: 1,234.56 → 1.234,56
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")

    if negative:
        return f"-R$ {formatted}"
    return f"R$ {formatted}"


def format_percentage(value: Union[Decimal, float, int], decimals: int = 2) -> str:
    """
    Format value as percentage with proper decimal places.

    Detects whether value is in 0-1 or 0-100 range automatically.
    """
    if not isinstance(value, Decimal):
        value = Decimal(str(value))

    # If absolute value <= 1, treat as 0-1 range (0.1234 → 12,34%)
    if abs(value) <= Decimal("1"):
        pct = value * Decimal("100")
    else:
        pct = value

    formatted = f"{pct:.{decimals}f}"
    # Convert decimal point to comma for pt-BR
    formatted = formatted.replace(".", ",")
    return f"{formatted}%"


def format_days(value: Union[Decimal, float, int]) -> str:
    """
    Format value as days with descriptor.

    Format: "23 dias" or "1 dia"
    """
    if not isinstance(value, Decimal):
        value = Decimal(str(value))

    # Integer or fractional
    if value == value.to_integral_value():
        num = int(value)
        label = "dia" if num == 1 else "dias"
        return f"{num} {label}"
    else:
        num = float(round(value, 1))
        label = "dia" if num == 1.0 else "dias"
        return f"{num} {label}"


def movement_indicator(
    current: Union[Decimal, float, int],
    prior: Union[Decimal, float, int],
    show_value: bool = False
) -> str:
    """
    Return text indicator of movement (up/down/flat) with optional value.

    Format: "↑" (up) or "↓" (down) or "→" (flat)
    """
    if not isinstance(current, Decimal):
        current = Decimal(str(current))
    if not isinstance(prior, Decimal):
        prior = Decimal(str(prior))

    diff = current - prior

    if prior == 0:
        if diff == 0:
            arrow = "→"
            pct_change = Decimal("0")
        elif diff > 0:
            arrow = "↑"
            pct_change = Decimal("100")
        else:
            arrow = "↓"
            pct_change = Decimal("-100")
    else:
        pct_change = (diff / abs(prior)) * Decimal("100")
        if abs(pct_change) < Decimal("0.1"):
            arrow = "→"
        elif diff > 0:
            arrow = "↑"
        else:
            arrow = "↓"

    if not show_value:
        return arrow

    sign = "+" if pct_change >= 0 else ""
    pct_str = f"{sign}{round(float(pct_change))}%"
    return f"{arrow} {pct_str}"
