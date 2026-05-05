"""
Mahalle isimlerinden parantezli ve slash'li ekleri temizler.
- 'celaliye(kamiloba)' -> 'celaliye'
- 'rahmanlar (atalar)' -> 'rahmanlar'
- 'barbaros/yesilbag' -> 'barbaros'

valide-i atik, 19 mayis gibi mesru isimlere dokunmaz.
"""
import pandas as pd
import shutil
import os

DATA_PATH = '../data/istanbul_emlak_final.csv'
BACKUP_PATH = '../data/istanbul_emlak_final_BEFORE_CLEAN.csv'

# Once yedek al
if not os.path.exists(BACKUP_PATH):
    shutil.copy(DATA_PATH, BACKUP_PATH)
    print(f"Yedek alindi: {BACKUP_PATH}")
else:
    print(f"Yedek zaten var: {BACKUP_PATH}")

df = pd.read_csv(DATA_PATH)
print(f"\nIslem oncesi: {len(df)} listing, {df['neighborhood'].nunique()} unique mahalle")

# Parantezden ve slash'tan oncesini al
def clean_name(name):
    s = str(name)
    # Once parantez
    if '(' in s:
        s = s.split('(')[0]
    # Sonra slash
    if '/' in s:
        s = s.split('/')[0]
    return s.strip()

# Once degisecekleri rapor et
df['neighborhood_new'] = df['neighborhood'].apply(clean_name)
changes = df[df['neighborhood'] != df['neighborhood_new']]

print(f"\n=== DEGISIKLIKLER ===")
print(f"Etkilenen listing sayisi: {len(changes)}")
if len(changes) > 0:
    print(f"\nDegisecek mahalleler:")
    summary = changes.groupby(['neighborhood', 'neighborhood_new']).size().reset_index(name='count')
    print(summary.to_string(index=False))

# Onayla ve uygula
df['neighborhood'] = df['neighborhood_new']
df = df.drop(columns=['neighborhood_new'])

df.to_csv(DATA_PATH, index=False)
print(f"\nIslem sonrasi: {len(df)} listing, {df['neighborhood'].nunique()} unique mahalle")
print(f"Kaydedildi: {DATA_PATH}")
print(f"Geri almak icin: cp {BACKUP_PATH} {DATA_PATH}")