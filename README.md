# FinX - Trading 212 Dividend Tracker

Hey there! 👋 This is my personal project to track and forecast dividends from my Trading 212 portfolio. I built this because I wanted a better way to keep track of my dividend income and upcoming payouts.

## Features

- 📊 Portfolio tracking and analysis
- 💰 Dividend forecasting and calculations
- 📅 Historical dividend data analysis
- 🔄 Real-time portfolio updates
- 💱 Currency conversion support (everything in GBP)

## Tech Stack

- **Backend**: FastAPI (Python)
- **Financial Data**: yfinance

## A Quick Note About Data Accuracy

Currently, the project uses yfinance for fetching stock data. While it's a great free resource, it might not always provide 100% accurate or complete data. I'm actively exploring other data sources to improve accuracy. If you have any suggestions, feel free to reach out!

## Future Plans

- 🔐 Implementing OAuth for secure login (moving away from direct T212 API integration)
- 📱 Adding more data sources for better accuracy
- 🎯 Enhanced portfolio analytics
- 📈 Better dividend forecasting algorithms

## Project Structure

```
FinX/
├── backend/
│   ├── service/      # Core business logic
│   ├── routers/      # API endpoints
│   ├── schemas.py    # Data models
│   ├── config.py     # Configuration
│   └── app.py        # Main application
├── requirements.txt  # Dependencies
```

## Getting Started

1. Create a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   uvicorn backend.app:app --reload
   ```

## API Endpoints

- `/dividends` - Get dividend forecasts and history
- `/health` - Check if the service is running

## Development

The project uses FastAPI for the backend API, which means you get automatic OpenAPI documentation at `/docs` when running the server.

## Contributing

Feel free to open issues or submit pull requests. I'm always happy to hear suggestions for improvements or new features!

## License
