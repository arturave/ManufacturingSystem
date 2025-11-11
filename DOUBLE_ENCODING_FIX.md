# Rozwiązanie Problemu Podwójnego Kodowania

## Problem
Dane binarne w bazie są **podwójnie zakodowane**:
1. Najpierw: binary → base64 (podczas zapisu)
2. Potem: base64 → hex (Supabase REST API)

### Dowody z logów:
```
DXF header: b'ICAwDQpTRUNUSU9ODQog'
   ↓ base64 decode
   '0\nSECTION\n' ✓ (poprawny nagłówek DXF)

STEP header: b'SVNPLTEwMzAzLTIxOw0K'
   ↓ base64 decode
   'ISO-10303-21;\n' ✓ (poprawny nagłówek STEP)

PNG header: 6956424f5277304b
   ↓ hex to ASCII
   'iVBORw0K' (początek base64 dla PNG)
```

## Rozwiązanie

### Przepływ dekodowania:
```
Supabase API zwraca: "\x494341774451..." (hex)
       ↓ decode hex
"ICAwDQpTRUNUSU9ODQog..." (base64)
       ↓ decode base64
b'0\nSECTION\n...' (oryginalne dane binarne)
```

### Zaktualizowana funkcja `safe_decode_binary()`:
```python
def safe_decode_binary(data, field_name="data"):
    # KROK 1: Dekoduj z hex (jeśli ma prefix \x)
    if data.startswith('\\x'):
        hex_str = data[2:]
        decoded_data = bytes.fromhex(hex_str)

        # KROK 2: Sprawdź czy to base64
        if all(32 <= b < 127 for b in decoded_data[:100]):
            decoded_str = decoded_data.decode('ascii')

            # KROK 3: Dekoduj z base64
            if re.match(r'^[A-Za-z0-9+/\r\n]+=*$', decoded_str[:1000]):
                result = base64.b64decode(decoded_str)
                return result
```

## Przepływ danych

### Zapis (działa poprawnie):
```
Python: bytes → base64.encode() → string
   ↓
Supabase API: przyjmuje base64 string
   ↓
PostgreSQL: zapisuje jako bytea
```

### Odczyt (naprawione):
```
PostgreSQL: bytea
   ↓
Supabase API: konwertuje na hex z \x
   ↓
Python: hex decode → base64 decode → bytes
```

## Weryfikacja

### Przed naprawą:
- DXF: `b'ICAwDQpTRUNUSU9ODQog'` → "not a DXF file"
- STEP: `b'SVNPLTEwMzAzLTIxOw0K'` → "buffer overflow"
- PNG: `6956424f5277304b` → "cannot identify image"

### Po naprawie:
- DXF: `b'0\nSECTION\n...'` ✓
- STEP: `b'ISO-10303-21;\n...'` ✓
- PNG: `b'\x89PNG\r\n\x1a\n...'` ✓

## Pliki zaktualizowane

1. **part_edit_enhanced_v4.py** (linie 55-155)
   - Obsługa podwójnego dekodowania hex→base64→binary

2. **products_module_enhanced.py** (linie 41-109)
   - Ta sama logika dekodowania

## Dlaczego to się stało?

### Przyczyna:
1. **Zapis**: Kod koduje `bytes` → `base64` dla JSON (poprawne)
2. **PostgreSQL**: Zapisuje base64 jako `bytea` (dekoduje base64)
3. **Problem**: Supabase nie wie, że dane były base64
4. **Odczyt**: Supabase traktuje surowe bajty jako binarne i koduje do hex
5. **Rezultat**: Otrzymujemy base64 zakodowane jako hex

### Rozwiązanie alternatywne (na przyszłość):
- Użyć Supabase Storage API zamiast przechowywać w kolumnach bytea
- Lub: zapisywać jako TEXT z base64, nie jako bytea

## Testowanie

Po zastosowaniu poprawki:
1. Otwórz produkt do edycji
2. Sprawdź czy pliki są widoczne
3. Sprawdź logi dla potwierdzenia:
   ```
   cad_2d_binary: Hex-decoded data looks like base64, attempting second decode
   cad_2d_binary: Successfully decoded base64 to 54973 bytes
   cad_2d_binary: Final decoded first 20 bytes: b'0\nSECTION\n...'
   ```

Pliki powinny teraz działać poprawnie!