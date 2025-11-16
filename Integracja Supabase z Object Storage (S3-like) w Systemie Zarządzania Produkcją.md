# Integracja Supabase z Object Storage (S3-like) w Systemie Zarządzania Produkcją

## Wstęp
Ten dokument wyjaśnia sens i korzyści z integracji bazy danych **Supabase** (opartej na PostgreSQL) z mechanizmem przechowywania plików w stylu **S3** (konkretnie: Supabase Storage, który jest w pełni S3-kompatybilny). Rozwiązanie to jest kluczowe dla aplikacji **Manufacturing System**, gdzie przechowujemy pliki typu 2D (DXF/DWG), 3D (STEP/IGES), skompresowaną dokumentację (ZIP/7Z) oraz grafiki (PNG/JPG dla thumbnails/previews). 

Integracja pozwala oddzielić **metadane** (struktura produktów, koszty, SLA) od **binarnych plików**, co poprawia wydajność, skalowalność i koszty. Dokument skierowany jest do innego programisty – zawiera uzasadnienie, architekturę, kroki implementacji i potencjalne pułapki. Nie zawiera kodu źródłowego (zgodnie z wytycznymi), ale odnosi się do istniejących modułów jak `products_module.py` i `part_edit_enhanced.py`.

## Sens Integracji: Dlaczego Supabase + S3-like Storage?
Aplikacja obsługuje duże pliki binarne (CAD, grafiki), co w czystej bazie danych (BYTEA w PostgreSQL) powoduje problemy:
- **Wydajność**: Zapytania DB stają się wolne (duże BLOB-y blokują indeksy, zwiększają backup time).
- **Koszty**: Przechowywanie w DB jest droższe (każdy bajt liczy się x2-3 vs. object storage).
- **Skalowalność**: DB nie jest zaprojektowane do plików >1MB; S3-like storage (Supabase Storage) to dedykowane rozwiązanie z CDN, wersjonowaniem i transformacjami (np. resize grafik).

**Korzyści hybrydowego podejścia (DB + Storage)**:
- **DB (Supabase)**: Przechowuje lekkie metadane (ID produktu, nazwa, URL do pliku, thumbnail_url, costs, SLA status). Szybkie zapytania (JOIN-y z `materials_dict`, `customers`).
- **Storage (S3-like)**: Przechowuje pliki binarne. Automatyczne skalowanie, globalne CDN (szybkie ładowanie thumbnails w UI), polityka dostępu (RLS – tylko autentykowani users uploadują).
- **Dla konkretnych typów plików**:
  - **2D/3D (CAD: DXF, STEP)**: Duże (5-50MB), rzadko modyfikowane – Storage zapewnia wersjonowanie (np. `cad/2d/product_id_v1.dxf`), URL w DB do podglądu w `integrated_viewer.py`.
  - **Skompresowana dokumentacja (ZIP/7Z)**: Archiwa (1-10MB) z raportami/PDF – Storage z cacheControl (długie TTL), URL do downloadu w `part_edit_enhanced.py`.
  - **Grafiki (PNG/JPG thumbnails/previews)**: Małe (10-500KB), często ładowane – Storage z transformacjami (resize na żywo via Supabase), URL w DB do CTkImage w `products_module.py`.
- **Ogólne zalety**:
  - **Koszt**: ~$0.006/GB/mies (Storage) vs. $0.023/GB (DB BYTEA) – oszczędność 70% dla 1TB plików.
  - **Bezpieczeństwo**: Signed URLs dla prywatnych plików, RLS w DB/Storage.
  - **Rozwój**: Łatwa migracja z legacy BYTEA (skrypt: pobierz binary, upload do Storage, update URL w DB).

Bez tej integracji: Aplikacja będzie wolna przy >100 produktach z plikami (np. thumbnails nie ładują się w UI z powodu blokad DB).

## Architektura Integracji
### Wysoki Poziom
1. **Metadane w DB (Supabase PostgreSQL)**:
   - Tabela `products_catalog`: Kolumny `id UUID`, `name TEXT`, `cad_2d_url TEXT`, `thumbnail_100_url TEXT`, `costs NUMERIC`, `sla_status TEXT`.
   - Indeksy na `name`, `is_active`, `thumbnail_100_url` (partial dla not null).
   - RLS: `ENABLE RLS; CREATE POLICY "Users can view own products" ON products_catalog FOR SELECT USING (auth.uid() = created_by);`.

2. **Pliki w Storage (Supabase S3-like Bucket)**:
   - Bucket: `product_files` (public dla thumbnails, private dla CAD/docs).
   - Ścieżki: `thumbnails/{product_id}_100.png`, `cad/2d/{product_id}.dxf`, `docs/{product_id}.zip`.
   - Polityki: `CREATE POLICY "Allow authenticated uploads" ON storage.objects FOR INSERT WITH CHECK (auth.role() = 'authenticated');`.

