import logging
import sys
import structlog


def setup_logging():
    """
    Configures structured logging for the entire application.
    Logs will be output in JSON format to 'bot.log'.
    """
    # Configure the standard library logging to redirect to structlog
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        stream=sys.stdout,  # Redirect stdlib logs to stdout
    )

    # It defines the pipeline for how each log entry is handled.
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
        structlog.dev.ConsoleRenderer()  # Or JSONRenderer() for file logs
    ]
    # Define the structlog processor chain
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure a file handler to write logs to bot.log
    log_file = "bot.log"
    handler = logging.FileHandler(log_file)

    # The JSONRenderer produces a string, so a simple formatter is needed
    # to pass the message through to the file.
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)

    # Get the root logger and add our file handler
    root_logger = logging.getLogger()
    # Clear existing handlers to avoid duplicate logs
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    log = structlog.get_logger("binance_bot")
    log.info("Logging setup complete. Logs will be written to bot.log")
