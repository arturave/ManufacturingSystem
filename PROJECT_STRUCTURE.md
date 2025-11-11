# Struktura Projektu - Manufacturing System
## Data aktualizacji: 2025-11-11

## 📁 Główne moduły aplikacji

### 🎯 Pliki główne
- **mfg_app.py** - Główna aplikacja systemu zarządzania produkcją
- **mfg_integrated.py** - Zintegrowany moduł aplikacji
- **setup.py** - Konfiguracja instalacji pakietu
- **requirements.txt** - Lista zależności Python

### 💼 Moduły biznesowe

#### Klienci
- **customer_module_enhanced.py** - Rozszerzony moduł zarządzania klientami

#### Produkty
- **products_module.py** - Wrapper dla modułu produktów (używa enhanced)
- **products_module_enhanced.py** - Ulepszone zarządzanie katalogiem produktów
- **products_selector_dialog.py** - Dialog wyboru produktów do zamówień
- **part_edit_enhanced.py** - Wrapper dla edycji części (używa v4)
- **part_edit_enhanced_v4.py** - Najnowsza wersja edytora części z obsługą binarną

#### Materiały
- **materials_dict_module.py** - Słownik materiałów

#### Oferty
- **quotations_module.py** - Moduł ofertowania

#### Dokumenty
- **wz_generator.py** - Generator dokumentów WZ
- **wz_dialog.py** - Dialog tworzenia WZ
- **attachments_manager.py** - Zarządzanie załącznikami
- **attachments_gui_widgets.py** - Widżety GUI dla załączników

### 🎨 Moduły pomocnicze

#### Przetwarzanie grafiki
- **image_processing.py** - Przetwarzanie obrazów i miniatur
- **integrated_viewer.py** - Zintegrowany podgląd plików

#### Przetwarzanie CAD
- **cad_processing.py** - Obsługa plików CAD (DXF, STEP, etc.)

#### Integracje zewnętrzne
- **outlook_agent.py** - Agent integracji z Outlook

### 🗄️ Baza danych
- **setup_database.sql** - Skrypt konfiguracji bazy danych
- **06_FIX_PRODUCTS_CATALOG.sql** - Najnowsze poprawki struktury bazy

### 🔧 Pliki konfiguracyjne
- **.env** - Zmienne środowiskowe (NIE COMMITOWAĆ!)
- **.env.example** - Przykład konfiguracji środowiska
- **pyproject.toml** - Konfiguracja projektu Python
- **pytest.ini** - Konfiguracja testów
- **.gitignore** - Pliki ignorowane przez Git
- **ManufacturingSystem.pyproj** - Projekt Visual Studio

### 📚 Dokumentacja
- **README.md** - Główny plik README
- **QUICK_START.md** - Szybki start
- **LICENSE** - Licencja projektu
- **PROJECT_STRUCTURE.md** - Ten plik

### 🚀 Skrypty uruchomieniowe
- **uruchom_system.bat** - Uruchamia aplikację
- **instalacja.bat** - Instaluje zależności
- **install_3d_rendering.bat** - Instaluje komponenty 3D
- **run_tests.bat** - Uruchamia testy

### 📂 Katalogi
- **archiv/** - Archiwum starych plików (organizowane po datach)
  - **2025-11-11/** - Archiwum z dnia 11.11.2025
- **screenshots/** - Zrzuty ekranu aplikacji
- **ManufacturingSystem/** - Dodatkowe zasoby (jeśli istnieje)

## 🔄 Przepływ danych

```
1. mfg_app.py (główna aplikacja)
   ├── customer_module_enhanced.py (zarządzanie klientami)
   ├── products_module_enhanced.py (katalog produktów)
   │   └── part_edit_enhanced_v4.py (edycja produktów)
   ├── quotations_module.py (oferty)
   ├── wz_dialog.py (dokumenty WZ)
   └── materials_dict_module.py (słownik materiałów)
```

## 📊 Struktura bazy danych

### Główne tabele:
- **customers** - Dane klientów
- **products_catalog** - Katalog produktów (szablony)
- **parts** - Części w zamówieniach
- **orders** - Zamówienia
- **quotations** - Oferty
- **materials_dict** - Słownik materiałów
- **delivery_notes** - Dokumenty WZ

### Kluczowe zmiany (2025-11-11):
1. **products_catalog** - główna tabela dla katalogu produktów
2. **parts** - tabela dla części w zamówieniach
3. Pliki CAD i dokumentacja przechowywane jako BYTEA (binarne)
4. Dodane pole dla dodatkowej dokumentacji (ZIP/7Z)

## 🔐 Bezpieczeństwo
- Dane logowania w pliku .env (nie commitować!)
- Połączenie z Supabase przez API
- Binarne przechowywanie plików w bazie (bezpieczniejsze niż ścieżki)

## 🛠️ Technologie
- **Python 3.x**
- **CustomTkinter** - GUI
- **Supabase** - Baza danych
- **Pillow** - Przetwarzanie obrazów
- **ReportLab** - Generowanie PDF
- **python-docx** - Dokumenty Word
- **openpyxl** - Pliki Excel

## 📝 Uwagi dla programistów

1. **Moduły z wrapperami**:
   - `products_module.py` → `products_module_enhanced.py`
   - `part_edit_enhanced.py` → `part_edit_enhanced_v4.py`

2. **Tryby pracy edytora części**:
   - `catalog_mode=True` - edycja produktu w katalogu
   - `view_only=True` - tylko podgląd
   - Standardowy - edycja części w zamówieniu

3. **Przechowywanie plików**:
   - Wszystkie pliki CAD, grafiki i dokumentacja w formacie binarnym
   - Nie używamy ścieżek do plików lokalnych

4. **Archiwizacja**:
   - Stare wersje i pliki testowe w folderze `archiv/YYYY-MM-DD/`

## 🚨 Ważne
- Nie modyfikuj plików wrapper-ów (`products_module.py`, `part_edit_enhanced.py`)
- Używaj najnowszych wersji: `*_enhanced.py` lub `*_v4.py`
- Wykonaj skrypt `06_FIX_PRODUCTS_CATALOG.sql` po aktualizacji