3. **Flow w Aplikacji**:
   - **Upload (np. w `part_edit_enhanced.py`)**: Czytaj plik lokalny → bytes → `supabase.storage.from('bucket').upload(path, bytes)` → pobierz `get_public_url(path)` → zapisz URL w DB via `insert/update`.
   - **Pobieranie (np. w `products_module.py`)**: Query DB po URL → `requests.get(url).content` → waliduj bytes (Pillow) → wyświetl w CTkImage.
   - **Generowanie thumbnails**: W `image_processing.py`: Z CAD/grafiki → Pillow resize → upload do Storage.

### Schemat Przepływu
```
Użytkownik edytuje produkt (part_edit_enhanced.py)
↓
Wczytaj plik lokalny → bytes (np. DXF 2D)
↓
Upload do Storage: supabase.storage.upload('cad/2d/id.dxf', bytes)
↓
Pobierz URL: get_public_url('cad/2d/id.dxf')
↓
Generuj thumbnail (Pillow): resize → upload('thumbnails/id_100.png')
↓
Zapisz metadane w DB: UPDATE products_catalog SET cad_2d_url = 'URL', thumbnail_100_url = 'thumb_URL'
↓
Wyświetl w UI (products_module.py): requests.get(thumb_URL) → CTkImage
```

## Korzyści dla Projektu Manufacturing System
- **Wydajność UI**: Thumbnails ładują się błyskawicznie (CDN), bez blokad DB – kluczowe dla listy produktów (100+ elementów).
- **Skalowalność**: Obsługa 1000+ plików bez wzrostu rozmiaru DB (tylko URL-e ~200B vs. 1MB binary).
- **Koszty**: Dla 100GB plików: ~$0.60/mies w Storage vs. ~$2.30 w DB BYTEA.
- **Funkcjonalność**: 
  - 2D/3D: Podgląd w `integrated_viewer.py` via URL (bez pobierania całego pliku).
  - Dokumentacja: Kompresja ZIP w Storage, URL do downloadu z progresem.
  - Grafiki: Automatyczne resize (Supabase transform: `?width=100`), walidacja sygnatury PNG/JPG.
- **Bezpieczeństwo**: Signed URLs dla docs (czasowe, np. 1h), RLS blokuje nieautoryzowany upload.

## Kroki Implementacji dla Innego Programisty
1. **Przygotowanie Supabase**:
   - Utwórz bucket `product_files` (Dashboard > Storage > New Bucket, public dla thumbnails).
   - Dodaj kolumny URL w `setup_database.sql`: `ALTER TABLE products_catalog ADD COLUMN cad_2d_url TEXT; ADD COLUMN thumbnail_100_url TEXT;`.
   - Włącz RLS na tabeli i Storage.

2. **W Modułach Python**:
   - W `part_edit_enhanced.py`: W `save_part()` – po wczytaniu bytes, użyj `upload_to_storage(bytes, filename)` → zapisz URL w `part_data`.
   - W `products_module.py`: W `load_products()` – query po URL, pobierz bytes via `requests.get(url)`, waliduj i cache (np. w dict).
   - W `image_processing.py`: Generuj thumbnails → upload → zwróć URL.

3. **Walidacja i Error Handling**:
   - Użyj `validate_image_bytes(bytes, 'thumbnail')` przed uploadem (sygnatura PNG/JPEG).
   - Fallback: Jeśli URL null, użyj placeholder (np. lokalny PNG).
   - Logi: `print(f"Uploaded to {url}")` w dev, Sentry w prod.

4. **Migracja Legacy**:
   - Skrypt: Query DB po starych BYTEA → dekoduj `safe_decode_binary` → upload do Storage → update URL → set BYTEA to NULL.

5. **Testy**:
   - W `tests/`: `pytest test_storage.py` – mock Supabase, sprawdź upload/download.
   - E2E: Dodaj produkt z plikiem → sprawdź, czy thumbnail w UI.

## Potencjalne Pułapki
- **CORS**: W Supabase Dashboard włącz CORS dla domeny app (dla requests.get z UI).
- **Rozmiar Plików**: Limit Storage 50MB/plik – waliduj przed upload (np. if len(bytes) > 50*1024*1024: error).
- **Koszty Egress**: Dla częstych download (np. thumbnails) – użyj cache w app (PIL cache lub Redis).
- **Autentykacja**: Użyj `supabase.auth.get_user()` przed upload – tylko logged-in users.

Ta integracja czyni system gotowym na produkcję – lekkie, szybkie i tanie. Jeśli potrzebujesz diagramu (np. Draw.io), daj znać!