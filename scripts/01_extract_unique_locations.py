"""
01_extract_unique_locations.py

P1 ciktisindan unique (district, sub_district, neighborhood) kombinasyonlarini cikarir.
Geocoding pipeline'in giris adimi.

Run:
    python 01_extract_unique_locations.py
"""

import pandas as pd
from pathlib import Path

# Paths
INPUT  = Path("../data/istanbul_emlak_final.csv")
OUTPUT = Path("../data/unique_locations.csv")

def main():
    df = pd.read_csv(INPUT)
    print(f"Loaded {len(df):,} listings from {INPUT.name}")

    # Unique (district, sub_district, neighborhood) kombinasyonlari
    cols = ["district", "sub_district", "neighborhood"]
    unique = (
        df[cols]
        .dropna()
        .drop_duplicates()
        .sort_values(cols)
        .reset_index(drop=True)
    )
    unique["location_id"] = range(len(unique))

    # Her unique konuma kac listing dustugunu say (bilgi amacli)
    counts = df.groupby(cols).size().reset_index(name="listing_count")
    unique = unique.merge(counts, on=cols, how="left")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    unique.to_csv(OUTPUT, index=False)

    print(f"\nUnique locations:        {len(unique):,}")
    print(f"Districts covered:        {unique['district'].nunique()}")
    print(f"Sub-districts covered:    {unique['sub_district'].nunique()}")
    print(f"Listings per location:    median={unique['listing_count'].median():.0f}, "
          f"max={unique['listing_count'].max()}")
    print(f"\nSaved to {OUTPUT}")

if __name__ == "__main__":
    main()