from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# Global variables to store processed data
stocks_data = None
companies_data = None
index_data = None

def load_and_process_data():
    """Load and process the S&P 500 data"""
    global stocks_data, companies_data, index_data
    
    print("Loading data...")
    
    # Load companies data
    companies_data = pd.read_csv('data/sp500_companies.csv')
    
    # Load index data
    index_data = pd.read_csv('data/sp500_index.csv')
    index_data['Date'] = pd.to_datetime(index_data['Date'])
    
    # Load stocks data in chunks to handle large file
    print("Loading stocks data (this may take a moment)...")
    chunks = []
    chunk_size = 100000
    
    for chunk in pd.read_csv('data/sp500_stocks.csv', chunksize=chunk_size):
        # Filter out rows with empty price data
        chunk = chunk.dropna(subset=['Close'])
        if not chunk.empty:
            chunks.append(chunk)
    
    stocks_data = pd.concat(chunks, ignore_index=True)
    stocks_data['Date'] = pd.to_datetime(stocks_data['Date'])
    
    # Calculate daily price changes based on previous day opening vs current day opening price
    print("Calculating daily price changes...")
    stocks_data = stocks_data.sort_values(['Symbol', 'Date'])
    
    # Calculate the price change from previous day opening to current day opening
    stocks_data['Prev_Day_Open'] = stocks_data.groupby('Symbol')['Open'].shift(1)
    stocks_data['Daily_Change_Pct'] = ((stocks_data['Open'] - stocks_data['Prev_Day_Open']) / stocks_data['Prev_Day_Open']) * 100
    
    # Also keep the intraday change for reference
    stocks_data['Intraday_Change_Pct'] = ((stocks_data['Close'] - stocks_data['Open']) / stocks_data['Open']) * 100
    
    # Merge with company names
    stocks_data = stocks_data.merge(
        companies_data[['Symbol', 'Shortname']], 
        on='Symbol', 
        how='left'
    )
    
    print("Data processing complete!")

def get_significant_declines(threshold=-20, start_date=None, end_date=None, symbol=None):
    """Get stocks with significant daily declines"""
    global stocks_data
    
    if stocks_data is None:
        return pd.DataFrame()
    
    # Filter data
    filtered_data = stocks_data.copy()
    
    if start_date:
        filtered_data = filtered_data[filtered_data['Date'] >= start_date]
    if end_date:
        filtered_data = filtered_data[filtered_data['Date'] <= end_date]
    if symbol:
        filtered_data = filtered_data[filtered_data['Symbol'].str.contains(symbol, case=False, na=False)]
    
    # Get significant declines
    significant_declines = filtered_data[
        (filtered_data['Daily_Change_Pct'] <= threshold) & 
        (filtered_data['Daily_Change_Pct'].notna())
    ].copy()
    
    # Sort by date (most recent first) and then by percentage change
    significant_declines = significant_declines.sort_values(
        ['Date', 'Daily_Change_Pct'], 
        ascending=[False, True]
    )
    
    return significant_declines

def calculate_recovery_times(threshold=-20, start_date=None, end_date=None, symbol=None):
    """Calculate recovery times for stocks after significant declines"""
    global stocks_data
    
    if stocks_data is None:
        return pd.DataFrame()
    
    # Get significant declines
    declines = get_significant_declines(threshold, start_date, end_date, symbol)
    
    if declines.empty:
        return pd.DataFrame()
    
    recovery_data = []
    
    for _, decline_row in declines.iterrows():
        symbol = decline_row['Symbol']
        decline_date = decline_row['Date']
        decline_price = decline_row['Close']
        decline_pct = decline_row['Daily_Change_Pct']
        low_price = decline_row['Low'] if pd.notna(decline_row['Low']) else decline_price
        
        # Get future data for this stock after the decline date
        future_data = stocks_data[
            (stocks_data['Symbol'] == symbol) & 
            (stocks_data['Date'] > decline_date)
        ].copy()
        
        if future_data.empty:
            continue
        
        # Calculate recovery targets (10%, 15%, 20%, 30%, 40%, 50%, 75%, 100% increase from low)
        recovery_targets = [10, 15, 20, 30, 40, 50, 75, 100]
        recovery_days = {}
        
        for target in recovery_targets:
            # Calculate the target price (open_price + target% increase)
            target_price = decline_row['Open'] * (1 + target / 100)
            
            # Find the first day when opening price reaches or exceeds target
            recovery_mask = future_data['Open'] >= target_price
            if recovery_mask.any():
                recovery_date = future_data.loc[recovery_mask.idxmax(), 'Date']
                days_to_recover = (recovery_date - decline_date).days
                recovery_days[f'recover_{target}pct_days'] = days_to_recover
            else:
                recovery_days[f'recover_{target}pct_days'] = None
        
        # Add to recovery data
        recovery_data.append({
            'date': decline_date,
            'symbol': symbol,
            'company_name': decline_row['Shortname'] if pd.notna(decline_row['Shortname']) else symbol,
            'decline_pct': decline_pct,
            'prev_day_open': decline_row['Prev_Day_Open'] if pd.notna(decline_row['Prev_Day_Open']) else None,
            'open_price': decline_row['Open'] if pd.notna(decline_row['Open']) else None,
            'volume': decline_row['Volume'] if pd.notna(decline_row['Volume']) else 0,
            **recovery_days
        })
    
    return pd.DataFrame(recovery_data)

