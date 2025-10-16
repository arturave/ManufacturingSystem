# 📦 Nowy moduł wyboru produktów dla zamówień/ofert

## ✅ Zrealizowane funkcjonalności

### 1. **Rozszerzony panel produktów**
- ➕ **Dodaj produkt** - przycisk w górnym menu
- 📋 **Menu kontekstowe** (prawy przycisk myszy) z opcjami:
  - 🔍 Szczegóły
  - ✏️ Edytuj
  - 📋 Duplikuj
  - 🗑️ Usuń
- **Pełny formularz** wprowadzania danych produktu ze wszystkimi polami bazy

### 2. **Selektor produktów z dwoma tabelami** (`products_selector_dialog.py`)

#### Lewa tabela - Dostępne produkty:
- Lista wszystkich produktów z bazy
- Filtrowanie po nazwie w czasie rzeczywistym
- Wyświetlanie: indeks, nazwa, materiał, grubość, ilość, koszt
- Ikony: 📦 dla produktów z grafiką, 📄 bez grafiki

#### Prawa tabela - Wybrane produkty:
- Produkty dodane do zamówienia/oferty
- Możliwość edycji ilości (podwójne kliknięcie)
- Podsumowanie: liczba produktów, łączna ilość, koszt

#### Przyciski sterujące:
- **→** Dodaj wybrane produkty
- **⇉** Dodaj wszystkie (przefiltrowane)
- **←** Usuń wybrane z zamówienia
- **⇇** Usuń wszystkie z zamówienia
- **✚** Duplikuj wybrane (po prawej)
- **DEL** Usuń wybrane z zamówienia

#### Menu kontekstowe (prawy przycisk myszy):

**Lewa tabela:**
- ➡️ Dodaj do zamówienia
- 🔍 Pokaż szczegóły
- ✏️ Edytuj produkt

**Prawa tabela:**
- 📝 Zmień ilość
- ✚ Duplikuj
- 🔍 Pokaż szczegóły
- 🗑️ Usuń z zamówienia

### 3. **Integracja z formularzem zamówienia**

Przycisk **"📦 Wybierz produkty"** w dialogu zamówienia:
- Otwiera nowy selektor produktów
- Zachowuje wcześniej wybrane produkty
- Automatycznie aktualizuje listę części
- Zwraca kompletne dane produktów

## 🎯 Jak używać

### Dodawanie produktów do zamówienia:

1. **Otwórz zamówienie** (nowe lub edycja)
2. **Kliknij "📦 Wybierz produkty"**
3. **W oknie selektora:**
   - Filtruj produkty po nazwie (pole u góry)
   - Zaznacz produkty (Ctrl+klik dla wielu)
   - Użyj przycisku **→** lub podwójne kliknięcie
   - Lub użyj **⇉** aby dodać wszystkie
4. **Edytuj ilości** (podwójne kliknięcie na produkcie po prawej)
5. **Kliknij "✅ Zatwierdź wybór"**
6. Produkty zostaną dodane do zamówienia

### Zarządzanie produktami w bazie:

1. **Otwórz "📦 Produkty"** z głównego menu
2. **Dodaj nowy produkt:**
   - Kliknij **"➕ Dodaj produkt"**
   - Wypełnij formularz
   - Dodaj grafikę (drag & drop lub Ctrl+V)
   - Załącz plik CAD
3. **Edytuj/Duplikuj/Usuń:**
   - Prawy przycisk myszy na produkcie
   - Wybierz odpowiednią opcję

## 📊 Struktura danych

### Przekazywane dane produktu:
```python
{
    'idx_code': 'IDX-00001',
    'name': 'Obudowa stalowa',
    'material': 'DC01',
    'material_id': 'uuid-materiału',
    'thickness_mm': 2.0,
    'qty': 5,
    'bending_cost': 50.00,
    'additional_costs': 20.00,
    'graphic_high_res': '/path/to/high_res.png',
    'graphic_low_res': '/path/to/low_res.png',
    'documentation_path': '/path/to/file.dxf'
}
```

## 🔧 Nowe pliki

1. **`products_selector_dialog.py`** - Dialog wyboru produktów z dwoma tabelami
2. Zaktualizowany **`products_module.py`** - dodano przyciski zarządzania
3. Zaktualizowany **`mfg_app.py`** - integracja z nowym selektorem

## 🎨 Wygląd interfejsu

```
┌─────────────────────────────────────────────────────────┐
│ 📦 Wybór produktów                                      │
├─────────────────────────────────────────────────────────┤
│ Filtruj: [____________] 🔍 Szukaj ❌ Wyczyść  [➕ Nowy] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Dostępne produkty        ┃  →  ┃  Produkty w zamówieniu│
│ ┌──────────────────────┐ ┃  ⇉  ┃ ┌──────────────────────┐
│ │ Idx │ Nazwa │ Mat... │ ┃  ←  ┃ │ Idx │ Nazwa │ Mat... │
│ │─────┼───────┼────────│ ┃  ⇇  ┃ │─────┼───────┼────────│
│ │ 001 │ Obudowa│ DC01  │ ┃ ─── ┃ │ 002 │ Pokrywa│ DC04  │
│ │ 003 │ Wspornik│ S235 │ ┃  ✚  ┃ │ 005 │ Blacha │ 1.4301│
│ │ ... │ ...   │ ...    │ ┃ DEL ┃ │ ... │ ...   │ ...    │
│ └──────────────────────┘ ┃     ┃ └──────────────────────┘
│                                                         │
│ Wybrano: 2 produktów | Łączna ilość: 15 | Koszt: 350 PLN│
├─────────────────────────────────────────────────────────┤
│ [✅ Zatwierdź wybór]                        [❌ Anuluj] │
└─────────────────────────────────────────────────────────┘
```

## ⚡ Skróty klawiszowe

- **Ctrl+klik** - zaznaczanie wielu produktów
- **Podwójne kliknięcie (lewa)** - dodaj do zamówienia
- **Podwójne kliknięcie (prawa)** - edytuj ilość
- **Prawy przycisk myszy** - menu kontekstowe
- **Delete** - usuń zaznaczone (prawa tabela)

## 🔄 Workflow

1. **Tworzenie produktów** → Panel Produkty → Dodaj produkt
2. **Wybór do zamówienia** → Nowe zamówienie → Wybierz produkty
3. **Edycja ilości** → Podwójne kliknięcie na wybranym produkcie
4. **Zatwierdzenie** → Zapisanie zamówienia z wybranymi produktami

## 📝 Uwagi

- Produkty są teraz niezależne od zamówień (centralna baza)
- Każdy produkt ma unikalny indeks (automatyczny)
- System wykrywa duplikaty przy tworzeniu
- Grafiki są opcjonalne ale zalecane
- Historia zmian jest zapisywana automatycznie

---

**Wersja:** 1.0
**Data:** 2025-10-16
**Status:** ✅ Gotowy do użycia