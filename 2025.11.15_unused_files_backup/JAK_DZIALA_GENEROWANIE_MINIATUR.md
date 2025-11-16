# JAK DZIAŁA GENEROWANIE MINIATUR

## 1. STRUKTURA INTERFEJSU

W oknie edycji produktu (`part_edit_enhanced_v4.py`) są 2 główne zakładki:

### Zakładka "PLIKI CAD":
- **Panel 2D** - dla plików DXF/DWG
  - Radio button: "Użyj jako główną grafikę" (wartość: "2D")
- **Panel 3D** - dla plików STEP/STL/IGES
  - Radio button: "Użyj jako główną grafikę" (wartość: "3D")

### Zakładka "GRAFIKA":
- **Panel Grafika użytkownika** - dla plików JPG/PNG/BMP
  - Radio button: "Użyj jako główną grafikę" (wartość: "USER")

## 2. JAK DZIAŁA WYBÓR GŁÓWNEJ GRAFIKI

```python
# W part_edit_enhanced_v4.py:
self.graphic_source_var = tk.StringVar(value="")  # Zmienna przechowująca wybór

# Każdy panel ma radio button połączony z tą zmienną:
self.frame_2d = EnhancedFilePreviewFrame(..., self.graphic_source_var, "2D")
self.frame_3d = EnhancedFilePreviewFrame(..., self.graphic_source_var, "3D")
self.frame_user = EnhancedFilePreviewFrame(..., self.graphic_source_var, "USER")
```

Gdy użytkownik kliknie radio button pod jednym z paneli:
- Wartość `graphic_source_var` zmienia się na "2D", "3D" lub "USER"
- Jest to zapisywane jako `primary_graphic_source` w bazie danych

## 3. PROCES GENEROWANIA MINIATUR

### Krok 1: Użytkownik wgrywa pliki
- Plik 2D (DXF/DWG) → zapisany jako `cad_2d_binary`
- Plik 3D (STEP/STL) → zapisany jako `cad_3d_binary`
- Grafika (JPG/PNG) → zapisana jako `user_image_binary`

### Krok 2: Użytkownik wybiera źródło
Klika radio button "Użyj jako główną grafikę" pod wybranym panelem

### Krok 3: Przy zapisie (`save_product_to_catalog`)
```python
# Sprawdź wartość primary_graphic_source
source_type = part_data.get('primary_graphic_source', '')

if source_type == 'USER':
    # Generuj miniatury z user_image_binary (JPG/PNG)
    image_source = part_data['user_image_binary']

elif source_type == '2D':
    # Tu powinna być konwersja DXF/DWG do obrazu
    # TODO: Implementacja konwertera CAD 2D

elif source_type == '3D':
    # Tu powinien być rendering 3D do obrazu
    # TODO: Implementacja renderera 3D
```

### Krok 4: Generowanie 3 rozmiarów
```python
if image_source:
    thumbnails = generate_thumbnails_from_image(image_source)
    # Zwraca:
    # - thumbnail_100 (100x100 px)
    # - preview_800 (800x800 px)
    # - preview_4k (3840x2160 px)
```

## 4. AKTUALNY STAN

✅ **DZIAŁA:**
- Wybór źródła głównej grafiki (radio buttons)
- Zapis wartości `primary_graphic_source` do bazy
- Generowanie miniatur z plików graficznych (JPG/PNG)

❌ **NIE DZIAŁA:**
- Generowanie miniatur z plików CAD 2D (DXF/DWG)
- Generowanie miniatur z plików CAD 3D (STEP/STL)

## 5. CO TRZEBA DODAĆ

### Dla plików CAD 2D (DXF/DWG):
```python
def convert_cad_2d_to_image(cad_binary: bytes) -> bytes:
    """
    Konwertuje plik DXF/DWG do obrazu PNG
    Wymaga biblioteki np. ezdxf lub matplotlib
    """
    # TODO: Implementacja
    pass
```

### Dla plików CAD 3D (STEP/STL):
```python
def render_cad_3d_to_image(cad_binary: bytes) -> bytes:
    """
    Renderuje model 3D do obrazu PNG
    Wymaga biblioteki np. trimesh, pythonOCC lub FreeCAD
    """
    # TODO: Implementacja
    pass
```

## 6. PRZYKŁAD UŻYCIA

1. **Użytkownik otwiera edycję produktu**
2. **Wgrywa pliki:**
   - Plik 2D: `projekt.dxf`
   - Plik 3D: `model.step`
   - Grafika: `zdjecie.jpg`
3. **Wybiera główne źródło:**
   - Klika radio "Użyj jako główną grafikę" pod panelem "Grafika użytkownika"
4. **Zapisuje produkt**
5. **System automatycznie:**
   - Rozpoznaje że `primary_graphic_source = "USER"`
   - Bierze `user_image_binary` (zdjecie.jpg)
   - Generuje 3 miniatury (100px, 800px, 4K)
   - Zapisuje wszystko do bazy

## 7. WIZUALIZACJA FLOW

```
Użytkownik wybiera radio button
           ↓
graphic_source_var = "2D" / "3D" / "USER"
           ↓
    Zapis do bazy:
primary_graphic_source = "2D" / "3D" / "USER"
           ↓
Przy zapisie sprawdź co wybrane:
           ↓
    ┌─────────────┬──────────────┬──────────────┐
    │    "2D"     │     "3D"     │    "USER"    │
    │             │              │              │
    │ cad_2d_binary│cad_3d_binary│user_image_binary│
    │      ↓      │      ↓       │      ↓       │
    │[TODO:Convert]│[TODO:Render]│[DZIAŁA: PIL] │
    │      ↓      │      ↓       │      ↓       │
    └─────────────┴──────────────┴──────────────┘
                      ↓
              generate_thumbnails()
                      ↓
        thumbnail_100, preview_800, preview_4k
```

## PODSUMOWANIE

System jest zaprojektowany prawidłowo i logika wyboru źródła działa.
Brakuje tylko konwerterów dla plików CAD do obrazów.
Dla plików graficznych (JPG/PNG) wszystko działa już teraz!