def get_combined_data(threshold=-20, start_date=None, end_date=None, symbol=None):
    """Get combined decline and recovery data"""
    recovery_data = calculate_recovery_times(threshold, start_date, end_date, symbol)
    return recovery_data

def calculate_recovery_statistics(threshold=-20, start_date=None, end_date=None, symbol=None):
    """Calculate recovery statistics including averages and percentages"""
    recovery_data = get_combined_data(threshold, start_date, end_date, symbol)
    
    if recovery_data.empty:
        return {
            'total_stocks': 0,
            'averages': {},
            'percentages': {}
        }
    
    total_stocks = len(recovery_data)
    statistics = {
        'total_stocks': total_stocks,
        'averages': {},
        'percentages': {}
    }
    
    # Calculate averages for each recovery target
    recovery_targets = [10, 15, 20, 30, 40, 50, 75, 100]
    
    for target in recovery_targets:
        days_key = f'recover_{target}pct_days'
        valid_days = recovery_data[days_key].dropna()
        
        if not valid_days.empty:
            avg_days = valid_days.mean()
            median_days = valid_days.median()
            min_days = valid_days.min()
            max_days = valid_days.max()
            recovered_count = len(valid_days)
            recovery_rate = (recovered_count / total_stocks) * 100
            
            statistics['averages'][f'{target}pct'] = {
                'average_days': round(avg_days, 1),
                'median_days': round(median_days, 1),
                'min_days': int(min_days),
                'max_days': int(max_days),
                'recovered_count': recovered_count,
                'total_count': total_stocks,
                'recovery_rate': round(recovery_rate, 1)
            }
        else:
            statistics['averages'][f'{target}pct'] = {
                'average_days': None,
                'median_days': None,
                'min_days': None,
                'max_days': None,
                'recovered_count': 0,
                'total_count': total_stocks,
                'recovery_rate': 0.0
            }
    
    # Calculate percentages for specific timeframes
    # 10% recovery in 30 days
    recovered_10pct_30days = recovery_data[
        (recovery_data['recover_10pct_days'].notna()) & 
        (recovery_data['recover_10pct_days'] <= 30)
    ]
    pct_10pct_30days = (len(recovered_10pct_30days) / total_stocks) * 100
    
    # 10% recovery in 60 days
    recovered_10pct_60days = recovery_data[
        (recovery_data['recover_10pct_days'].notna()) & 
        (recovery_data['recover_10pct_days'] <= 60)
    ]
    pct_10pct_60days = (len(recovered_10pct_60days) / total_stocks) * 100
    
    # 20% recovery in 30 days
    recovered_20pct_30days = recovery_data[
        (recovery_data['recover_20pct_days'].notna()) & 
        (recovery_data['recover_20pct_days'] <= 30)
    ]
    pct_20pct_30days = (len(recovered_20pct_30days) / total_stocks) * 100
    
    # 15% recovery in 30 days
    recovered_15pct_30days = recovery_data[
        (recovery_data['recover_15pct_days'].notna()) & 
        (recovery_data['recover_15pct_days'] <= 30)
    ]
    pct_15pct_30days = (len(recovered_15pct_30days) / total_stocks) * 100
    
    # 15% recovery in 60 days
    recovered_15pct_60days = recovery_data[
        (recovery_data['recover_15pct_days'].notna()) & 
        (recovery_data['recover_15pct_days'] <= 60)
    ]
    pct_15pct_60days = (len(recovered_15pct_60days) / total_stocks) * 100
    
    # 20% recovery in 60 days
    recovered_20pct_60days = recovery_data[
        (recovery_data['recover_20pct_days'].notna()) & 
        (recovery_data['recover_20pct_days'] <= 60)
    ]
    pct_20pct_60days = (len(recovered_20pct_60days) / total_stocks) * 100
    
    # 30% recovery in 90 days
    recovered_30pct_90days = recovery_data[
        (recovery_data['recover_30pct_days'].notna()) & 
        (recovery_data['recover_30pct_days'] <= 90)
    ]
    pct_30pct_90days = (len(recovered_30pct_90days) / total_stocks) * 100
    
    statistics['percentages'] = {
        '10pct_30days': {
            'percentage': round(pct_10pct_30days, 1),
            'count': len(recovered_10pct_30days),
            'total': total_stocks
        },
        '10pct_60days': {
            'percentage': round(pct_10pct_60days, 1),
            'count': len(recovered_10pct_60days),
            'total': total_stocks
        },
        '15pct_30days': {
            'percentage': round(pct_15pct_30days, 1),
            'count': len(recovered_15pct_30days),
            'total': total_stocks
        },
        '15pct_60days': {
            'percentage': round(pct_15pct_60days, 1),
            'count': len(recovered_15pct_60days),
            'total': total_stocks
        },
        '20pct_30days': {
            'percentage': round(pct_20pct_30days, 1),
            'count': len(recovered_20pct_30days),
            'total': total_stocks
        },
        '20pct_60days': {
            'percentage': round(pct_20pct_60days, 1),
            'count': len(recovered_20pct_60days),
            'total': total_stocks
        },
        '30pct_90days': {
            'percentage': round(pct_30pct_90days, 1),
            'count': len(recovered_30pct_90days),
            'total': total_stocks
        }
    }
    
    return statistics

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/stock_history')
def stock_history():
    """Stock history page"""
    return render_template('stock_history.html')

