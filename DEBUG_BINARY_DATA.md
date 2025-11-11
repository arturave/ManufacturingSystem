# Debugowanie Problemu z Plikami Binarnymi

## Problem
Przy wczytywaniu produktu do edycji:
- Pliki DXF nie są rozpoznawane ("not a DXF file")
- Pliki STEP powodują błąd przepełnienia bufora
- Obrazy PNG nie są identyfikowane

## Zmiany w kodzie

### 1. Ulepszone debugowanie w `safe_decode_binary()` (linie 55-127)
- Dodano szczegółowe logowanie każdego kroku dekodowania
- Rozpoznawanie formatów:
  - Hex z prefiksem `\\x`
  - Czysty hex (same znaki 0-9, A-F)
  - Base64
- Wyświetlanie rozmiaru danych przed i po dekodowaniu

### 2. Debugowanie wczytywania plików (linie 574-657)
- Logowanie typu i rozmiaru surowych danych
- Wyświetlanie pierwszych 50 znaków danych
- Informacje o wynikach dekodowania

### 3. Weryfikacja plików w `load_binary_to_preview()` (linie 631-688)
- Sprawdzanie sygnatur plików:
  - DXF: powinien zaczynać się od tekstu ASCII
  - PNG: sygnatura `\\x89PNG\\r\\n\\x1a\\n`
  - STEP: powinien zawierać "ISO-10303-21"
- Logowanie zapisanych bajtów do pliku tymczasowego

## Jak przetestować

1. **Uruchom aplikację i otwórz produkt do edycji**
2. **Sprawdź konsolę dla komunikatów**:

```
=== Loading CAD 2D Binary ===
Raw data type: <class 'str'>
Raw data length: XXXXX chars
First 50 chars: \\x494341774451...

cad_2d_binary: String data, length=XXXXX
cad_2d_binary: Detected hex format with \\x prefix
cad_2d_binary: Decoded hex to XXXXX bytes

Loading binary data for 12-017118_INOX304_2m.dxf
Binary data type: <class 'bytes'>
Binary data length: XXXXX
DXF header (first 100 bytes): b'0\\nSECTION...'
Wrote XXXXX bytes to temp file: C:\\Users\\...\\tmp.dxf
```

## Oczekiwane wyniki

### Poprawne dekodowanie:
- DXF: Header powinien zawierać "0\\nSECTION" lub podobny tekst ASCII
- PNG: Pierwsze 8 bajtów to `89504e470d0a1a0a` (hex)
- STEP: Powinien zaczynać się od "ISO-10303-21"

### Jeśli nadal są błędy:

1. **"All chars are hex"** → dane są w formacie hex bez prefiksu
2. **"Looks like base64"** → dane są zakodowane w base64
3. **"Unknown data format"** → format nie został rozpoznany

## Możliwe przyczyny problemów

1. **Podwójne kodowanie**: Dane mogły być zakodowane do base64, a następnie do hex
2. **Uszkodzone dane**: Dane w bazie mogą być uszkodzone
3. **Niepoprawny format**: Baza może zwracać dane w innym formacie niż oczekiwany

## Rozwiązania

### Jeśli dane są w base64 zakodowane jako hex:
1. Najpierw dekoduj z hex
2. Potem dekoduj z base64

### Jeśli dane są uszkodzone:
1. Dodaj nowy produkt z plikami
2. Sprawdź czy nowe dane są poprawnie zapisane

## Logi do analizy

Zbierz następujące informacje:
1. Typ surowych danych (`Raw data type`)
2. Pierwsze 50 znaków (`First 50 chars`)
3. Metoda dekodowania (`Detected hex format` / `Looks like base64`)
4. Rozmiar po dekodowaniu (`Decoded to X bytes`)
5. Weryfikacja sygnatury pliku

Te informacje pomogą zidentyfikować dokładny problem z dekodowaniem.