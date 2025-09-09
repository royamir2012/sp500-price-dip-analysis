from flask import Flask, render_template, request, jsonify, session
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json
import uuid
from collections import defaultdict, Counter

app = Flask(__name__)
app.secret_key = 'sp500_admin_secret_key_2024'  # Change this in production

# Global variables to store processed data
stocks_data = None
companies_data = None
index_data = None

# Analytics tracking
user_analytics = {
    'sessions': {},  # session_id -> session_data
    'page_views': defaultdict(int),  # page -> count
    'api_calls': defaultdict(int),  # endpoint -> count
    'user_actions': [],  # list of all user actions
    'daily_stats': defaultdict(lambda: {
        'unique_users': set(),
        'page_views': 0,
        'api_calls': 0,
        'actions': []
    })
}

def track_user_action(action_type, details=None, endpoint=None):
    """Track user actions for analytics"""
    global user_analytics
    
    # Get or create session
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        session['first_visit'] = datetime.now().isoformat()
        session['user_agent'] = request.headers.get('User-Agent', 'Unknown')
        session['ip_address'] = request.remote_addr
    
    session_id = session['session_id']
    current_time = datetime.now()
    today = current_time.strftime('%Y-%m-%d')
    
    # Initialize session data if not exists
    if session_id not in user_analytics['sessions']:
        user_analytics['sessions'][session_id] = {
            'first_visit': session.get('first_visit'),
            'last_activity': current_time.isoformat(),
            'user_agent': session.get('user_agent'),
            'ip_address': session.get('ip_address'),
            'actions': [],
            'page_views': 0,
            'api_calls': 0
        }
    
    # Update session data
    user_analytics['sessions'][session_id]['last_activity'] = current_time.isoformat()
    
    # Track action
    action_data = {
        'timestamp': current_time.isoformat(),
        'action_type': action_type,
        'details': details or {},
        'endpoint': endpoint,
        'session_id': session_id
    }
    
    user_analytics['user_actions'].append(action_data)
    user_analytics['sessions'][session_id]['actions'].append(action_data)
    user_analytics['daily_stats'][today]['actions'].append(action_data)
    user_analytics['daily_stats'][today]['unique_users'].add(session_id)
    
    # Update counters
    if action_type == 'page_view':
        user_analytics['page_views'][details.get('page', 'unknown')] += 1
        user_analytics['sessions'][session_id]['page_views'] += 1
        user_analytics['daily_stats'][today]['page_views'] += 1
    elif action_type == 'api_call':
        user_analytics['api_calls'][endpoint] += 1
        user_analytics['sessions'][session_id]['api_calls'] += 1
        user_analytics['daily_stats'][today]['api_calls'] += 1

def get_analytics_summary():
    """Get analytics summary for admin dashboard"""
    global user_analytics
    
    # Calculate summary statistics
    total_sessions = len(user_analytics['sessions'])
    total_actions = len(user_analytics['user_actions'])
    total_page_views = sum(user_analytics['page_views'].values())
    total_api_calls = sum(user_analytics['api_calls'].values())
    
    # Recent activity (last 24 hours)
    recent_cutoff = datetime.now() - timedelta(hours=24)
    recent_actions = [
        action for action in user_analytics['user_actions']
        if datetime.fromisoformat(action['timestamp']) > recent_cutoff
    ]
    
    # Top pages and API endpoints
    top_pages = dict(Counter(user_analytics['page_views']).most_common(10))
    top_api_endpoints = dict(Counter(user_analytics['api_calls']).most_common(10))
    
    # Daily stats (last 7 days)
    daily_stats = {}
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        if date in user_analytics['daily_stats']:
            daily_stats[date] = {
                'unique_users': len(user_analytics['daily_stats'][date]['unique_users']),
                'page_views': user_analytics['daily_stats'][date]['page_views'],
                'api_calls': user_analytics['daily_stats'][date]['api_calls']
            }
    
    return {
        'total_sessions': total_sessions,
        'total_actions': total_actions,
        'total_page_views': total_page_views,
        'total_api_calls': total_api_calls,
        'recent_actions_count': len(recent_actions),
        'top_pages': top_pages,
        'top_api_endpoints': top_api_endpoints,
        'daily_stats': daily_stats,
        'recent_actions': recent_actions[-20:]  # Last 20 actions
    }

