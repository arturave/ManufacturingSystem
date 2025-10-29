# Instrukcje integracji nowych funkcjonalności

## 📋 Spis treści
1. [Naprawa widoku v_orders_full](#1-naprawa-widoku-v_orders_full)
2. [Instalacja tabel w bazie danych](#2-instalacja-tabel-w-bazie-danych)
3. [Integracja załączników w ofertach](#3-integracja-załączników-w-ofertach)
4. [Integracja załączników w zamówieniach](#4-integracja-załączników-w-zamówieniach)
5. [Rozszerzenie konwersji ofert](#5-rozszerzenie-konwersji-ofert)
6. [Integracja generowania WZ](#6-integracja-generowania-wz)

---

## 1. Naprawa widoku v_orders_full

### ⚠️ PRIORYTET KRYTYCZNY - Wykonaj jako pierwsze!

**Problem:** Widok `v_orders_full` używa nieistniejącej kolumny `c.contact` zamiast nowych kolumn z rozszerzonej tabeli `customers`.

**Rozwiązanie:**

1. Zaloguj się do **Supabase Dashboard**
2. Przejdź do **SQL Editor**
3. Otwórz plik `fix_orders_view.sql`
4. Skopiuj całą zawartość i wklej do SQL Editor
5. Kliknij **RUN** (wykonaj zapytanie)

```sql
-- Plik: fix_orders_view.sql
-- Ten skrypt naprawia widok v_orders_full
```

**Weryfikacja:**
```sql
SELECT COUNT(*) FROM v_orders_full;
-- Powinno zwrócić liczbę zamówień (nie błąd)
```

---

## 2. Instalacja tabel w bazie danych

### Krok 2.1: Dodanie tabel attachments i delivery_notes

1. Otwórz **Supabase SQL Editor**
2. Otwórz plik `add_attachments_and_wz_tables.sql`
3. Skopiuj całą zawartość i wklej do SQL Editor
4. Kliknij **RUN**

Ten skrypt utworzy:
- Tabelę `attachments` - załączniki jako archiwa ZIP
- Tabelę `delivery_notes` - dokumenty WZ
- Automatycznie utworzy tabelę `quotations` jeśli nie istnieje
- Funkcje pomocnicze i triggery
- Uprawnienia dla roli `anon`

**Weryfikacja:**
```sql
-- Sprawdź czy tabele zostały utworzone
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('attachments', 'delivery_notes', 'quotations');

-- Powinno zwrócić 3 wiersze
```

---

## 3. Integracja załączników w ofertach

### Krok 3.1: Import modułów

W pliku `quotations_module.py` dodaj import na początku pliku:

```python
# Na początku pliku, po innych importach:
from attachments_gui_widgets import AttachmentsWidget
```

### Krok 3.2: Dodanie widgetu załączników do QuotationDialog

W klasie `QuotationDialog.__init__` dodaj:

```python
def __init__(self, parent, db: QuotationManager, quotation_data=None):
    super().__init__(parent)
    self.db = db
    self.quotation_data = quotation_data
    self.items = []
    self.quotation_id = quotation_data['id'] if quotation_data else None  # DODAJ TO

    # ... reszta kodu ...
```

### Krok 3.3: Dodanie widgetu w setup_ui

W metodzie `QuotationDialog.setup_ui()`, po sekcji "Notes" (przed "Bottom buttons"):

```python
def setup_ui(self):
    # ... istniejący kod ...

    # Notes
    notes_frame = ctk.CTkFrame(main_frame)
    notes_frame.pack(fill="x", pady=10)
    # ... kod notatek ...

    # DODAJ TO - Załączniki
    self.attachments_widget = AttachmentsWidget(
        main_frame,
        db_client=self.db.client,
        entity_type='quotation',
        entity_id=self.quotation_id
    )
    self.attachments_widget.pack(fill="both", expand=True, padx=5, pady=10)

    # Bottom buttons
    btn_frame = ctk.CTkFrame(main_frame)
    # ... reszta kodu ...
```

### Krok 3.4: Aktualizacja entity_id po zapisaniu

W metodzie `QuotationDialog.save_quotation()`, po utworzeniu oferty:

```python
def save_quotation(self):
    # ... istniejący kod tworzenia oferty ...

    result = self.db.create_quotation(quotation)
    if result:
        # DODAJ TO - Ustaw ID dla widgetu załączników
        self.quotation_id = result['id']
        self.attachments_widget.set_entity_id(result['id'])

        messagebox.showinfo("Sukces", f"Oferta {result['quote_no']} została utworzona")
        # NIE zamykaj okna od razu aby użytkownik mógł dodać załączniki
        # self.destroy()  # ZAKOMENTUJ lub usuń tę linię
    else:
        messagebox.showerror("Błąd", "Nie udało się utworzyć oferty")
```

---

## 4. Integracja załączników w zamówieniach

### Krok 4.1: Import w mfg_app.py

Na początku pliku `mfg_app.py` dodaj:

```python
from attachments_gui_widgets import AttachmentsWidget
```

### Krok 4.2: Dodanie widgetu w OrderDialog

W klasie `OrderDialog.__init__`:

```python
def __init__(self, parent, db: SupabaseManager, order_data=None):
    super().__init__(parent)
    self.db = db
    self.order_data = order_data
    self.parts_list = []
    self.order_id = order_data['id'] if order_data else None  # DODAJ TO

    # ... reszta kodu ...
```

W metodzie `OrderDialog.setup_ui()`, po sekcji części (parts section):

```python
def setup_ui(self):
    # ... istniejący kod ...

    # Parts section
    # ... kod części ...

    # DODAJ TO - Załączniki
    self.attachments_widget = AttachmentsWidget(
        main_frame,
        db_client=self.db.client,
        entity_type='order',
        entity_id=self.order_id
    )
    self.attachments_widget.pack(fill="both", expand=True, padx=5, pady=10)

    # Bottom buttons
    # ... reszta kodu ...
```

### Krok 4.3: Aktualizacja po zapisaniu zamówienia

W metodzie gdzie zapisujesz zamówienie (prawdopodobnie `save_order()`):

```python
def save_order(self):
    # ... istniejący kod ...

    result = self.db.create_order(order)
    if result:
        # DODAJ TO
        self.order_id = result['id']
        self.attachments_widget.set_entity_id(result['id'])

        messagebox.showinfo("Sukces", "Zamówienie zostało utworzone")
        # Nie zamykaj okna od razu
        # self.destroy()  # ZAKOMENTUJ
```

---

## 5. Rozszerzenie konwersji ofert

### Krok 5.1: Import w quotations_module.py

Na początku pliku dodaj:

```python
from attachments_manager import AttachmentsManager
```

### Krok 5.2: Aktualizacja metody convert_to_order

W klasie `QuotationManager`, znajdź metodę `convert_to_order()` i zmodyfikuj ją:

```python
def convert_to_order(self, quotation_id: str):
    """Konwertuj ofertę na zamówienie"""
    try:
        # ... istniejący kod konwersji ...

        if order_response.data:
            order_id = order_response.data[0]['id']

            # Dodaj części do zamówienia
            for item in items_response.data:
                # ... istniejący kod dodawania części ...

            # DODAJ TO - Kopiuj załączniki z oferty do zamówienia
            attachments_manager = AttachmentsManager(self.client)
            copied_count = attachments_manager.copy_attachments(
                source_entity_type='quotation',
                source_entity_id=quotation_id,
                target_entity_type='order',
                target_entity_id=order_id,
                created_by='system'
            )

            if copied_count > 0:
                print(f"✅ Skopiowano {copied_count} załączników z oferty do zamówienia")

            # Zaktualizuj ofertę
            self.client.table('quotations').update({
                'status': 'CONVERTED',
                'converted_to_order': order_id
            }).eq('id', quotation_id).execute()

            return order_response.data[0]

        return None
    except Exception as e:
        print(f"Error converting quotation: {e}")
        return None
```

---

## 6. Integracja generowania WZ

### Krok 6.1: Import w mfg_app.py

```python
from wz_dialog import WZGeneratorDialog
```

### Krok 6.2: Dodanie przycisku w MainApplication

W klasie `MainApplication`, znajdź miejsce gdzie są przyciski zamówień (prawdopodobnie w metodzie tworzenia nagłówka lub menu zamówień).

Dodaj nowy przycisk:

```python
# W metodzie setup_ui() lub podobnej, w sekcji przycisków zamówień:

ctk.CTkButton(
    button_frame,  # Użyj odpowiedniej ramki przycisków
    text="📦 Generuj WZ",
    width=130,
    height=35,
    command=self.generate_wz,
    fg_color="#FF6B6B"
).pack(side="left", padx=5)
```

### Krok 6.3: Dodanie metody generate_wz

W klasie `MainApplication`:

```python
def generate_wz(self):
    """Generuje dokument WZ dla wybranego zamówienia"""
    # Pobierz wybrane zamówienie z listy
    selection = self.orders_tree.selection()
    if not selection:
        messagebox.showwarning("Uwaga", "Wybierz zamówienie do wygenerowania WZ")
        return

    # Pobierz ID zamówienia z tagów
    item = self.orders_tree.item(selection[0])
    order_id = item['tags'][1]  # Drugi tag to ID zamówienia

    # Otwórz dialog generowania WZ
    try:
        dialog = WZGeneratorDialog(self, self.db.client, order_id)
        dialog.focus()
    except Exception as e:
        messagebox.showerror("Błąd", f"Nie można otworzyć dialogu WZ:\n{e}")
```

---

## ✅ Weryfikacja integracji

### Test 1: Lista zamówień
1. Uruchom aplikację
2. Przejdź do listy zamówień
3. **Oczekiwany rezultat:** Lista zamówień wyświetla dane (brak pustej listy)

### Test 2: Załączniki w ofercie
1. Utwórz nową ofertę
2. Zapisz ofertę
3. Dodaj załączniki (kilka plików)
4. **Oczekiwany rezultat:** Pliki są widoczne na liście załączników

### Test 3: Konwersja oferty z załącznikami
1. Utwórz ofertę z załącznikami
2. Konwertuj ofertę na zamówienie
3. Otwórz zamówienie
4. **Oczekiwany rezultat:** Załączniki zostały skopiowane do zamówienia

### Test 4: Generowanie WZ
1. Wybierz zamówienie z listy
2. Kliknij "Generuj WZ"
3. Wypełnij dane odbiorcy
4. Wygeneruj PDF/Word/Excel
5. **Oczekiwany rezultat:** Dokument jest poprawnie wygenerowany

---

## 🐛 Rozwiązywanie problemów

### Problem: Brak modułu 'attachments_manager'
**Rozwiązanie:** Upewnij się że plik `attachments_manager.py` jest w tym samym folderze co `mfg_app.py`

### Problem: Błąd przy dodawaniu załączników
**Rozwiązanie:** Sprawdź czy tabela `attachments` została utworzona w bazie danych (wykonaj skrypt SQL ponownie)

### Problem: Błąd generowania PDF
**Rozwiązanie:** Zainstaluj brakujące biblioteki:
```bash
pip install reportlab python-docx openpyxl
```

### Problem: Lista zamówień nadal pusta
**Rozwiązanie:**
1. Sprawdź czy skrypt `fix_orders_view.sql` został wykonany
2. Zrestartuj aplikację
3. Sprawdź logi błędów w terminalu

---

## 📞 Wsparcie

W razie problemów sprawdź:
1. Logi w terminalu (console output)
2. Supabase Dashboard → SQL Editor → wykonaj `SELECT * FROM v_orders_full LIMIT 5;`
3. Uprawnienia tabeli (RLS policies)

**Koniec instrukcji integracji**
