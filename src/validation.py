from binance.client import Client
from binance.exceptions import BinanceAPIException
from decimal import Decimal, ROUND_DOWN
import structlog
from typing import Optional

log = structlog.get_logger()


class OrderValidator:
    """
    A class to validate order parameters against Binance's exchange rules.
    It fetches and caches the rules to avoid repeated API calls.
    """
    def __init__(self, client: Client):
        self.client = client
        self.exchange_info = None
        self._fetch_exchange_info()

    def _fetch_exchange_info(self):
        """Fetches and caches exchange information."""
        try:
            log.info("Fetching exchange information for validation...")
            self.exchange_info = self.client.futures_exchange_info()
            log.info("Successfully fetched exchange information.")
        except BinanceAPIException as e:
            log.error("Failed to fetch exchange info.", error=str(e))
            self.exchange_info = None

    def get_symbol_info(self, symbol: str):
        """Retrieves the trading rules for a specific symbol."""
        if not self.exchange_info:
            log.warning("Exchange info not available, skipping validation.")
            return None

        for s in self.exchange_info['symbols']:
            if s['symbol'] == symbol:
                return s
        return None

    def validate_order_params(
            self,
            symbol: str,
            quantity: float,
            price: Optional[float] = None) -> bool:
        """
        Validates quantity and price against the symbol's trading rules.
        Returns True if valid, False otherwise.
        """
        symbol_info = self.get_symbol_info(symbol)
        if not symbol_info:
            log.error("Symbol not found in exchange info.", symbol=symbol)
            return False

        filters = {f['filterType']: f for f in symbol_info['filters']}
        # Validate quantity against LOT_SIZE filter
        lot_size_filter = filters.get('LOT_SIZE')
        if lot_size_filter:
            min_qty = Decimal(lot_size_filter['minQty'])
            max_qty = Decimal(lot_size_filter['maxQty'])
            step_size = Decimal(lot_size_filter['stepSize'])

            if Decimal(str(quantity)) < min_qty:
                log.error(
                    "Quantity is too small.",
                    quantity=quantity,
                    min_qty=str(min_qty)
                    )
                return False
            if Decimal(str(quantity)) > max_qty:
                log.error("Quantity is too large.",
                          quantity=quantity,
                          max_qty=str(max_qty)
                          )
                return False

            # Check if quantity conforms to step size
            base_qty = Decimal(str(quantity)) - min_qty
            if base_qty % step_size != 0:
                log.error(
                    "Invalid quantity precision.",
                    quantity=quantity,
                    step_size=str(step_size))
                # Suggest a valid quantity
                quantized = base_qty.quantize(step_size, rounding=ROUND_DOWN)
                valid_qty = quantized + min_qty
                log.info(f"A valid quantity might be: {valid_qty}")
                return False

        # Validate price against PRICE_FILTER if provided
        if price is not None:
            price_filter = filters.get('PRICE_FILTER')
            if price_filter:
                min_price = Decimal(price_filter['minPrice'])
                max_price = Decimal(price_filter['maxPrice'])
                tick_size = Decimal(price_filter['tickSize'])

                if Decimal(str(price)) < min_price:
                    log.error("Price is too low.",
                              price=price,
                              min_price=str(min_price))
                    return False
                if Decimal(str(price)) > max_price and max_price > 0:
                    # max_price can be 0
                    log.error("Price is too high.",
                              price=price,
                              max_price=str(max_price))
                    return False

                # Check if price conforms to tick size
                if (Decimal(str(price)) - min_price) % tick_size != 0:
                    log.error("Invalid price precision (tick size).",
                              price=price, tick_size=str(tick_size))
                    return False

        log.info("Order parameters are valid.",
                 symbol=symbol, quantity=quantity, price=price)
        return True
