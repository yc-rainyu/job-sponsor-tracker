import re

_TRADE_AS = re.compile(r'\b(?:t/as?|trading as)\b', re.IGNORECASE)


def _normalise(name: str) -> str:
    name = ' '.join(name.split()).lower()
    name = name.replace('&', ' and ')
    name = re.sub(r'[^\w\s]', '', name)
    name = ' '.join(name.split())
    name = re.sub(r'\bpublic limited company\b', 'plc', name)
    name = re.sub(r'\blimited\b', 'ltd', name)
    name = re.sub(r'\bcompany\b', 'co', name)
    name = re.sub(r'^the ', '', name)
    return name


def normalise_name(raw: str) -> tuple[str, str | None, str | None]:
    parts = _TRADE_AS.split(raw, maxsplit=1)
    legal_norm = _normalise(parts[0])
    if len(parts) == 1:
        return legal_norm, None, None
    trading_raw = parts[1].strip()
    return legal_norm, trading_raw, _normalise(trading_raw)
