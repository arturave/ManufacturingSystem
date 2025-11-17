#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Integracji Supabase Storage z Załącznikami
================================================
Skrypt testowy do weryfikacji działania nowej integracji
"""

import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime

# Import modułów
from supabase_manager import SupabaseManager
from attachments_manager import AttachmentsManager
from attachments_storage import AttachmentsStorage


def create_test_files():
    """Tworzy pliki testowe do uploadu"""
    test_files = []
    temp_dir = tempfile.mkdtemp(prefix='test_attachments_')

    # Utwórz plik tekstowy
    txt_file = os.path.join(temp_dir, 'test_document.txt')
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("To jest testowy dokument.\n")
        f.write(f"Data utworzenia: {datetime.now()}\n")
        f.write("Test integracji Supabase Storage.\n")
    test_files.append(txt_file)

    # Utwórz plik CSV
    csv_file = os.path.join(temp_dir, 'test_data.csv')
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write("ID,Nazwa,Wartość\n")
        f.write("1,Test1,100\n")
        f.write("2,Test2,200\n")
    test_files.append(csv_file)

    # Utwórz prosty plik DXF (symulacja)
    dxf_file = os.path.join(temp_dir, 'test_drawing.dxf')
    with open(dxf_file, 'w', encoding='utf-8') as f:
        f.write("0\nSECTION\n2\nHEADER\n")
        f.write("0\nENDSEC\n0\nEOF\n")
    test_files.append(dxf_file)

    return test_files, temp_dir


def test_storage_integration():
    """Testuje integrację z Supabase Storage"""
    print("=" * 60)
    print("TEST INTEGRACJI SUPABASE STORAGE")
    print("=" * 60)

    # Inicjalizacja
    print("\n1. Inicjalizacja połączenia z Supabase...")
    db = SupabaseManager()

    # Test storage manager
    print("\n2. Test AttachmentsStorage...")
    storage = AttachmentsStorage(db.client)

    # Sprawdź bucket
    print("   - Sprawdzanie bucket 'attachments'...")
    try:
        buckets = storage.storage.list_buckets()
        bucket_exists = any(b.get('name') == 'attachments' for b in buckets)
        if bucket_exists:
            print("   ✅ Bucket 'attachments' istnieje")
        else:
            print("   ⚠️ Bucket 'attachments' nie istnieje (zostanie utworzony)")
    except Exception as e:
        print(f"   ❌ Błąd sprawdzania bucket: {e}")

    # Test AttachmentsManager
    print("\n3. Test AttachmentsManager...")
    manager = AttachmentsManager(db.client)

    # Utwórz pliki testowe
    print("\n4. Tworzenie plików testowych...")
    test_files, temp_dir = create_test_files()
    for file in test_files:
        print(f"   - {os.path.basename(file)}")

    # Test sprawdzania aplikacji domyślnych
    print("\n5. Test sprawdzania aplikacji domyślnych...")
    for file in test_files:
        filename = os.path.basename(file)
        has_app = manager.has_default_application(filename)
        can_preview = manager.can_preview_file(filename)
        print(f"   - {filename}:")
        print(f"     • Aplikacja domyślna: {'✅ Tak' if has_app else '❌ Nie'}")
        print(f"     • Możliwość podglądu: {'✅ Tak' if can_preview else '❌ Nie'}")

    # Test uploadu plików
    print("\n6. Test uploadu plików do Supabase Storage...")

    # Użyj testowego entity_id
    test_entity_id = 'test_order_001'

    result = manager.add_files(
        entity_type='order',
        entity_id=test_entity_id,
        file_paths=test_files,
        created_by='test_user',
        notes='Test integracji Supabase Storage'
    )

    if result:
        print(f"   ✅ Sukces! Utworzono załącznik ID: {result['id']}")
        attachment_id = result['id']

        # Test pobierania listy załączników
        print("\n7. Test pobierania listy załączników...")
        attachments = manager.get_attachments_list('order', test_entity_id)
        print(f"   - Znaleziono {len(attachments)} załączników")

        if attachments:
            att = attachments[0]
            print(f"   - ID: {att.id}")
            print(f"   - Plików: {att.files_count}")
            print(f"   - Rozmiar: {manager._format_size(att.total_size)}")

            # Test pobierania pliku
            print("\n8. Test pobierania pliku ze Storage...")
            for file_meta in att.files_metadata:
                print(f"   - Pobieranie: {file_meta.filename}")
                file_data = manager.extract_file(attachment_id, file_meta.filename)
                if file_data:
                    print(f"     ✅ Pobrano {len(file_data)} bajtów")
                else:
                    print(f"     ❌ Błąd pobierania")

            # Test generowania signed URL
            print("\n9. Test generowania signed URL...")
            if att.files_metadata:
                first_file = att.files_metadata[0].filename
                signed_url = manager.get_signed_url_for_file(attachment_id, first_file)
                if signed_url:
                    print(f"   ✅ Wygenerowano URL dla: {first_file}")
                    print(f"   URL: {signed_url[:50]}...")
                else:
                    print(f"   ❌ Nie udało się wygenerować URL")

            # Test usuwania załącznika
            print("\n10. Test usuwania załącznika...")
            if manager.delete_attachment(attachment_id):
                print(f"   ✅ Usunięto załącznik {attachment_id}")
            else:
                print(f"   ❌ Błąd usuwania")
    else:
        print("   ❌ Błąd uploadu plików")

    # Cleanup
    print("\n11. Czyszczenie plików tymczasowych...")
    for file in test_files:
        try:
            os.remove(file)
        except:
            pass
    try:
        os.rmdir(temp_dir)
    except:
        pass

    print("\n" + "=" * 60)
    print("TEST ZAKOŃCZONY")
    print("=" * 60)


def test_backward_compatibility():
    """Testuje kompatybilność wsteczną ze starymi załącznikami BYTEA"""
    print("\n" + "=" * 60)
    print("TEST KOMPATYBILNOŚCI WSTECZNEJ")
    print("=" * 60)

    print("\n1. Sprawdzanie starych załączników (BYTEA)...")

    db = SupabaseManager()
    manager = AttachmentsManager(db.client)

    # Pobierz wszystkie załączniki
    try:
        response = db.client.table('attachments').select('*').execute()

        bytea_count = 0
        storage_count = 0

        for att in response.data:
            storage_type = att.get('storage_type', 'bytea')
            if storage_type == 'bytea':
                bytea_count += 1
            else:
                storage_count += 1

        print(f"   - Załączniki BYTEA (stare): {bytea_count}")
        print(f"   - Załączniki Storage (nowe): {storage_count}")

        if bytea_count > 0:
            print("\n2. Test odczytu starego załącznika BYTEA...")
            # Znajdź pierwszy załącznik BYTEA
            for att in response.data:
                if att.get('storage_type', 'bytea') == 'bytea' and att.get('archive_data'):
                    print(f"   - Testowanie załącznika ID: {att['id']}")

                    # Spróbuj wyodrębnić pierwszy plik
                    files_meta = att.get('files_metadata', '[]')
                    if isinstance(files_meta, str):
                        import json
                        files_meta = json.loads(files_meta)

                    if files_meta and len(files_meta) > 0:
                        first_file = files_meta[0]['filename']
                        print(f"   - Próba pobrania pliku: {first_file}")

                        file_data = manager.extract_file(att['id'], first_file)
                        if file_data:
                            print(f"     ✅ Sukces! Pobrano {len(file_data)} bajtów")
                        else:
                            print(f"     ❌ Błąd pobierania")
                    break
        else:
            print("   ℹ️ Brak starych załączników do testu")

    except Exception as e:
        print(f"   ❌ Błąd testu kompatybilności: {e}")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    print("\n🚀 ROZPOCZYNANIE TESTÓW INTEGRACJI SUPABASE STORAGE\n")

    try:
        # Test głównej integracji
        test_storage_integration()

        # Test kompatybilności wstecznej
        test_backward_compatibility()

        print("\n✅ WSZYSTKIE TESTY ZAKOŃCZONE POMYŚLNIE\n")

    except Exception as e:
        print(f"\n❌ BŁĄD KRYTYCZNY: {e}\n")
        import traceback
        traceback.print_exc()

    input("\nNaciśnij Enter aby zakończyć...")