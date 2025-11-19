#!/usr/bin/env python3
"""
Simple test script to validate benchmark service improvements
"""

import sys
import os
import traceback
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.benchmark_service import BenchmarkService

def test_benchmark_service():
    """Test the benchmark service with some error handling"""
    
    print("Testing benchmark service improvements...")
    
    # Test with a valid benchmark
    benchmark_id = 'CSI300'
    
    # Define date range
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
    
    print(f"Attempting to fetch {benchmark_id} data from {start_date} to {end_date}")
    
    try:
        # Test the benchmark service
        df = BenchmarkService.get_benchmark_data(
            benchmark_id=benchmark_id,
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"✓ Successfully fetched {len(df)} rows of data for {benchmark_id}")
        print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"  Columns: {list(df.columns)}")
        
        # Test benchmark metrics calculation
        returns = BenchmarkService.calculate_benchmark_returns(df)
        print(f"  Calculated {len(returns)} return values")
        
        equity = BenchmarkService.calculate_benchmark_equity(df)
        print(f"  Calculated {len(equity)} equity values")
        
    except Exception as e:
        print(f"✗ Error fetching benchmark data: {str(e)}")
        print(f"  Error type: {type(e).__name__}")
        traceback.print_exc()
        return False
    
    # Test with an invalid date range to simulate network issues
    print("\nTesting error handling with potentially problematic dates...")
    try:
        # This might cause issues if the dates are too far in the past or future
        df = BenchmarkService.get_benchmark_data(
            benchmark_id=benchmark_id,
            start_date='20000101',  # Very old date
            end_date=end_date
        )
        print(f"✓ Successfully fetched data for wider date range")
    except Exception as e:
        print(f"! Expected or handled error for wide date range: {str(e)}")
    
    print("\nTesting benchmark list...")
    try:
        benchmarks = BenchmarkService.get_benchmark_list()
        print(f"✓ Available benchmarks: {[b['name'] for b in benchmarks]}")
    except Exception as e:
        print(f"✗ Error getting benchmark list: {str(e)}")
        traceback.print_exc()
        return False
    
    print("\nAll tests completed successfully!")
    return True

if __name__ == "__main__":
    success = test_benchmark_service()
    if success:
        print("\n✓ Benchmark service test completed successfully!")
        sys.exit(0)
    else:
        print("\n✗ Benchmark service test failed!")
        sys.exit(1)