def load_and_process_data():
    """Load and process the S&P 500 data"""
    global stocks_data, companies_data, index_data
    
    try:
        import os
        print("=" * 60)
        print("STARTING DATA LOADING PROCESS")
        print("=" * 60)
        print(f"Current working directory: {os.getcwd()}")
        print(f"Python version: {os.sys.version}")
        
        # Check if data directory exists
        print("\n1. CHECKING DATA DIRECTORY...")
        if not os.path.exists('data'):
            print("❌ ERROR: data directory not found!")
            print(f"   Current directory contents: {os.listdir('.')}")
            return False
        else:
            print("✅ data directory found")
            data_files = os.listdir('data')
            print(f"   Files in data directory: {data_files}")
            
            # Check file sizes
            for file in data_files:
                file_path = os.path.join('data', file)
                file_size = os.path.getsize(file_path)
                file_size_mb = file_size / (1024 * 1024)
                print(f"   📁 {file}: {file_size_mb:.2f} MB")
        
        # Load companies data
        print("\n2. LOADING COMPANIES DATA...")
        companies_file = 'data/sp500_companies.csv'
        if not os.path.exists(companies_file):
            print(f"❌ ERROR: {companies_file} not found!")
            return False
        
        print(f"   📂 Loading from: {companies_file}")
        companies_data = pd.read_csv(companies_file)
        print(f"✅ SUCCESS: Loaded {len(companies_data)} companies")
        print(f"   📊 Columns: {list(companies_data.columns)}")
        print(f"   📅 Sample data: {companies_data.head(2).to_dict()}")
        
        # Load index data
        print("\n3. LOADING INDEX DATA...")
        index_file = 'data/sp500_index.csv'
        if not os.path.exists(index_file):
            print(f"❌ ERROR: {index_file} not found!")
            return False
        
        print(f"   📂 Loading from: {index_file}")
        index_data = pd.read_csv(index_file)
        index_data['Date'] = pd.to_datetime(index_data['Date'])
        print(f"✅ SUCCESS: Loaded {len(index_data)} index records")
        print(f"   📊 Columns: {list(index_data.columns)}")
        print(f"   📅 Date range: {index_data['Date'].min()} to {index_data['Date'].max()}")
        
        # Load stocks data in chunks to handle large file
        print("\n4. LOADING STOCKS DATA...")
        stocks_file = 'data/sp500_stocks.csv'
        if not os.path.exists(stocks_file):
            print(f"❌ ERROR: {stocks_file} not found!")
            return False
        
        # Get file size
        file_size = os.path.getsize(stocks_file)
        file_size_mb = file_size / (1024 * 1024)
        print(f"   📂 Loading from: {stocks_file}")
        print(f"   📏 File size: {file_size_mb:.2f} MB")
        
        chunks = []
        chunk_size = 50000  # Reduced chunk size for better memory management
        print(f"   🔄 Processing in chunks of {chunk_size:,} records...")
        
        print("   📊 Processing stock data in chunks...")
        chunk_count = 0
        total_records_processed = 0
        valid_records = 0
        
        for chunk in pd.read_csv(stocks_file, chunksize=chunk_size):
            chunk_count += 1
            chunk_records = len(chunk)
            total_records_processed += chunk_records
            
            print(f"   📦 Chunk {chunk_count}: {chunk_records:,} records (Total processed: {total_records_processed:,})")
            
            # Check chunk columns
            if chunk_count == 1:
                print(f"   📋 Columns found: {list(chunk.columns)}")
                print(f"   🔍 Sample record: {chunk.iloc[0].to_dict()}")
            
            # Filter out rows with empty price data - use Open instead of Close
            chunk_before = len(chunk)
            chunk = chunk.dropna(subset=['Open'])
            chunk_after = len(chunk)
            valid_records += chunk_after
            
            if chunk_before != chunk_after:
                print(f"   🧹 Filtered out {chunk_before - chunk_after:,} records with missing Open prices")
            
            if not chunk.empty:
                chunks.append(chunk)
                print(f"   ✅ Added chunk with {len(chunk):,} valid records")
            else:
                print(f"   ⚠️  Chunk {chunk_count} had no valid records after filtering")
            
            # Process all available data (removed artificial limit)
            # Note: This will process the full dataset for complete analysis
        
        print(f"\n   📈 CHUNK PROCESSING SUMMARY:")
        print(f"   📊 Total chunks processed: {chunk_count}")
        print(f"   📊 Total records processed: {total_records_processed:,}")
        print(f"   📊 Valid records found: {valid_records:,}")
        print(f"   📊 Chunks with data: {len(chunks)}")
        
        if not chunks:
            print("❌ ERROR: No valid stock data found!")
            return False
            
        print(f"\n   🔗 Concatenating {len(chunks)} chunks...")
        stocks_data = pd.concat(chunks, ignore_index=True)
        stocks_data['Date'] = pd.to_datetime(stocks_data['Date'])
        print(f"✅ SUCCESS: Loaded {len(stocks_data):,} stock records")
        print(f"   📊 Final DataFrame shape: {stocks_data.shape}")
        print(f"   📊 Columns: {list(stocks_data.columns)}")
        print(f"   📅 Date range: {stocks_data['Date'].min()} to {stocks_data['Date'].max()}")
        print(f"   🏢 Unique symbols: {stocks_data['Symbol'].nunique()}")
        
        # Calculate daily price changes based on previous day opening vs current day opening price
        print("\n5. CALCULATING DAILY PRICE CHANGES...")
        print("   🔄 Sorting data by Symbol and Date...")
        stocks_data = stocks_data.sort_values(['Symbol', 'Date'])
        
        print("   📊 Calculating previous day opening prices...")
        stocks_data['Prev_Day_Open'] = stocks_data.groupby('Symbol')['Open'].shift(1)
        
        print("   📈 Calculating daily change percentages...")
        stocks_data['Daily_Change_Pct'] = ((stocks_data['Open'] - stocks_data['Prev_Day_Open']) / stocks_data['Prev_Day_Open']) * 100
        
        print("   📊 Calculating intraday change percentages...")
        stocks_data['Intraday_Change_Pct'] = ((stocks_data['Close'] - stocks_data['Open']) / stocks_data['Open']) * 100
        
        print("   🔗 Merging with company names...")
        stocks_data = stocks_data.merge(
            companies_data[['Symbol', 'Shortname']], 
            on='Symbol', 
            how='left'
        )
        
        print("\n" + "=" * 60)
        print("🎉 DATA LOADING COMPLETE!")
        print("=" * 60)
        print(f"✅ Total stock records: {len(stocks_data):,}")
        print(f"✅ Unique stocks: {stocks_data['Symbol'].nunique()}")
        print(f"✅ Date range: {stocks_data['Date'].min().strftime('%Y-%m-%d')} to {stocks_data['Date'].max().strftime('%Y-%m-%d')}")
        print(f"✅ Companies loaded: {len(companies_data):,}")
        print(f"✅ Index records: {len(index_data):,}")
        print(f"✅ Memory usage: {stocks_data.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ CRITICAL ERROR DURING DATA LOADING!")
        print("=" * 60)
        print(f"❌ Error type: {type(e).__name__}")
        print(f"❌ Error message: {str(e)}")
        print("\n📋 Full traceback:")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return False

