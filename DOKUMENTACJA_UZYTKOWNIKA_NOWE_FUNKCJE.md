# Dokumentacja użytkownika - Nowe funkcjonalności

## 📌 Przegląd nowych funkcji

System został rozszerzony o następujące funkcjonalności:

1. **System załączników** - dodawanie, przeglądanie i pobieranie załączników do ofert i zamówień
2. **Konwersja ofert** - automatyczne kopiowanie załączników przy konwersji oferty na zamówienie
3. **Dokumenty WZ** - generowanie dokumentów wydania zewnętrznego w formatach PDF, Word i Excel

---

## 📎 System załączników

### Czym są załączniki?

Załączniki to pliki które można dołączyć do oferty lub zamówienia, takie jak:
- Rysunki techniczne (PDF, DXF, DWG)
- Specyfikacje (Word, Excel)
- Zdjęcia produktów
- Dokumentacja techniczna
- Inne pliki

**Zalety:**
- Wszystkie pliki są spakowane w archiwum ZIP i przechowywane w bazie danych
- Automatyczna kompresja - oszczędność miejsca
- Bezpieczne przechowywanie
- Łatwy dostęp i podgląd

### Jak dodać załączniki do oferty?

1. **Otwórz ofertę** (nową lub istniejącą)
2. Przewiń w dół do sekcji **"📎 Załączniki"**
3. Kliknij przycisk **"➕ Dodaj pliki"**
4. Wybierz jeden lub więcej plików z dysku
5. Opcjonalnie wprowadź notatki do załącznika
6. Kliknij **OK**

**Uwaga:** Zapisz ofertę przed dodaniem załączników!

### Jak dodać załączniki do zamówienia?

Proces jest identyczny jak w przypadku ofert:

1. **Otwórz zamówienie** (nowe lub istniejące)
2. Przewiń w dół do sekcji **"📎 Załączniki"**
3. Kliknij **"➕ Dodaj pliki"**
4. Wybierz pliki
5. Zapisz

### Podgląd załączników

Aby obejrzeć załącznik:

1. Wybierz załącznik z listy (kliknij na wiersz)
2. Kliknij przycisk **"👁️ Podgląd"**
3. Jeśli załącznik zawiera wiele plików, wybierz który chcesz otworzyć
4. Plik otworzy się w domyślnej aplikacji (np. PDF w Adobe Reader)

**Podwójne kliknięcie** na załączniku również otwiera podgląd.

### Pobieranie załączników

Aby pobrać załącznik na dysk:

1. Wybierz załącznik z listy
2. Kliknij **"💾 Pobierz"**
3. **Jeśli załącznik zawiera jeden plik:**
   - Pojawi się okno "Zapisz jako"
   - Wybierz lokalizację i nazwę pliku
   - Kliknij "Zapisz"

4. **Jeśli załącznik zawiera wiele plików:**
   - Wszystkie pliki zostaną rozpakowane do folderu tymczasowego
   - Folder otworzy się automatycznie w eksploratorze
   - Skopiuj potrzebne pliki do swojej lokalizacji

### Usuwanie załączników

1. Wybierz załącznik z listy
2. Kliknij **"🗑️ Usuń"**
3. Potwierdź usunięcie

**Uwaga:** Usunięcie załącznika jest nieodwracalne!

### Informacje o załącznikach

Pod listą załączników wyświetlane są statystyki:
- Liczba plików
- Liczba archiwów
- Całkowity rozmiar

Przykład: `12 plików w 3 archiwach | Razem: 5.2 MB`

---

## 🔄 Konwersja ofert na zamówienia

### Automatyczne kopiowanie załączników

Gdy konwertujesz ofertę na zamówienie, **wszystkie załączniki są automatycznie kopiowane** do nowo utworzonego zamówienia.

### Jak to działa?

1. Otwórz moduł **"💼 Oferty"**
2. Wybierz ofertę z listy
3. Kliknij **"🔄 Konwertuj na zamówienie"**
4. Potwierdź konwersję
5. System:
   - Tworzy nowe zamówienie z danymi z oferty
   - Kopiuje wszystkie pozycje (części)
   - **Kopiuje wszystkie załączniki**
   - Oznacza ofertę jako "Zamówienie"

### Sprawdzenie skopiowanych załączników

