# Wybory Prezydenckie 2025 - Analizy Statystyczna Nieprawidłowości/Scraper

## 🗳️ O Projekcie

Cześć! Z powodu istniejących **"cudów"** i nieprawidłowości w komisjach wyborczych (oraz nadmiaru wolnego czasu w weekend) postanowiłem stworzyć program, który pobierze dane ze **wszystkich kilkudziesięciu tysięcy obwodów** i je usystematyzuje.

Program to **scraper**, który przeszedł przez stronę każdego obwodu oraz pobrał dane o **Nawrockim** oraz **Trzaskowskim** - kod znajdziesz w pliku `main.py`.

## 🔍 Najważniejsze Odkrycia

Jednak najbardziej interesujące są **wyniki**, które udało mu się zebrać. Poprzez najprostszą arytmetykę wychodzi, iż:

> ### 📊 **TRZASKOWSKI**: `934` razy posiadał **mniejszą ilość głosów** w drugiej turze niż w pierwszej
> ### 📊 **NAWROCKI**: `260` razy posiadał **mniejszą ilość głosów** w drugiej turze niż w pierwszej

## 💭 Moja Interpretacja

**Z całą pewnością** mogę powiedzieć, że **nie jest to fałszowanie wyborów na taką skalę**. Wystarczy, iż:
- 🚢 Na statku/małej komisji zagłosuje mniej ludzi
- ✈️ Więcej ludzi gdzieś wyjedzie 
- ❌ Wystąpił jakiś błąd przy pobieraniu 
- 📋 i tak dalej... nie jestem ekspertem

Ale na pewno są to wyniki, które może **ktoś inteligentniejszy ode mnie** głęboko i szeroko **przenanalizować**.

## 📥 Zapraszam!

**Do zapoznania się z wynikami, korzystania z nich i głębokiej ANALIZY**
- 📈 Prosta analiza głosów znajduje się w pliku `analyze.ipynb`
- 📊 Wyniki głosowania i nieprawidłowości w plikach **CSV** oraz **XLSX**

## 🔍 Proszę jedynie o wzmiankę podczas publikacji odkryć bądź jakiś badań

---
## Przegląd techniczny
Ten projekt zawiera kompletną analizę statystyczną wyników Wyborów Prezydenckich 2025 w Polsce, ze szczególnym uwzględnieniem anomalii między pierwszą a drugą turą głosowania. Projekt obejmuje scraping danych z oficjalnych źródeł, analizę statystyczną oraz identyfikację nietypowych wzorców głosowania.

## Struktura Projektu

```
protestwyborczyw/
├── main.py                              # Główny skrypt do scrapingu danych
├── wersja_na_serwer.ipynb              # Wersja notebook do uruchamiania na serwerze
├── analyze.ipynb                        # Notebook z analizą statystyczną
├── election_results_first_FINAL.csv    # Wyniki pierwszej tury (CSV)
├── election_results_second_FINAL.csv   # Wyniki drugiej tury (CSV)
├── wyniki_wszystkie/                   # Folder z przetworzonych wyników
│   ├── election_results_first_FINAL.xlsx
│   ├── election_results_second_FINAL.xlsx
│   ├── extreme_changes.csv             # Komisje z ekstremalnymi zmianami
│   ├── extreme_changes.xlsx
│   ├── weird_nawrocki_sum.csv          # Podejrzane wzrosty Nawrockiego
│   ├── weird_nawrocki_sum.xlsx
│   ├── weird_nawrocki.csv
│   ├── weird_nawrocki.xlsx
│   ├── weird_trzaskowski_sum.csv       # Podejrzane wzrosty Trzaskowskiego
│   ├── weird_trzaskowski_sum.xlsx
│   ├── weird_trzaskowski.csv
│   └── weird_trzaskowski.xlsx
└── readme.md
```

## Opis Komponentów

### 1. Scraping Danych

#### main.py
Główny skrypt wykorzystujący Playwright do asynchronicznego scrapingu wyników wyborów:
- **Zakres danych**: Komisje wyborcze od ID 1404408 do 1477701, w linku na koncu mozna dzieki temu sie poruszac
- **Architektura**: Asynchroniczny scraping z kontrolą równoległości
- **Optymalizacja**: Batching (30 komisji na batch) z max 15 równoległymi sesjami, ale mozna wiecej ;)
- **Output**: CSV z kolumnami: `obkw_id`, `location`, `trzaskowski_votes`, `nawrocki_votes`

```python
# Kluczowe parametry scrapingu
FIRST_OBKW_MIN = 1404408
FIRST_OBKW_MAX = 1414924  
SECOND_OBKW_MIN = 1467408
SECOND_OBKW_MAX = 1477701
batch_size = 30
max_concurrent = 15
```

#### wersja_na_serwer.ipynb
Zoptymalizowana wersja notebook do uruchamiania na serwerach:
- Zwiększona równoległość (max 40 równoczesnych sesji)
- Mniejsze batche (20 komisji) dla lepszej kontroli
- Wbudowane logowanie postępu scrapingu

### 2. Analiza Danych

#### analyze.ipynb  
Kompleksowa analiza statystyczna obejmująca... tutaj ktoś mądrzejszy musi to zrobić, na razie zabawa i pierwsze wnioski o "cudach"

### 3. Wyniki Analizy

#### Pliki CSV/XLSX w wyniki_wszystkie/

**Struktura Wyników:**
- `election_results_*_FINAL.*`: Kompletne dane z obu tur
- `extreme_changes.*`: Komisje z największymi zmianami między turami  
- `weird_nawrocki.*`: Komisje z podejrzanymi spadkami głosów Nawrockiego
- `weird_trzaskowski.*`: Komisje z podejrzanymi spadkami głosów Trzaskowskiego
- `*_sum.*`: Zagregowane statystyki według adresu obwodów



## Wymagania Techniczne

### Środowisko Python
```bash
pip install -r requirements.txt
playwright install chromium
```


### Uruchamianie

1. **Scraping danych:**
```bash
python main.py
```

2. **Analiza w Jupyter:**
```bash
jupyter notebook analyze.ipynb
```

3. **Uruchamianie na serwerze:**
```bash
jupyter notebook wersja_na_serwer.ipynb
```

UWAGA NIE PRZESADZAJ Z ILOSCIA OTWARTYCH OKIEN, MOZLIWE USZKODZENIE KOMPUTERA ORAZ PODEJRZENIE ATAKU DDOS 
## Metodologia

### Proces Scrapingu
1. **Asynchroniczny dostęp** do bazy PKW
2. **Kontrola błędów** z retry logic
3. **Rate limiting** dla stabilności
4. **Walidacja danych** w czasie rzeczywistym

### Analiza Statystyczna
1. **Preprocessing**: Cleaning i normalizacja danych
2. **Sprawdzenie pierwszych wniosków o różnicach**

Zachęcam do dalszej profesjonalnej analizy!

## Zastrzeżenia

- **Źródło danych**: Oficjalne wyniki z Państwowej Komisji Wyborczej
- **Okres**: Wybory Prezydenckie 2025 (I i II tura)
- **Metodologia**: Analiza statystyczna, nie prawna interpretacja
- **Cel**: Identyfikacja wzorców do dalszej analizy


---
*Projekt stworzony w celach analitycznych i edukacyjnych. Wszystkie dane pochodzą z oficjalnych źródeł PKW.*