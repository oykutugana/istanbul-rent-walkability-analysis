# Geocoding Pipeline

P1 dataset → neighborhood-level geo features → P2 input.

## Klasor Yapisi

```
istanbul/
├── data/
│   ├── istanbul_emlak_final.csv          # P1 ciktisi (input)
│   ├── unique_locations.csv              # 01 ciktisi
│   ├── geocode_cache.json                # 02 cache
│   ├── geocoded_locations.csv            # 02 ciktisi
│   ├── poi_raw/                          # 03 ciktisi
│   │   ├── raw_transit.json
│   │   ├── raw_restaurants.json
│   │   ├── raw_cafes.json
│   │   ├── raw_universities.json
│   │   └── raw_parks.json
│   └── istanbul_emlak_with_geo.csv       # 04 ciktisi (P2 input)
├── geocoding/
│   ├── 01_extract_unique_locations.py
│   ├── 02_geocode_locations.py
│   ├── 03_fetch_pois.py
│   ├── 04_compute_features.py
│   └── README.md
├── p1/
└── p2/
```

## Bagimliliklar

```bash
pip install pandas numpy requests
```

## Calistirma Sirasi

`geocoding/` klasoru icindeyken sirayla:

```bash
cd geocoding/

python 01_extract_unique_locations.py
python 02_geocode_locations.py     # ~10-15 dk (Nominatim 1 req/sec)
python 03_fetch_pois.py            # ~2-5 dk (5 sehir capinda sorgu)
python 04_compute_features.py      # ~1-2 dk (lokal hesap)
```

## Ozellikler

* **Cache:** 02 ve 03 cache kullaniyor. Kesilirse `python 02_...` tekrar calistir, kaldigi yerden devam eder.
* **3-tier fallback (02):** mahalle → semt → ilce. Strategy 3'e dusen kayitlar `is_district_center=1` flag'i alir.
* **Bbox dogrulama (02):** Istanbul disindaki sonuclar reddedilir (yanlis sehirden gelen "merkez mh." sorunlari).
* **Eksik veri yonetimi (04):** Geocoding fail eden mahallelerin feature'lari ilce medianiyla doldurulur.

## Cikti Feature'lari

| Feature | Tip | Aciklama |
| :--- | :--- | :--- |
| `nearest_metro_km` | float | En yakin metro/Marmaray istasyonuna haversine mesafe |
| `metro_500m` | int | 500m icindeki istasyon sayisi |
| `metro_1km` | int | 1km icindeki istasyon sayisi |
| `weighted_1km` | float | 1km icindeki agirlikli istasyon (metro=1.0, tram=0.7, halt=0.5) |
| `cafe_1km` | int | 1km icindeki kafe sayisi |
| `restaurant_1km` | int | 1km icindeki restoran sayisi |
| `university_2km` | int | 2km icindeki universite sayisi |
| `park_1km` | int | 1km icindeki park sayisi |
| `is_periphery` | int | Sehir merkezinden 15km+ ise 1 |
| `is_district_center` | int | Geocoding strateji 3'e dustuyse 1 |

## Notlar

* Nominatim ToS: max 1 req/sec, User-Agent zorunlu (script icinde tanimli).
* Overpass timeout 300sn, agir yuk donemlerinde 504/429 alabilir - script otomatik retry yapar.
* Toplam disk kullanimi: ~50-100 MB (POI raw JSON'lari dahil).
