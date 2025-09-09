# src/utils/sentiment.py

import requests
import structlog
from typing import Optional, Dict, Any

log = structlog.get_logger()


def get_fear_and_greed_index() -> Optional[Dict[str, Any]]:
    """
    Fetches the latest Crypto Fear & Greed Index from the alternative.me API.

    return: A dictionary containing the index data, or None if the
    request fails.Example: {'value': '55', 'value_classification': 'Greed',...}
    """
    url = "https://api.alternative.me/fng/?limit=1"
    log.info("Fetching Fear & Greed Index...")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        # Raise an exception for bad status codes (4xx or 5xx)

        data = response.json()
        if 'data' in data and len(data['data']) > 0:
            index_data = data['data'][0]
            log.info(
                "Successfully fetched Fear & Greed Index.",
                value=index_data.get('value'),
                classification=index_data.get('value_classification')
            )
            return index_data
        else:
            log.warning("Fear & Greed Index API returned no data.")
            return None

    except requests.exceptions.RequestException as e:
        log.error("Failed to fetch Fear & Greed Index.", error=str(e))
        return None
    except ValueError:  # Catches JSON decoding errors
        log.error("Failed to parse JSON response from Fear & Greed Index API.")
        return None
