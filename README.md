# FullStockAI

FullStockAI is an experimental stock analysis and prediction platform built with Flask and various machine learning services.

## Development

```bash
pip install -e .
pytest
```

The application uses timezone-aware datetimes. Ensure the environment variable `TZ=UTC` (see `.env.example`).

## Running

```bash
python app.py
```

## Tests

Run all tests with `pytest`.