@app.route('/api/significant_declines')
def api_significant_declines():
    """API endpoint to get combined decline and recovery data"""
    try:
        # Get parameters
        threshold = float(request.args.get('threshold', -20))
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        symbol = request.args.get('symbol', '')
        
        # Convert dates
        start_date = pd.to_datetime(start_date_str) if start_date_str else None
        end_date = pd.to_datetime(end_date_str) if end_date_str else None
        
        # Get combined data
        combined_data = get_combined_data(threshold, start_date, end_date, symbol)
        
        # Convert to JSON-friendly format
        result = []
        for _, row in combined_data.iterrows():
            result.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'symbol': row['symbol'],
                'company_name': row['company_name'],
                'decline_pct': round(row['decline_pct'], 2),
                'prev_day_open': round(row['prev_day_open'], 2) if pd.notna(row['prev_day_open']) else None,
                'open_price': round(row['open_price'], 2),
                'volume': int(row['volume']) if pd.notna(row['volume']) else 0,
                'recover_10pct_days': None if pd.isna(row['recover_10pct_days']) else int(row['recover_10pct_days']),
                'recover_15pct_days': None if pd.isna(row['recover_15pct_days']) else int(row['recover_15pct_days']),
                'recover_20pct_days': None if pd.isna(row['recover_20pct_days']) else int(row['recover_20pct_days']),
                'recover_30pct_days': None if pd.isna(row['recover_30pct_days']) else int(row['recover_30pct_days']),
                'recover_40pct_days': None if pd.isna(row['recover_40pct_days']) else int(row['recover_40pct_days']),
                'recover_50pct_days': None if pd.isna(row['recover_50pct_days']) else int(row['recover_50pct_days']),
                'recover_75pct_days': None if pd.isna(row['recover_75pct_days']) else int(row['recover_75pct_days']),
                'recover_100pct_days': None if pd.isna(row['recover_100pct_days']) else int(row['recover_100pct_days'])
            })
        
        return jsonify({
            'success': True,
            'data': result,
            'count': len(result)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/stocks')
def api_stocks():
    """API endpoint to get all available stocks"""
    try:
        global stocks_data, companies_data
        
        if stocks_data is None or companies_data is None:
            return jsonify({
                'success': False,
                'error': 'Data not loaded'
            })
        
        # Get unique stocks with their company names
        unique_stocks = stocks_data[['Symbol']].drop_duplicates()
        stocks_with_names = unique_stocks.merge(
            companies_data[['Symbol', 'Shortname']], 
            on='Symbol', 
            how='left'
        )
        
        # Convert to list of dictionaries
        stocks_list = []
        for _, row in stocks_with_names.iterrows():
            stocks_list.append({
                'symbol': row['Symbol'],
                'name': row['Shortname'] if pd.notna(row['Shortname']) else row['Symbol']
            })
        
        # Sort by symbol
        stocks_list.sort(key=lambda x: x['symbol'])
        
        return jsonify({
            'success': True,
            'stocks': stocks_list,
            'count': len(stocks_list)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/stock_history')
def api_stock_history():
    """API endpoint to get stock price history"""
    try:
        global stocks_data
        
        if stocks_data is None:
            return jsonify({
                'success': False,
                'error': 'Data not loaded'
            })
        
        # Get parameters
        symbol = request.args.get('symbol', '').upper()
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if not symbol:
            return jsonify({
                'success': False,
                'error': 'Symbol is required'
            })
        
        # Convert dates
        start_date = pd.to_datetime(start_date_str) if start_date_str else None
        end_date = pd.to_datetime(end_date_str) if end_date_str else None
        
        # Filter data
        stock_data = stocks_data[stocks_data['Symbol'] == symbol].copy()
        
        if stock_data.empty:
            return jsonify({
                'success': False,
                'error': f'No data found for symbol {symbol}'
            })
        
        # Apply date filters
        if start_date:
            stock_data = stock_data[stock_data['Date'] >= start_date]
        if end_date:
            stock_data = stock_data[stock_data['Date'] <= end_date]
        
        # Sort by date
        stock_data = stock_data.sort_values('Date')
        
        # Convert to JSON-friendly format
        history = []
        for _, row in stock_data.iterrows():
            history.append({
                'date': row['Date'].strftime('%Y-%m-%d'),
                'prev_day_open': round(row['Prev_Day_Open'], 2) if pd.notna(row['Prev_Day_Open']) else None,
                'open': round(row['Open'], 2) if pd.notna(row['Open']) else None,
                'volume': int(row['Volume']) if pd.notna(row['Volume']) else 0,
                'daily_change_pct': round(row['Daily_Change_Pct'], 2) if pd.notna(row['Daily_Change_Pct']) else None
            })
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'history': history,
            'count': len(history)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/recovery_stats')
def api_recovery_stats():
    """API endpoint to get recovery statistics"""
    try:
        # Get parameters
        threshold = float(request.args.get('threshold', -20))
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        symbol = request.args.get('symbol', '')
        
        # Convert dates
        start_date = pd.to_datetime(start_date_str) if start_date_str else None
        end_date = pd.to_datetime(end_date_str) if end_date_str else None
        
        # Get recovery statistics
        stats = calculate_recovery_statistics(threshold, start_date, end_date, symbol)
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/stats')
def api_stats():
    """API endpoint to get statistics"""
    try:
        global stocks_data
        
        if stocks_data is None:
            return jsonify({'success': False, 'error': 'Data not loaded'})
        
        # Get parameters
        threshold = float(request.args.get('threshold', -20))
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        symbol = request.args.get('symbol', '')
        
        # Convert dates
        start_date = pd.to_datetime(start_date_str) if start_date_str else None
        end_date = pd.to_datetime(end_date_str) if end_date_str else None
        
        # Basic statistics
        total_records = len(stocks_data)
        unique_symbols = stocks_data['Symbol'].nunique()
        date_range = {
            'start': stocks_data['Date'].min().strftime('%Y-%m-%d'),
            'end': stocks_data['Date'].max().strftime('%Y-%m-%d')
        }
        
        # Count significant declines with current filters
        significant_declines = get_significant_declines(threshold, start_date, end_date, symbol)
        decline_count = len(significant_declines)
        
        # Worst single day decline
        worst_decline = stocks_data.loc[stocks_data['Daily_Change_Pct'].idxmin()]
        worst_decline_info = {
            'date': worst_decline['Date'].strftime('%Y-%m-%d'),
            'symbol': worst_decline['Symbol'],
            'company_name': worst_decline['Shortname'] if pd.notna(worst_decline['Shortname']) else worst_decline['Symbol'],
            'change_pct': round(worst_decline['Daily_Change_Pct'], 2)
        }
        
        return jsonify({
            'success': True,
            'stats': {
                'total_records': total_records,
                'unique_symbols': unique_symbols,
                'date_range': date_range,
                'significant_declines_count': decline_count,
                'worst_decline': worst_decline_info
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    # Load data when starting the app
    load_and_process_data()
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)
