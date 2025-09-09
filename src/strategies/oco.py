# src/strategies/oco.py

from binance.client import Client
from binance.exceptions import BinanceAPIException
import structlog

log = structlog.get_logger()


def place_simulated_oco_order(
        client: Client,
        symbol: str,
        side: str,
        quantity: float,
        take_profit_price: float,
        stop_loss_price: float
        ):
    """
    Simulates an OCO (One-Cancels-the-Other) order for Binance Futures.
    This is not a native OCO order. It places two separate orders:
    1. A TAKE_PROFIT_MARKET order.
    2. A STOP_MARKET order.
    Both orders use `reduceOnly=True` to ensure they only close a position.

    A separate monitoring system would be needed to cancel the remaining order
    once one of them is filled.

    :param client: The Binance client instance.
    :param side: The side of the orders to CLOSE the position
        (e.g., 'SELL' for a long position).
    :param quantity: The amount to trade.
    :param take_profit_price: The price to trigger the take-profit order.
    :param stop_loss_price: The price to trigger the stop-loss order.
    """
    local_log = log.bind(
        symbol=symbol,
        side=side,
        quantity=quantity,
        take_profit_price=take_profit_price,
        stop_loss_price=stop_loss_price,
        strategy='SIMULATED_OCO'
    )
    local_log.info("Attempting to place simulated OCO orders.")

    orders_placed = []

    try:
        # Place Take-Profit order
        local_log.info("Placing TAKE_PROFIT_MARKET order.")
        tp_order = client.futures_create_order(
            symbol=symbol,
            side=side.upper(),
            type='TAKE_PROFIT_MARKET',
            stopPrice=take_profit_price,
            quantity=quantity,
            reduceOnly=True
        )
        local_log.info(
            "Take-profit order placed.",
            order_id=tp_order.get('orderId')
        )
        orders_placed.append(tp_order)
        print("Take-profit order placed:", tp_order)

    except BinanceAPIException as e:
        local_log.error(
            "Failed to place take-profit order.",
            error_code=e.code,
            error_message=e.message
        )
        print(f"Error placing take-profit order: {e}")
        # If TP fails, we don't place the SL to avoid a dangling order
        return None

    try:
        # Place Stop-Loss order
        local_log.info("Placing STOP_MARKET order.")
        sl_order = client.futures_create_order(
            symbol=symbol,
            side=side.upper(),
            type='STOP_MARKET',
            stopPrice=stop_loss_price,
            quantity=quantity,
            reduceOnly=True
        )
        local_log.info(
            "Stop-loss order placed.",
            order_id=sl_order.get('orderId')
        )
        orders_placed.append(sl_order)
        print("Stop-loss order placed:", sl_order)

    except BinanceAPIException as e:
        local_log.error(
            "Failed to place stop-loss order.",
            error_code=e.code,
            error_message=e.message
        )
        print(f"Error placing stop-loss order: {e}")
        # If SL fails, we should try to cancel the TP order we just placed
        try:
            client.futures_cancel_order(
                symbol=symbol,
                orderId=tp_order.get('orderId')
            )
            local_log.warning(
                "Successfully cancelled the orphaned take-profit order."
            )
            print("Cancelled the take-profit order as the stop-loss failed.")
        except BinanceAPIException as cancel_e:
            local_log.error(
                "Failed to cancel the orphaned take-profit order.",
                error=str(cancel_e)
            )
            print(
                f"CRITICAL: Failed to cancel take-profit order "
                f"{tp_order.get('orderId')}. "
                "Please cancel it manually."
            )
        return None

    local_log.info(
        "Simulated OCO orders placed successfully. "
        "A monitoring system is required to manage cancellation."
    )
    print(
        "\nIMPORTANT: Both Take-Profit and Stop-Loss orders "
        "have been placed."
    )
    print(
        "You must monitor these orders. When one is filled, "
        "you must manually cancel the other."
    )

    return orders_placed
