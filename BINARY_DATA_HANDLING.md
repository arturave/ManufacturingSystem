# Obsługa Danych Binarnych - Dokumentacja

## Architektura Rozwiązania

### Problem
Supabase REST API używa JSON do komunikacji, który nie obsługuje natywnie typu `bytes`. Jednocześnie PostgreSQL oferuje typ `bytea` dla efektywnego przechowywania danych binarnych.

### Rozwiązanie
System używa dwuetapowego przetwarzania:

1. **Zapis (Python → Supabase → PostgreSQL)**
   - Python: `bytes` → base64 string (dla JSON)
   - Supabase REST API: przyjmuje base64 string
   - PostgreSQL: automatycznie dekoduje base64 → przechowuje jako `bytea`

2. **Odczyt (PostgreSQL → Supabase → Python)**
   - PostgreSQL: zwraca `bytea`
   - Supabase REST API: konwertuje na `bytes`/`bytearray`/`memoryview`
   - Python: używa `safe_decode_binary()` do obsługi różnych formatów

## Implementacja

### Funkcja `safe_decode_binary()`
Uniwersalna funkcja dekodująca dane binarne z różnych formatów:
```python
def safe_decode_binary(data, field_name="data"):
    """
    Obsługuje:
    - bytes (zwraca bez zmian)
    - bytearray/memoryview (z PostgreSQL bytea)
    - string (próbuje dekodować z base64)
    """
```

### Lokalizacje w kodzie

#### `products_module_enhanced.py`
- **Linie 628-685**: Kodowanie do base64 przed zapisem
- **Uwaga**: Zawsze koduje `bytes` → base64 dla Supabase REST API

#### `part_edit_enhanced_v4.py`
- **Linie 41-73**: Definicja `safe_decode_binary()`
- **Linie 561-601**: Użycie przy wczytywaniu plików CAD i obrazów
- **Linia 650**: Użycie przy wyświetlaniu miniaturek

## Typy Plików

### Obsługiwane formaty binarnych
- **CAD 2D**: DXF, DWG
- **CAD 3D**: STEP, STL, IGS, STP
- **Obrazy**: JPG, PNG, BMP
- **Dokumentacja**: PDF, DOC, DOCX
- **Archiwa**: ZIP, 7Z

### Pola w bazie danych
```sql
-- Tabela: products_catalog
cad_2d_binary         bytea  -- Pliki CAD 2D
cad_3d_binary         bytea  -- Pliki CAD 3D
user_image_binary     bytea  -- Zdjęcia produktów
documentation_binary  bytea  -- Dokumentacja główna
additional_documentation bytea -- Dokumentacja dodatkowa
thumbnail_100         bytea  -- Miniaturka 100x100
preview_800          bytea  -- Podgląd 800px
preview_4k           bytea  -- Podgląd 4K
```

## Przepływ Danych

### 1. Dodawanie nowego produktu
```
Użytkownik wybiera plik
    ↓
Python wczytuje jako bytes
    ↓
Kodowanie base64.b64encode()
    ↓
Wysłanie przez Supabase REST API (JSON)
    ↓
PostgreSQL dekoduje i zapisuje jako bytea
```

### 2. Odczytywanie produktu
```
PostgreSQL zwraca bytea
    ↓
Supabase konwertuje na bytes/bytearray
    ↓
safe_decode_binary() rozpoznaje format
    ↓
Zwraca bytes do aplikacji
    ↓
Wyświetlenie/przetworzenie pliku
```

## Diagnostyka Problemów

### Błąd: "Object of type bytes is not JSON serializable"
**Przyczyna**: Próba wysłania surowych bytes bez kodowania base64
**Rozwiązanie**: Użyj `base64.b64encode(data).decode('utf-8')`

### Błąd: "Invalid base64-encoded string"
**Przyczyna**: Nieprawidłowe padding lub znaki w base64
**Rozwiązanie**: Użyj `fix_base64_padding()` przed dekodowaniem

### Błąd: "Could not decode field_name"
**Przyczyna**: Dane w nierozpoznawalnym formacie
**Rozwiązanie**: Sprawdź typ danych w debuggerze

## Wydajność

### Rozmiary danych
- Base64 zwiększa rozmiar o ~33% podczas transmisji
- PostgreSQL bytea przechowuje dane w oryginalnym rozmiarze
- Kompresja ZIP przed zapisem może zmniejszyć rozmiar 50-90%

### Limity
- Supabase REST API: max 10MB per request
- PostgreSQL bytea: teoretycznie do 1GB
- Zalecane: < 5MB per plik dla wydajności

## Migracja

### Skrypty migracji
1. `MIGRATE_TO_BLOB_STORAGE_SAFE.sql` - zachowuje stare kolumny
2. `MIGRATE_TO_BLOB_STORAGE.sql` - usuwa stare kolumny

### Status migracji
Sprawdź używając:
```sql
SELECT * FROM analyze_migration_status();
```

## Przyszłe Ulepszenia

1. **Kompresja**: Automatyczna kompresja ZIP przed zapisem
2. **Chunking**: Podział dużych plików na części
3. **CDN**: Użycie Supabase Storage dla bardzo dużych plików
4. **Cache**: Lokalne cache'owanie często używanych plików

## Podsumowanie

System efektywnie obsługuje pliki binarne poprzez:
- Kodowanie base64 tylko dla transportu (JSON)
- Natywne przechowywanie bytea w PostgreSQL
- Inteligentne dekodowanie różnych formatów
- Obsługę błędów i walidację

To rozwiązanie łączy wymagania REST API (JSON) z wydajnością bazy danych (bytea).