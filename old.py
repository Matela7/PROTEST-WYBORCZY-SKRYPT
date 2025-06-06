import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import concurrent.futures
from tqdm import tqdm
import threading

FIRST_OBKW_MAX = 1436239
FIRST_OBKW_MIN = 1404408

SECOND_OBKW_MAX = 1499538
SECOND_OBKW_MIN = 1467396

OKBW_OVERALL = 29815
URL_TEMPLATE_FIRST = "https://wybory.gov.pl/prezydent2025/pl/obkw/1/{}"

results_list_first = []
results_list_second = []
election_results = pd.DataFrame(
    {
        "id": [],
        "address": [],
        "Nawrocki_first": 0,
        "Trzaskowski_first": 0,
        "Nawrocki_second": 0,
        "Trzaskowski_second": 0,
    }
)

def scraper_selenium_fast(site):
    # MEGA szybka konfiguracja Chrome
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-images')  # Nie ładuj obrazków
    options.add_argument('--disable-plugins')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-renderer-backgrounding')
    options.add_argument('--disable-backgrounding-occluded-windows')
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-features=TranslateUI')
    options.add_argument('--disable-default-apps')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        driver.get(site)
        
        # Krótsze oczekiwanie
        time.sleep(1)  # Zmniejszone z 5 do 2 sekund
        # WebDriverWait(driver, 2).until(
        #     EC.presence_of_element_located((By.CSS_SELECTOR, ".table-responsive"))
        # )
        # Pobierz HTML
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        commission_id = site.split('/')[-1]
        
        # Extract address - szybciej
        address = "Unknown"
        address_element = soup.select_one('.col-xs-12.col-sm-8.col-lg-9.col-xl-10')
        if address_element:
            address = address_element.get_text(strip=True)
        
       
        nawrocki_first = 0
        trzaskowski_first = 0
        
        # Znajdź tabele z wynikami
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            for row in rows:
                row_text = row.get_text()
                
                # Szukaj Trzaskowskiego
                if 'Trzaskowski' in row_text or 'TRZASKOWSKI' in row_text:
                    numbers = re.findall(r'\d+', row_text.replace(' ', ''))
                    if numbers:
                        trzaskowski_first = int(numbers[-1])
                
                # Szukaj Nawrockiego
                if 'Nawrocki' in row_text or 'NAWROCKI' in row_text:
                    numbers = re.findall(r'\d+', row_text.replace(' ', ''))
                    if numbers:
                        nawrocki_first = int(numbers[-1])
        
        # Jeśli nie znaleziono w tabelach, szukaj w całej stronie
        if nawrocki_first == 0 and trzaskowski_first == 0:
            page_text = soup.get_text()
            
            trzaskowski_pattern = r'Trzaskowski[^0-9]*(\d+)'
            nawrocki_pattern = r'Nawrocki[^0-9]*(\d+)'
            
            trzaskowski_match = re.search(trzaskowski_pattern, page_text, re.IGNORECASE)
            nawrocki_match = re.search(nawrocki_pattern, page_text, re.IGNORECASE)
            
            if trzaskowski_match:
                trzaskowski_first = int(trzaskowski_match.group(1))
            if nawrocki_match:
                nawrocki_first = int(nawrocki_match.group(1))
        result = {
            "id": commission_id,
            "address": address,
            "Nawrocki": nawrocki_first,
            "Trzaskowski": trzaskowski_first,
        }
        
        print(f"✓ {commission_id}: T={trzaskowski_first}, N={nawrocki_first}")
        return result
        
    except Exception as e:
        print(f"✗ Error {site}: {str(e)}")
        return None
    finally:
        driver.quit()

def scrape_parallel_selenium(start_id, end_id, max_workers=5):
    """Równoległe scrapowanie z Selenium"""
    urls = [URL_TEMPLATE_FIRST.format(obkw) for obkw in range(start_id, end_id + 1)]
    results = []
    
    print(f"Scrapowanie {len(urls)} stron z {max_workers} workerami...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Użyj tqdm do progress bara
        future_to_url = {executor.submit(scraper_selenium_fast, url): url for url in urls}
        
        for future in tqdm(concurrent.futures.as_completed(future_to_url), total=len(urls)):
            result = future.result()
            if result:
                results.append(result)
                
                # Zapisuj co 100 wyników
                if len(results) % 100 == 0:
                    temp_df = pd.DataFrame(results)
                    temp_df.to_csv("temp_results.csv", index=False)
                    print(f"Zapisano {len(results)} wyników...")
    
    return results

def scrape_in_batches(start_id, end_id, batch_size=50, max_workers=3):
    """Scrapowanie w batchach - jeszcze bezpieczniejsze"""
    all_ids = list(range(start_id, end_id + 1))
    batches = [all_ids[i:i + batch_size] for i in range(0, len(all_ids), batch_size)]
    
    all_results = []
    
    for i, batch in enumerate(batches):
        print(f"Batch {i+1}/{len(batches)} - IDs: {batch[0]} do {batch[-1]}")
        
        batch_urls = [URL_TEMPLATE_FIRST.format(obkw) for obkw in batch]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            batch_results = list(executor.map(scraper_selenium_fast, batch_urls))
        
        valid_results = [r for r in batch_results if r is not None]
        all_results.extend(valid_results)
        
        # Zapisz po każdym batchu
        temp_df = pd.DataFrame(all_results)
        temp_df.to_csv(f"results_batch_{i+1}.csv", index=False)
        
        print(f"Batch {i+1} ukończony: {len(valid_results)}/{len(batch)} sukces")
        
        # Krótka przerwa między batchami
        time.sleep(1)
    
    return all_results

if __name__ == "__main__":
    print("MEGA SZYBKI SCRAPER STARTUJE!")
    
    # Opcja 1: Pełna równoległość (może być niestabilna)
    # results = scrape_parallel_selenium(FIRST_OBKW_MIN, FIRST_OBKW_MIN + 100, max_workers=5)
    
    # Opcja 2: Bezpieczniejsza - batche (REKOMENDOWANA)
    results_first = scrape_in_batches(FIRST_OBKW_MIN, FIRST_OBKW_MAX + 2, batch_size=20, max_workers=10)
    
    # Zapisz finalne wyniki
    election_results_first = pd.DataFrame(results_first)
    election_results_first.to_csv("election_results_first_FINAL.csv", index=False)

    results_second = scrape_in_batches(SECOND_OBKW_MIN, SECOND_OBKW_MAX + 2, batch_size=20, max_workers=10)
    election_results_second = pd.DataFrame(results_second)
    election_results_second.to_csv("election_results_second_FINAL.csv", index=False)