"""
Input validation helpers for the trading bot.
All functions raise ValueError with descriptive messages on bad input.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional

SUPPORTED_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}
SUPPORTED_SIDES = {"BUY", "SELL"}


def validate_symbol(symbol: str) -> str:
    """Return upper-cased symbol or raise ValueError."""
    symbol = symbol.strip().upper()
    if not symbol.isalnum():
        raise ValueError(f"Invalid symbol '{symbol}'. Use alphanumeric characters only (e.g. BTCUSDT).")
    return symbol


def validate_side(side: str) -> str:
    """Return upper-cased side or raise ValueError."""
    side = side.strip().upper()
    if side not in SUPPORTED_SIDES:
        raise ValueError(f"Invalid side '{side}'. Must be one of: {', '.join(sorted(SUPPORTED_SIDES))}.")
    return side


def validate_order_type(order_type: str) -> str:
    """Return upper-cased order type or raise ValueError."""
    order_type = order_type.strip().upper()
    if order_type not in SUPPORTED_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. Must be one of: {', '.join(sorted(SUPPORTED_ORDER_TYPES))}."
        )
    return order_type


def validate_quantity(quantity: str | float) -> str:
    """Return quantity as a string-formatted Decimal or raise ValueError."""
    try:
        qty = Decimal(str(quantity))
    except InvalidOperation:
        raise ValueError(f"Invalid quantity '{quantity}'. Must be a positive number.")
    if qty <= 0:
        raise ValueError(f"Quantity must be greater than zero, got {qty}.")
    return str(qty)


def validate_price(price: Optional[str | float], order_type: str) -> Optional[str]:
    """
    Validate price field.

    - LIMIT / STOP_MARKET orders require a price > 0.
    - MARKET orders must NOT supply a price.
    """
    order_type = order_type.strip().upper()

    if order_type == "MARKET":
        if price is not None:
            raise ValueError("Price must NOT be provided for MARKET orders.")
        return None

    # LIMIT or STOP_MARKET
    if price is None:
        raise ValueError(f"Price is required for {order_type} orders.")
    try:
        p = Decimal(str(price))
    except InvalidOperation:
        raise ValueError(f"Invalid price '{price}'. Must be a positive number.")
    if p <= 0:
        raise ValueError(f"Price must be greater than zero, got {p}.")
    return str(p)


def validate_stop_price(stop_price: Optional[str | float], order_type: str) -> Optional[str]:
    """Stop price is required only for STOP_MARKET orders."""
    if order_type.upper() != "STOP_MARKET":
        return None
    if stop_price is None:
        raise ValueError("--stop-price is required for STOP_MARKET orders.")
    try:
        sp = Decimal(str(stop_price))
    except InvalidOperation:
        raise ValueError(f"Invalid stop price '{stop_price}'. Must be a positive number.")
    if sp <= 0:
        raise ValueError(f"Stop price must be greater than zero, got {sp}.")
    return str(sp)
