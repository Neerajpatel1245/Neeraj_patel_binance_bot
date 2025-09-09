import time
import random
from binance.client import Client
from binance.exceptions import BinanceAPIException
import structlog

log = structlog.get_logger()


def execute_twap_strategy(
        client: Client,
        symbol: str,
        side: str,
        total_quantity: float,
        duration_minutes: int
        ):
    """
    Executes a TWAP (Time-Weighted Average Price) strategy.
    It splits the total quantity into smaller, randomized chunks and
    executes them at randomized intervals over the specified duration.

    :param client: The Binance client instance.
    :param symbol: The trading symbol.
    :param side: 'BUY' or 'SELL'.
    :param total_quantity: The total amount to trade.
    :param duration_minutes:The total duration in minutes to execute the order.
    """
    local_log = log.bind(
        strategy='TWAP',
        symbol=symbol,
        side=side,
        total_quantity=total_quantity,
        duration_minutes=duration_minutes
    )
    local_log.info("Starting TWAP strategy.")
    print(f"Starting TWAP strategy for {total_quantity} "
          f"{symbol} over {duration_minutes} minutes.")

    # Define the number of intervals (e.g., one order every 30 seconds)
    interval_seconds = 30
    num_intervals = (duration_minutes * 60) // interval_seconds

    if num_intervals == 0:
        log.error(
            "Duration is too short for any intervals. "
            "Minimum duration is 1 minute for a 30s interval."
            )
        print(
            "Error: Duration is too short. Please provide a longer duration."
            )
        return

    quantity_per_interval = total_quantity / num_intervals

    executed_quantity = 0.0
    start_time = time.time()
    end_time = start_time + duration_minutes * 60

    for i in range(num_intervals):
        if time.time() > end_time:
            local_log.warning(
                "TWAP duration ended before all orders could be placed."
                )
            break

        # Randomize quantity (+/- 20%) to make it less predictable
        rand_factor_qty = random.uniform(0.8, 1.2)
        order_quantity = quantity_per_interval * rand_factor_qty

        # Ensure we don't exceed the total quantity
        if executed_quantity + order_quantity > total_quantity:
            order_quantity = total_quantity - executed_quantity

        # Ensure the quantity is valid before placing the order
        # NOTE: A full implementation would use the OrderValidator here.
        # For simplicity, we'll just format it to a reasonable precision.
        order_quantity_str = f"{order_quantity:.3f}"

        local_log.info(
            "Placing TWAP child order.",
            interval=i+1,
            num_intervals=num_intervals,
            order_quantity=float(order_quantity_str)
        )

        try:
            client.futures_create_order(
                symbol=symbol,
                side=side.upper(),
                type=Client.ORDER_TYPE_MARKET,
                quantity=order_quantity_str
            )
            executed_quantity += float(order_quantity_str)
            print(
                f"Interval {i+1}/{num_intervals}: Placed "
                f"market {side} order for {order_quantity_str} {symbol}."
                )
        except BinanceAPIException as e:
            local_log.error(
                "Failed to place TWAP child order.",
                error_code=e.code,
                error_message=e.message
            )
            print(f"Error placing order in interval {i+1}: {e}")
            # Decide whether to continue or stop on error
            continue

        if executed_quantity >= total_quantity:
            local_log.info("Total quantity has been executed.")
            break

        # Randomize sleep time (+/- 20%)
        rand_factor_time = random.uniform(0.8, 1.2)
        sleep_duration = interval_seconds * rand_factor_time
        time.sleep(sleep_duration)

    local_log.info(
        "TWAP strategy finished.",
        executed_quantity=executed_quantity,
        total_quantity=total_quantity
    )
    print(
        f"\nTWAP strategy finished. Total executed: "
        f"{executed_quantity}/{total_quantity} {symbol}."
        )
