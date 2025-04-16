import re

def parse_quantity_unit(text):
    match = re.search(r"\((\d+\.?\d*)\s*(\w+)", text)
    if match:
        quantity = float(match.group(1))
        unit = match.group(2).lower()
        return quantity, unit
    return 1, "unit"
