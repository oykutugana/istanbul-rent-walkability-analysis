import time
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchWindowException, TimeoutException
import os
import random

# Istanbul ilceleri
DISTRICTS = [
    "arnavutkoy", "atasehir", "avcilar", "bagcilar", "bahcelievler",
    "bakirkoy", "basaksehir", "bayrampasa", "besiktas", "beykoz", "beylikduzu",
    "beyoglu", "buyukcekmece", "catalca", "cekmekoy", "esenler", "esenyurt",
    "eyupsultan", "fatih", "gaziosmanpasa", "gungoren", "kadikoy", "kagithane",
    "kartal", "kucukcekmece", "maltepe", "pendik", "sancaktepe", "sariyer",
    "silivri", "sultanbeyli", "sultangazi", "sile", "sisli", "tuzla",
    "umraniye", "uskudar", "zeytinburnu"
]

# Fiyat dilimleri
PRICE_SLICES = [
    (10000, 14000), (14001, 18000), (18001, 22000), (22001, 26000),
    (26001, 31000), (31001, 37000), (37001, 45000), (45001, 55000),
    (55001, 75000), (75001, 110000), (110001, 150000)
]

# Dosya yollari
OUTPUT_FILE = "../data/istanbul_emlak_data.csv"
CHECKPOINT_FILE = "../data/tamamlanan_dilimler.txt"

# Sampling orani ve limitler
SAMPLE_RATE = 0.50
MIN_SLICE_LIMIT = 10
MAX_SLICE_LIMIT = 200


# ─── Driver ───────────────────────────────────────────────────────────────────

def get_driver():
    options = uc.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    driver = uc.Chrome(options=options, version_main=146)
    driver.maximize_window()
    driver.set_page_load_timeout(60)
    return driver


# ─── Checkpoint ───────────────────────────────────────────────────────────────

def load_checkpoints():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return set(f.read().splitlines())
    return set()


def mark_as_completed(key):
    with open(CHECKPOINT_FILE, "a") as f:
        f.write(key + "\n")


# ─── CSV yardimcilari ─────────────────────────────────────────────────────────

def get_existing_count_for_slice(district, min_price, max_price):
    """Bu dilim icin CSV'de kac satir var?"""
    if not os.path.exists(OUTPUT_FILE):
        return 0
    try:
        df = pd.read_csv(OUTPUT_FILE)
        mask = (
            (df['district'].str.lower() == district.lower()) &
            (df['price_min_filter'] == min_price) &
            (df['price_max_filter'] == max_price)
        )
        return int(mask.sum())
    except:
        return 0


# ─── Sahibinden yardimcilari ──────────────────────────────────────────────────

def is_blocked(driver):
    """Bot engeli veya bos sayfa mi?"""
    url = driver.current_url
    return "check" in url or url.rstrip("/") == "https://www.sahibinden.com"


def wait_for_unblock(driver, url):
    """
    Bot engeli tespit edilince kullaniciya haber ver,
    cozene kadar ENTER bekle, sonra sayfayi yeniden yukle.
    """
    print("\n" + "="*55)
    print("  BOT ENGELI TESPIT EDILDI!")
    print("  Tarayicide dogrulamayi tamamlayin (CAPTCHA / basili tut vb.)")
    print("  Tamamlayinca asagida ENTER'a basin.")
    print("="*55)
    input("  >>> ENTER ile devam et: ")
    safe_get(driver, url)
    time.sleep(random.uniform(10, 18))


def safe_get(driver, url, retries=3):
    """
    Timeout'a karsi korumal driver.get().
    Basarili olursa True, tum denemeler bittiyse False doner.
    """
    for attempt in range(1, retries + 1):
        try:
            driver.get(url)
            return True
        except TimeoutException:
            print(f"  [TIMEOUT] Deneme {attempt}/{retries} - sayfa durdurulup tekrar denenecek...")
            try:
                driver.execute_script("window.stop();")
            except:
                pass
            time.sleep(random.uniform(10, 20))
        except Exception as e:
            print(f"  [HATA] driver.get(): {e}")
            time.sleep(random.uniform(10, 20))
    print(f"  [VAZGECILDI] {url} yuklenemedi.")
    return False


