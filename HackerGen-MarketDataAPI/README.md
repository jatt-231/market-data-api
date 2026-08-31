# Hacker Gen Market Data API

Independent, standalone market data infrastructure for the Hacker Gen ecosystem.
Provides validated, standardized OTC candle data from Quotex, decoupled from any trading logic.

## Architecture

External Provider (Quotex) -> Provider Adapter -> Validation -> API -> Consumers

This API is intentionally independent from the Hacker Gen AI Trading Assistant.
Any future consumer (including the Trading Assistant) should only talk to this API,
never directly to Quotex or any other provider.

## Setup

1. Create virtual environment: python -m venv venv
2. Activate: .\venv\Scripts\Activate
3. Install dependencies: pip install fastapi uvicorn requests python-dotenv
4. Install pyquotex: pip install git+https://github.com/cleitonleonel/pyquotex.git
5. Create .env file with QUOTEX_EMAIL, QUOTEX_PASSWORD, and API_KEY
6. Run: uvicorn main:app --reload

## Important Notes

- VPN required: Quotex is blocked in some regions. VPN must be ON during local development.
- Demo account only: This API connects using the PRACTICE/DEMO account, never REAL money.
- pyquotex is unofficial: It may break if Quotex changes their system.

## Endpoints

GET / - No auth - Basic welcome message
GET /health - No auth - Basic health check
GET /status - Auth required - Detailed provider status
GET /pairs - Auth required - List of all available trading pairs
GET /candles - Auth required - Latest live candles for a symbol
GET /history - Auth required - Historical candles from saved CSV

Protected endpoints require header: x-api-key

## Data Validation

All candles are validated before being served. Invalid candles are skipped and logged.

## Historical Data Collection

Run fetch_historical_data.py to bulk-download historical candles into a CSV file.

## Logging

Logs are written to logs/hackergen_api.log. Third-party debug noise is suppressed.

## Status

Completed: Core endpoints, validation, error handling, API key security, logging
Not yet done: Database storage, multi-provider failover, stability testing, VPS deployment