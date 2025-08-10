# FullStockAI

FullStockAI is a lightweight stock prediction and WebSocket demo application. It exposes HTTP and WebSocket endpoints for retrieving model predictions and streaming quote data.

## Quick Start

1. **Install dependencies**
   ```bash
   pip install .
   ```
   This uses the dependencies defined in `pyproject.toml`.

2. **Run the test suite**
   ```bash
   pytest -q
   ```

3. **Start the development server**
   ```bash
   python app.py
   ```

## Environment Variables

Create a `.env` file based on `.env.example` to configure database and email credentials.

## Testing

The repository includes tests exercising the HTTP and WebSocket prediction flows. Run `pytest` to execute them.
