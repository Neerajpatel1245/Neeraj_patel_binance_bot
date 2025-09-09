import sys
import os
import pandas as pd


# --- DYNAMIC PATH CORRECTION ---
try:
    PROJECT_ROOT = os.path.abspath(
        os.path.join(os.getcwd()))
    SRC_PATH = os.path.join(PROJECT_ROOT, 'src')
    if SRC_PATH not in sys.path:
        sys.path.insert(0, SRC_PATH)
    from data_loader import load_and_validate_data
except ImportError:
    print(
        "Error: Could not import 'data_loader'. "
        "Please ensure 'tests/backtesting/data_loader.py' exists."
        )
    sys.exit(1)

# --- CONFIGURATION ---
CSV_FILE = os.path.join(PROJECT_ROOT, 'data', 'historical_data.csv')


# --- ADVANCED AUTOMATED ORDER CLASS ---
class Order:
    """An advanced, stateful Order class for automated execution."""
    def __init__(
            self,
            order_type,
            side,
            quantity,
            price=None,
            trigger_price=None
            ):
        self.order_type = order_type.upper()
        self.side = side.upper()
        self.quantity = quantity
        self.price = price
        self.trigger_price = trigger_price
        self.status = 'PENDING'
        self.created_at = None
        self.filled_at = None
        self.filled_price = None
        self.oco_peer = None
        self._validate()

    def _validate(self):
        if self.order_type in ['LIMIT', 'STOP_LIMIT'] and self.price is None:
            raise ValueError("LIMIT/STOP_LIMIT orders require a 'price'.")
        if self.order_type == 'STOP_LIMIT' and self.trigger_price is None:
            raise ValueError("STOP_LIMIT orders require a 'trigger_price'.")

    def __repr__(self):
        return (
            f"<Order | {self.status} {self.order_type} "
            f"{self.side} {self.quantity} "
            f"@ LMT:{self.price}/"
            f"TRG:{self.trigger_price}>"
        )

    def link_oco_peer(self, peer_order):
        self.oco_peer = peer_order
        peer_order.oco_peer = self

    def update(self, timestamp, current_price):
        if self.is_done:
            return
        if self.created_at is None:
            self.created_at = timestamp

        if self.order_type == 'STOP_LIMIT' and self.status == 'PENDING':
            if (self.is_buy and current_price >= self.trigger_price) or \
               (self.is_sell and current_price <= self.trigger_price):
                self.status = 'ACTIVE'
                print(f"{timestamp} - ACTIVATED: {self}")

        is_active = self.status == 'ACTIVE' or self.order_type == 'LIMIT'
        if is_active:
            if (self.is_buy and current_price <= self.price) or \
               (self.is_sell and current_price >= self.price):
                self.fill(timestamp, current_price)

    def fill(self, timestamp, fill_price):
        if self.status == 'FILLED':
            return
        self.status = 'FILLED'
        self.filled_at = timestamp
        self.filled_price = fill_price
        print(f"{timestamp} - FILLED: {self}")
        if self.oco_peer:
            self.oco_peer.cancel(timestamp)

    def cancel(self, timestamp):
        if self.is_done:
            return
        self.status = 'CANCELLED'
        print(f"{timestamp} - CANCELLED: {self}")

    @property
    def is_buy(self):
        return self.side == 'BUY'

    @property
    def is_sell(self):
        return self.side == 'SELL'

    @property
    def is_done(self):
        return self.status in ['FILLED', 'CANCELLED']


# --- BACKTESTER CLASS ---
class Backtester:
    def __init__(self, initial_cash=10000.0):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.position_size = 0.0
        self.trade_log = []
        self._orders = []

    def place_oco_order(self, quantity, take_profit_price, stop_loss_price):
        tp = Order('LIMIT', 'SELL', quantity, price=take_profit_price)
        sl = Order(
            'STOP_LIMIT',
            'SELL',
            quantity,
            price=stop_loss_price,
            trigger_price=stop_loss_price)
        tp.link_oco_peer(sl)
        self._orders.extend([tp, sl])
        print(
            f"Placed OCO: TP @ ${take_profit_price}, SL @ ${stop_loss_price}"
            )

    def run(self, data):
        print("\n--- Starting Backtest ---")
        initial_buy_price = data['Execution Price'].iloc[0]
        self.position_size = 1.0
        self.cash -= initial_buy_price * self.position_size
        print(f"Simulating initial BUY of 1.0 unit @ ${initial_buy_price:.2f}")

        tp_price = initial_buy_price * 1.05
        sl_price = initial_buy_price * 0.98
        self.place_oco_order(1.0, tp_price, sl_price)

        for i in range(len(data)):
            current_price = data['Execution Price'].iloc[i]
            timestamp = data['Timestamp IST'].iloc[i]

            for order in self._orders:
                order.update(timestamp, current_price)
                if order.status == 'FILLED':
                    self._execute_fill(order)

            self._orders = [o for o in self._orders if not o.is_done]

        print("--- Backtest Finished ---\n")

    def _execute_fill(self, order):
        if order.is_buy:
            self.cash -= order.filled_price * order.quantity
            self.position_size += order.quantity
        elif order.is_sell:
            self.cash += order.filled_price * order.quantity
            self.position_size -= order.quantity
        self.trade_log.append({
            "Timestamp": order.filled_at,
            "Type": order.side,
            "Price": order.filled_price
            })

    def print_results(self, data):
        last_price = data['Execution Price'].iloc[-1]
        final_val = self.cash + (self.position_size * last_price)
        pnl = final_val - self.initial_cash
        pnl_pct = (pnl / self.initial_cash) * 100
        print("--- Backtest Results ---")
        print(f"Final Portfolio Value: ${final_val:,.2f}")
        print(f"Total PnL:             ${pnl:,.2f} ({pnl_pct:.2f}%)")
        print(f"Trades Filled:         {len(self.trade_log)}")
        print("------------------------")


def main():
    trade_data = load_and_validate_data(CSV_FILE)
    if not trade_data:
        return

    df = pd.DataFrame(trade_data)
    df['Execution Price'] = pd.to_numeric(df['Execution Price'])
    df['Timestamp IST'] = pd.to_datetime(
        df['Timestamp IST'],
        format='%d-%m-%Y %H:%M'
        )
    df = df.sort_values(by='Timestamp IST').reset_index(drop=True)

    backtester = Backtester(initial_cash=10000.0)
    backtester.run(df)
    backtester.print_results(df)


if __name__ == "__main__":
    main()
