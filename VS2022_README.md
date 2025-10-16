# 🛠️ Visual Studio 2022 - Instrukcja projektu

## 📋 Wymagania wstępne

### 1. Instalacja Visual Studio 2022
- Pobierz [Visual Studio 2022](https://visualstudio.microsoft.com/vs/)
- Podczas instalacji zaznacz:
  - ✅ **Python development** workload
  - ✅ **Python 3 (64-bit)**
  - ✅ **Python native development tools**

### 2. Python 3.11+
- Jeśli nie masz, pobierz z [python.org](https://python.org)
- Lub zainstaluj przez Visual Studio Installer

---

## 🚀 Otwieranie projektu

### Metoda 1: Przez Solution
1. Uruchom Visual Studio 2022
2. **File** → **Open** → **Project/Solution**
3. Wybierz `ManufacturingSystem.sln`
4. Projekt zostanie załadowany automatycznie

### Metoda 2: Przez folder
1. **File** → **Open** → **Folder**
2. Wybierz folder z projektem
3. VS automatycznie wykryje pliki Python

---

## ⚙️ Konfiguracja środowiska

### 1. Tworzenie środowiska wirtualnego
W Visual Studio:
1. **View** → **Other Windows** → **Python Environments**
2. Kliknij **+ Add Environment**
3. Wybierz **Virtual Environment**
4. Ustaw:
   - Location: `./env`
   - Base Interpreter: Python 3.11
5. Kliknij **Create**

### 2. Instalacja zależności
W **Solution Explorer**:
1. Kliknij prawym na `requirements.txt`
2. Wybierz **Install Python Packages**

Lub w **Package Manager Console**:
```powershell
pip install -r requirements.txt
```

### 3. Konfiguracja Supabase
1. Skopiuj `.env.example` jako `.env`
2. Edytuj `.env` w Visual Studio
3. Wpisz dane z Supabase:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

---

## 🎯 Uruchamianie

### Debug Mode (F5)
1. Upewnij się, że `mfg_integrated.py` jest ustawiony jako **Startup File**
   - Prawy klick → **Set as Startup File**
2. Naciśnij **F5** lub kliknij **▶ Start**

### Różne konfiguracje
W górnym pasku wybierz:
- **Debug** - tryb debugowania z breakpointami
- **Release** - tryb wydania bez debugowania
- **Production** - tryb produkcyjny z optymalizacją

### Profile uruchamiania
W **Debug** → **Debug Properties**:
- **System Zintegrowany** - pełna aplikacja
- **Tylko Zamówienia** - Faza 1
- **Agent Outlook** - debug agenta

---

## 🐛 Debugowanie

### Breakpointy
- Kliknij na lewym marginesie obok linii kodu
- Lub naciśnij **F9** na linii

### Okna debugowania
- **Locals** (Ctrl+Alt+V, L) - zmienne lokalne
- **Watch** (Ctrl+Alt+W, 1) - obserwowane wyrażenia
- **Call Stack** (Ctrl+Alt+C) - stos wywołań
- **Immediate** (Ctrl+Alt+I) - wykonywanie poleceń

### Skróty debugowania
- **F5** - kontynuuj
- **F10** - krok naprzód
- **F11** - wejdź do funkcji
- **Shift+F11** - wyjdź z funkcji
- **Ctrl+Shift+F5** - restart

---

## 🧪 Testy jednostkowe

### Uruchamianie testów
1. **Test** → **Test Explorer** (Ctrl+E, T)
2. Kliknij **Run All Tests**

### Dodawanie testów
1. W folderze `tests/` utwórz plik `test_*.py`
2. Visual Studio automatycznie wykryje testy

### Coverage (pokrycie kodu)
1. **Test** → **Analyze Code Coverage**
2. Wyniki w oknie **Code Coverage Results**

---

## 📦 IntelliSense i podpowiedzi

### Konfiguracja IntelliSense
1. **Tools** → **Options**
2. **Python** → **IntelliSense**
3. Włącz:
   - ✅ Auto list members
   - ✅ Parameter information
   - ✅ Quick info
   - ✅ Complete word

### Type Hints
Projekt używa type hints dla lepszego IntelliSense:
```python
def process_order(order: Order) -> Optional[Dict]:
    ...
```

---

## 🔧 Narzędzia i rozszerzenia

### Zalecane rozszerzenia
W **Extensions** → **Manage Extensions**:
- **Python Docstring Generator**
- **Python Indent**
- **Git for Visual Studio**
- **Markdown Editor**

### Code Analysis
1. **Analyze** → **Run Code Analysis**
2. Lub włącz automatyczne: **Tools** → **Options** → **Python** → **Linting**

### Formatowanie kodu
- **Ctrl+K, Ctrl+D** - formatuj dokument
- **Ctrl+K, Ctrl+F** - formatuj zaznaczenie

---

## 📊 Metryki kodu

### Code Metrics
1. **Analyze** → **Calculate Code Metrics**
2. Wyświetli:
   - Maintainability Index
   - Cyclomatic Complexity
   - Depth of Inheritance
   - Lines of Code

---

## 🌐 Integracja z Git

### Podstawowe operacje
- **Team Explorer** (Ctrl+0, Ctrl+M)
- **Changes** - zobacz zmiany
- **Branches** - zarządzaj gałęziami
- **Sync** - synchronizuj z remote

### Commity
1. W **Team Explorer** → **Changes**
2. Wpisz message
3. **Commit All** lub **Commit All and Push**

---

## ⚡ Skróty produktywności

### Nawigacja
- **Ctrl+T** - Go to All
- **Ctrl+,** - Go to File
- **F12** - Go to Definition
- **Shift+F12** - Find All References
- **Ctrl+F12** - Go to Implementation

### Edycja
- **Ctrl+.** - Quick Actions
- **Ctrl+Space** - IntelliSense
- **Ctrl+Shift+Space** - Parameter Info
- **Alt+Enter** - Show potential fixes

### Refaktoryzacja
- **Ctrl+R, R** - Rename
- **Ctrl+R, M** - Extract Method
- **Ctrl+R, V** - Extract Variable

---

## 📝 Snippets

### Tworzenie własnych
1. **Tools** → **Code Snippets Manager**
2. Language: **Python**
3. **Add** lub **Import**

### Przykładowe snippety
Wpisz i naciśnij Tab:
- `class` - nowa klasa
- `def` - nowa funkcja
- `try` - blok try/except
- `with` - context manager

---

## 🚀 Build i Deploy

### Build projektu
1. **Build** → **Build Solution** (Ctrl+Shift+B)
2. Sprawdź **Output** window

### Tworzenie paczki
1. W terminalu:
```bash
python setup.py sdist bdist_wheel
```

### Publikacja
1. **Build** → **Publish**
2. Wybierz target (folder, FTP, etc.)

---

## ❓ Rozwiązywanie problemów

### Problem: "No Python interpreter"
**Rozwiązanie:**
1. **Tools** → **Options** → **Python** → **Interpreters**
2. Dodaj interpreter Python 3.11

### Problem: "Module not found"
**Rozwiązanie:**
1. Sprawdź czy środowisko jest aktywne
2. Reinstaluj pakiety: `pip install -r requirements.txt`

### Problem: "IntelliSense not working"
**Rozwiązanie:**
1. **Tools** → **Options** → **Text Editor** → **Python** → **IntelliSense**
2. Reset IntelliSense database

### Problem: "Can't debug"
**Rozwiązanie:**
1. Sprawdź **Debug** → **Options** → **Python** → **Debugging**
2. Włącz **Enable Python debugging**

---

## 📚 Dokumentacja

- [Visual Studio Python Documentation](https://docs.microsoft.com/en-us/visualstudio/python/)
- [Python Tools for Visual Studio (PTVS)](https://github.com/microsoft/PTVS)
- [Visual Studio Shortcuts](https://docs.microsoft.com/en-us/visualstudio/ide/default-keyboard-shortcuts)

---

## 💡 Tips & Tricks

1. **Multi-cursor editing**: Alt+Shift+Click
2. **Column selection**: Alt+Shift+Arrow keys
3. **Duplicate line**: Ctrl+D
4. **Move line**: Alt+Up/Down
5. **Comment**: Ctrl+K, Ctrl+C
6. **Uncomment**: Ctrl+K, Ctrl+U
7. **Format document**: Ctrl+K, Ctrl+D
8. **Peek Definition**: Alt+F12
9. **Navigate back/forward**: Ctrl+-, Ctrl+Shift+-
10. **Close all tabs**: Alt+W, L

---

**Visual Studio 2022 Version**: 17.0+  
**Python Tools Version**: Latest  
**Project Type**: Python Application (.pyproj)
