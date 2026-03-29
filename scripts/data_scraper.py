import time
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchWindowException
import os
import random

# 1. ISTANBUL ILCELERI
DISTRICTS = [
    "adalar", "arnavutkoy", "atasehir", "avcilar", "bagcilar", "bahcelievler",
    "bakirkoy", "basaksehir", "bayrampasa", "besiktas", "beykoz", "beylikduzu",
    "beyoglu", "buyukcekmece", "catalca", "cekmekoy", "esenler", "esenyurt",
    "eyupsultan", "fatih", "gaziosmanpasa", "gungoren", "kadikoy", "kagithane",
    "kartal", "kucukcekmece", "maltepe", "pendik", "sancaktepe", "sariyer",
    "silivri", "sultanbeyli", "sultangazi", "sile", "sisli", "tuzla",
    "umraniye", "uskudar", "zeytinburnu"
]

# Fiyat dilimleri (1000 ilan siniri)
PRICE_SLICES = [
    (10000, 14000), (14001, 18000), (18001, 22000), (22001, 26000),
    (26001, 31000), (31001, 37000), (37001, 45000), (45001, 55000),
    (55001, 75000), (75001, 150000)
]

# Dosya yollari
OUTPUT_FILE = "../data/istanbul_emlak_data.csv"
CHECKPOINT_FILE = "../data/tamamlanan_dilimler.txt"

# Tarayıcı ayarları + başlatma
def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    # Chrome 146 surumune gore sabitlendi
    driver = uc.Chrome(options=options, version_main=146)
    driver.maximize_window()
    return driver

# Tamamlanan dilimleri dosyadan yukle
def load_checkpoints():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return set(f.read().splitlines())
    return set()

# Tamamlanan dilimi dosyaya kaydet
def mark_as_completed(key):

    with open(CHECKPOINT_FILE, "a") as f:
        f.write(key + "\n")

def collect_data(target_rows=23000):
    completed_list = load_checkpoints()
    driver = get_driver()
    total_rows = 0

    # Mevcut veri varsa satir sayisini guncelle
    if os.path.exists(OUTPUT_FILE):
        try:
            total_rows = len(pd.read_csv(OUTPUT_FILE))
            print(f"Durum: Mevcut dosyada {total_rows} satir bulundu. Devam ediliyor...")
        except:
            pass

    try:
        # Oturum hazirligi (captcha icin manuel giris)
        driver.get("https://www.sahibinden.com")
        print("\nTarayici acildi. Manuel dogrulamayi tamamlayin.")
        input("Devam etmek icin ENTER tusuna basin.")

        for district in DISTRICTS:
            for (min_price, max_price) in PRICE_SLICES:
                key = f"{district}_{min_price}_{max_price}"

                if key in completed_list:
                    print(f"Atlandi: {key}")
                    continue

                if total_rows >= target_rows:
                    break

                url = f"https://www.sahibinden.com/kiralik-daire/istanbul-{district}?price_min={min_price}&price_max={max_price}&a107889_min=40&a107889_max=160"
                print(f"\n{district.upper()} | {min_price}-{max_price} TL araligi taraniyor...")

                driver.get(url)
                time.sleep(random.uniform(22, 35))

                for page in range(50):
                    # Guvenlik kontrolu
                    if "sahibinden.com/" == driver.current_url or "check" in driver.current_url:
                        print("Guvenlik engeli tespit edildi. Bekleniyor...")
                        time.sleep(20)

                    offset = page * 20
                    if page > 0:
                        driver.get(f"{url}&pagingOffset={offset}")
                        time.sleep(random.uniform(20, 28))

                    listings = driver.find_elements(By.CLASS_NAME, "searchResultsItem")
                    if not listings:
                        break

                    page_data = []
                    for listing in listings:
                        try:
                            try:
                                price = listing.find_element(By.CLASS_NAME, "searchResultsPriceValue").text
                            except:
                                price = None

                            attributes = listing.find_elements(By.CLASS_NAME, "searchResultsAttributeValue")
                            m2 = attributes[0].text if len(attributes) > 0 else None
                            rooms = attributes[1].text if len(attributes) > 1 else None

                            try:
                                location_raw = listing.find_element(By.CLASS_NAME, "searchResultsLocationValue").text
                                district_name = location_raw.split("\n")[0].strip()
                                neighborhood = location_raw.split("\n")[1].strip() if "\n" in location_raw else None
                            except:
                                district_name, neighborhood = None, None

                            page_data.append({
                                "price": price,
                                "area_m2": m2,
                                "room_count": rooms,
                                "district": district_name,
                                "neighborhood": neighborhood
                            })
                        except:
                            continue

                    if page_data:
                        df_page = pd.DataFrame(page_data)
                        df_page.to_csv(OUTPUT_FILE, mode='a', header=not os.path.exists(OUTPUT_FILE), index=False)
                        total_rows += len(page_data)
                        print(f"Kayit: Sayfa {page + 1} | +{len(page_data)} Satir | Toplam: {total_rows}")
                    else:
                        break

                    if total_rows >= target_rows:
                        break

                mark_as_completed(key)
                completed_list.add(key)

    except NoSuchWindowException:
        print("Hata: Tarayici penceresi kapatildi.")
    finally:
        driver.quit()
        print(f"Veri toplama islemi tamamlandi. Toplam Veri: {total_rows}")


if __name__ == "__main__":
    collect_data()