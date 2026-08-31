import csv

FILENAME = "USDBDT_otc_M1_history.csv"

total_rows = 0
valid_rows = 0
invalid_rows = 0
duplicate_timestamps = 0
issues = []

seen_timestamps = set()

with open(FILENAME, mode="r") as file:
    reader = csv.DictReader(file)

    for row in reader:
        total_rows += 1

        try:
            timestamp = int(row["timestamp"])
            open_price = float(row["open"])
            high = float(row["high"])
            low = float(row["low"])
            close = float(row["close"])
        except (ValueError, TypeError):
            invalid_rows += 1
            issues.append(f"Row {total_rows}: missing/invalid numeric value")
            continue

        # Duplicate timestamp check
        if timestamp in seen_timestamps:
            duplicate_timestamps += 1
        seen_timestamps.add(timestamp)

        # OHLC logic check (document Section 10/12 ke rules)
        if high < low:
            invalid_rows += 1
            issues.append(f"Row {total_rows}: High ({high}) < Low ({low})")
            continue

        if high < open_price or high < close:
            invalid_rows += 1
            issues.append(f"Row {total_rows}: High is lower than Open/Close")
            continue

        if low > open_price or low > close:
            invalid_rows += 1
            issues.append(f"Row {total_rows}: Low is higher than Open/Close")
            continue

        valid_rows += 1

print("========== VALIDATION REPORT ==========")
print(f"Total rows checked:     {total_rows}")
print(f"Valid candles:          {valid_rows}")
print(f"Invalid candles:        {invalid_rows}")
print(f"Duplicate timestamps:   {duplicate_timestamps}")
print("========================================")

if issues:
    print("\nSample issues (first 10):")
    for issue in issues[:10]:
        print(" -", issue)
else:
    print("\n✅ No issues found. Data looks clean!")