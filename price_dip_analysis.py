#!/usr/bin/env python3
"""
Price Dip Analysis Tool
=======================

A comprehensive analysis tool for S&P 500 significant price declines and recovery patterns.

This script provides:
- Detection of stocks with significant daily price declines
- Analysis of recovery times from low prices
- Statistical summaries of recovery patterns
- Time-based recovery percentage analysis

Usage:
    python price_dip_analysis.py

Author: S&P 500 Analysis System
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Add the current directory to Python path to import from app.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import load_and_process_data, get_significant_declines, get_combined_data, calculate_recovery_statistics

def main():
    print("S&P 500 Price Dip Analysis Tool")
    print("=" * 50)
    print("Loading and processing data...")
    
    # Load and process data
    load_and_process_data()
    
    print("\n1. Finding all stocks with >20% daily declines:")
    declines = get_significant_declines(threshold=-20)
    print(f"Found {len(declines)} significant declines")
    
    if not declines.empty:
        print("\nTop 10 worst single-day declines:")
        print("-" * 80)
        print(f"{'Date':<12} {'Symbol':<8} {'Company':<35} {'Change %':<10} {'Close Price':<12}")
        print("-" * 80)
        
        top_10 = declines.head(10)
        for _, row in top_10.iterrows():
            company_name = row['Shortname'] if pd.notna(row['Shortname']) else row['Symbol']
            if len(company_name) > 35:
                company_name = company_name[:32] + "..."
            print(f"{row['Date'].strftime('%Y-%m-%d'):<12} {row['Symbol']:<8} {company_name:<35} "
                  f"{row['Daily_Change_Pct']:<10.2f} ${row['Close']:<11.2f}")
    
    print(f"\n\n2. Finding significant declines in 2024:")
    start_date = pd.to_datetime('2024-01-01')
    end_date = pd.to_datetime('2024-12-31')
    declines_2024 = get_significant_declines(threshold=-20, start_date=start_date, end_date=end_date)
    print(f"Found {len(declines_2024)} significant declines in 2024")
    
    if not declines_2024.empty:
        print("\nAll significant declines in 2024:")
        print("-" * 80)
        print(f"{'Date':<12} {'Symbol':<8} {'Company':<35} {'Change %':<10} {'Close Price':<12}")
        print("-" * 80)
        
        for _, row in declines_2024.iterrows():
            company_name = row['Shortname'] if pd.notna(row['Shortname']) else row['Symbol']
            if len(company_name) > 35:
                company_name = company_name[:32] + "..."
            print(f"{row['Date'].strftime('%Y-%m-%d'):<12} {row['Symbol']:<8} {company_name:<35} "
                  f"{row['Daily_Change_Pct']:<10.2f} ${row['Close']:<11.2f}")
    
    print(f"\n\n3. Finding significant declines for Apple (AAPL):")
    aapl_declines = get_significant_declines(threshold=-20, symbol='AAPL')
    if not aapl_declines.empty:
        print(f"Found {len(aapl_declines)} significant declines for AAPL")
        for _, row in aapl_declines.iterrows():
            print(f"Date: {row['Date'].strftime('%Y-%m-%d')}, Change: {row['Daily_Change_Pct']:.2f}%")
    else:
        print("No significant declines found for AAPL")
    
    print(f"\n\n4. Worst single-day decline in the dataset:")
    if not declines.empty:
        worst_decline = declines.loc[declines['Daily_Change_Pct'].idxmin()]
        print(f"Date: {worst_decline['Date'].strftime('%Y-%m-%d')}")
        print(f"Stock: {worst_decline['Symbol']} ({worst_decline['Shortname'] if pd.notna(worst_decline['Shortname']) else 'N/A'})")
        print(f"Daily Change: {worst_decline['Daily_Change_Pct']:.2f}%")
    
    # Recovery time analysis
    print("\n\n5. Recovery Time Analysis:")
    print("=" * 50)
    
    # Get recovery times for all significant declines
    recovery_data = get_combined_data(threshold=-20)
    
    if not recovery_data.empty:
        print(f"Found {len(recovery_data)} stocks with significant declines and recovery data")
        
        # Show recovery times for the worst single-day decline
        worst_decline = recovery_data.loc[recovery_data['decline_pct'].idxmin()]
        print(f"\nRecovery times for the worst decline ({worst_decline['symbol']} on {worst_decline['date'].strftime('%Y-%m-%d')}):")
        print(f"Decline: {worst_decline['decline_pct']:.2f}%")
        print(f"Low Price: ${worst_decline['low_price']:.2f}")
        
        recovery_targets = [10, 20, 30, 40, 50, 75, 100]
        for target in recovery_targets:
            days_key = f'recover_{target}pct_days'
            days = worst_decline[days_key]
            if pd.notna(days):
                print(f"  +{target}% from low: {int(days)} days")
            else:
                print(f"  +{target}% from low: Not yet recovered")
    else:
        print("No recovery data found")
    
    # Recovery statistics
    print("\n\n6. Recovery Statistics:")
    print("=" * 50)
    
    stats = calculate_recovery_statistics(threshold=-20)
    
    if stats['total_stocks'] > 0:
        print(f"Total stocks analyzed: {stats['total_stocks']}")
        
        # Show averages for each recovery target
        recovery_targets = [10, 20, 30, 40, 50, 75, 100]
        print(f"\nAverage recovery times:")
        print("-" * 60)
        print(f"{'Target':<8} {'Avg Days':<10} {'Median':<10} {'Min':<8} {'Max':<8} {'Recovered':<10} {'Rate':<8}")
        print("-" * 60)
        
        for target in recovery_targets:
            target_key = f'{target}pct'
            if target_key in stats['averages']:
                avg_data = stats['averages'][target_key]
                if avg_data['average_days'] is not None:
                    print(f"+{target}%:    {avg_data['average_days']:<10.1f} {avg_data['median_days']:<10.1f} "
                          f"{avg_data['min_days']:<8} {avg_data['max_days']:<8} "
                          f"{avg_data['recovered_count']:<10} {avg_data['recovery_rate']:<8.1f}%")
                else:
                    print(f"+{target}%:    {'N/A':<10} {'N/A':<10} {'N/A':<8} {'N/A':<8} "
                          f"{avg_data['recovered_count']:<10} {avg_data['recovery_rate']:<8.1f}%")
        
        # Show percentage statistics
        print(f"\nRecovery percentages within timeframes:")
        print("-" * 60)
        print(f"{'Target':<15} {'Timeframe':<12} {'Count':<8} {'Percentage':<12}")
        print("-" * 60)
        
        percentages = stats['percentages']
        print(f"+10% recovery:   {'30 days':<12} {percentages['10pct_30days']['count']:<8} {percentages['10pct_30days']['percentage']:<12.1f}%")
        print(f"+10% recovery:   {'60 days':<12} {percentages['10pct_60days']['count']:<8} {percentages['10pct_60days']['percentage']:<12.1f}%")
        print(f"+20% recovery:   {'30 days':<12} {percentages['20pct_30days']['count']:<8} {percentages['20pct_30days']['percentage']:<12.1f}%")
        print(f"+20% recovery:   {'60 days':<12} {percentages['20pct_60days']['count']:<8} {percentages['20pct_60days']['percentage']:<12.1f}%")
        print(f"+30% recovery:   {'90 days':<12} {percentages['30pct_90days']['count']:<8} {percentages['30pct_90days']['percentage']:<12.1f}%")
    else:
        print("No recovery statistics available")
    
    # Show recovery times for recent 2024 declines
    print(f"\n\n7. Recovery Times for 2024 Declines:")
    print("=" * 50)
    
    recovery_2024 = get_combined_data(threshold=-20, start_date=start_date, end_date=end_date)
    
    if not recovery_2024.empty:
        print(f"Found {len(recovery_2024)} stocks with 2024 declines and recovery data")
        
        print(f"\nDetailed recovery data for 2024 declines:")
        print("-" * 120)
        print(f"{'Date':<12} {'Symbol':<8} {'Company':<25} {'Decline':<8} {'Open':<8} {'Close':<8} {'+10%':<6} {'+20%':<6} {'+30%':<6} {'+50%':<6} {'+100%':<6}")
        print("-" * 120)
        
        for _, row in recovery_2024.iterrows():
            company_name = row['company_name'][:25] if len(row['company_name']) > 25 else row['company_name']
            
            # Format recovery days
            recover_10 = f"{int(row['recover_10pct_days'])}d" if pd.notna(row['recover_10pct_days']) else "N/A"
            recover_20 = f"{int(row['recover_20pct_days'])}d" if pd.notna(row['recover_20pct_days']) else "N/A"
            recover_30 = f"{int(row['recover_30pct_days'])}d" if pd.notna(row['recover_30pct_days']) else "N/A"
            recover_50 = f"{int(row['recover_50pct_days'])}d" if pd.notna(row['recover_50pct_days']) else "N/A"
            recover_100 = f"{int(row['recover_100pct_days'])}d" if pd.notna(row['recover_100pct_days']) else "N/A"
            
            print(f"{row['date'].strftime('%Y-%m-%d'):<12} {row['symbol']:<8} {company_name:<25} "
                  f"{row['decline_pct']:<8.1f}% ${row['open_price']:<7.2f} ${row['decline_price']:<7.2f} {recover_10:<6} {recover_20:<6} {recover_30:<6} {recover_50:<6} {recover_100:<6}")
    else:
        print("No 2024 recovery data found")
    
    # List all available stocks
    print(f"\n\n8. Available Stocks in Database:")
    print("=" * 50)
    
    # Get unique stocks from the global data
    from app import stocks_data, companies_data
    
    unique_stocks = stocks_data[['Symbol']].drop_duplicates()
    stocks_with_names = unique_stocks.merge(
        companies_data[['Symbol', 'Shortname']], 
        on='Symbol', 
        how='left'
    )
    
    print(f"Total stocks available: {len(stocks_with_names)}")
    print("\nFirst 20 stocks:")
    print("-" * 60)
    print(f"{'Symbol':<8} {'Company Name':<40}")
    print("-" * 60)
    
    for i, (_, row) in enumerate(stocks_with_names.head(20).iterrows()):
        company_name = row['Shortname'] if pd.notna(row['Shortname']) else row['Symbol']
        if len(company_name) > 40:
            company_name = company_name[:37] + "..."
        print(f"{row['Symbol']:<8} {company_name:<40}")
    
    if len(stocks_with_names) > 20:
        print(f"... and {len(stocks_with_names) - 20} more stocks")
    
    print(f"\n\n9. Summary:")
    print("=" * 50)
    print("This analysis shows:")
    print("- Stocks with significant intraday price declines (>20%)")
    print("- Recovery times from low prices (days to reach +10%, +20%, +30%, etc.)")
    print("- Statistical patterns in recovery behavior")
    print("- Time-based recovery success rates")
    print("- Complete list of all available stocks in the database")
    
    print("\nYou can also use the API endpoints:")
    print("- GET /api/stats - Get dataset statistics")
    print("- GET /api/significant_declines - Get combined decline and recovery data")
    print("- GET /api/recovery_stats - Get recovery statistics")
    print("- GET /api/stocks - Get all available stocks")
    print("- GET /api/stock_history - Get stock price history")

if __name__ == "__main__":
    main()
