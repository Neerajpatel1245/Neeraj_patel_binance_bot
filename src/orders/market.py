# src/orders/market.py

from binance.client import Client
from binance.exceptions import BinanceAPIException
import structlog

log = structlog.get_logger()


def place_market_order(
        client: Client,
        symbol: str,
        side: str,
        quantity: float
        ):
    """
    Places a market order on Binance Futures.

    :param client: The Binance client instance.
    :param symbol: The trading symbol (e.g., 'BTCUSDT').
    :param side: 'BUY' or 'SELL'.
    :param quantity: The amount to trade.
    """
    local_log = log.bind(
        symbol=symbol,
        side=side,
        quantity=quantity,
        order_type='MARKET'
    )
    local_log.info("Attempting to place market order.")

    try:
        order = client.futures_create_order(
            symbol=symbol,
            side=side.upper(),
            type=Client.ORDER_TYPE_MARKET,
            quantity=quantity
        )
        local_log.info(
            "Market order placed successfully.",
            order_id=order.get('orderId'),
            client_order_id=order.get('clientOrderId'),
            status=order.get('status')
        )
        print("Market order placed successfully:", order)
        return order
    except BinanceAPIException as e:
        local_log.error(
            "Failed to place market order due to API error.",
            error_code=e.code,
            error_message=e.message,
            exc_info=True
        )
        print(f"Error placing market order: {e}")
        return None
    except Exception as e:
        local_log.error(
            "An unexpected error occurred while placing market order.",
            error=str(e),
            exc_info=True
        )
        print(f"An unexpected error occurred: {e}")
        return None