Po konwersji:
1. Przejdź do listy zamówień
2. Otwórz nowo utworzone zamówienie
3. Przewiń do sekcji załączników
4. Wszystkie pliki z oferty powinny być widoczne

**Uwaga:** Załączniki są **kopiowane**, nie przenoszone. Oznacza to, że oferta nadal ma swoje załączniki, a zamówienie ma ich kopię.

---

## 📄 Generowanie dokumentów WZ

### Czym jest dokument WZ?

WZ (Wydanie Zewnętrzne) to dokument potwierdzający wydanie towaru odbiorcy. Zawiera:
- Numer WZ (generowany automatycznie: WZ-{numer_zamówienia})
- Dane wystawcy (Twoja firma)
- Dane odbiorcy (klient z zamówienia)
- Lista wydanych pozycji
- Data wystawienia
- Miejsca na podpisy

### Jak wygenerować dokument WZ?

1. **Przejdź do listy zamówień**
2. **Wybierz zamówienie** z listy (kliknij na wiersz)
3. Kliknij przycisk **"📦 Generuj WZ"**
4. Otworzy się okno dialogowe generowania WZ

### Okno generowania WZ

#### Sekcja "Informacje podstawowe"
- **Nr WZ:** Automatycznie wygenerowany numer (nie można edytować)
- **Zamówienie:** Numer zamówienia
- **Data wystawienia:** Data dzisiejsza (można zmienić)

#### Sekcja "Dane odbiorcy"
Wszystkie pola są automatycznie wypełnione danymi klienta z zamówienia. Możesz je edytować:
- Nazwa odbiorcy
- Adres
- Kod pocztowy i miasto
- NIP
- Osoba kontaktowa

**Wskazówka:** Edytuj dane jeśli np. towar ma być dostarczony na inny adres niż siedziby firmy.

#### Sekcja "Pozycje WZ"
Lista pozycji jest automatycznie wypełniona częściami z zamówienia:
- Lp. (kolejny numer)
- Nazwa części
- Ilość
- Jednostka (domyślnie "szt")
- Uwagi (materiał i grubość)

**Uwaga:** Aktualnie lista pozycji jest tylko do odczytu.

#### Sekcja "Uwagi"
- **Uwagi:** Dodatkowe informacje o zamówieniu (przepisane z zamówienia, można edytować)
- **Informacje o transporcie:** Np. "Dostawa kurierem", "Odbiór własny" itp.

### Generowanie dokumentu

Masz do wyboru kilka opcji:

#### 1. Generuj PDF (czerwony przycisk)
- Format: Adobe PDF
- **Zalety:** Profesjonalny wygląd, gotowy do druku, nie można edytować
- **Użycie:** Oficjalne dokumenty, archiwizacja

#### 2. Generuj Word (niebieski przycisk)
- Format: Microsoft Word (DOCX)
- **Zalety:** Można edytować, dodawać własne uwagi
- **Użycie:** Gdy potrzebujesz dostosować dokument

#### 3. Generuj Excel (zielony przycisk)
- Format: Microsoft Excel (XLSX)
- **Zalety:** Arkusz kalkulacyjny, łatwa edycja w Excelu
- **Użycie:** Gdy potrzebujesz przeliczeń lub arkusza

#### 4. Generuj wszystkie (zielony, większy przycisk)
- Generuje jednocześnie: PDF + Word + Excel
- Wszystkie pliki są zapisywane w wybranym folderze
- Nazwy plików: `WZ_2025-00001.pdf`, `WZ_2025-00001.docx`, `WZ_2025-00001.xlsx`

### Proces generowania

1. Kliknij wybrany przycisk formatu
2. Pojawi się okno "Zapisz jako"
3. Wybierz lokalizację i potwierdź nazwę pliku
4. Kliknij "Zapisz"
5. Dokument zostanie wygenerowany
6. Pojawi się pytanie "Czy otworzyć dokument?"
   - **TAK** - dokument otworzy się w domyślnej aplikacji
   - **NIE** - dokument jest zapisany, możesz go otworzyć później

### Zapisywanie do bazy danych

Po wygenerowaniu dokumentu, informacje o WZ są automatycznie zapisywane w bazie danych:
- Numer WZ
- Data wystawienia
- Dane odbiorcy
- Lista pozycji
- Status: "ISSUED" (Wystawione)

