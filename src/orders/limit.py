# src/orders/limit.py

from binance.client import Client
from binance.exceptions import BinanceAPIException
import structlog

log = structlog.get_logger()


def place_limit_order(
    client: Client,
    symbol: str,
    side: str,
    quantity: float,
    price: float
):
    """
    Places a limit order on Binance Futures.

    :param client: The Binance client instance.
    :param symbol: The trading symbol (e.g., 'BTCUSDT').
    :param side: 'BUY' or 'SELL'.
    :param quantity: The amount to trade.
    :param price: The price at which to execute the order.
    """
    local_log = log.bind(
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=price,
        order_type='LIMIT'
    )
    local_log.info("Attempting to place limit order.")

    try:
        order = client.futures_create_order(
            symbol=symbol,
            side=side.upper(),
            type=Client.ORDER_TYPE_LIMIT,
            timeInForce=Client.TIME_IN_FORCE_GTC,  # Good 'Til Canceled
            quantity=quantity,
            price=price
        )
        local_log.info(
            "Limit order placed successfully.",
            order_id=order.get('orderId'),
            client_order_id=order.get('clientOrderId'),
            status=order.get('status')
        )
        print("Limit order placed successfully:", order)
        return order
    except BinanceAPIException as e:
        local_log.error(
            "Failed to place limit order due to API error.",
            error_code=e.code,
            error_message=e.message,
            exc_info=True
        )
        print(f"Error placing limit order: {e}")
        return None
    except Exception as e:
        local_log.error(
            "An unexpected error occurred while placing limit order.",
            error=str(e),
            exc_info=True
        )
        print(f"An unexpected error occurred: {e}")
        return None
