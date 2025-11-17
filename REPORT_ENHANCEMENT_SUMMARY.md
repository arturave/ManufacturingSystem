# Podsumowanie Ulepszeń Systemu Raportowania

## Data: 2025-11-17

## Wprowadzone Zmiany

### 1. Scentralizowany System Ustawień
- **Nowy moduł**: `settings_manager.py`
  - Zarządzanie ustawieniami aplikacji
  - Obsługa logo producenta i użytkownika
  - Konfiguracja raportów i eksportu
  - Ustawienia wyświetlania i motywu

- **Dialog ustawień**: `settings_dialog.py`
  - Graficzny interfejs konfiguracji
  - Zakładki: Dane firmy, Logo, Raporty, Wyświetlanie, Eksport
  - Możliwość importu/eksportu ustawień

### 2. Logo w Aplikacji
- **Logo producenta**: Automatyczne ładowanie z pliku `logo.jpg`
- **Logo użytkownika**: Możliwość ustawienia własnego logo w ustawieniach
- **Wyświetlanie**: Logo pojawia się w nagłówku aplikacji
- **Skalowanie**: Automatyczne dopasowanie rozmiaru (80x60 px)

### 3. Zaawansowany Generator Raportów
- **Nowy moduł**: `advanced_report_generator.py`
  - Generowanie raportów Excel z miniaturami
  - Generowanie raportów Word z miniaturami
  - Konwersja do PDF (wymaga docx2pdf)
  - Wsparcie dla logo firmy w raportach

### 4. Miniatury w Raportach
- **Excel**: Miniatury produktów osadzone w komórkach
- **Word/PDF**: Miniatury w tabelach produktów
- **Konfiguracja**: Możliwość włączenia/wyłączenia w ustawieniach
- **Rozmiar**: Automatyczne skalowanie (60x40 px dla Excel, 0.8" dla Word)

## Użytkowanie

### Otwieranie Ustawień
1. Kliknij przycisk "⚙️ Ustawienia" w nagłówku aplikacji
2. Skonfiguruj żądane opcje
3. Kliknij "Zapisz" aby zastosować zmiany

### Ustawianie Logo Użytkownika
1. Otwórz Ustawienia → zakładka "Logo"
2. Wybierz "Logo użytkownika"
3. Kliknij "Przeglądaj..." i wybierz plik obrazu
4. Zapisz ustawienia

### Generowanie Raportów z Miniaturami
```python
from advanced_report_generator import AdvancedReportGenerator

# Inicjalizacja generatora
generator = AdvancedReportGenerator()

# Dane produktów (muszą zawierać 'thumbnail_data' lub 'thumb_data')
products = [
    {
        'name': 'Produkt 1',
        'idx_code': 'IDX001',
        'material': 'Stal',
        'thickness_mm': 5,
        'qty': 10,
        'price': 100.50,
        'thumbnail_data': b'...'  # Dane binarne obrazu
    },
    # ...
]

# Informacje o kliencie
customer_info = {
    'name': 'Firma ABC',
    'address': 'ul. Przykładowa 1, 00-000 Warszawa',
    'nip': '1234567890'
}

# Informacje o zamówieniu
order_info = {
    'order_number': 'ZAM/2025/001',
    'date': '2025-11-17'
}

# Generowanie raportu Excel
success = generator.generate_excel_report(
    data=products,
    output_path='raport.xlsx',
    title='Raport Zamówienia',
    customer_info=customer_info,
    order_info=order_info
)

# Generowanie raportu PDF
success = generator.generate_pdf_report(
    data=products,
    output_path='raport.pdf',
    title='Raport Zamówienia',
    customer_info=customer_info,
    order_info=order_info
)

# Generowanie wielu formatów jednocześnie
results = generator.generate_comprehensive_report(
    data=products,
    output_dir='raporty',
    base_name='zamowienie_001',
    formats=['xlsx', 'pdf', 'docx'],
    title='Raport Zamówienia',
    customer_info=customer_info,
    order_info=order_info
)
```

## Wymagania

### Zainstalowane moduły
- `openpyxl` - generowanie plików Excel
- `python-docx` - generowanie plików Word
- `docx2pdf` - konwersja Word do PDF (Windows)
- `Pillow` - obsługa obrazów
- `customtkinter` - interfejs graficzny

### Instalacja brakujących modułów
```bash
pip install openpyxl python-docx docx2pdf Pillow customtkinter
```

## Struktura Plików

```
ManufacturingSystem/
├── logo.jpg                          # Logo producenta
├── settings/                         # Katalog ustawień
│   ├── app_settings.json           # Plik konfiguracji
│   └── logos/                      # Katalog na logo
│       ├── manufacturer_logo.jpg   # Kopia logo producenta
│       └── user_logo.jpg          # Logo użytkownika
├── settings_manager.py             # Moduł zarządzania ustawieniami
├── settings_dialog.py              # Dialog ustawień GUI
├── advanced_report_generator.py    # Generator raportów z miniaturami
└── mfg_app.py                     # Główna aplikacja (zaktualizowana)
```

## Konfiguracja Ustawień

### Przykładowy plik app_settings.json
```json
{
  "company_name": "Manufacturing System",
  "company_address": "ul. Produkcyjna 10\n00-000 Warszawa",
  "company_phone": "+48 123 456 789",
  "company_email": "kontakt@firma.pl",
  "company_nip": "1234567890",
  "company_regon": "123456789",
  "manufacturer_logo_path": "settings/logos/manufacturer_logo.jpg",
  "user_logo_path": "settings/logos/user_logo.jpg",
  "use_user_logo": false,
  "report_include_thumbnails": true,
  "report_thumbnail_size": [60, 40],
  "report_include_details": true,
  "report_language": "pl",
  "list_show_thumbnails": true,
  "list_thumbnail_size": [50, 50],
  "theme_mode": "dark",
  "color_theme": "blue",
  "export_format": "xlsx",
  "export_include_attachments": true,
  "export_compress_images": true,
  "export_image_quality": 85
}
```

## Rozwiązywanie Problemów

### Logo nie wyświetla się
1. Sprawdź czy plik `logo.jpg` istnieje w głównym katalogu aplikacji
2. Upewnij się, że plik jest prawidłowym obrazem (JPG, PNG)
3. Sprawdź uprawnienia do odczytu pliku

### Miniatury nie pojawiają się w raportach
1. Sprawdź czy w ustawieniach włączona jest opcja "Dołączaj miniatury w raportach"
2. Upewnij się, że produkty mają dane miniatur (`thumbnail_data` lub `thumb_data`)
3. Sprawdź czy dane miniatur są prawidłowymi danymi binarnymi obrazów

### Błąd przy generowaniu PDF
1. Upewnij się, że zainstalowany jest moduł `docx2pdf`
2. Na Windows wymagany jest zainstalowany Microsoft Word
3. Alternatywnie generuj raport w formacie DOCX

## Przyszłe Ulepszenia

1. **Szablony raportów**: Możliwość tworzenia i zapisywania własnych szablonów
2. **Wykresy w raportach**: Dodanie wykresów statystycznych
3. **Podpis cyfrowy**: Możliwość dodania podpisu cyfrowego do PDF
4. **Email z raportami**: Automatyczne wysyłanie raportów mailem
5. **Harmonogram raportów**: Automatyczne generowanie raportów okresowych