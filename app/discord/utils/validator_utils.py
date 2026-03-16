#app/discord/utils/validator_utils.py
import re

def is_valid_url(url: str | None) -> bool:
    if not url:
        return False
    return bool(re.match(r'^https?://', url))