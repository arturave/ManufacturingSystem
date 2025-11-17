# Raport z Analizy Problemu Miniatur

## Data: 2025-11-17

## Problem
Miniatury nie są wyświetlane w listach produktów mimo włączonych ustawień.

## Analiza

### 1. Stan bazy danych
Po przeprowadzeniu testu stwierdzono:
- **7 produktów** w bazie danych
- **4 produkty (57%)** mają miniatury
- **3 produkty (43%)** nie mają miniatur

### 2. Format przechowywania miniatur
Miniatury są przechowywane jako **HTTP URL-e** do Supabase Storage, a NIE jako data URL-e (base64):
```
preview_800_url: "https://[supabase-url]/storage/v1/object/[path]"
thumbnail_100_url: "https://[supabase-url]/storage/v1/object/[path]"
```

### 3. Problemy zidentyfikowane

#### Problem 1: Kod oczekuje data URL-ów
Obecny kod w `products_selector_dialog_v2.py` i `mfg_app.py` szuka miniatur w formacie data URL:
```python
if preview_url.startswith('data:image'):
    # Dekoduj base64...
```

Ale w rzeczywistości miniatury są HTTP URL-ami, które wymagają pobrania ze Storage.

#### Problem 2: Brak relacji w bazie danych
Brak relacji między tabelami:
- `parts` - części zamówień
- `products_catalog` - katalog produktów

To uniemożliwia pobieranie miniatur dla części zamówień.

## Rozwiązania

### Rozwiązanie 1: Obsługa HTTP URL-i (zalecane)

Zaktualizować metodę pobierania miniatur aby obsługiwała HTTP URL-e:

```python
def get_thumbnail_from_url(url):
    """Pobierz miniaturę z HTTP URL"""
    try:
        if url.startswith('http'):
            # Pobierz obrazek z URL
            import requests
            from PIL import Image
            import io

            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                image = Image.open(io.BytesIO(response.content))
                image.thumbnail((40, 40), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(image)
    except Exception as e:
        print(f"Error loading thumbnail from URL: {e}")
    return None
```

### Rozwiązanie 2: Konwersja do base64 przy zapisie

Alternatywnie, przy zapisywaniu produktów konwertować miniatury do base64:

```python
def convert_url_to_base64(url):
    """Konwertuj HTTP URL na data URL base64"""
    import requests
    import base64

    response = requests.get(url)
    if response.status_code == 200:
        base64_data = base64.b64encode(response.content).decode()
        mime_type = response.headers.get('content-type', 'image/jpeg')
        return f"data:{mime_type};base64,{base64_data}"
    return None
```

### Rozwiązanie 3: Dodanie relacji w bazie danych

Dodać kolumnę `product_catalog_id` do tabeli `parts`:

```sql
ALTER TABLE parts
ADD COLUMN product_catalog_id UUID REFERENCES products_catalog(id);
```

Lub przechowywać miniaturę bezpośrednio w tabeli `parts`:

```sql
ALTER TABLE parts
ADD COLUMN preview_url TEXT;
```

## Implementacja Szybkiego Rozwiązania

Ze względu na to, że miniatury są w Supabase Storage, najprostszym rozwiązaniem jest użycie publicznych URL-i przez klienta Supabase:

```python
def get_thumbnail_from_storage(product, supabase_client):
    """Get thumbnail using Supabase client"""
    try:
        if product.get('preview_800_url'):
            url = product['preview_800_url']

            # Jeśli to publiczny URL, pobierz bezpośrednio
            if url.startswith('http'):
                # Użyj requests lub urllib
                import urllib.request
                from PIL import Image
                import io

                with urllib.request.urlopen(url) as response:
                    image_data = response.read()
                    image = Image.open(io.BytesIO(image_data))
                    image.thumbnail((40, 40), Image.Resampling.LANCZOS)
                    return ImageTk.PhotoImage(image)

    except Exception as e:
        print(f"Error: {e}")
    return None
```

## Kroki do naprawy

1. **Zaktualizować metodę `get_product_thumbnail` w `products_selector_dialog_v2.py`** aby obsługiwała HTTP URL-e
2. **Zaktualizować metodę `_get_part_thumbnail` w `mfg_app.py`** aby obsługiwała HTTP URL-e
3. **Opcjonalnie: Dodać cache miniatur** aby nie pobierać ich za każdym razem
4. **Testować z produktami które mają miniatury** (np. PC-202511-0001, PC-202511-0002)

## Tymczasowe obejście

Dopóki miniatury nie zostaną naprawione, można:
1. Wyłączyć wyświetlanie miniatur w ustawieniach
2. Używać tylko produktów z miniaturami
3. Ręcznie dodać miniatury w formacie base64 do produktów