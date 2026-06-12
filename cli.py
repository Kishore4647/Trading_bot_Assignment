#!/usr/bin/env python3
"""
CLI entry point for the Binance Futures Testnet Trading Bot.

Usage examples:
    python cli.py place-order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
    python cli.py place-order --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 100000
    python cli.py place-order --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --stop-price 90000
    python cli.py ping
"""

from __future__ import annotations

import json
import os
import sys

import click
from dotenv import load_dotenv

from bot.client import BinanceAPIError, BinanceClient
from bot.logging_config import setup_logging
from bot.orders import OrderManager

load_dotenv()

# ── ANSI colour helpers ──────────────────────────────────────────────
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"


def _colour(text: str, code: str) -> str:
    return f"{code}{text}{RESET}" if sys.stdout.isatty() else text


def _print_separator(char: str = "─", width: int = 60) -> None:
    click.echo(char * width)


def _print_order_result(result) -> None:
    """Pretty-print an OrderResult to stdout."""
    _print_separator()
    if result.success:
        click.echo(_colour("  ✅  ORDER PLACED SUCCESSFULLY", GREEN + BOLD))
        _print_separator()
        click.echo(f"  Order ID        : {_colour(str(result.order_id), CYAN)}")
        click.echo(f"  Client Order ID : {result.client_order_id}")
        click.echo(f"  Symbol          : {result.symbol}")
        click.echo(f"  Side            : {_colour(result.side, YELLOW)}")
        click.echo(f"  Type            : {result.order_type}")
        click.echo(f"  Status          : {_colour(result.status, GREEN)}")
        click.echo(f"  Quantity        : {result.quantity}")
        click.echo(f"  Executed Qty    : {result.executed_qty}")
        avg = result.avg_price if result.avg_price and result.avg_price != "0" else "N/A"
        click.echo(f"  Avg Price       : {avg}")
        if result.price and result.price != "0":
            click.echo(f"  Limit Price     : {result.price}")
    else:
        click.echo(_colour("  ❌  ORDER FAILED", RED + BOLD))
        _print_separator()
        click.echo(f"  Reason: {_colour(result.error_message, RED)}")
    _print_separator()


# ── CLI group ────────────────────────────────────────────────────────

@click.group()
@click.option(
    "--api-key",
    envvar="BINANCE_API_KEY",
    default=None,
    help="Binance Testnet API key (or set BINANCE_API_KEY env var).",
)
@click.option(
    "--api-secret",
    envvar="BINANCE_API_SECRET",
    default=None,
    help="Binance Testnet API secret (or set BINANCE_API_SECRET env var).",
)
@click.option("--log-dir", default="logs", show_default=True, help="Directory for log files.")
@click.pass_context
def cli(ctx: click.Context, api_key: str, api_secret: str, log_dir: str) -> None:
    """Binance Futures Testnet Trading Bot."""
    ctx.ensure_object(dict)
    logger = setup_logging(log_dir)
    ctx.obj["logger"] = logger
    ctx.obj["api_key"] = api_key
    ctx.obj["api_secret"] = api_secret


def _require_credentials(ctx: click.Context):
    """Return (api_key, api_secret) or abort with a clear message."""
    api_key = ctx.obj.get("api_key")
    api_secret = ctx.obj.get("api_secret")
    if not api_key or not api_secret:
        click.echo(
            _colour(
                "\nError: API credentials are required.\n"
                "Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables,\n"
                "or pass --api-key / --api-secret flags.\n",
                RED,
            )
        )
        sys.exit(1)
    return api_key, api_secret


# ── ping ─────────────────────────────────────────────────────────────

@cli.command()
@click.pass_context
def ping(ctx: click.Context) -> None:
    """Check connectivity to Binance Futures Testnet."""
    api_key, api_secret = _require_credentials(ctx)
    logger = ctx.obj["logger"]
    client = BinanceClient(api_key, api_secret)
    try:
        data = client.get_server_time()
        click.echo(_colour(f"✅  Connected to Binance Futures Testnet — server time: {data['serverTime']}", GREEN))
        logger.info("Ping successful — serverTime=%s", data["serverTime"])
    except Exception as exc:
        click.echo(_colour(f"❌  Connection failed: {exc}", RED))
        logger.error("Ping failed: %s", exc)
        sys.exit(1)


# ── place-order ───────────────────────────────────────────────────────

@cli.command("place-order")
@click.option("--symbol", required=True, help="Trading pair, e.g. BTCUSDT.")
@click.option(
    "--side",
    required=True,
    type=click.Choice(["BUY", "SELL"], case_sensitive=False),
    help="Order side.",
)
@click.option(
    "--type",
    "order_type",
    required=True,
    type=click.Choice(["MARKET", "LIMIT", "STOP_MARKET"], case_sensitive=False),
    help="Order type.",
)
@click.option("--quantity", required=True, type=str, help="Order quantity.")
@click.option("--price", default=None, type=str, help="Limit price (required for LIMIT orders).")
@click.option("--stop-price", default=None, type=str, help="Stop trigger price (required for STOP_MARKET orders).")
@click.option("--dry-run", is_flag=True, default=False, help="Print request details without submitting.")
@click.pass_context
def place_order(
    ctx: click.Context,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: str,
    stop_price: str,
    dry_run: bool,
) -> None:
    """Place a Market, Limit, or Stop-Market order on Binance Futures Testnet."""
    logger = ctx.obj["logger"]

    # ── Print request summary ─────────────────────────────────────────
    _print_separator()
    click.echo(_colour("  📋  ORDER REQUEST SUMMARY", CYAN + BOLD))
    _print_separator()
    click.echo(f"  Symbol     : {symbol.upper()}")
    click.echo(f"  Side       : {side.upper()}")
    click.echo(f"  Type       : {order_type.upper()}")
    click.echo(f"  Quantity   : {quantity}")
    click.echo(f"  Price      : {price or 'N/A (MARKET)'}")
    click.echo(f"  Stop Price : {stop_price or 'N/A'}")
    if dry_run:
        click.echo(_colour("\n  ⚠️   DRY-RUN — order NOT submitted.\n", YELLOW))
        return

    api_key, api_secret = _require_credentials(ctx)
    client = BinanceClient(api_key, api_secret)
    manager = OrderManager(client)

    logger.info(
        "CLI place-order — symbol=%s side=%s type=%s qty=%s price=%s stop_price=%s",
        symbol,
        side,
        order_type,
        quantity,
        price,
        stop_price,
    )

    result = manager.place_order(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        stop_price=stop_price,
    )

    _print_order_result(result)

    if not result.success:
        logger.error("Order submission failed: %s", result.error_message)
        sys.exit(1)

    logger.info("Order result: %s", json.dumps(result.raw, indent=2))


# ── entry point ───────────────────────────────────────────────────────

if __name__ == "__main__":
    cli(obj={})
