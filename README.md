# Binance Futures Order Bot
This is a comprehensive, CLI-based trading bot for the Binance USDT-M Futures market. It is designed with a professional, modular architecture and includes robust validation, structured logging, and a suite of advanced trading strategies.

## Features
- **Market Orders:** Execute orders immediately at the current best market price.

- **Limit Orders:** Place orders that execute only at a specified price or better.

- **Stop-Limit Orders:** Place a limit order automatically when a specific stop price is reached.

- **Simulated OCO (One-Cancels-the-Other):** Place a take-profit and a stop-loss order simultaneously. If one is filled, a monitoring system (to be implemented by the user) would cancel the other.

- **TWAP (Time-Weighted Average Price):** Execute a large order by breaking it into smaller, randomized chunks over a specified duration to minimize market impact.

- **Grid Trading:** Automate a buy-low, sell-high strategy by placing a grid of buy and sell limit orders within a defined price range.

- **Sentiment Analysis Filter:** An optional --use-sentiment-filter flag on core orders uses the Crypto Fear & Greed Index to inform trading decisions (e.g., only buy in a "Fearful" market).

- **Strategy Backtesting:** Includes a backtesting module using backtesting.py to empirically test the performance of the Grid strategy on historical data.


## Project Structure

The project is organized in a clean, modular structure to ensure maintainability and clarity.

```
your-name-binance-bot/
├──.env                  # Secure API keys and configuration (must be created)
├──.gitignore            # Specifies files for Git to ignore
├── README.md             # This file
├── requirements.txt      # Project dependencies
├── bot.log               # Log file for all bot activities
└── src/
    ├── __init__.py
    ├── main.py           # Main CLI entry point
    ├── client.py         # Binance API client setup
    ├── logger.py         # Structured logging configuration
    ├── validation.py     # Pre-flight order validation logic
    ├── orders/           # Package for core order types
    │   ├── __init__.py
    │   ├── market.py
    │   └── limit.py
    ├── strategies/       # Package for advanced trading strategies
    │   ├── __init__.py
    │   ├── stop_limit.py
    │   ├── oco.py
    │   ├── twap.py
    │   └── grid.py
    └── utils/            # Utility functions
        ├── __init__.py
        └── sentiment.py  # Fear & Greed Index API utility
└── tests/
    ├── __init__.py
    └── backtesting/      # Strategy backtesting module
        ├── __init__.py
        ├── data_loader.py
        └── test_strategies.py
└── data/
    └── historical_data.csv
```



### Install Dependencies
Install all the required Python packages using the `requirements.txt` file.
```bash
pip install -r requirements.txt
```

### Configure API Keys
The bot requires Binance API keys to interact with your account. These should be stored securely in a `.env` file.

1.  **Create the `.env` file** in the root directory of the project. You can copy the example below.
2.  **Generate API Keys on Binance**:
    - Log in to your **Binance Testnet** account: [https://testnet.binancefuture.com/](https://testnet.binancefuture.com/)
    - **IMPORTANT**: For development and testing, **always use the Testnet** to avoid risking real funds.
    - Navigate to the API Management section and create a new API key.
    - Ensure that "Enable Futures" permissions are checked.
3.  **Populate the `.env` file**: Open the `.env` file and replace the placeholder values with your actual Testnet API Key and Secret.

**`.env` file content:**
```env
# -------------------------------------------------
# Binance API Credentials
# Replace with your actual API keys from Binance Testnet
# -------------------------------------------------
BINANCE_API_KEY="YOUR_TESTNET_API_KEY_HERE"
BINANCE_API_SECRET="YOUR_TESTNET_API_SECRET_HERE"

# Set to "True" to use the Binance Testnet, "False" for the live market.
# ALWAYS use "True" for development and testing.
USE_TESTNET="True"
```

## How to Use the Bot

All commands are executed through the main entry point `src/main.py`. The interface is designed to be intuitive and self-documenting.

### General Help
To see all available commands or get help for a specific command:
```bash
# See all commands
python -m src.main --help

# Get help for the 'market' command
python -m src.main market --help
```

### Core Orders

#### Market Order
Places an order that executes immediately at the current market price.
```bash
python -m src.main market --symbol BTCUSDT --side BUY --quantity 0.001
```

#### Limit Order
Places an order that executes only when the market price reaches your specified price.
```bash
python -m src.main limit --symbol BTCUSDT --side SELL --quantity 0.001 --price 65000
```

#### Using the Sentiment Filter (Optional)
You can add the `--use-sentiment-filter` flag to `market` or `limit` orders. This will only execute the order if the market sentiment is favorable (buy on fear, sell on greed), based on the Crypto Fear & Greed Index.[5]
```bash
python -m src.main market --symbol BTCUSDT --side BUY --quantity 0.001 --use-sentiment-filter
```

### Advanced Strategies

#### Stop-Limit Order
Places a limit order to BUY 0.1 ETH at $3000 only when the price reaches the stop price of $2990.
```bash
python -m src.main stop-limit --symbol ETHUSDT --side BUY --quantity 0.1 --price 3000 --stop-price 2990
```

#### Simulated OCO (One-Cancels-the-Other) Order
Places a take-profit order at $68,000 and a stop-loss order at $62,000 for a 0.01 BTC position. Both orders are `reduceOnly`, meaning they can only close an existing position.
**Note**: This is a simulated OCO. After one order is filled, the other must be cancelled manually.
```bash
python -m src.main oco --symbol BTCUSDT --side SELL --quantity 0.01 --take-profit 68000 --stop-loss 62000
```

#### TWAP (Time-Weighted Average Price) Strategy
Executes a total order to BUY 1 BTC over 60 minutes by placing smaller, randomized orders at regular intervals to reduce market impact.
```bash
python -m src.main twap --symbol BTCUSDT --side BUY --quantity 1 --duration 60
```

#### Grid Trading Strategy
Sets up an initial grid of 10 buy/sell limit orders for ETHUSDT between $2500 and $3500, with 0.05 ETH per order. This strategy profits from market volatility.
**Note**: This command only sets up the initial grid. A long-running monitoring process would be needed to replace filled orders to keep the strategy active.
```bash
python -m src.main grid --symbol ETHUSDT --range-top 3500 --range-bottom 2500 --grids 10 --quantity 0.05
```

## Additional Modules

### Backtesting
To run the backtest for the Grid strategy, you first need to download the historical data.

1.  **Download Sample Data**: Use the historical data link provided in the assignment resources.
2.  **Create `data` Folder**: Create a folder named `data` in the project's root directory.
3.  **Place Data File**: Place the downloaded CSV file inside `data/`, for example: `data/historical_data.csv`.
4.  **Run the Backtesting Script**:
    ```bash
    python tests/backtesting/test_strategies.py
    ```
    This will run a simulation and an optimization
