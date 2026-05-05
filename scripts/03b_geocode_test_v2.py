"""
Geocoding test v2: 'mahallesi' eki + district dogrulamasi + bbox kontrolu.
"""
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

geolocator = Nominatim(user_agent="istanbul_rent_24018020_v2")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.1)

# Istanbul bbox (genis)
ISTANBUL_BBOX = {
    'lat_min': 40.80, 'lat_max': 41.30,
    'lon_min': 28.55, 'lon_max': 29.55,
}

# District ascii -> Turkce karsiligi (Nominatim adres karsilastirmasi icin)
DISTRICT_TR = {
    'avcilar': 'avcılar', 'esenler': 'esenler', 'bagcilar': 'bağcılar',
    'buyukcekmece': 'büyükçekmece', 'kartal': 'kartal', 'beyoglu': 'beyoğlu',
    'fatih': 'fatih', 'uskudar': 'üsküdar', 'sisli': 'şişli',
    'kadikoy': 'kadıköy', 'besiktas': 'beşiktaş', 'umraniye': 'ümraniye',
    'sariyer': 'sarıyer', 'maltepe': 'maltepe', 'pendik': 'pendik',
    'sancaktepe': 'sancaktepe', 'eyupsultan': 'eyüp',
    # gerekirse genisletilir
}


def is_in_istanbul(lat, lon):
    return (ISTANBUL_BBOX['lat_min'] <= lat <= ISTANBUL_BBOX['lat_max']
            and ISTANBUL_BBOX['lon_min'] <= lon <= ISTANBUL_BBOX['lon_max'])


def district_in_address(district, address):
    """Adres metninde dogru ilce gecip gecmedigini kontrol eder."""
    addr_low = address.lower()
    # Hem ASCII hem Turkce versiyonu kontrol et
    if district in addr_low:
        return True
    if district in DISTRICT_TR and DISTRICT_TR[district] in addr_low:
        return True
    return False


def geocode_safe(neighborhood, district):
    """3 stratejili guvenli geocoding."""
    queries = [
        f"{neighborhood} mahallesi, {district}, istanbul",  # en katı
        f"{neighborhood}, {district}, istanbul, turkey",  # orta
        f"{district}, istanbul",  # fallback (district merkezi)
    ]

    for i, q in enumerate(queries):
        loc = geocode(q)
        if not loc:
            continue

        # Bbox kontrolu
        if not is_in_istanbul(loc.latitude, loc.longitude):
            continue

        # Fallback degilse district kontrolu
        if i < 2 and not district_in_address(district, loc.address):
            continue

        return {
            'lat': loc.latitude,
            'lon': loc.longitude,
            'address': loc.address,
            'strategy': i,  # 0=tight, 1=medium, 2=fallback
        }

    return None


# TEST CASES (oncekiler + sorunlu olanlar)
test_cases = [
    ("avcilar", "merkez"),
    ("esenler", "sanayi"),  # ONCEDEN YANLISTI
    ("bagcilar", "merkez"),
    ("buyukcekmece", "celaliye"),
    ("kartal", "rahmanlar"),
    ("beyoglu", "piri pasa"),
    ("fatih", "kocamustafapasa"),
    ("uskudar", "valide-i atik"),
    # Ekstra test: yaygin sentinel'ler farkli ilcelerde
    ("sisli", "cumhuriyet"),
    ("kadikoy", "merkez"),
    ("pendik", "yeni"),
    ("kucukcekmece", "yenisehir"),
]

print(f"{'Mahalle':<22} {'Ilce':<15} {'Strateji':<10} {'Koordinat':<22} Adres")
print("-" * 130)

basari, fail = 0, 0
for district, nh in test_cases:
    res = geocode_safe(nh, district)

    if res:
        coord = f"({res['lat']:.4f}, {res['lon']:.4f})"
        strat = ['tight', 'medium', 'FALLBACK'][res['strategy']]
        addr_short = res['address'][:55] + "..." if len(res['address']) > 55 else res['address']
        print(f"{nh:<22} {district:<15} {strat:<10} {coord:<22} {addr_short}")
        basari += 1
    else:
        print(f"{nh:<22} {district:<15} {'FAIL':<10} {'-':<22} -")
        fail += 1

print("-" * 130)
print(f"\nBasari: {basari}/{len(test_cases)}, Fail: {fail}")
print(f"Not: 'FALLBACK' isaretli olanlar mahalle yerine ilce merkezi kullaniyor.")