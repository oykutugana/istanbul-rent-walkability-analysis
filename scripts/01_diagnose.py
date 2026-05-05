"""
Mahalle isimlerinde temizlik gerektiren durumlari tani.
Hicbir veriyi degistirmez, sadece raporlar.
"""
import pandas as pd

DATA_PATH = '../data/istanbul_emlak_final.csv'

df = pd.read_csv(DATA_PATH)

print(f"Toplam listing: {len(df)}")
print(f"Unique district: {df['district'].nunique()}")
print(f"Unique mahalle: {df['neighborhood'].nunique()}")
print()

# Parantezli mahalleler
parantezli = df[df['neighborhood'].str.contains(r'\(', regex=True, na=False)]
print(f"=== PARANTEZLI MAHALLELER ===")
print(f"Listing sayisi: {len(parantezli)}")
if len(parantezli) > 0:
    print("\nUnique parantezli isimler:")
    print(parantezli[['district', 'neighborhood']].drop_duplicates().to_string(index=False))

print()

# 'mahallesi/mah' kelimesi iceren
mah_keyword = df[df['neighborhood'].str.contains(r'mahalle|mah\.', regex=True, na=False, case=False)]
print(f"=== 'MAHALLESI/MAH.' KELIMESI ICEREN ===")
print(f"Listing sayisi: {len(mah_keyword)}")
if len(mah_keyword) > 0:
    print(f"Ornek (ilk 15):")
    print(mah_keyword[['district', 'neighborhood']].drop_duplicates().head(15).to_string(index=False))

print()

# Bos ya da NaN
nan_count = df['neighborhood'].isna().sum()
empty_count = (df['neighborhood'].astype(str).str.strip() == '').sum()
print(f"=== EKSIK DEGERLER ===")
print(f"NaN: {nan_count}")
print(f"Bos string: {empty_count}")

print()

# Anormal uzunluk
short = df[df['neighborhood'].astype(str).str.len() < 3]
long_n = df[df['neighborhood'].astype(str).str.len() > 30]
print(f"=== ANORMAL UZUNLUK ===")
print(f"3 karakterden kisa: {len(short)}")
if len(short) > 0:
    print(f"  Ornek: {short['neighborhood'].unique()[:5]}")
print(f"30 karakterden uzun: {len(long_n)}")
if len(long_n) > 0:
    print(f"  Ornek: {long_n['neighborhood'].unique()[:3]}")

print()

# Sayisal karakter iceren
numeric = df[df['neighborhood'].astype(str).str.contains(r'\d', regex=True, na=False)]
print(f"=== RAKAM ICEREN ===")
print(f"Listing sayisi: {len(numeric)}")
if len(numeric) > 0:
    print(f"Unique isimler: {numeric['neighborhood'].unique()}")

print()

# Ozel karakterler (parantez disi)
special = df[df['neighborhood'].astype(str).str.contains(r'[^a-z0-9 ]', regex=True, na=False)]
print(f"=== OZEL KARAKTER (parantez disi dahil) ===")
print(f"Listing sayisi: {len(special)}")
if len(special) > 0:
    print(f"Unique isimler (ilk 20):")
    print(special['neighborhood'].unique()[:20])

print()

# Yaygin sentinel ('merkez', 'cumhuriyet') sayilari
print(f"=== EN YAYGIN MAHALLE ISIMLERI ===")
print(df['neighborhood'].value_counts().head(10))