def parse_total_listing_count(driver):
    """
    Yontem 1: data-totalmatches attribute (en guvenilir)
    Yontem 2: result-text-sub-group icindeki <span>
    Doner: int veya None (bot engeli / parse hatasi)
    """
    try:
        wrapper = driver.find_element(By.CLASS_NAME, "resultsTextWrapper")
        val = wrapper.get_attribute("data-totalmatches")
        if val and val.strip().isdigit():
            return int(val.strip())
    except:
        pass

    try:
        container = driver.find_element(By.CLASS_NAME, "result-text-sub-group")
        for span in container.find_elements(By.TAG_NAME, "span"):
            text = span.text.strip().replace(".", "").replace(",", "").replace(" ", "")
            if text.isdigit():
                return int(text)
    except:
        pass

    return None  # parse edilemedi → muhtemelen bot engeli


# ─── Ana fonksiyon ────────────────────────────────────────────────────────────

def collect_data(target_rows=25000):
    completed_list = load_checkpoints()
    driver = get_driver()
    total_rows = 0

    if os.path.exists(OUTPUT_FILE):
        try:
            total_rows = len(pd.read_csv(OUTPUT_FILE))
            print(f"Durum: Mevcut dosyada {total_rows} satir bulundu. Devam ediliyor...")
        except:
            pass

    try:
        safe_get(driver, "https://www.sahibinden.com")
        print("\nTarayici acildi. Manuel dogrulamayi tamamlayin.")
        input("Devam etmek icin ENTER tusuna basin.")

        for district in DISTRICTS:
            if total_rows >= target_rows:
                print("Hedef satir sayisina ulasildi, durduruluyor.")
                break

            for (min_price, max_price) in PRICE_SLICES:
                key = f"{district}_{min_price}_{max_price}"

                if key in completed_list:
                    print(f"Atlandi (checkpoint): {key}")
                    continue

                if total_rows >= target_rows:
                    break

                url = (
                    f"https://www.sahibinden.com/kiralik-daire/istanbul-{district}"
                    f"?price_min={min_price}&price_max={max_price}"
                    f"&a107889_min=30&a107889_max=250"
                )
                print(f"\n{district.upper()} | {min_price}-{max_price} TL | URL yukleniyor...")

                # ── Ilk yukleme ──────────────────────────────────────────────
                if not safe_get(driver, url):
                    # Timeout: checkpoint'e yazma, bir sonraki dilimde tekrar gelecek
                    print(f"  Sayfa yuklenemedi (timeout), bu dilim atlanip devam ediliyor.")
                    continue

                time.sleep(random.uniform(22, 35))

                # ── Bot engeli kontrolu ──────────────────────────────────────
                if is_blocked(driver):
                    wait_for_unblock(driver, url)

                # ── Toplam ilan sayisini oku ─────────────────────────────────
                total_in_slice = parse_total_listing_count(driver)

                if total_in_slice is None:
                    # Parse basarisiz = muhtemelen hala engel var
                    print("  Ilan sayisi okunamadi, tekrar engel mi?")
                    wait_for_unblock(driver, url)
                    total_in_slice = parse_total_listing_count(driver)

                if total_in_slice is None:
                    # Ikinci denemede de olmadi; checkpoint'e YAZMA, sonraki calistirmada tekrar gelsin
                    print(f"  [ATLANDI - checkpoint yazilmadi] {key}")
                    continue

                if total_in_slice == 0:
                    # Gercekten ilan yok → checkpoint'e yaz, bir daha ugramma
                    print(f"  Bu kriterde hic ilan yok, atlaniyor: {key}")
                    mark_as_completed(key)
                    completed_list.add(key)
                    continue

                # ── Hedef hesapla ─────────────────────────────────────────────
                slice_limit = int(total_in_slice * SAMPLE_RATE)
                slice_limit = max(MIN_SLICE_LIMIT, min(slice_limit, MAX_SLICE_LIMIT))
                print(f"  Toplam ilan: {total_in_slice} | Hedef (%{int(SAMPLE_RATE*100)}): {slice_limit}")

                already_collected = get_existing_count_for_slice(district, min_price, max_price)
                if already_collected >= slice_limit:
                    print(f"  Zaten yeterli veri var ({already_collected}/{slice_limit}), atlaniyor.")
                    mark_as_completed(key)
                    completed_list.add(key)
                    continue

                slice_rows = already_collected

                # ── Sayfalama ─────────────────────────────────────────────────
                for page in range(50):
                    if slice_rows >= slice_limit:
                        break

                    offset = page * 20
                    if page > 0:
                        paged_url = f"{url}&pagingOffset={offset}"
                        if not safe_get(driver, paged_url):
                            print(f"  Sayfa {page+1} yuklenemedi, dilim sonlandiriliyor.")
                            break
                        time.sleep(random.uniform(20, 28))

                    # Sayfa ortasinda bot engeli
                    if is_blocked(driver):
                        paged_url = f"{url}&pagingOffset={offset}"
                        wait_for_unblock(driver, paged_url)

                    listings = driver.find_elements(By.CLASS_NAME, "searchResultsItem")
                    if not listings:
                        print(f"  Sayfa {page+1}: Ilan bulunamadi, dilim bitti.")
                        break

                    page_data = []
                    for listing in listings:
                        if slice_rows + len(page_data) >= slice_limit:
                            break
                        try:
                            try:
                                price = listing.find_element(By.CLASS_NAME, "searchResultsPriceValue").text
                            except:
                                price = None

                            attributes = listing.find_elements(By.CLASS_NAME, "searchResultsAttributeValue")
                            m2    = attributes[0].text if len(attributes) > 0 else None
                            rooms = attributes[1].text if len(attributes) > 1 else None

                            try:
                                location_raw = listing.find_element(By.CLASS_NAME, "searchResultsLocationValue").text
                                district_name = location_raw.split("\n")[0].strip()
                                neighborhood  = location_raw.split("\n")[1].strip() if "\n" in location_raw else None
                            except:
                                district_name, neighborhood = None, None

                            page_data.append({
                                "price":            price,
                                "area_m2":          m2,
                                "room_count":       rooms,
                                "district":       district,         # arama motoruna yazilan
                                "sub_district":       district_name,   # ilandan cekilen
                                "neighborhood":     neighborhood,
                                "price_min_filter": min_price,
                                "price_max_filter": max_price,
                            })
                        except:
                            continue

                    if page_data:
                        df_page = pd.DataFrame(page_data)
                        df_page.to_csv(
                            OUTPUT_FILE, mode='a',
                            header=not os.path.exists(OUTPUT_FILE),
                            index=False
                        )
                        slice_rows  += len(page_data)
                        total_rows  += len(page_data)
                        print(
                            f"  Sayfa {page+1} | +{len(page_data)} | "
                            f"Dilim: {slice_rows}/{slice_limit} | Toplam: {total_rows}"
                        )
                    else:
                        print(f"  Sayfa {page+1}: Veri yok, durdu.")
                        break

                # Dilim bitti → checkpoint'e yaz
                mark_as_completed(key)
                completed_list.add(key)
                print(f"  Tamamlandi: {key} ({slice_rows} ilan cekildi)")

    except NoSuchWindowException:
        print("Hata: Tarayici penceresi kapatildi.")
    finally:
        driver.quit()
        print(f"\nVeri toplama tamamlandi. Toplam: {total_rows} satir")


if __name__ == "__main__":
    collect_data()