# src/strategies/stop_limit.py

from binance.client import Client
from binance.exceptions import BinanceAPIException
import structlog

log = structlog.get_logger()


def place_stop_limit_order(
    client: Client,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    stop_price: float,
):
    """
    Places a stop-limit order on Binance Futures.
    This order places a limit order when the stop_price is reached.

    :param client: The Binance client instance.
    :param symbol: The trading symbol.
    :param side: 'BUY' or 'SELL'.
    :param quantity: The amount to trade.
    :param price: The price of the limit order to be placed.
    :param stop_price: The price that triggers the limit order.
    """
    local_log = log.bind(
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=price,
        stop_price=stop_price,
        order_type='STOP_LIMIT'
    )
    local_log.info("Attempting to place stop-limit order.")

    try:
        # For Futures, the correct type is 'STOP' for a stop-limit order.
        # The 'price' is the limit price, and 'stopPrice' is the trigger.
        order = client.futures_create_order(
            symbol=symbol,
            side=side.upper(),
            type='STOP',
            timeInForce=Client.TIME_IN_FORCE_GTC,
            quantity=quantity,
            price=price,
            stopPrice=stop_price
        )
        local_log.info(
            "Stop-limit order placed successfully.",
            order_id=order.get('orderId'),
            status=order.get('status')
        )
        print("Stop-limit order placed successfully:", order)
        return order
    except BinanceAPIException as e:
        local_log.error(
            "Failed to place stop-limit order due to API error.",
            error_code=e.code,
            error_message=e.message,
            exc_info=True
        )
        print(f"Error placing stop-limit order: {e}")
        return None
    except Exception as e:
        local_log.error(
            "An unexpected error occurred while placing stop-limit order.",
            error=str(e),
            exc_info=True
        )
        print(f"An unexpected error occurred: {e}")
        return None
