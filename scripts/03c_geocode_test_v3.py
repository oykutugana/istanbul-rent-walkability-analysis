"""
Geocoding test v3:
- Adresin SON kismindan ilce kontrolu (Pendik tuzagi cozumu)
- Sonuc tipi (Place type) kontrolu — cami, isyeri reddi
- Daha akilli fallback stratejisi
"""
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

geolocator = Nominatim(user_agent="istanbul_rent_24018020_v3")
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

# Reddedilecek place tipleri (mesken/mahalle aramiyoruz, isyeri/cami buluyorsa hatali)
BAD_TYPES = {'place_of_worship', 'office', 'school', 'shop', 'amenity', 'commercial',
             'industrial', 'building', 'company', 'religious', 'restaurant', 'cafe'}


def is_in_istanbul(lat, lon):
    return (ISTANBUL_BBOX['lat_min'] <= lat <= ISTANBUL_BBOX['lat_max']
            and ISTANBUL_BBOX['lon_min'] <= lon <= ISTANBUL_BBOX['lon_max'])


def correct_district(district, raw_result):
    """
    Nominatim'in addressdetails dictionary'sinden ilce bilgisini cek.
    'town', 'city_district', 'suburb', 'county' alanlarinda gecmeli.
    """
    if not raw_result or 'address' not in raw_result.raw:
        return False

    addr = raw_result.raw['address']
    district_tr = DISTRICT_TR.get(district, district)

    # Hangi alanlarda district aranmali
    fields = ['town', 'city_district', 'suburb', 'county', 'municipality']
    for f in fields:
        val = addr.get(f, '').lower()
        if district in val or district_tr in val:
            return True
    return False


def is_acceptable_type(raw_result):
    """Place tipi kabul edilebilir mi? (cami, isyeri, fabrika reddi)"""
    if not raw_result or not raw_result.raw:
        return True  # tip yoksa varsayilan kabul

    place_type = raw_result.raw.get('type', '').lower()
    place_class = raw_result.raw.get('class', '').lower()

    if place_type in BAD_TYPES or place_class in BAD_TYPES:
        return False
    return True


def geocode_safe(neighborhood, district):
    """Coklu strateji + sıkı dogrulama."""
    queries = [
        (f"{neighborhood} mahallesi, {district}, istanbul", 'tight'),
        (f"{neighborhood}, {district}, istanbul, turkey", 'medium'),
        (f"{district}, istanbul", 'fallback'),
    ]

    for q, label in queries:
        loc = geocode_raw(q)
        if not loc:
            continue
        if not is_in_istanbul(loc.latitude, loc.longitude):
            continue
        if not is_acceptable_type(loc):
            continue
        # Fallback haricinde ilce dogrulamasi
        if label != 'fallback' and not correct_district(district, loc):
            continue

        return {
            'lat': loc.latitude, 'lon': loc.longitude,
            'address': loc.address,
            'strategy': label,
            'place_type': loc.raw.get('type', '?'),
        }
    return None


# Genis test seti
test_cases = [
    ("avcilar", "merkez"),
    ("esenler", "sanayi"),  # KRITIK: Pendik tuzagi
    ("bagcilar", "merkez"),
    ("buyukcekmece", "celaliye"),  # KRITIK: fallback'e dusmemeli
    ("kartal", "rahmanlar"),
    ("beyoglu", "piri pasa"),
    ("fatih", "kocamustafapasa"),
    ("uskudar", "valide-i atik"),
    ("sisli", "cumhuriyet"),
    ("kadikoy", "merkez"),  # KRITIK: cami yerine ilce merkezi
    ("pendik", "yeni"),
    ("kucukcekmece", "yenisehir"),  # KRITIK: fallback yerine bulmali
    ("besiktas", "bebek"),  # pilot test mahalle
    ("kadikoy", "caferaga"),  # pilot test mahalle
    ("esenyurt", "merkez"),  # pilot test mahalle
]

print(f"{'Mahalle':<22} {'Ilce':<15} {'Strateji':<10} {'Tip':<18} {'Koordinat':<22} Adres")
print("-" * 145)

for district, nh in test_cases:
    res = geocode_safe(nh, district)
    if res:
        coord = f"({res['lat']:.4f}, {res['lon']:.4f})"
        addr_short = res['address'][:50] + "..."
        print(f"{nh:<22} {district:<15} {res['strategy']:<10} {res['place_type']:<18} {coord:<22} {addr_short}")
    else:
        print(f"{nh:<22} {district:<15} {'FAIL':<10} {'-':<18} {'-':<22} -")

print("-" * 145)