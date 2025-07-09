import csv

def test_csv_parsing(file_path):
    print(f"Testing CSV file: {file_path}")
    print("=" * 80)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        # Read first 10 lines to check the structure
        for i, line in enumerate(f):
            if i >= 10:  # Only read first 10 lines
                break
            print(f"Line {i+1}: {line.strip()}")
    
    # Now try reading with csv.DictReader
    print("\nTrying to parse with csv.DictReader...")
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        print(f"Field names: {reader.fieldnames}")
        
        # Print first 3 rows of data
        print("\nFirst 3 rows of data:")
        for i, row in enumerate(reader):
            if i >= 3:  # Only show first 3 rows
                break
            print(f"Row {i+1}:")
            for key, value in row.items():
                print(f"  {key}: {value}")
            print()

if __name__ == "__main__":
    test_csv_parsing("c:\\temp\\TwinFallsStakeChanges.csv")
