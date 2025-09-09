from binance.client import Client
from binance.exceptions import BinanceAPIException
import numpy as np
import structlog

log = structlog.get_logger()


def setup_grid_strategy(
        client: Client,
        symbol: str,
        range_top: float,
        range_bottom: float,
        num_grids: int,
        quantity_per_grid: float
        ):
    """
    Sets up the initial grid of limit orders for a grid trading strategy.
    This function places a series of buy orders below the current price and
    sell orders above the current price.

    A separate, long-running process would be needed to monitor these orders
    and replace them as they get filled.

    :param client: The Binance client instance.
    :param symbol: The trading symbol.
    :param range_top: The upper price of the grid range.
    :param range_bottom: The lower price of the grid range.
    :param num_grids: The number of grid lines.
    :param quantity_per_grid: The quantity to trade at each grid line.
    """
    local_log = log.bind(
        strategy='GRID_SETUP',
        symbol=symbol,
        range_top=range_top,
        range_bottom=range_bottom,
        num_grids=num_grids,
        quantity_per_grid=quantity_per_grid
    )
    local_log.info("Setting up grid trading strategy.")
    print("--- Setting up Grid Trading Strategy ---")

    if range_bottom >= range_top:
        log.error(
            "Grid range is invalid: bottom price must be lower "
            "than top price."
        )
        print("Error: Bottom price must be lower than top price.")
        return

    try:
        # Get current market price to distinguish between buy and sell grids
        ticker = client.futures_symbol_ticker(symbol=symbol)
        current_price = float(ticker['price'])
        local_log.info("Fetched current price.", current_price=current_price)
        print(f"Current price for {symbol}: {current_price}")
    except BinanceAPIException as e:
        local_log.error("Failed to fetch current price.", error=str(e))
        print(f"Error fetching current price: {e}")
        return

    # Create the grid levels using a linear space
    grid_levels = np.linspace(range_bottom, range_top, num_grids)

    buy_orders_placed = 0
    sell_orders_placed = 0

    print("\nPlacing grid orders...")
    for level in grid_levels:
        # Format to avoid scientific notation; might need adjustment.
        price_str = f"{level:.3f}"

        # NOTE: A full implementation would use the
        # OrderValidator here to ensure
        # the price and quantity match the symbol's precision rules.

        if level < current_price:
            # Place a BUY limit order
            side = 'BUY'
        elif level > current_price:
            # Place a SELL limit order
            side = 'SELL'
        else:
            # Skip the level closest to the current price
            # to avoid immediate execution
            local_log.info(
                "Skipping grid level too close to current price.",
                level=level
            )
            continue

        try:
            client.futures_create_order(
                symbol=symbol,
                side=side,
                type=Client.ORDER_TYPE_LIMIT,
                timeInForce=Client.TIME_IN_FORCE_GTC,
                quantity=quantity_per_grid,
                price=price_str
            )
            local_log.info(
                "Placed grid order.",
                side=side,
                price=price_str,
                quantity=quantity_per_grid
            )
            print(f"  - Placed {side} order at {price_str}")
            if side == 'BUY':
                buy_orders_placed += 1
            else:
                sell_orders_placed += 1
        except BinanceAPIException as e:
            local_log.error(
                "Failed to place grid order.",
                side=side,
                price=price_str,
                error_code=e.code,
                error_message=getattr(e, "message", str(e))
            )
            err_msg = getattr(e, "message", str(e))
            print(
                f"  - FAILED to place {side} order at {price_str}: "
                f"{err_msg}"
            )

    print("\n--- Grid Setup Complete ---")
    print(f"Total Buy Orders Placed: {buy_orders_placed}")
    print(f"Total Sell Orders Placed: {sell_orders_placed}")
    print("\nIMPORTANT: This script only sets up the initial grid.")
    print(
        "A long-running monitoring process is required to replace "
        "filled orders to keep the strategy active."
    )
