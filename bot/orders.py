"""
Order placement logic layer.

Sits between the CLI and the raw BinanceClient.  Validates inputs,
delegates to the client, and returns a normalised OrderResult.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from bot.client import BinanceClient
from bot.validators import (
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)

logger = logging.getLogger("trading_bot.orders")


@dataclass
class OrderResult:
    """Normalised view of a Binance order response."""

    success: bool
    order_id: Optional[int] = None
    client_order_id: Optional[str] = None
    symbol: Optional[str] = None
    side: Optional[str] = None
    order_type: Optional[str] = None
    status: Optional[str] = None
    quantity: Optional[str] = None
    executed_qty: Optional[str] = None
    avg_price: Optional[str] = None
    price: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "OrderResult":
        return cls(
            success=True,
            order_id=data.get("orderId"),
            client_order_id=data.get("clientOrderId"),
            symbol=data.get("symbol"),
            side=data.get("side"),
            order_type=data.get("type"),
            status=data.get("status"),
            quantity=data.get("origQty"),
            executed_qty=data.get("executedQty"),
            avg_price=data.get("avgPrice"),
            price=data.get("price"),
            raw=data,
        )

    @classmethod
    def from_error(cls, message: str) -> "OrderResult":
        return cls(success=False, error_message=message)


class OrderManager:
    """
    High-level order manager.

    Validates all user inputs before forwarding to BinanceClient so
    that invalid data is caught early and logged clearly.
    """

    def __init__(self, client: BinanceClient) -> None:
        self._client = client

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: str | float,
        price: Optional[str | float] = None,
        stop_price: Optional[str | float] = None,
    ) -> OrderResult:
        """
        Validate inputs and place an order.

        Returns an OrderResult (never raises — errors are captured inside).
        """
        try:
            symbol = validate_symbol(symbol)
            side = validate_side(side)
            order_type = validate_order_type(order_type)
            quantity_str = validate_quantity(quantity)
            price_str = validate_price(price, order_type)
            stop_price_str = validate_stop_price(stop_price, order_type)

            logger.debug(
                "Validated inputs — symbol=%s side=%s type=%s qty=%s price=%s stop_price=%s",
                symbol,
                side,
                order_type,
                quantity_str,
                price_str,
                stop_price_str,
            )

            raw = self._client.place_order(
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity_str,
                price=price_str,
                stop_price=stop_price_str,
            )
            return OrderResult.from_api_response(raw)

        except ValueError as exc:
            logger.warning("Validation error: %s", exc)
            return OrderResult.from_error(f"Validation error: {exc}")
        except Exception as exc:  # network errors, API errors, etc.
            logger.error("Order failed: %s", exc, exc_info=True)
            return OrderResult.from_error(str(exc))
