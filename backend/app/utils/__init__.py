from datetime import datetime, date

def format_date(d) -> str:
    """Helper to convert date or datetime objects to standard YYYY-MM-DD strings."""
    if isinstance(d, (date, datetime)):
        return d.strftime("%Y-%m-%d")
    return str(d) if d else ""
