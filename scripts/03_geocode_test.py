"""
8 ornek mahalle ile geocoding'i test eder.
ASCII karakter, parantez temizligi sonrasi formatin calistigini dogrular.
"""
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

geolocator = Nominatim(user_agent="istanbul_rent_24018020")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.1)

# Karisik test seti: yaygin isimler, ASCII, temizlenmisler, sentinel
test_cases = [
    ("avcilar", "merkez"),  # sentinel + ilce kombinasyonu
    ("esenler", "sanayi"),  # yaygin isim
    ("bagcilar", "merkez"),  # yine sentinel
    ("buyukcekmece", "celaliye"),  # parantezi temizledigimiz
    ("kartal", "rahmanlar"),  # parantezi temizledigimiz
    ("beyoglu", "piri pasa"),  # ASCII Turkce karakter
    ("fatih", "kocamustafapasa"),  # uzun ASCII
    ("uskudar", "valide-i atik"),  # tireli mesru isim
]

print(f"{'Mahalle':<25} {'Ilce':<15} {'Sonuc':<10} {'Koordinat':<25} Adres")
print("-" * 130)

basari = 0
for district, nh in test_cases:
    query = f"{nh}, {district}, Istanbul, Turkey"
    location = geocode(query)

    if location:
        coord = f"({location.latitude:.4f}, {location.longitude:.4f})"
        addr_short = location.address[:60] + "..." if len(location.address) > 60 else location.address
        print(f"{nh:<25} {district:<15} {'OK':<10} {coord:<25} {addr_short}")
        basari += 1
    else:
        print(f"{nh:<25} {district:<15} {'FAIL':<10} {'-':<25} -")

print("-" * 130)
print(f"\nBasari: {basari}/{len(test_cases)}")