def initialize_data_on_import():
    """Initialize data when module is imported (works under gunicorn)."""
    try:
        print("🚀 Starting S&P 500 Price Dip Analysis App...")
        print("📊 Initializing data loading process...")
        ok = load_and_process_data()
        if not ok:
            print("❌ CRITICAL ERROR: Failed to load data. App will not function properly.")
            print("Please check that all data files are present in the 'data/' directory.")
        else:
            print("✅ App started successfully with data loaded!")
    except Exception as e:
        print(f"❌ Startup error: {e}")
        import traceback
        traceback.print_exc()

# Call initializer at import time so it runs under gunicorn
initialize_data_on_import()

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
    track_user_action('page_view', {'page': 'main_dashboard'})
    return render_template('index.html')

@app.route('/test')
def test():
    """Simple test endpoint"""
    return jsonify({
        'message': 'App is running!',
        'timestamp': datetime.now().isoformat(),
        'data_status': {
            'stocks_loaded': stocks_data is not None,
            'companies_loaded': companies_data is not None
        }
    })

@app.route('/health')
def health():
    """Health check endpoint for debugging"""
    global stocks_data, companies_data, index_data
    
    import os
    
    health_status = {
        'status': 'healthy',
        'environment': {
            'python_version': os.sys.version,
            'working_directory': os.getcwd(),
            'files_in_directory': os.listdir('.'),
            'data_directory_exists': os.path.exists('data'),
            'data_files': os.listdir('data') if os.path.exists('data') else []
        },
        'data_loaded': {
            'stocks_data': stocks_data is not None,
            'companies_data': companies_data is not None,
            'index_data': index_data is not None
        },
        'data_counts': {}
    }
    
    if stocks_data is not None:
        health_status['data_counts']['stocks_records'] = len(stocks_data)
        health_status['data_counts']['unique_stocks'] = stocks_data['Symbol'].nunique()
        health_status['data_counts']['date_range'] = {
            'start': stocks_data['Date'].min().strftime('%Y-%m-%d'),
            'end': stocks_data['Date'].max().strftime('%Y-%m-%d')
        }
    else:
        health_status['data_counts']['stocks_records'] = 0
        health_status['data_counts']['unique_stocks'] = 0
    
    if companies_data is not None:
        health_status['data_counts']['companies'] = len(companies_data)
    else:
        health_status['data_counts']['companies'] = 0
    
    if index_data is not None:
        health_status['data_counts']['index_records'] = len(index_data)
    else:
        health_status['data_counts']['index_records'] = 0
    
    return jsonify(health_status)

