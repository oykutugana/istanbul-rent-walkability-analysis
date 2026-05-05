"""
FAIL durumundaki 19 mahalleyi analiz eder + listing etkisini hesaplar.
"""
import pandas as pd

DATA_PATH = '../data/istanbul_emlak_final.csv'
COORD_PATH = '../data/neighborhood_coordinates.csv'

df = pd.read_csv(DATA_PATH)
coords = pd.read_csv(COORD_PATH)

print(f"Koordinat tablosu: {len(coords)} satir")
print(f"Strategy dagilimi:")
print(coords['strategy'].value_counts())

# FAIL'leri ayikla
fails = coords[coords['strategy'] == 'FAIL']
print(f"\n=== {len(fails)} FAIL MAHALLESI ===")
print(fails[['district', 'neighborhood']].to_string(index=False))

# Listing etkisi: bu mahallelerde kac listing var?
fail_keys = set(zip(fails['district'], fails['neighborhood']))
df['key'] = list(zip(df['district'], df['neighborhood']))
affected = df[df['key'].isin(fail_keys)]

print(f"\n=== ETKILENEN LISTING SAYISI ===")
print(f"Toplam: {len(affected)} ({100*len(affected)/len(df):.2f}%)")

print(f"\nMahalle bazinda dagilim:")
print(affected.groupby(['district', 'neighborhood']).size().sort_values(ascending=False).to_string())

# Fallback olanlari da gorelim
fallbacks = coords[coords['strategy'] == 'fallback']
fb_keys = set(zip(fallbacks['district'], fallbacks['neighborhood']))
fb_affected = df[df['key'].isin(fb_keys)]
print(f"\n=== FALLBACK LISTING SAYISI ===")
print(f"Toplam: {len(fb_affected)} ({100*len(fb_affected)/len(df):.2f}%)")