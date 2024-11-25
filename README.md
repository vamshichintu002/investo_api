# Investment Portfolio Advisor API

A FastAPI-based backend service that processes client investment data and generates personalized portfolio recommendations.

## Features

- Real-time client form monitoring
- Investment capacity calculation
- Risk profile assessment
- Portfolio strategy generation
- Automated financial goal processing
- Emergency fund ratio analysis

## Prerequisites

- Python 3.11+
- Supabase account and project
- PostgreSQL database (provided by Supabase)

## Dependencies

The project uses the following main dependencies:
- FastAPI (0.104.1) - Web framework
- Uvicorn (0.24.0) - ASGI server
- Pandas (2.1.4) - Data manipulation
- NumPy (1.26.2) - Numerical computations
- Matplotlib (3.8.2) - Data visualization
- YFinance (0.2.35) - Financial data
- Python-dotenv (1.0.0) - Environment management
- OpenAI (>=1.0.0) - AI capabilities
- Lyzr-agent-api (0.1.0) - Agent functionality
- Supabase - Database and authentication

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd backend_2-main
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with the following:
```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key_or_service_role_key
OPENAI_API_KEY=your_openai_api_key
LYZR_API_KEY=your_lyzr_api_key
```

## Database Setup

The API expects a table named `client_forms` in your Supabase database with the following structure:

```sql
CREATE TABLE client_forms (
    client_id TEXT PRIMARY KEY,
    name TEXT,
    age INTEGER,
    occupation TEXT,
    city TEXT,
    monthly_income NUMERIC,
    monthly_expenses NUMERIC,
    emergency_cash NUMERIC,
    risk_tolerance TEXT,
    financial_goals JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);
```

## Running the API

1. Start the server:
```bash
python api.py
```

The API will run on `http://0.0.0.0:8000`

2. Monitor the logs to see:
   - New client form submissions
   - Processing status
   - Generated recommendations

## API Features

### Background Tasks
- Continuous monitoring of client form submissions
- Automatic processing of new entries
- Real-time portfolio analysis

### Financial Analysis
- Investment capacity calculation
- Risk tolerance assessment
- Emergency fund ratio analysis
- Goal-based investment planning

### Portfolio Strategy
- Asset allocation recommendations
- Risk-adjusted portfolio generation
- Goal-aligned investment strategies

## Data Processing Flow

1. Client form submission is detected
2. Financial metrics are calculated
3. Risk profile is determined
4. Portfolio strategy is generated
5. Results are stored in unified table

## Error Handling

The API includes comprehensive error handling for:
- Database connection issues
- Invalid data formats
- Processing failures
- Missing required fields

## Monitoring and Logging

The API provides detailed logging for:
- New form submissions
- Processing status
- Error messages
- Connection status

## Security

- Uses Supabase authentication
- Environment-based configuration
- Secure API key handling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request


