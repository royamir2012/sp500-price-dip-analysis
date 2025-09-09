# S&P 500 Price Dip Analysis App

A comprehensive web application for analyzing significant daily price declines in S&P 500 stocks and their recovery patterns from low prices.

## Features

- **Real-time Analysis**: Processes historical S&P 500 stock data to identify significant daily declines (previous day opening vs current day opening)
- **Recovery Time Analysis**: Calculates how many days it takes for stocks to increase by 10%, 20%, 30%, 40%, 50%, 75%, and 100% from their opening price on the dip day
- **Recovery Statistics**: Provides average recovery times and success rates for different recovery targets
- **Time-based Analysis**: Shows percentage of stocks whose opening price went up by specific percentages within timeframes (10% in 30/60 days, 20% in 30/60 days, 30% in 90 days)
- **Stock Database**: Complete list of all 172 S&P 500 stocks with company names
- **Stock Price History**: Interactive charts showing price history for any stock with customizable date ranges
- **Price Statistics**: Calculates highest, lowest, average prices and total return for selected stocks
- **Flexible Filtering**: Filter by date range, decline threshold, and specific stock symbols with automatic metric updates
- **Interactive Dashboard**: Modern, responsive web interface with real-time statistics and combined data views
- **Comprehensive Data**: Analyzes all S&P 500 stocks with company names and trading data
- **Performance Optimized**: Handles large datasets efficiently with chunked processing
- **Standalone Analysis Tool**: Includes `price_dip_analysis.py` for command-line analysis

## Data Sources

The application uses three CSV files:
- `data/sp500_companies.csv` - Company information (symbols, names, sectors)
- `data/sp500_stocks.csv` - Historical daily stock prices and volumes
- `data/sp500_index.csv` - S&P 500 index data

## Installation

1. **Clone or download the project files**

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Ensure your data files are in the correct location**:
   ```
   sp500analysis/
   ├── data/
   │   ├── sp500_companies.csv
   │   ├── sp500_stocks.csv
   │   └── sp500_index.csv
   ├── templates/
   │   └── index.html
   ├── app.py
   ├── price_dip_analysis.py
   ├── requirements.txt
   └── README.md
   ```

## Usage

### Web Application

1. **Start the application**:
   ```bash
   python app.py
   ```

2. **Open your web browser** and navigate to:
   ```
   http://localhost:8080
   ```

3. **Use the interface**:
   - View overall statistics in the dashboard cards
   - Adjust the decline threshold (default: -20%)
   - Set date ranges to filter results
   - Search for specific stock symbols
   - Click "Search Declines" to find significant declines and recovery data

### Command Line Analysis

Run the standalone analysis tool for detailed reports:

```bash
python price_dip_analysis.py
```

This provides:
- Top 10 worst single-day declines
- 2024 decline analysis
- Recovery time statistics
- Average recovery times by target
- Time-based recovery success rates

## Features Explained

### Dashboard Statistics
- **Total Records**: Number of stock price records in the dataset
- **Unique Stocks**: Number of different S&P 500 stocks analyzed
- **Significant Declines**: Count of all declines meeting the current threshold (updates dynamically)
- **Date Range**: The time period covered by the data
- **Avg +10% Days**: Average days to reach +10% from low price
- **+10% in 30d**: Percentage of stocks that recovered +10% within 30 days

### Filtering Options
- **Decline Threshold**: Set the percentage decline threshold (e.g., -20% for 20% drops) - automatically updates all metrics
- **Start/End Date**: Filter results to specific date ranges - automatically updates all metrics
- **Symbol**: Search for specific stock symbols (e.g., AAPL, MSFT) - automatically updates all metrics
- **Real-time Updates**: All statistics and recovery metrics update automatically when filters change
- **Dynamic Descriptions**: Threshold descriptions update to reflect current filter values

### Combined Results Table

