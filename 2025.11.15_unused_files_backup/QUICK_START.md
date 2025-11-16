# 🚀 SZYBKI START - System Zarządzania Produkcją

## Instalacja w 5 krokach

### 1️⃣ Uruchom instalator
```bash
instalacja.bat
```

### 2️⃣ Przygotuj Supabase
1. Załóż konto na [supabase.com](https://supabase.com)
2. Utwórz nowy projekt
3. W SQL Editor wykonaj cały skrypt z `setup_database.sql`
4. W Storage utwórz bucket o nazwie `attachments`

### 3️⃣ Skonfiguruj połączenie
Edytuj plik `.env`:
```
SUPABASE_URL=https://twoj-projekt.supabase.co
SUPABASE_KEY=twoj-klucz-anon
```

### 4️⃣ Uruchom system
```bash
uruchom_system.bat
```

### 5️⃣ Pierwsze kroki w aplikacji
1. Dodaj pierwszego klienta (przycisk "👥 Klienci")
2. Utwórz pierwsze zamówienie (przycisk "➕ Nowe zamówienie")
3. System automatycznie nada numer procesowy
4. Możesz dodać detale i załączniki

---

## 📁 Struktura plików

```
manufacturing-system/
│
├── mfg_integrated.py      # Główna aplikacja (wszystkie fazy)
├── mfg_app.py             # Faza 1 - Zamówienia
├── quotations_module.py   # Faza 2 - Oferty
├── outlook_agent.py       # Faza 3 - Agent Outlook
│
├── setup_database.sql     # Skrypt tworzący bazę danych
├── requirements.txt       # Lista zależności Python
├── .env.example          # Przykład konfiguracji
├── .env                  # Twoja konfiguracja (utworz!)
│
├── instalacja.bat        # Instalator automatyczny
├── uruchom_system.bat    # Launcher aplikacji
│
└── README.md            # Pełna dokumentacja
```

---

## 🎯 Funkcje według faz

### Faza 1 - Zarządzanie zamówieniami ✅
- Rejestracja zamówień i klientów
- Automatyczna numeracja (YYYY-00001)
- System 6 statusów z historią zmian
- Dashboard z alertami SLA
- Eksport do Excel, Word, PDF

### Faza 2 - Moduł ofertowania ✅
- Tworzenie ofert cenowych
- Kalkulacja marży automatyczna
- Konwersja oferta → zamówienie
- Generowanie profesjonalnych PDF
- Śledzenie statusów ofert

### Faza 3 - Agent Outlook ✅
- Automatyczne przetwarzanie emaili
- Rozpoznawanie zapytań i zamówień
- Ekstraktowanie i analiza załączników
- Automatyczne potwierdzenia
- Alerty terminów realizacji

---

## ⚙️ Wymagania systemowe

- **System:** Windows 10/11
- **Python:** 3.11 lub nowszy
- **RAM:** minimum 4 GB
- **Miejsce:** ~200 MB
- **Internet:** wymagane (Supabase)
- **Outlook:** opcjonalnie dla Fazy 3

---

## 🆘 Rozwiązywanie problemów

### Problem: "Python nie jest zainstalowany"
**Rozwiązanie:** Pobierz Python z [python.org](https://python.org). Podczas instalacji zaznacz "Add Python to PATH".

### Problem: "Brak połączenia z bazą danych"
**Rozwiązanie:** Sprawdź dane w pliku `.env`. Upewnij się, że projekt Supabase jest aktywny.

### Problem: "Agent Outlook niedostępny"
**Rozwiązanie:** Zainstaluj pywin32:
```bash
pip install pywin32
python .venv\Scripts\pywin32_postinstall.py -install
```

### Problem: "Brak numerów procesowych"
**Rozwiązanie:** Wykonaj ponownie w Supabase SQL Editor sekcję z triggerami ze skryptu `setup_database.sql`.

---

## 📞 Wsparcie

- **Dokumentacja techniczna:** `PROJECT_DOCUMENTATION_2025.md`
- **Logi agenta:** `outlook_agent.log`
- **Diagnostyka:** W aplikacji menu "ℹ️ O systemie" → "🔧 Diagnostyka"

---

## 🎨 Skróty klawiszowe

- **Podwójne kliknięcie** - edycja zamówienia
- **Prawy przycisk** - menu kontekstowe
- **F5** - odświeżenie (w planach)
- **Ctrl+E** - eksport (w planach)

---

## 📊 Kody kolorów statusów

- 🟠 **Pomarańczowy** - Wpłynęło
- 🔵 **Niebieski** - Potwierdzono
- 🟣 **Fioletowy** - Na planie
- 🟡 **Złoty** - W realizacji
- 🟢 **Zielony** - Gotowe
- ⚫ **Szary** - Wyfakturowane
- 🔴 **Czerwony** - Przeterminowane

---

## 🚀 Uruchomienie w różnych trybach

### Tryb produkcyjny (wszystkie moduły)
```bash
python mfg_integrated.py
```

### Tylko moduł zamówień (Faza 1)
```bash
python mfg_app.py
```

### Tryb debugowania
```bash
python mfg_integrated.py 2> debug.log
```

---

**Wersja:** 1.1 Zintegrowana  
**Data:** 2025  
**Autor:** Production IT Team
