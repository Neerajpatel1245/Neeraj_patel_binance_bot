import sys
import os
import csv
import structlog

log = structlog.get_logger()
PROJECT_ROOT = os.path.abspath(
        os.path.join(os.getcwd(), '..', '..'))
CSV_FILE_PATH = os.path.join(PROJECT_ROOT, 'data', 'historical_data.csv')


def load_and_validate_data(filename=CSV_FILE_PATH):
    """
    Loads trade data from a specified CSV file, validates that it contains
    all necessary columns, and returns the data as a list of dictionaries.

    Args:
        filename (str): The path to the CSV file.

    Returns:
        list[dict] | None: A list of dictionaries, where each dictionary
                          represents a row of trade data. Returns None if
                          the file is not found or if validation fails.
    """
    print(f"Attempting to load data from '{filename}'...")

    # 1. Initialize `required_columns`
    # This list is initialized with the actual column names from your CSV
    # that are essential for any meaningful trade analysis or reporting.
    required_columns = [
        "Timestamp IST",
        "Coin",
        "Side",
        "Execution Price",
        "Size Tokens",
        "Size USD",
        "Closed PnL"
    ]

    try:
        with open(filename, mode='r', encoding='utf-8') as infile:
            # Using csv.DictReader is best practice as it maps data to
            # headers automatically
            reader = csv.DictReader(infile)

            # --- Validation Step ---
            actual_headers = reader.fieldnames

            # If there are no headers, abort early to avoid passing
            # None to set()
            if actual_headers is None:
                msg = (
                    f"Error: The CSV file '{filename}' is missing "
                    "a header row."
                )
                print(msg, file=sys.stderr)
                return None

            # Check if the set of required columns is a subset
            # of the actual headers
            if not set(required_columns).issubset(set(actual_headers)):
                missing_columns = set(required_columns) - set(actual_headers)
                print(
                    f"Error: The CSV file '{filename}' is missing the"
                    f"following required columns: {list(missing_columns)}",
                    file=sys.stderr
                )
                return None

            # --- Data Loading Step ---
            # Convert the reader object to a list of dictionaries
            data = [row for row in reader]

            if not data:
                print(
                    f"Warning: The file '{filename}' is empty or contains"
                    "only a header row."
                    )
                return []

            print(
                f"Successfully loaded and validated {len(data)} trade records."
                )
            return data

    except FileNotFoundError:
        print(
            f"Error: The file '{filename}' was not found."
            " Please ensure it's in the correct directory.",
            file=sys.stderr
            )
        raise
    except Exception as e:
        print(
            f"An unexpected error occurred while reading the file: {e}",
            file=sys.stderr
            )
        raise