@app.route('/stock_history')
def stock_history():
    """Stock history page"""
    track_user_action('page_view', {'page': 'stock_history'})
    return render_template('stock_history.html')

@app.route('/api/significant_declines')
def api_significant_declines():
    """API endpoint to get combined decline and recovery data"""
    track_user_action('api_call', {'endpoint': '/api/significant_declines'}, '/api/significant_declines')
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
    track_user_action('api_call', {'endpoint': '/api/stocks'}, '/api/stocks')
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
    track_user_action('api_call', {'endpoint': '/api/stock_history'}, '/api/stock_history')
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
    track_user_action('api_call', {'endpoint': '/api/recovery_stats'}, '/api/recovery_stats')
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
    track_user_action('api_call', {'endpoint': '/api/stats'}, '/api/stats')
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

# Admin Dashboard Routes
@app.route('/admin')
def admin_dashboard():
    """Admin dashboard page - accessible to all users"""
    track_user_action('page_view', {'page': 'admin_dashboard'})
    return render_template('admin_dashboard.html')

@app.route('/api/admin/analytics')
def api_admin_analytics():
    """API endpoint for admin analytics data"""
    track_user_action('api_call', {'endpoint': '/api/admin/analytics'}, '/api/admin/analytics')
    try:
        analytics_data = get_analytics_summary()
        return jsonify({
            'success': True,
            'data': analytics_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/admin/sessions')
def api_admin_sessions():
    """API endpoint to get detailed session data"""
    track_user_action('api_call', {'endpoint': '/api/admin/sessions'}, '/api/admin/sessions')
    try:
        global user_analytics
        
        # Get session details
        sessions_data = []
        for session_id, session_info in user_analytics['sessions'].items():
            sessions_data.append({
                'session_id': session_id,
                'first_visit': session_info['first_visit'],
                'last_activity': session_info['last_activity'],
                'user_agent': session_info['user_agent'],
                'ip_address': session_info['ip_address'],
                'page_views': session_info['page_views'],
                'api_calls': session_info['api_calls'],
                'total_actions': len(session_info['actions'])
            })
        
        # Sort by last activity (most recent first)
        sessions_data.sort(key=lambda x: x['last_activity'], reverse=True)
        
        return jsonify({
            'success': True,
            'sessions': sessions_data[:50]  # Limit to 50 most recent sessions
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/admin/actions')
def api_admin_actions():
    """API endpoint to get detailed user actions"""
    track_user_action('api_call', {'endpoint': '/api/admin/actions'}, '/api/admin/actions')
    try:
        global user_analytics
        
        # Get recent actions with more details
        recent_actions = user_analytics['user_actions'][-100:]  # Last 100 actions
        
        return jsonify({
            'success': True,
            'actions': recent_actions
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    # For local development
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting Flask app on port {port}")
    app.run(debug=False, host='0.0.0.0', port=port)
