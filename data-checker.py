#!/usr/bin/env python3
"""
Script to inspect the dataframe of a parquet file.
Usage: python data-checker.py <parquet_file_path>
"""

import sys
import pandas as pd
import argparse
from pathlib import Path


def inspect_parquet_file(file_path):
    """Inspect a parquet file and display comprehensive information."""
    try:
        # Read the parquet file
        print(f"📁 Loading parquet file: {file_path}")
        df = pd.read_parquet(file_path)
        
        # Basic information
        print(f"\n📊 Basic Information:")
        print(f"   Shape: {df.shape} (rows, columns)")
        print(f"   Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        
        # Column information
        print(f"\n📋 Column Information:")
        for col in df.columns:
            dtype = df[col].dtype
            non_null_count = df[col].count()
            null_count = df[col].isnull().sum()
            unique_count = df[col].nunique()
            
            print(f"   {col}:")
            print(f"     Type: {dtype}")
            print(f"     Non-null: {non_null_count:,}")
            print(f"     Null: {null_count:,}")
            print(f"     Unique: {unique_count:,}")
            
            # Show sample values for object columns
            if dtype == 'object' and unique_count <= 10:
                sample_values = df[col].dropna().unique()[:5]
                print(f"     Sample values: {list(sample_values)}")
            elif dtype in ['int64', 'float64']:
                print(f"     Min: {df[col].min():.2f}")
                print(f"     Max: {df[col].max():.2f}")
                print(f"     Mean: {df[col].mean():.2f}")
            print()
        
        # Show first few rows
        print(f"\n👁️  First 5 rows:")
        print(df.head())
        
        # Show last few rows if dataframe is large
        if len(df) > 10:
            print(f"\n👁️  Last 5 rows:")
            print(df.tail())
        
        # Data types summary
        print(f"\n📈 Data Types Summary:")
        dtype_counts = df.dtypes.value_counts()
        for dtype, count in dtype_counts.items():
            print(f"   {dtype}: {count} columns")
        
        # Check for duplicates
        duplicate_count = df.duplicated().sum()
        if duplicate_count > 0:
            print(f"\n⚠️  Found {duplicate_count:,} duplicate rows")
        else:
            print(f"\n✅ No duplicate rows found")
            
        return df
        
    except FileNotFoundError:
        print(f"❌ Error: File '{file_path}' not found")
        return None
    except Exception as e:
        print(f"❌ Error reading parquet file: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description='Inspect a parquet file')
    parser.add_argument('file_path', help='Path to the parquet file')
    parser.add_argument('--sample', type=int, help='Number of rows to sample and display')
    
    args = parser.parse_args()
    
    file_path = Path(args.file_path)
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    
    df = inspect_parquet_file(file_path)
    
    if df is not None and args.sample:
        print(f"\n🎲 Random sample of {args.sample} rows:")
        print(df.sample(min(args.sample, len(df))))
    
    if df is not None:
        print(f"\n✅ Inspection complete!")


if __name__ == "__main__":
    main()