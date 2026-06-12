
from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

logger = logging.getLogger("trading_bot.client")

BASE_URL = "https://testnet.binancefuture.com"


class BinanceAPIError(Exception):
   

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"Binance API error {code}: {message}")


class BinanceClient:
    """
    Minimal authenticated client for Binance USDT-M Futures Testnet.

    Args:
        api_key:    Your testnet API key.
        api_secret: Your testnet API secret.
        timeout:    HTTP request timeout in seconds (default 10).
    """

    def __init__(self, api_key: str, api_secret: str, timeout: int = 10) -> None:
        if not api_key or not api_secret:
            raise ValueError("api_key and api_secret must not be empty.")
        self._api_key = api_key
        self._api_secret = api_secret.encode()
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self._api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        logger.debug("BinanceClient initialised (base_url=%s)", BASE_URL)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _sign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Append a HMAC-SHA256 signature to *params* and return it."""
        params["timestamp"] = int(time.time() * 1000)
        query_string = urlencode(params)
        signature = hmac.new(self._api_secret, query_string.encode(), hashlib.sha256).hexdigest()
        params["signature"] = signature
        return params

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False,
    ) -> Dict[str, Any]:
        """
        Dispatch an HTTP request and return the parsed JSON body.

        Raises:
            BinanceAPIError: on API-level errors (non-2xx or error payload).
            requests.RequestException: on network / timeout failures.
        """
        url = BASE_URL + path
        params = params or {}

        if signed:
            params = self._sign(params)

        logger.debug("→ %s %s  params=%s", method.upper(), url, {k: v for k, v in params.items() if k != "signature"})

        try:
            if method.upper() == "GET":
                response = self._session.get(url, params=params, timeout=self._timeout)
            else:
                response = self._session.post(url, data=params, timeout=self._timeout)
        except requests.exceptions.Timeout as exc:
            logger.error("Request timed out: %s", exc)
            raise
        except requests.exceptions.ConnectionError as exc:
            logger.error("Connection error: %s", exc)
            raise

        logger.debug("← HTTP %s  body=%s", response.status_code, response.text[:500])

        try:
            data = response.json()
        except ValueError:
            response.raise_for_status()
            return {}

        if isinstance(data, dict) and "code" in data and data["code"] != 200:
            raise BinanceAPIError(data["code"], data.get("msg", "Unknown error"))

        response.raise_for_status()
        return data

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def get_server_time(self) -> Dict[str, Any]:
        """Return the Binance server time (useful for connectivity checks)."""
        return self._request("GET", "/fapi/v1/time")

    def get_exchange_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Return exchange info, optionally filtered by symbol."""
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._request("GET", "/fapi/v1/exchangeInfo", params=params)

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: str,
        price: Optional[str] = None,
        stop_price: Optional[str] = None,
        time_in_force: str = "GTC",
    ) -> Dict[str, Any]:
        """
        Submit a new order to Binance Futures Testnet.

        Args:
            symbol:        Trading pair, e.g. "BTCUSDT".
            side:          "BUY" or "SELL".
            order_type:    "MARKET", "LIMIT", or "STOP_MARKET".
            quantity:      Order quantity as a string.
            price:         Limit price (required for LIMIT).
            stop_price:    Trigger price (required for STOP_MARKET).
            time_in_force: "GTC" (default), "IOC", or "FOK" for LIMIT orders.

        Returns:
            Raw Binance order response dict.
        """
        params: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }

        if order_type == "LIMIT":
            params["price"] = price
            params["timeInForce"] = time_in_force

        if order_type == "STOP_MARKET":
            params["stopPrice"] = stop_price

        logger.info(
            "Placing order — symbol=%s side=%s type=%s qty=%s price=%s",
            symbol,
            side,
            order_type,
            quantity,
            price or "N/A",
        )

        result = self._request("POST", "/fapi/v1/order", params=params, signed=True)
        logger.info("Order placed successfully — orderId=%s status=%s", result.get("orderId"), result.get("status"))
        return result