**Korzyść:** Historia wszystkich wygenerowanych dokumentów WZ jest dostępna w bazie.

---

## 💡 Wskazówki i najlepsze praktyki

### Załączniki

1. **Dodawaj załączniki od razu**
   - Dodaj wszystkie potrzebne pliki gdy tworzysz ofertę/zamówienie
   - Nie musisz zamykać okna aby dodać załączniki

2. **Organizuj załączniki**
   - Dodawaj powiązane pliki jako jeden załącznik (np. wszystkie rysunki razem)
   - Używaj notatek do opisu zawartości załącznika

3. **Sprawdzaj przed wysłaniem**
   - Podejrzyj załączniki przed wysłaniem oferty do klienta
   - Upewnij się że wszystkie pliki są aktualne

### Konwersja ofert

1. **Sprawdź załączniki przed konwersją**
   - Upewnij się że oferta ma wszystkie potrzebne załączniki
   - Po konwersji będziesz mógł dodać więcej załączników do zamówienia

2. **Weryfikuj dane po konwersji**
   - Sprawdź czy wszystkie pozycje zostały skopiowane
   - Sprawdź czy załączniki są dostępne

### Dokumenty WZ

1. **Weryfikuj dane odbiorcy**
   - Sprawdź czy adres dostawy jest poprawny
   - Zaktualizuj dane jeśli konieczne

2. **Dodawaj informacje o transporcie**
   - Uzupełnij pole "Informacje o transporcie"
   - Podaj sposób dostawy i firmę kurierską

3. **Generuj wszystkie formaty**
   - Użyj przycisku "Generuj wszystkie" aby mieć pełną dokumentację
   - PDF dla archiwum, Word/Excel do dalszej edycji

4. **Nazywanie plików**
   - System automatycznie sugeruje nazwę: `WZ_{numer}.pdf`
   - Możesz zmienić nazwę na własną

---

## ❓ Najczęściej zadawane pytania (FAQ)

### Q: Czy mogę dodać załączniki do oferty po jej zapisaniu?
**A:** Tak! Otwórz ofertę w trybie edycji i dodaj załączniki w sekcji "📎 Załączniki".

### Q: Jakie typy plików mogę dodać jako załączniki?
**A:** Wszystkie typy plików są obsługiwane: PDF, Word, Excel, DXF, DWG, obrazy, ZIP, itp.

### Q: Czy jest limit rozmiaru załączników?
**A:** Nie ma sztywnego limitu, ale zalecamy pliki do 10 MB na pojedynczy załącznik. Większe pliki mogą spowalniać system.

### Q: Co się stanie z załącznikami gdy usunę ofertę?
**A:** Załączniki zostaną automatycznie usunięte wraz z ofertą.

### Q: Czy mogę edytować wygenerowany dokument WZ?
**A:** Tak, jeśli wygenerujesz format Word lub Excel. Format PDF jest tylko do odczytu.

### Q: Gdzie są przechowywane załączniki?
**A:** Załączniki są przechowywane w bazie danych jako spakowane archiwa ZIP. Nie musisz się martwić o zarządzanie plikami.

### Q: Czy mogę wygenerować WZ dla zamówienia które już ma WZ?
**A:** Tak, możesz wygenerować dokument WZ wielokrotnie (np. z różnymi datami lub danymi odbiorcy).

### Q: Jak znaleźć wcześniej wygenerowane dokumenty WZ?
**A:** Wszystkie wygenerowane WZ są zapisywane w folderze który wybrałeś podczas generowania. Dodatkowo, informacje o WZ są w bazie danych.

---

## 🆘 Pomoc i wsparcie

W razie problemów:

1. **Sprawdź logi** - błędy są wyświetlane w terminalu aplikacji
2. **Zrestartuj aplikację** - czasami pomaga
3. **Sprawdź połączenie z bazą danych** - zakładka "Diagnostyka" w menu "O systemie"
4. **Skontaktuj się z działem IT** - podaj szczegółowy opis problemu

---

**Ostatnia aktualizacja:** 2025-10-28
**Wersja systemu:** 1.1 Zintegrowana + Rozszerzenia

**Koniec dokumentacji użytkownika**
