# ANALIZA PÓL TABELI products_catalog

## 1. POLA AKTYWNIE UŻYWANE W APLIKACJI ✅

### Podstawowe pola:
- **id** - klucz główny
- **idx_code** - indeks produktu (wyświetlany w listach)
- **name** - nazwa produktu
- **material_id** - powiązanie z materiałem
- **thickness_mm** - grubość materiału
- **customer_id** - powiązanie z klientem
- **is_active** - flaga aktywności
- **created_at** - data utworzenia
- **updated_at** - data aktualizacji

### Pola kosztowe:
- **material_laser_cost** - koszt materiału i lasera (UŻYWANE)
- **bending_cost** - koszt gięcia (UŻYWANE)
- **additional_costs** - koszty dodatkowe (UŻYWANE)
- **material_cost** - koszt materiału (DUPLIKAT?)
- **laser_cost** - koszt lasera (DUPLIKAT?)

### Pola opisowe:
- **description** - opis produktu
- **notes** - uwagi
- **category** - kategoria produktu

### Pola binarne (pliki CAD i dokumenty):
- **cad_2d_binary** - plik CAD 2D (bytea)
- **cad_3d_binary** - plik CAD 3D (bytea)
- **user_image_binary** - obraz użytkownika (bytea)
- **additional_documentation** - dodatkowa dokumentacja (bytea)

### Pola metadanych plików:
- **cad_2d_filename** - nazwa pliku CAD 2D
- **cad_3d_filename** - nazwa pliku CAD 3D
- **user_image_filename** - nazwa obrazu
- **additional_documentation_filename** - nazwa dokumentacji
- **cad_2d_filesize** - rozmiar pliku CAD 2D
- **cad_3d_filesize** - rozmiar pliku CAD 3D
- **user_image_filesize** - rozmiar obrazu
- **additional_documentation_filesize** - rozmiar dokumentacji

### Pola graficzne:
- **thumbnail_100** - miniatura 100x100 (bytea) - **PROBLEM: NIE GENEROWANE!**
- **preview_800** - podgląd 800px (bytea) - **PROBLEM: NIE GENEROWANE!**
- **preview_4k** - podgląd 4K (bytea) - **PROBLEM: NIE GENEROWANE!**
- **primary_graphic_source** - źródło grafiki (2D/3D/USER)

## 2. POLA NIEUŻYWANE W APLIKACJI ❌

### Pola nieużywane (można usunąć):
- **graphic_high_res** (text) - zastąpione przez binarne
- **graphic_low_res** (text) - zastąpione przez binarne
- **documentation_path** (text) - zastąpione przez binarne
- **tags** (text[]) - nie używane
- **usage_count** - nie aktualizowane
- **last_used_at** - nie aktualizowane
- **created_by** - nie wypełniane
- **updated_by** - nie wypełniane
- **render_settings** (jsonb) - nie używane
- **graphics_updated_at** - nie aktualizowane
- **cad_2d_mimetype** - nie używane
- **cad_3d_mimetype** - nie używane
- **user_image_mimetype** - nie używane
- **documentation_mimetype** - nie używane
- **additional_documentation_mimetype** - nie używane
- **subcategory** - nie używane
- **width_mm** - nie używane
- **height_mm** - nie używane
- **length_mm** - nie używane
- **weight_kg** - nie używane
- **surface_area_m2** - nie używane
- **production_time_minutes** - nie używane
- **machine_type** - nie używane

## 3. PROBLEMY ZIDENTYFIKOWANE 🔴

### Problem 1: Brak generowania miniatur
Kod zapisuje `thumbnail_100`, `preview_800`, `preview_4k` ale **NIE GENERUJE** tych miniatur!
W kodzie brakuje funkcji:
```python
# BRAKUJE:
def generate_thumbnail(image_data):
    # Generuj miniaturę 100x100
    pass

def generate_preview_800(image_data):
    # Generuj podgląd 800px
    pass

def generate_preview_4k(image_data):
    # Generuj podgląd 4K
    pass
```

### Problem 2: Duplikacja pól kosztowych
- **material_laser_cost** - używane jako główne pole
- **material_cost** + **laser_cost** - duplikacja, można usunąć

### Problem 3: Za dużo nieużywanych pól
Tabela ma **57 kolumn**, z czego **~30 nie jest używanych**!

## 4. REKOMENDACJE 📋

### Natychmiastowe działania:

1. **Dodać generowanie miniatur** - napisać funkcje generujące miniatury przy zapisie

2. **Usunąć trigger problematyczny** (już zrobione w skryptach SQL)

3. **Opcjonalnie: Wyczyścić nieużywane kolumny**:
```sql
-- Przykład czyszczenia
ALTER TABLE products_catalog
DROP COLUMN IF EXISTS graphic_high_res,
DROP COLUMN IF EXISTS graphic_low_res,
DROP COLUMN IF EXISTS documentation_path,
DROP COLUMN IF EXISTS tags,
DROP COLUMN IF EXISTS usage_count,
DROP COLUMN IF EXISTS last_used_at,
DROP COLUMN IF EXISTS created_by,
DROP COLUMN IF EXISTS updated_by,
DROP COLUMN IF EXISTS render_settings,
DROP COLUMN IF EXISTS graphics_updated_at;
```

### Długoterminowe:

1. **Zrefaktoryzować strukturę** - podzielić na mniejsze tabele:
   - products_catalog (podstawowe dane)
   - products_files (pliki binarne)
   - products_costs (koszty)
   - products_dimensions (wymiary - jeśli potrzebne)

2. **Dodać indeksy** dla często używanych pól

3. **Zoptymalizować przechowywanie plików** - rozważyć storage zewnętrzny

## 5. KOD DO DODANIA - GENEROWANIE MINIATUR

```python
from PIL import Image
import io
import base64

def generate_thumbnails(image_data: bytes) -> dict:
    """Generuj miniatury z danych obrazu"""
    try:
        # Otwórz obraz
        img = Image.open(io.BytesIO(image_data))

        # Thumbnail 100x100
        thumb_100 = img.copy()
        thumb_100.thumbnail((100, 100), Image.Resampling.LANCZOS)
        thumb_100_bytes = io.BytesIO()
        thumb_100.save(thumb_100_bytes, format='PNG')

        # Preview 800px
        preview_800 = img.copy()
        preview_800.thumbnail((800, 800), Image.Resampling.LANCZOS)
        preview_800_bytes = io.BytesIO()
        preview_800.save(preview_800_bytes, format='PNG')

        # Preview 4K (3840x2160 max)
        preview_4k = img.copy()
        preview_4k.thumbnail((3840, 2160), Image.Resampling.LANCZOS)
        preview_4k_bytes = io.BytesIO()
        preview_4k.save(preview_4k_bytes, format='PNG')

        return {
            'thumbnail_100': thumb_100_bytes.getvalue(),
            'preview_800': preview_800_bytes.getvalue(),
            'preview_4k': preview_4k_bytes.getvalue()
        }
    except Exception as e:
        print(f"Error generating thumbnails: {e}")
        return {}
```

## PODSUMOWANIE

1. **57 kolumn to za dużo** - większość nie jest używana
2. **Brak generowania miniatur** - trzeba dodać kod
3. **Struktura wymaga refaktoryzacji** - ale można działać na obecnej