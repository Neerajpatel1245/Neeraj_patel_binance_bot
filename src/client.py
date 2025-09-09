import os
from dotenv import load_dotenv
from binance.client import Client
import structlog

log = structlog.get_logger()


def get_binance_client() -> Client:
    """
    Initializes and returns a Binance client instance.
    - Loads API keys from the.env file.
    - Sets the client to use the Testnet based on the
        USE_TESTNET environment variable.
    """
    load_dotenv()
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    use_testnet_str = os.getenv("USE_TESTNET", "True").lower()
    use_testnet = use_testnet_str in ['true', '1', 't']

    if not api_key or not api_secret:
        log.error(
            "Binance API key or secret not found. "
            "Please set them in the .env file."
        )
        raise ValueError("API key/secret not configured.")

    log.info("Initializing Binance client...", testnet=use_testnet)

    try:
        client = Client(api_key, api_secret, testnet=use_testnet)
        # Test connection
        client.futures_ping()
        log.info("Binance client initialized and connection successful.")
        return client
    except Exception as e:
        log.error("Failed to initialize Binance client.", error=str(e))
        raise
