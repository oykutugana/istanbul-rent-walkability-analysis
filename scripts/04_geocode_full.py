"""
382 mahalle icin tam geocoding pipeline.
- Cache mekanizmasi: cokerse kaldigi yerden devam eder
- Progress raporu
- Output: data/neighborhood_coordinates.csv
"""
import pandas as pd
import os
import time
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

DATA_PATH = '../data/istanbul_emlak_final.csv'
OUTPUT_PATH = '../data/neighborhood_coordinates.csv'

geolocator = Nominatim(user_agent="istanbul_rent_24018020_full")
geocode_raw = RateLimiter(
    lambda q: geolocator.geocode(q, addressdetails=True, exactly_one=True),
    min_delay_seconds=1.1
)

ISTANBUL_BBOX = {'lat_min': 40.80, 'lat_max': 41.30, 'lon_min': 28.55, 'lon_max': 29.55}

DISTRICT_TR = {
    'avcilar': 'avcılar', 'esenler': 'esenler', 'bagcilar': 'bağcılar',
    'buyukcekmece': 'büyükçekmece', 'kartal': 'kartal', 'beyoglu': 'beyoğlu',
    'fatih': 'fatih', 'uskudar': 'üsküdar', 'sisli': 'şişli',
    'kadikoy': 'kadıköy', 'besiktas': 'beşiktaş', 'umraniye': 'ümraniye',
    'sariyer': 'sarıyer', 'maltepe': 'maltepe', 'pendik': 'pendik',
    'sancaktepe': 'sancaktepe', 'eyupsultan': 'eyüp', 'kucukcekmece': 'küçükçekmece',
    'bahcelievler': 'bahçelievler', 'bakirkoy': 'bakırköy', 'basaksehir': 'başakşehir',
    'bayrampasa': 'bayrampaşa', 'beykoz': 'beykoz', 'beylikduzu': 'beylikdüzü',
    'cekmekoy': 'çekmeköy', 'esenyurt': 'esenyurt', 'gaziosmanpasa': 'gaziosmanpaşa',
    'gungoren': 'güngören', 'kagithane': 'kağıthane', 'silivri': 'silivri',
    'sultanbeyli': 'sultanbeyli', 'sultangazi': 'sultangazi', 'tuzla': 'tuzla',
    'zeytinburnu': 'zeytinburnu', 'adalar': 'adalar', 'arnavutkoy': 'arnavutköy',
    'atasehir': 'ataşehir', 'catalca': 'çatalca', 'sile': 'şile',
}

BAD_TYPES = {'place_of_worship', 'office', 'school', 'shop', 'commercial',
             'industrial', 'company', 'religious', 'restaurant', 'cafe'}


def is_in_istanbul(lat, lon):
    return (ISTANBUL_BBOX['lat_min'] <= lat <= ISTANBUL_BBOX['lat_max']
            and ISTANBUL_BBOX['lon_min'] <= lon <= ISTANBUL_BBOX['lon_max'])


def correct_district(district, raw_result):
    if not raw_result or 'address' not in raw_result.raw:
        return False
    addr = raw_result.raw['address']
    district_tr = DISTRICT_TR.get(district, district)
    fields = ['town', 'city_district', 'suburb', 'county', 'municipality']
    for f in fields:
        val = addr.get(f, '').lower()
        if district in val or district_tr in val:
            return True
    return False


def is_acceptable_type(raw_result):
    if not raw_result or not raw_result.raw:
        return True
    place_type = raw_result.raw.get('type', '').lower()
    place_class = raw_result.raw.get('class', '').lower()
    if place_type in BAD_TYPES or place_class in BAD_TYPES:
        return False
    return True


def geocode_safe(neighborhood, district):
    queries = [
        (f"{neighborhood} mahallesi, {district}, istanbul", 'tight'),
        (f"{neighborhood}, {district}, istanbul, turkey", 'medium'),
        (f"{district}, istanbul", 'fallback'),
    ]
    for q, label in queries:
        try:
            loc = geocode_raw(q)
        except Exception as e:
            print(f"    HATA: {e}")
            continue
        if not loc:
            continue
        if not is_in_istanbul(loc.latitude, loc.longitude):
            continue
        if not is_acceptable_type(loc):
            continue
        if label != 'fallback' and not correct_district(district, loc):
            continue
        return {
            'lat': loc.latitude, 'lon': loc.longitude,
            'address': loc.address[:200],
            'strategy': label,
            'place_type': loc.raw.get('type', '?'),
        }
    return None


# Veriyi yukle
df = pd.read_csv(DATA_PATH)
unique_pairs = df[['district', 'neighborhood']].drop_duplicates().reset_index(drop=True)
print(f"Toplam unique mahalle: {len(unique_pairs)}")

# Cache yukle
if os.path.exists(OUTPUT_PATH):
    cached = pd.read_csv(OUTPUT_PATH)
    print(f"Cache yuklendi: {len(cached)} mahalle daha onceden geocoded")
    cached_keys = set(zip(cached['district'], cached['neighborhood']))
else:
    cached = pd.DataFrame()
    cached_keys = set()

# Geocoding
results = []
total = len(unique_pairs)
fail_count = 0
fallback_count = 0
tight_count = 0
medium_count = 0

start = time.time()
for i, row in unique_pairs.iterrows():
    district, nh = row['district'], row['neighborhood']

    # Cache kontrolu
    if (district, nh) in cached_keys:
        continue

    res = geocode_safe(nh, district)

    if res:
        results.append({
            'district': district, 'neighborhood': nh,
            'lat': res['lat'], 'lon': res['lon'],
            'strategy': res['strategy'], 'place_type': res['place_type'],
            'address': res['address'],
        })
        if res['strategy'] == 'tight':
            tight_count += 1
        elif res['strategy'] == 'medium':
            medium_count += 1
        else:
            fallback_count += 1
    else:
        fail_count += 1
        results.append({
            'district': district, 'neighborhood': nh,
            'lat': None, 'lon': None,
            'strategy': 'FAIL', 'place_type': None, 'address': None,
        })

    # Her 25 mahallede bir cache yaz + progress
    if (i + 1) % 25 == 0:
        elapsed = time.time() - start
        remaining = elapsed * (total - i - 1) / (i + 1)
        print(
            f"  [{i + 1}/{total}] tight:{tight_count} medium:{medium_count} fallback:{fallback_count} FAIL:{fail_count} | {elapsed / 60:.1f} dk gecti, ~{remaining / 60:.1f} dk kaldi")
        # Cache kaydet
        df_partial = pd.concat([cached, pd.DataFrame(results)], ignore_index=True)
        df_partial.to_csv(OUTPUT_PATH, index=False)

# Final kaydet
df_final = pd.concat([cached, pd.DataFrame(results)], ignore_index=True)
df_final.to_csv(OUTPUT_PATH, index=False)

elapsed = time.time() - start
print(f"\n=== TAMAMLANDI ({elapsed / 60:.1f} dakika) ===")
print(f"Toplam: {len(df_final)}")
print(f"Tight  : {tight_count}")
print(f"Medium : {medium_count}")
print(f"Fallback: {fallback_count}")
print(f"FAIL   : {fail_count}")
print(f"\nKaydedildi: {OUTPUT_PATH}")