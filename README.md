# 🏭 System Zarządzania Produkcją - Laser/Prasa
**Wersja 1.1 - Kompletne rozwiązanie z CustomTkinter i Supabase**

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-green)
![Supabase](https://img.shields.io/badge/Database-Supabase-orange)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)

## 📋 Opis systemu

Profesjonalny system do zarządzania zamówieniami produkcyjnymi dla lasera i prasy krawędziowej. Aplikacja oferuje nowoczesny interfejs graficzny, pełną funkcjonalność CRUD, zaawansowane raportowanie oraz integrację z chmurą.

### ✨ Główne funkcje (Faza 1)

- **🎯 Zarządzanie zamówieniami**
  - Automatyczna numeracja procesowa (YYYY-00001)
  - 6 statusów: Wpłynęło → Potwierdzono → Na planie → W realizacji → Gotowe → Wyfakturowane
  - Śledzenie terminów z alertami SLA
  - Załączanie plików (DXF, DWG, STP, PDF, grafiki)

- **👥 Baza klientów**
  - Pełne zarządzanie kontaktami
  - Historia zamówień
  - Statystyki per klient

- **🔧 Zarządzanie detalami**
  - Indeksowanie części
  - Specyfikacja materiałów i grubości
  - Kontrola duplikatów
  - Załączniki per detal

- **📊 Dashboard i raporty**
  - Wykresy statusów w czasie rzeczywistym
  - Monitoring SLA (przeterminowane/pilne/w terminie)
  - Eksport do Excel, Word, PDF
  - Statystyki finansowe
  - Analiza wydajności

- **🎨 Nowoczesny interfejs**
  - Dark mode CustomTkinter
  - Kolorowe kodowanie statusów
  - Menu kontekstowe
  - Auto-odświeżanie co 5 minut

## 🚀 Szybki start

### Wymagania systemowe

- Windows 10/11
- Python 3.11 lub nowszy
- Połączenie internetowe (dla Supabase)
- ~100MB wolnego miejsca

### Instalacja krok po kroku

#### 1. Przygotuj Supabase (5 minut)

1. Załóż darmowe konto na [supabase.com](https://supabase.com)
2. Utwórz nowy projekt (zapamiętaj hasło!)
3. Przejdź do **SQL Editor** i wykonaj cały skrypt z pliku `setup_database.sql`
4. Przejdź do **Storage** → **New bucket** → nazwa: `attachments` → Create
5. W **Settings** → **API** skopiuj:
   - Project URL
   - anon public key

#### 2. Skonfiguruj środowisko Python (3 minuty)

```bash
# Klonuj lub pobierz pliki projektu
cd manufacturing-system

# Utwórz środowisko wirtualne
python -m venv venv

# Aktywuj środowisko
# Windows Command Prompt:
venv\Scripts\activate.bat
# Windows PowerShell:
venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate

# Zainstaluj zależności
pip install -r requirements.txt
```

#### 3. Konfiguracja aplikacji (1 minuta)

1. Skopiuj plik `.env.example` jako `.env`
2. Edytuj `.env` i wpisz swoje dane z Supabase:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
```

#### 4. Uruchomienie

```bash
python mfg_app.py
```

## 📚 Instrukcja użytkowania

### Pierwsze kroki

1. **Dodaj klientów**
   - Kliknij "👥 Klienci" w górnym menu
   - Dodaj firmę (nazwa + kontakt)

2. **Utwórz zamówienie**
   - Kliknij "➕ Nowe zamówienie"
   - Wybierz klienta
   - Wypełnij dane zamówienia
   - Dodaj detale (części) - system ostrzeże przed duplikatami
   - Zapisz - numer procesowy zostanie nadany automatycznie

3. **Zarządzaj statusami**
   - Prawy klick na zamówieniu → "📊 Zmień status"
   - System automatycznie loguje historię zmian

4. **Monitoruj terminy**
   - Dashboard pokazuje w czasie rzeczywistym:
     - 🔴 Przeterminowane
     - 🟡 Pilne (≤2 dni)
     - 🟢 W terminie

### Eksport danych

- **Excel**: Pełne dane tabelaryczne z formatowaniem
- **Word**: Profesjonalny raport do druku
- **PDF**: Dokument do archiwizacji/wysyłki

### Filtry i wyszukiwanie

Lewy panel oferuje zaawansowane filtrowanie:
- Po kliencie
- Po statusie
- Zakres dat
- Wyszukiwanie w tytułach

### Raporty i analizy

Kliknij "📄 Raporty" aby zobaczyć:
- 📊 **Wykresy**: trendy miesięczne, top klienci, przychody
- 📈 **Statystyki**: wskaźniki KPI, średnie czasy realizacji
- 💰 **Finansowe**: podsumowania per status
- ⏰ **Terminy**: lista SLA z priorytetami

## 🔧 Rozwiązywanie problemów

### Błąd połączenia z bazą danych
- Sprawdź plik `.env` - czy dane są poprawne
- Upewnij się, że masz połączenie internetowe
- Sprawdź czy projekt Supabase jest aktywny

### Brak numerów procesowych
- Wykonaj ponownie sekcję z triggerami w `setup_database.sql`
- Sprawdź tabelę `process_counters`

### Nie można przesłać plików
- Sprawdź czy bucket `attachments` istnieje
- Upewnij się, że polityki RLS są włączone

### Aplikacja się nie uruchamia
```bash
# Sprawdź wersję Pythona
python --version  # Powinno być 3.11+

# Przeinstaluj zależności
pip install --upgrade -r requirements.txt

# Sprawdź logi
python mfg_app.py 2> error.log
```

## 🎯 Roadmap

### ✅ Faza 1 (Zrealizowana)
- System zamówień z pełnym CRUD
- Zarządzanie klientami i detalami
- Dashboard z wykresami
- Eksport do różnych formatów
- System alertów SLA

### 🚧 Faza 2 (Planowana)
- Moduł ofertowania
- Konwersja oferta → zamówienie  
- Szablony ofert
- Kalkulacja kosztów

### 🔮 Faza 3 (Przyszłość)
- Agent Outlook (automatyzacja emaili)
- Parsowanie załączników
- Automatyczne przypomnienia
- Integracja z CypCloud

## 📊 Architektura techniczna

```
┌─────────────────────────┐
│   CustomTkinter GUI     │
│   (Dark Mode UI)        │
└───────────┬─────────────┘
            │
    ┌───────▼────────┐
    │ SupabaseManager│
    │   (API Layer)  │
    └───────┬────────┘
            │
    ┌───────▼────────────┐
    │    Supabase Cloud  │
    ├────────────────────┤
    │ • PostgreSQL DB    │
    │ • Row Level Sec.   │
    │ • Storage Bucket   │
    │ • Real-time Sub.   │
    └────────────────────┘
```

## 🔒 Bezpieczeństwo

**Wersja MVP (desktop)**:
- Używa klucza `anon` dla prostoty
- RLS włączone ale permisywne

**Zalecenia dla produkcji**:
- Implementuj Supabase Auth
- Użyj roli `authenticated`
- Ogranicz RLS do user_id
- Szyfruj wrażliwe dane
- Regularne backupy

## 💡 Wskazówki

1. **Kopie zapasowe**: Eksportuj regularnie dane do Excel
2. **Wydajność**: System obsługuje tysiące zamówień bez spowolnienia
3. **Skróty**: Podwójne kliknięcie otwiera edycję
4. **Kolory**: Czerwony = pilne, Zielony = gotowe, Szary = zafakturowane

## 📞 Wsparcie

- **Dokumentacja techniczna**: `PROJECT_DOCUMENTATION_2025.md`
- **SQL Schema**: `setup_database.sql`
- **Wymagania biznesowe**: `how.txt`

## 📜 Licencja

System stworzony dla wewnętrznego użytku produkcyjnego.

---

**Autor**: Production IT Team  
**Wersja**: 1.1  
**Data**: 2025  
**Stack**: Python 3.11 | CustomTkinter | Supabase | PostgreSQL
