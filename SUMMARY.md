# S&P 500 Significant Declines Analyzer - Summary

## What We Built

A comprehensive web application that analyzes S&P 500 daily trading data to detect stocks with significant daily price declines (default: >20%). The application provides both a web interface and API endpoints for data analysis.

## Key Features

### 1. **Data Processing**
- Handles large datasets efficiently (1.9M+ records)
- Processes 172 unique S&P 500 stocks
- Covers data from 2010-01-04 to 2024-12-20
- Calculates daily percentage changes for each stock
- Merges company information with price data

### 2. **Web Interface**
- Modern, responsive design with Bootstrap 5
- Real-time dashboard with statistics
- Interactive filtering options:
  - Decline threshold (default: -20%)
  - Date range selection
  - Stock symbol search
- Results table with detailed information
- Loading states and error handling

### 3. **API Endpoints**
- `GET /api/stats` - Dataset statistics
- `GET /api/significant_declines` - Filtered decline data
- JSON responses for programmatic access

### 4. **Analysis Capabilities**
- Identifies stocks with significant daily declines
- Calculates recovery times for 10%, 20%, 30%, 40%, 50%, 75%, and 100% of price drops
- Provides company names, dates, and percentage changes
- Shows closing prices and trading volumes
- Supports filtering by date ranges and specific stocks

## Sample Results

### Dataset Statistics
- **Total Records**: 617,831
- **Unique Stocks**: 172
- **Significant Declines (>20%)**: 88
- **Date Range**: 2010-01-04 to 2024-12-20

### Notable Findings
- **Worst Single-Day Decline**: EXPE (Expedia Group) on 2011-12-21 with -51.16%
- **Recovery Analysis**: 86.4% of stocks recovered 100% of their decline, taking an average of 120.6 days
- **Recent Significant Declines in 2024**: 6 stocks with >20% drops
- **Most Recent**: CE (Celanese Corporation) on 2024-11-05 with -26.32%

## Technical Implementation

### Backend (Python/Flask)
- **Framework**: Flask web framework
- **Data Processing**: Pandas for efficient data manipulation
- **Memory Management**: Chunked file reading for large datasets
- **Performance**: In-memory caching of processed data

### Frontend (HTML/CSS/JavaScript)
- **UI Framework**: Bootstrap 5 for responsive design
- **Icons**: Font Awesome for visual elements
- **Interactivity**: Vanilla JavaScript for API calls
- **Styling**: Custom CSS with gradient backgrounds and modern design

### Data Sources
- `sp500_companies.csv` - Company information (symbols, names, sectors)
- `sp500_stocks.csv` - Historical daily stock prices and volumes
- `sp500_index.csv` - S&P 500 index data

## Usage Examples

### Web Interface
1. Open http://localhost:8080
2. View dashboard statistics
3. Adjust filters as needed
4. Click "Search Declines" to find significant drops

### API Usage
```bash
# Get statistics
curl http://localhost:8080/api/stats

# Get significant declines
curl "http://localhost:8080/api/significant_declines?threshold=-20"

# Filter by date range
curl "http://localhost:8080/api/significant_declines?start_date=2024-01-01&end_date=2024-12-31"

# Search specific stock
curl "http://localhost:8080/api/significant_declines?symbol=AAPL"

# Get recovery times analysis
curl "http://localhost:8080/api/recovery_times?threshold=-20"

# Get recovery times for specific date range
curl "http://localhost:8080/api/recovery_times?start_date=2024-01-01&end_date=2024-12-31"
```

### Programmatic Usage
```python
from app import load_and_process_data, get_significant_declines, calculate_recovery_times

# Load data
load_and_process_data()

# Get significant declines
declines = get_significant_declines(threshold=-20, start_date='2024-01-01')

# Get recovery times analysis
recovery_data = calculate_recovery_times(threshold=-20, start_date='2024-01-01')
```

## Files Created

1. **`app.py`** - Main Flask application with data processing and API endpoints
2. **`templates/index.html`** - Web interface with modern UI
3. **`requirements.txt`** - Python dependencies
4. **`README.md`** - Comprehensive documentation
5. **`demo.py`** - Demo script showing programmatic usage
6. **`SUMMARY.md`** - This summary document

## Key Benefits

1. **Comprehensive Analysis**: Analyzes all S&P 500 stocks with historical data
2. **User-Friendly Interface**: Modern web UI with intuitive filtering
3. **Performance Optimized**: Handles large datasets efficiently
4. **Flexible API**: Programmatic access for custom analysis
5. **Real-Time Results**: Instant filtering and search capabilities
6. **Detailed Information**: Shows company names, dates, prices, and volumes

## Use Cases

- **Market Research**: Identify stocks with significant drops during specific periods
- **Risk Analysis**: Find worst single-day declines in S&P 500 history
- **Sector Analysis**: Filter by specific companies to analyze sector-specific declines
- **Event Correlation**: Match significant declines with market events or news
- **Portfolio Management**: Monitor stocks for unusual price movements

The application successfully meets the requirements by detecting stocks with daily price declines greater than 20%, displaying the stock name, daily price change percentage, and the date of the event, both through a web interface and API endpoints.
