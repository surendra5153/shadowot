import logging
import os
from taxii2client.v21 import Collection


def pull_cisa_iocs():
    """Best-effort TAXII subscription, safe to disable when unreachable."""
    if os.environ.get("ENABLE_CISA_FEED", "false").lower() != "true":
        return []
    try:
        collection_url = os.environ.get(
            "CISA_AIS_COLLECTION_URL",
            "https://ais2.us-cert.gov/taxii2/collections/",
        )
        collection = Collection(collection_url)
        envelope = collection.get_objects()
        return envelope.get("objects", [])
    except Exception as exc:
        logging.warning("CISA AIS feed unavailable: %s", exc)
        return []
