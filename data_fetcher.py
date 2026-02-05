class DataFetchError(Exception):
    pass

def fetch_data(symbol, interval):
    # Minimal stub: replace with actual data fetching logic
    # For now, return dummy data
    return [
        {"time": "2024-01-01 00:00", "open": 1.0, "high": 1.1, "low": 0.9, "close": 1.05, "volume": 1000},
        # ...add more dummy data as needed...
    ]
