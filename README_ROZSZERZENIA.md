# System Zarządzania Produkcją - Rozszerzenia

## 🚀 Szybki start

Ten dokument opisuje nowe rozszerzenia systemu dodane w wersji 1.1+.

---

## 📦 Co nowego?

### 1. ✅ Naprawa listy zamówień (KRYTYCZNE!)
Problem z pustą listą zamówień został rozwiązany.

### 2. 📎 System załączników
Dodawanie, przeglądanie i pobieranie załączników do ofert i zamówień.
- Automatyczne pakowanie do ZIP
- Przechowywanie w bazie danych
- Kompresja plików

### 3. 🔄 Konwersja ofert z załącznikami
Automatyczne kopiowanie załączników przy konwersji oferty na zamówienie.

### 4. 📄 Generowanie dokumentów WZ
Tworzenie dokumentów wydania zewnętrznego w formatach:
- PDF (profesjonalny)
- Word (edytowalny)
- Excel (arkusz)

---

## 📂 Struktura plików

```
ManufacturingSystem/
│
├── SQL Scripts (do wykonania w Supabase)
│   ├── fix_orders_view.sql              ⚠️ WYKONAJ NAJPIERW!
│   └── add_attachments_and_wz_tables.sql
│
├── Python Modules (kod)
│   ├── attachments_manager.py           - Zarządzanie załącznikami
│   ├── wz_generator.py                  - Generator dokumentów WZ
│   ├── attachments_gui_widgets.py       - Widget GUI załączników
│   └── wz_dialog.py                     - Dialog generowania WZ
│
├── Documentation (dokumentacja)
│   ├── README_ROZSZERZENIA.md           ← ZACZYNASZ TUTAJ
│   ├── PODSUMOWANIE_IMPLEMENTACJI.md    - Przegląd całości
│   ├── INSTRUKCJE_INTEGRACJI.md         - Dla programisty
│   └── DOKUMENTACJA_UZYTKOWNIKA_NOWE_FUNKCJE.md - Dla użytkownika
```

---

## 🎯 Dla kogo jest która dokumentacja?

### 👨‍💻 Programista / Integrator
**Przeczytaj:**
1. `PODSUMOWANIE_IMPLEMENTACJI.md` - poznaj co zostało zrobione
2. `INSTRUKCJE_INTEGRACJI.md` - instrukcje krok po kroku jak zintegrować

**Wykonaj:**
1. Skrypty SQL w Supabase
2. Integrację kodu według instrukcji
3. Testy akceptacyjne

**Czas:** ~2-3 godziny

### 👤 Użytkownik końcowy
**Przeczytaj:**
- `DOKUMENTACJA_UZYTKOWNIKA_NOWE_FUNKCJE.md` - jak używać nowych funkcji

**Dowiesz się:**
- Jak dodawać załączniki do ofert i zamówień
- Jak konwertować oferty na zamówienia
- Jak generować dokumenty WZ
- FAQ i najlepsze praktyki

---

## ⚡ Szybki przewodnik instalacji

### Krok 1: Baza danych (5-10 min)
```sql
-- W Supabase SQL Editor wykonaj w kolejności:
-- 1. fix_orders_view.sql            ⚠️ NAJPIERW!
-- 2. add_attachments_and_wz_tables.sql
```

### Krok 2: Kod Python (30-60 min)
Postępuj zgodnie z `INSTRUKCJE_INTEGRACJI.md`

### Krok 3: Testy (30 min)
Wykonaj testy z `PODSUMOWANIE_IMPLEMENTACJI.md`

---

## ✅ Checkli wdrożenia

- [ ] Wykonano `fix_orders_view.sql` w Supabase
- [ ] Zweryfikowano działanie listy zamówień
- [ ] Wykonano `add_attachments_and_wz_tables.sql`
- [ ] Zweryfikowano utworzenie tabel
- [ ] Skopiowano pliki Python do projektu
- [ ] Zintegrowano załączniki w ofertach
- [ ] Zintegrowano załączniki w zamówieniach
- [ ] Rozszerzono konwersję ofert
- [ ] Zintegrowano generowanie WZ
- [ ] Wykonano Test 1 (lista zamówień)
- [ ] Wykonano Test 2 (załączniki oferta)
- [ ] Wykonano Test 3 (podgląd)
- [ ] Wykonano Test 4 (konwersja z załącznikami)
- [ ] Wykonano Test 5 (WZ PDF)
- [ ] Wykonano Test 6 (WZ wszystkie formaty)
- [ ] Wykonano Test 7 (usuwanie załączników)

---

## 🆘 Szybka pomoc

### Problem: Pusta lista zamówień
**Rozwiązanie:** Wykonaj `fix_orders_view.sql` w Supabase

### Problem: Błąd przy dodawaniu załączników
**Rozwiązanie:** Sprawdź czy wykonano `add_attachments_and_wz_tables.sql`

### Problem: Brak modułu 'attachments_manager'
**Rozwiązanie:** Skopiuj plik do folderu projektu

### Problem: Błąd generowania PDF
**Rozwiązanie:** Zainstaluj: `pip install reportlab python-docx openpyxl`

---

## 📊 Statystyki

- **9 nowych plików**
- **~2000 linii kodu**
- **3 nowe tabele w bazie**
- **4 główne funkcjonalności**
- **Czas wdrożenia: 2-3 godziny**

---

## 🎓 Wymagania

### Baza danych:
- Supabase (PostgreSQL)
- Dostęp do SQL Editor

### Python:
- Python 3.11+
- Biblioteki: reportlab, python-docx, openpyxl

### System:
- Windows 10/11 (zalecane)
- Linux/Mac (może wymagać drobnych dostosowań)

---

## 📞 Kontakt i wsparcie

- **Email:** support@production.local
- **Dokumentacja:** Pliki Markdown w folderze projektu
- **Logi błędów:** Terminal aplikacji

---

## 🎉 Gotowy do startu?

1. **Programista?** → Przejdź do `INSTRUKCJE_INTEGRACJI.md`
2. **Użytkownik?** → Przejdź do `DOKUMENTACJA_UZYTKOWNIKA_NOWE_FUNKCJE.md`
3. **Manager?** → Przeczytaj `PODSUMOWANIE_IMPLEMENTACJI.md`

---

**Wersja:** 1.1 Rozszerzona
**Data:** 2025-10-28
**Status:** ✅ Gotowe do wdrożenia

**Powodzenia! 🚀**
