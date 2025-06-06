import pandas as pd
import asyncio
import re
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import aiofiles
from tqdm.asyncio import tqdm

FIRST_OBKW_MAX = 1436239
FIRST_OBKW_MIN = 1404408

SECOND_OBKW_MAX = 1499538
SECOND_OBKW_MIN = 1467396

URL_TEMPLATE_FIRST = "https://wybory.gov.pl/prezydent2025/pl/obkw/1/{}"
URL_TEMPLATE_SECOND = "https://wybory.gov.pl/prezydent2025/pl/obkw/2/{}"

async def scrape_single_page(page, url):
    """Scrapowanie pojedynczej strony"""
    try:
        await page.goto(url, wait_until='domcontentloaded', timeout=10000)
        
        # Try to wait for visible table, but don't fail if it's hidden
        try:
            await page.wait_for_selector('.table-responsive', state='visible', timeout=5000)
        except:
            # If table is not visible, wait for DOM to be ready and continue
            await page.wait_for_load_state('networkidle', timeout=5000)
        
        # Pobierz HTML
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        commission_id = url.split('/')[-1]
        
        # Wyciągnij adres
        address = "Unknown"
        address_element = soup.select_one('.col-xs-12.col-sm-8.col-lg-9.col-xl-10')
        if address_element:
            address = address_element.get_text(strip=True)
        
        nawrocki_votes = 0
        trzaskowski_votes = 0
        
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
                        trzaskowski_votes = int(numbers[-1])
                
                # Szukaj Nawrockiego
                if 'Nawrocki' in row_text or 'NAWROCKI' in row_text:
                    numbers = re.findall(r'\d+', row_text.replace(' ', ''))
                    if numbers:
                        nawrocki_votes = int(numbers[-1])
        
        # Jeśli nie znaleziono w tabelach, szukaj w całej stronie
        if nawrocki_votes == 0 and trzaskowski_votes == 0:
            page_text = soup.get_text()
            
            trzaskowski_pattern = r'Trzaskowski[^0-9]*(\d+)'
            nawrocki_pattern = r'Nawrocki[^0-9]*(\d+)'
            
            trzaskowski_match = re.search(trzaskowski_pattern, page_text, re.IGNORECASE)
            nawrocki_match = re.search(nawrocki_pattern, page_text, re.IGNORECASE)
            
            if trzaskowski_match:
                trzaskowski_votes = int(trzaskowski_match.group(1))
            if nawrocki_match:
                nawrocki_votes = int(nawrocki_match.group(1))
        
        result = {
            "id": commission_id,
            "address": address,
            "Nawrocki": nawrocki_votes,
            "Trzaskowski": trzaskowski_votes,
        }
        
        print(f"✓ {commission_id}: T={trzaskowski_votes}, N={nawrocki_votes}")
        return result
        
    except Exception as e:
        print(f"✗ Error {url}: {str(e)}")
        return None

async def scrape_batch_async(urls, max_concurrent=10):
    """Asynchroniczne scrapowanie batcha URLi"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-images',
                '--disable-plugins',
                '--disable-extensions'
            ]
        )
        
        # Utwórz semafore do kontroli liczby równoczesnych połączeń
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def scrape_with_semaphore(url):
            async with semaphore:
                page = await browser.new_page()
                try:
                    result = await scrape_single_page(page, url)
                    return result
                finally:
                    await page.close()
        
        # Uruchom wszystkie zadania równocześnie z progress barem
        tasks = [scrape_with_semaphore(url) for url in urls]
        results = await tqdm.gather(*tasks, desc="Scrapowanie")
        
        await browser.close()
        
        # Filtruj tylko udane wyniki
        return [r for r in results if r is not None]

async def scrape_in_batches_async(start_id, end_id, url_template, batch_size=50, max_concurrent=10):
    """Scrapowanie w batchach asynchronicznie"""
    all_ids = list(range(start_id, end_id + 1))
    batches = [all_ids[i:i + batch_size] for i in range(0, len(all_ids), batch_size)]
    
    all_results = []
    
    for i, batch in enumerate(batches):
        print(f"Batch {i+1}/{len(batches)} - IDs: {batch[0]} do {batch[-1]}")
        
        batch_urls = [url_template.format(obkw_id) for obkw_id in batch]
        
        # Scrapuj batch asynchronicznie
        batch_results = await scrape_batch_async(batch_urls, max_concurrent)
        all_results.extend(batch_results)
        
        # Zapisz po każdym batchu
        temp_df = pd.DataFrame(all_results)
        await save_to_csv_async(temp_df, f"results_batch_{i+1}.csv")
        
        print(f"Batch {i+1} ukończony: {len(batch_results)}/{len(batch)} sukces")
        
        # Krótka przerwa między batchami
        await asyncio.sleep(0.5)
    
    return all_results

async def save_to_csv_async(df, filename):
    """Asynchroniczne zapisywanie do CSV"""
    csv_content = df.to_csv(index=False)
    async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
        await f.write(csv_content)

async def main():
    print("ASYNC PLAYWRIGHT SCRAPER STARTUJE!")
    
    # Scrapuj pierwszą turę
    print("Scrapowanie pierwszej tury...")
    results_first = await scrape_in_batches_async(
        FIRST_OBKW_MIN, 
        FIRST_OBKW_MAX, 
        URL_TEMPLATE_FIRST,
        batch_size=30, 
        max_concurrent=15
    )
    
    # Zapisz finalne wyniki pierwszej tury
    election_results_first = pd.DataFrame(results_first)
    await save_to_csv_async(election_results_first, "election_results_first_FINAL.csv")
    print(f"Pierwsza tura ukończona: {len(results_first)} wyników")
    
    # Scrapuj drugą turę
    print("Scrapowanie drugiej tury...")
    results_second = await scrape_in_batches_async(
        SECOND_OBKW_MIN, 
        SECOND_OBKW_MAX, 
        URL_TEMPLATE_SECOND,
        batch_size=30, 
        max_concurrent=15
    )
    
    # Zapisz finalne wyniki drugiej tury
    election_results_second = pd.DataFrame(results_second)
    await save_to_csv_async(election_results_second, "election_results_second_FINAL.csv")
    print(f"Druga tura ukończona: {len(results_second)} wyników")
    
    print("SCRAPING ZAKOŃCZONY!")

if __name__ == "__main__":
    # Uruchom główną funkcję asynchroniczną
    asyncio.run(main())