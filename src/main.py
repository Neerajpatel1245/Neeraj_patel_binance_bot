import argparse
import sys
from src.logger import setup_logging
from src.client import get_binance_client
from src.validation import OrderValidator
from src.orders.market import place_market_order
from src.orders.limit import place_limit_order
from src.strategies.stop_limit import place_stop_limit_order
from src.strategies.oco import place_simulated_oco_order
from src.strategies.twap import execute_twap_strategy
from src.strategies.grid import setup_grid_strategy
from src.utils.sentiment import get_fear_and_greed_index


def main():
    # Setup logging as the first step
    setup_logging()

    parser = argparse.ArgumentParser(
        description="A CLI-based trading bot for Binance USDT-M Futures."
    )
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available commands"
    )

    # --- Market Order Parser ---
    market_parser = subparsers.add_parser(
        "market", help="Place a market order."
    )
    market_parser.add_argument(
        "--symbol", required=True, help="Trading symbol (e.g., BTCUSDT)"
    )
    market_parser.add_argument(
        "--side", required=True, choices=["BUY", "SELL"], help="Order side"
    )
    market_parser.add_argument(
        "--quantity", required=True, type=float, help="Order quantity"
    )
    market_parser.add_argument(
        "--use-sentiment-filter", action="store_true",
        help="Use Fear & Greed Index to filter trade"
    )

    # --- Limit Order Parser ---
    limit_parser = subparsers.add_parser("limit", help="Place a limit order.")
    limit_parser.add_argument("--symbol", required=True, help="Trading symbol")
    limit_parser.add_argument(
        "--side", required=True, choices=["BUY", "SELL"], help="Order side"
    )
    limit_parser.add_argument(
        "--quantity", required=True, type=float, help="Order quantity"
    )
    limit_parser.add_argument(
        "--price", required=True, type=float, help="Order price"
    )
    limit_parser.add_argument(
        "--use-sentiment-filter", action="store_true",
        help="Use Fear & Greed Index to filter trade"
    )

    # --- Stop-Limit Order Parser ---
    stop_limit_parser = subparsers.add_parser(
        "stop-limit", help="Place a stop-limit order."
    )
    stop_limit_parser.add_argument(
        "--symbol", required=True, help="Trading symbol"
    )
    stop_limit_parser.add_argument(
        "--side", required=True, choices=["BUY", "SELL"], help="Order side"
    )
    stop_limit_parser.add_argument(
        "--quantity", required=True, type=float, help="Order quantity"
    )
    stop_limit_parser.add_argument(
        "--price", required=True, type=float, help="Limit price for the order"
    )
    stop_limit_parser.add_argument(
        "--stop-price", required=True, type=float,
        help="Trigger price for the limit order"
    )

    # --- OCO Strategy Parser ---
    oco_parser = subparsers.add_parser(
        "oco", help="Place a simulated OCO (One-Cancels-the-Other) order."
    )
    oco_parser.add_argument(
        "--symbol", required=True, help="Trading symbol"
    )
    oco_parser.add_argument(
        "--side", required=True, choices=["BUY", "SELL"],
        help="Side to CLOSE the position (e.g., SELL for a long position)"
    )
    oco_parser.add_argument(
        "--quantity", required=True, type=float, help="Order quantity"
    )
    oco_parser.add_argument(
        "--take-profit", required=True, type=float,
        help="Take-profit trigger price"
    )
    oco_parser.add_argument(
        "--stop-loss", required=True, type=float,
        help="Stop-loss trigger price"
    )

    # --- TWAP Strategy Parser ---
    twap_parser = subparsers.add_parser(
        "twap", help="Execute a TWAP (Time-Weighted Average Price) strategy."
    )
    twap_parser.add_argument(
        "--symbol", required=True, help="Trading symbol"
    )
    twap_parser.add_argument(
        "--side", required=True, choices=["BUY", "SELL"], help="Order side"
    )
    twap_parser.add_argument(
        "--quantity", required=True, type=float, help="Total quantity to trade"
    )
    twap_parser.add_argument(
        "--duration", required=True, type=int, help="Total duration in minutes"
    )

    # --- Grid Strategy Parser ---
    grid_parser = subparsers.add_parser(
        "grid", help="Set up a grid trading strategy."
    )
    grid_parser.add_argument(
        "--symbol", required=True, help="Trading symbol"
    )
    grid_parser.add_argument(
        "--range-top", required=True, type=float,
        help="Upper price of the grid range"
    )
    grid_parser.add_argument(
        "--range-bottom", required=True, type=float,
        help="Lower price of the grid range"
    )
    grid_parser.add_argument(
        "--grids", required=True, type=int, help="Number of grid lines"
    )
    grid_parser.add_argument(
        "--quantity", required=True, type=float,
        help="Quantity to trade at each grid line"
    )

    args = parser.parse_args()

    try:
        client = get_binance_client()
        validator = OrderValidator(client)
    except Exception as e:
        print(f"Failed to start the bot: {e}")
        sys.exit(1)

    # --- Command Execution ---
    if args.command in ["market", "limit"]:
        if args.use_sentiment_filter:
            sentiment = get_fear_and_greed_index()
            if sentiment:
                classification = sentiment.get(
                    'value_classification', 'Neutral'
                ).lower()
                print(f"Current market sentiment: {classification.title()}")
                if args.side == 'BUY' and "fear" not in classification:
                    print(
                        "Sentiment filter active: Aborting BUY order because "
                        "market is not in 'Fear' or 'Extreme Fear'."
                    )
                    return
                if args.side == 'SELL' and "greed" not in classification:
                    print(
                        "Sentiment filter active: Aborting SELL order because "
                        "market is not in 'Greed' or 'Extreme Greed'."
                    )
                    return
            else:
                print(
                    "Could not fetch sentiment data. "
                    "Proceeding without filter."
                )

    if args.command == "market":
        if validator.validate_order_params(args.symbol, args.quantity):
            place_market_order(
                client, args.symbol, args.side, args.quantity
            )

    elif args.command == "limit":
        if validator.validate_order_params(
            args.symbol, args.quantity, args.price
        ):
            place_limit_order(
                client, args.symbol, args.side, args.quantity, args.price
            )

    elif args.command == "stop-limit":
        if validator.validate_order_params(
            args.symbol, args.quantity, args.price
        ):
            place_stop_limit_order(
                client, args.symbol, args.side, args.quantity,
                args.price, args.stop_price
            )

    elif args.command == "oco":
        place_simulated_oco_order(
            client, args.symbol, args.side, args.quantity,
            args.take_profit, args.stop_loss
        )

    elif args.command == "twap":
        execute_twap_strategy(
            client, args.symbol, args.side, args.quantity, args.duration
        )

    elif args.command == "grid":
        setup_grid_strategy(
            client, args.symbol, args.range_top, args.range_bottom,
            args.grids, args.quantity
        )


if __name__ == "__main__":
    main()
