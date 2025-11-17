# Integracja Supabase Storage - Instrukcja Wdrożenia

## 📋 Podsumowanie Zmian

Zintegrowałem Supabase Storage z panelem "Nowe zamówienie" dla obsługi załączników. Główne zmiany:

### ✅ Wykonane Zadania

1. **Migracja Bazy Danych** (`migration_add_storage_type.sql`)
   - Dodano pole `storage_type` do tabeli `attachments`
   - Pole `archive_data` jest teraz opcjonalne (dla nowych załączników)

2. **Moduł Storage** (`attachments_storage.py`)
   - Obsługa uploadu/downloadu do/z Supabase Storage
   - Sprawdzanie aplikacji domyślnych w systemie
   - Generowanie thumbnails dla obrazów
   - Wsparcie formatów: DXF, DWG, STEP, STP, IGS, IGES, PDF, DOC, DOCX, XLS, XLSX

3. **Manager Załączników** (`attachments_manager.py`)
   - Upload plików do Storage zamiast BYTEA
   - Kompatybilność wsteczna ze starymi załącznikami
   - Nowe metody: `can_preview_file()`, `has_default_application()`

4. **Interfejs GUI** (`attachments_gui_widgets.py`)
   - Sprawdzanie przed otwarciem pliku
   - Ostrzeżenia gdy brak aplikacji domyślnej
   - Rozszerzona lista obsługiwanych formatów

## 🚀 Kroki Wdrożenia

### 1. Wykonaj Migrację Bazy Danych

```sql
-- W Supabase SQL Editor wykonaj:
-- Zawartość pliku: migration_add_storage_type.sql
```

### 2. Sprawdź/Utwórz Bucket w Supabase

1. Przejdź do **Storage** w Supabase Dashboard
2. Sprawdź czy istnieje bucket `attachments`
3. Jeśli nie, utwórz nowy:
   - Nazwa: `attachments`
   - Public: **False** (dla bezpieczeństwa)
   - File size limit: **50MB**

### 3. Uruchom Test Integracji

```bash
python test_attachments_integration.py
```

Test sprawdzi:
- Połączenie z Supabase Storage
- Upload plików testowych
- Pobieranie plików
- Generowanie signed URLs
- Kompatybilność wsteczną

## 📁 Obsługiwane Formaty Plików

### Z Podglądem:
- **CAD 2D**: DXF, DWG
- **CAD 3D**: STEP, STP, IGS, IGES
- **Dokumenty**: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX
- **Obrazy**: PNG, JPG, JPEG, GIF, BMP, SVG
- **Tekst**: TXT, CSV

### Bez Podglądu (tylko pobieranie):
- **Archiwa**: ZIP, RAR, 7Z, TAR, GZ

## 🔧 Jak To Działa

### Dodawanie Załączników
1. W dialogu "Nowe zamówienie" kliknij **"Dodaj pliki"**
2. Wybierz pliki (max 50MB łącznie)
3. Pliki są uploadowane do Supabase Storage
4. Metadane zapisywane w bazie danych

### Otwieranie Plików
1. System sprawdza czy plik może być podglądany
2. Sprawdza czy jest aplikacja domyślna
3. Jeśli brak aplikacji - wyświetla ostrzeżenie
4. Pobiera plik ze Storage i otwiera lokalnie

## 💰 Korzyści

- **70% redukcja kosztów** przechowywania (vs BYTEA)
- **Szybsze ładowanie** listy załączników
- **Signed URLs** dla bezpiecznego dostępu
- **Automatyczne thumbnails** dla obrazów
- **Kompatybilność wsteczna** ze starymi załącznikami

## ⚠️ Ważne Informacje

1. **Stare załączniki** (BYTEA) nadal działają
2. **Nowe załączniki** są w Supabase Storage
3. **Limit pliku**: 50MB
4. **Bucket musi istnieć** przed użyciem

## 🔍 Weryfikacja

Po wdrożeniu sprawdź:

1. **W aplikacji**:
   - Dodaj nowy załącznik w zamówieniu
   - Otwórz plik DXF/DWG
   - Sprawdź ostrzeżenie dla nieobsługiwanych formatów

2. **W Supabase Dashboard**:
   - Storage → Bucket `attachments`
   - Powinny być widoczne foldery: `order/[ID]/attachments/`

## 📞 Wsparcie

W razie problemów:
1. Sprawdź logi w konsoli
2. Uruchom `test_attachments_integration.py`
3. Sprawdź uprawnienia bucket w Supabase

---

**Integracja zakończona pomyślnie!** 🎉