The comprehensive table shows:
- **Date**: When the significant decline occurred
- **Symbol**: Stock ticker symbol
- **Company Name**: Full company name
- **Decline (%)**: The percentage decline from previous day opening to current day opening
- **Prev Day Open**: Opening price of the previous trading day
- **Open Price**: Opening price on the decline day
- **Open Price**: Stock's opening price on the dip day (baseline for recovery)
- **Volume**: Trading volume for that day
- **Recovery Columns**: Days until stock opening price increased by +10%, +20%, +30%, +40%, +50%, +75%, +100% from the opening price on the dip day
- **N/A**: Indicates the stock hasn't reached that recovery level yet

### Recovery Statistics

The analysis provides:
- **Average Recovery Times**: Mean, median, min, max days for each recovery target
- **Recovery Rates**: Percentage of stocks that achieved each recovery level
- **Time-based Success Rates**: Percentage of stocks that recovered within specific timeframes:
  - +10% within 30 days
  - +20% within 60 days
  - +30% within 90 days

## Technical Details

### Data Processing
- Loads large CSV files in chunks for memory efficiency
- Calculates daily percentage changes by comparing previous day opening to current day opening
- Also calculates intraday changes (opening to closing) for reference
- Merges company information with price data
- Filters out invalid or missing data
- Calculates recovery times from opening prices (not from decline recovery)

### Performance
- Processes ~1.9 million records efficiently
- Uses pandas for fast data manipulation
- Implements chunked reading for large files
- Caches processed data in memory

### API Endpoints
- `GET /` - Main web interface
- `GET /stock_history` - Stock price history page
- `GET /api/stats` - Get dataset statistics
- `GET /api/significant_declines` - Get combined decline and recovery data
- `GET /api/recovery_stats` - Get recovery statistics and averages
- `GET /api/stocks` - Get all available stocks
- `GET /api/stock_history` - Get stock price history data

### API Usage Examples
```bash
# Get statistics
curl http://localhost:8080/api/stats

# Get combined decline and recovery data
curl "http://localhost:8080/api/significant_declines?threshold=-20"

# Filter by date range
curl "http://localhost:8080/api/significant_declines?start_date=2024-01-01&end_date=2024-12-31"

# Search specific stock
curl "http://localhost:8080/api/significant_declines?symbol=AAPL"

# Get recovery statistics
curl "http://localhost:8080/api/recovery_stats?threshold=-20"

# Get recovery statistics for specific date range
curl "http://localhost:8080/api/recovery_stats?start_date=2024-01-01&end_date=2024-12-31"

# Get all available stocks
curl "http://localhost:8080/api/stocks"

# Get stock price history
curl "http://localhost:8080/api/stock_history?symbol=AAPL&start_date=2024-01-01&end_date=2024-12-31"
```

## Example Use Cases

1. **Market Research**: Identify stocks that experienced significant drops during specific periods
2. **Recovery Analysis**: Understand how quickly stocks bounce back from significant declines
3. **Risk Assessment**: Analyze recovery patterns to assess investment risk
4. **Sector Analysis**: Filter by specific companies to analyze sector-specific recovery patterns
5. **Event Correlation**: Match significant declines with market events or news
6. **Investment Timing**: Use recovery statistics to inform entry/exit strategies

## Troubleshooting

### Common Issues

1. **"Data not loaded" error**:
   - Ensure all CSV files are in the `data/` directory
   - Check file permissions and readability

2. **Memory issues with large datasets**:
   - The application uses chunked processing to handle large files
   - If you still experience issues, consider reducing the dataset size

3. **No results found**:
   - Try adjusting the decline threshold (make it less negative)
   - Check if your date range contains data
   - Verify stock symbols are correct

### Performance Tips

- The initial data loading may take 30-60 seconds for large datasets
- Subsequent searches are much faster due to in-memory caching
- Use specific date ranges to improve search performance

## Data Format Requirements

### sp500_companies.csv
```
Exchange,Symbol,Shortname,Longname,Sector,Industry,...
```

### sp500_stocks.csv
```
Date,Symbol,Adj Close,Close,High,Low,Open,Volume
```

### sp500_index.csv
```
Date,S&P500
```

## License

This project is for educational and research purposes. Please ensure you have proper licenses for any commercial use of the data.

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the application.
