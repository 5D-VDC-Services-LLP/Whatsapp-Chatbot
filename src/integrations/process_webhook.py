import logging

logger = logging.getLogger(__name__)

async def process_webhook_event(payload: dict):
    """
    Central handler for webhook payloads.
    Add validation and routing logic here based on platform.
    """
    object_type = payload.get("object")
    entry = payload.get("entry")

    if not object_type or not isinstance(entry, list):
        raise ValueError("Malformed payload: missing 'object' or 'entry' field")

    for item in entry:
        changes = item.get("changes", [])
        for change in changes:
            value = change.get("value")
            field = change.get("field")

            if field == "messages" and value:
                logger.info(f"Received message event: {value}")
                # TODO: Delegate to message-specific handler here
            else:
                logger.warning(f"Unhandled change type: {field} | {value}")
