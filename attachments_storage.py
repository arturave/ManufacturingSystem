#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Attachments Storage Module
Integracja z Supabase Storage dla przechowywania plików w Object Storage
"""

import os
import io
import mimetypes
import tempfile
import subprocess
import platform
from typing import Optional, Dict, List, Tuple
from pathlib import Path
from datetime import datetime
import hashlib
import json


class AttachmentsStorage:
    """Manager do obsługi przechowywania plików w Supabase Storage"""

    # Bucket dla plików załączników
    BUCKET_NAME = 'attachments'

    # Maksymalny rozmiar pliku (50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024

    # Formaty plików z podglądem
    PREVIEW_FORMATS = {
        # Pliki CAD
        'dxf': True,
        'dwg': True,
        'step': True,
        'stp': True,
        'igs': True,
        'iges': True,
        # Grafiki
        'png': True,
        'jpg': True,
        'jpeg': True,
        'gif': True,
        'bmp': True,
        'svg': True,
        # Dokumenty
        'pdf': True,
        'doc': True,
        'docx': True,
        'xls': True,
        'xlsx': True,
        'ppt': True,
        'pptx': True,
        'txt': True,
        'csv': True,
        # Archiwa (bez podglądu, tylko pobieranie)
        'zip': False,
        'rar': False,
        '7z': False,
        'tar': False,
        'gz': False,
    }

    def __init__(self, supabase_client):
        """
        Inicjalizacja storage managera

        Args:
            supabase_client: Klient Supabase
        """
        self.client = supabase_client
        self.storage = supabase_client.storage

        # Sprawdź/utwórz bucket jeśli nie istnieje
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Upewnia się że bucket istnieje z lepszą obsługą błędów"""
        try:
            # Sprawdź czy bucket istnieje
            buckets = self.storage.list_buckets()
            bucket_exists = any(b.get('name') == self.BUCKET_NAME for b in buckets)

            if not bucket_exists:
                try:
                    # Utwórz bucket (prywatny dla bezpieczeństwa)
                    self.storage.create_bucket(
                        self.BUCKET_NAME,
                        options={
                            'public': False,  # Domyślnie prywatny
                            'file_size_limit': self.MAX_FILE_SIZE,
                            'allowed_mime_types': None  # Wszystkie typy plików
                        }
                    )
                    print(f"✅ Utworzono bucket: {self.BUCKET_NAME}")
                except Exception as create_error:
                    error_msg = str(create_error).lower()
                    # Różne możliwe komunikaty o istnieniu bucketu
                    if any(msg in error_msg for msg in ['already exists', 'bucket already exists', 'duplicate']):
                        print(f"ℹ️ Bucket {self.BUCKET_NAME} już istnieje")
                    elif 'permission' in error_msg or 'unauthorized' in error_msg:
                        print(f"⚠️ Brak uprawnień do utworzenia bucketu {self.BUCKET_NAME}")
                    else:
                        print(f"⚠️ Nie można utworzyć bucketu: {create_error}")

        except AttributeError as e:
            print(f"⚠️ Nieprawidłowa konfiguracja klienta Supabase: {e}")
        except ConnectionError as e:
            print(f"⚠️ Błąd połączenia z Supabase: {e}")
        except Exception as e:
            print(f"⚠️ Nieoczekiwany błąd przy sprawdzaniu bucketu: {e}")
            # Nie rzucaj wyjątku - pozwól aplikacji kontynuować

    def upload_file(
        self,
        file_data: bytes,
        filename: str,
        entity_type: str,
        entity_id: str,
        file_category: str = 'attachments'
    ) -> Optional[Dict[str, str]]:
        """
        Uploaduje plik do Supabase Storage

        Args:
            file_data: Dane pliku jako bytes
            filename: Nazwa pliku
            entity_type: Typ encji ('order' lub 'quotation')
            entity_id: ID encji
            file_category: Kategoria pliku (attachments, thumbnails, documents)

        Returns:
            Dict z URL-ami (public_url, signed_url) lub None w przypadku błędu
        """
        # Walidacja wejścia
        if not file_data:
            print(f"⚠️ Brak danych pliku: {filename}")
            return None

        if not filename or not isinstance(filename, str):
            print(f"⚠️ Nieprawidłowa nazwa pliku")
            return None

        try:
            # Walidacja rozmiaru
            file_size = len(file_data)
            if file_size > self.MAX_FILE_SIZE:
                size_mb = self.MAX_FILE_SIZE / 1024 / 1024
                print(f"⚠️ Plik {filename} przekracza maksymalny rozmiar {size_mb:.0f}MB")
                return None

            if file_size == 0:
                print(f"⚠️ Plik {filename} jest pusty")
                return None

            # Generuj unikalną ścieżkę dla pliku
            file_ext = os.path.splitext(filename)[1].lower()
            file_hash = hashlib.md5(file_data).hexdigest()[:8]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # Struktura: entity_type/entity_id/category/timestamp_hash_filename
            storage_path = f"{entity_type}/{entity_id}/{file_category}/{timestamp}_{file_hash}_{filename}"

            # Upload do storage
            bucket = self.storage.from_(self.BUCKET_NAME)

            # Sprawdź czy plik już istnieje
            try:
                existing = bucket.list(path=f"{entity_type}/{entity_id}/{file_category}")
                if existing and any(f['name'].endswith(filename) for f in existing):
                    # Jeśli plik o tej nazwie istnieje, dodaj hash do nazwy
                    storage_path = f"{entity_type}/{entity_id}/{file_category}/{timestamp}_{file_hash}_{filename}"
            except Exception as list_error:
                print(f"⚠️ Nie można sprawdzić istniejących plików: {list_error}")

            # Upload pliku
            response = bucket.upload(
                path=storage_path,
                file=file_data,
                file_options={
                    'content-type': mimetypes.guess_type(filename)[0] or 'application/octet-stream',
                    'cache-control': '3600',  # Cache na 1 godzinę
                    'upsert': False  # Nie nadpisuj istniejących plików
                }
            )

            # Pobierz URL-e
            public_url = bucket.get_public_url(storage_path)

            # Generuj signed URL (ważny przez 1 godzinę) dla prywatnych plików
            signed_url = None
            try:
                signed_response = bucket.create_signed_url(
                    path=storage_path,
                    expires_in=3600  # 1 godzina
                )
                if signed_response and 'signedURL' in signed_response:
                    signed_url = signed_response['signedURL']
            except Exception as url_error:
                print(f"⚠️ Nie udało się wygenerować signed URL: {url_error}")

            print(f"✅ Uploaded: {filename} → {storage_path}")

            return {
                'storage_path': storage_path,
                'public_url': public_url,
                'signed_url': signed_url,
                'filename': filename,
                'size': file_size,
                'content_type': mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            }

        except ValueError as e:
            print(f"❌ Błąd walidacji pliku {filename}: {e}")
            return None
        except ConnectionError as e:
            print(f"❌ Błąd połączenia podczas uploadu {filename}: {e}")
            return None
        except Exception as e:
            print(f"❌ Nieoczekiwany błąd uploadu pliku {filename}: {e}")
            return None

    def download_file(self, storage_path: str) -> Optional[bytes]:
        """
        Pobiera plik z Supabase Storage

        Args:
            storage_path: Ścieżka do pliku w storage

        Returns:
            Dane pliku jako bytes lub None
        """
        # Walidacja wejścia
        if not storage_path or not isinstance(storage_path, str):
            print(f"⚠️ Nieprawidłowa ścieżka do pliku")
            return None

        try:
            bucket = self.storage.from_(self.BUCKET_NAME)
            response = bucket.download(storage_path)

            if response:
                print(f"✅ Pobrano plik: {storage_path}")
                return response

            print(f"⚠️ Plik nie został znaleziony: {storage_path}")
            return None

        except FileNotFoundError:
            print(f"⚠️ Plik nie istnieje: {storage_path}")
            return None
        except ConnectionError as e:
            print(f"❌ Błąd połączenia podczas pobierania pliku {storage_path}: {e}")
            return None
        except PermissionError as e:
            print(f"❌ Brak uprawnień do pobrania pliku {storage_path}: {e}")
            return None
        except Exception as e:
            print(f"❌ Nieoczekiwany błąd pobierania pliku {storage_path}: {e}")
            return None

    def delete_file(self, storage_path: str) -> bool:
        """
        Usuwa plik z Supabase Storage

        Args:
            storage_path: Ścieżka do pliku w storage

        Returns:
            True jeśli sukces, False w przypadku błędu
        """
        # Walidacja wejścia
        if not storage_path or not isinstance(storage_path, str):
            print(f"⚠️ Nieprawidłowa ścieżka do pliku")
            return False

        try:
            bucket = self.storage.from_(self.BUCKET_NAME)
            bucket.remove([storage_path])
            print(f"✅ Usunięto plik: {storage_path}")
            return True

        except FileNotFoundError:
            print(f"⚠️ Plik nie istnieje: {storage_path}")
            return False
        except PermissionError as e:
            print(f"❌ Brak uprawnień do usunięcia pliku {storage_path}: {e}")
            return False
        except ConnectionError as e:
            print(f"❌ Błąd połączenia podczas usuwania pliku {storage_path}: {e}")
            return False
        except Exception as e:
            print(f"❌ Nieoczekiwany błąd usuwania pliku {storage_path}: {e}")
            return False

    def list_files(
        self,
        entity_type: str,
        entity_id: str,
        file_category: str = None
    ) -> List[Dict]:
        """
        Listuje pliki dla danej encji

        Args:
            entity_type: Typ encji ('order' lub 'quotation')
            entity_id: ID encji
            file_category: Opcjonalna kategoria do filtrowania

        Returns:
            Lista plików z metadanymi
        """
        try:
            bucket = self.storage.from_(self.BUCKET_NAME)

            # Buduj ścieżkę
            if file_category:
                path = f"{entity_type}/{entity_id}/{file_category}"
            else:
                path = f"{entity_type}/{entity_id}"

            files = bucket.list(path=path)

            # Formatuj wyniki
            result = []
            for file in files:
                result.append({
                    'name': file['name'],
                    'size': file.get('metadata', {}).get('size', 0),
                    'created_at': file.get('created_at'),
                    'updated_at': file.get('updated_at'),
                    'storage_path': f"{path}/{file['name']}"
                })

            return result

        except Exception as e:
            print(f"❌ Błąd listowania plików: {e}")
            return []

    def get_signed_url(self, storage_path: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generuje signed URL dla prywatnego pliku

        Args:
            storage_path: Ścieżka do pliku w storage
            expires_in: Czas ważności URL w sekundach (domyślnie 1 godzina)

        Returns:
            Signed URL lub None
        """
        try:
            bucket = self.storage.from_(self.BUCKET_NAME)
            response = bucket.create_signed_url(
                path=storage_path,
                expires_in=expires_in
            )

            if response and 'signedURL' in response:
                return response['signedURL']

            return None

        except Exception as e:
            print(f"❌ Błąd generowania signed URL: {e}")
            return None

    def can_preview_file(self, filename: str) -> bool:
        """
        Sprawdza czy plik może być podglądany

        Args:
            filename: Nazwa pliku

        Returns:
            True jeśli plik może być podglądany
        """
        ext = os.path.splitext(filename)[1].lower().lstrip('.')
        return self.PREVIEW_FORMATS.get(ext, False)

    def has_default_application(self, filename: str) -> bool:
        """
        Sprawdza czy system ma domyślną aplikację dla typu pliku

        Args:
            filename: Nazwa pliku

        Returns:
            True jeśli system może otworzyć plik
        """
        try:
            ext = os.path.splitext(filename)[1].lower()

            if platform.system() == 'Windows':
                # Na Windows sprawdź rejestr
                import winreg
                try:
                    # Sprawdź w rejestrze Windows
                    with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, ext) as key:
                        # Pobierz domyślną wartość (np. "txtfile")
                        file_type = winreg.QueryValue(key, "")
                        if file_type:
                            # Sprawdź czy istnieje shell/open/command
                            try:
                                with winreg.OpenKey(
                                    winreg.HKEY_CLASSES_ROOT,
                                    f"{file_type}\\shell\\open\\command"
                                ) as cmd_key:
                                    return True
                            except:
                                pass
                    return False
                except WindowsError:
                    return False

            elif platform.system() == 'Darwin':  # macOS
                # Użyj LaunchServices
                mime_type, _ = mimetypes.guess_type(filename)
                if mime_type:
                    result = subprocess.run(
                        ['open', '-g', '-b', 'com.apple.TextEdit', '--args'],
                        capture_output=True,
                        text=True
                    )
                    # Jeśli komenda działa, system ma aplikacje
                    return result.returncode == 0 or True  # Zakładamy że macOS ma zawsze aplikacje
                return False

            else:  # Linux
                # Sprawdź xdg-mime
                mime_type, _ = mimetypes.guess_type(filename)
                if mime_type:
                    result = subprocess.run(
                        ['xdg-mime', 'query', 'default', mime_type],
                        capture_output=True,
                        text=True
                    )
                    return bool(result.stdout.strip())
                return False

        except Exception as e:
            print(f"⚠️ Błąd sprawdzania aplikacji: {e}")
            return False

    def open_file_with_default_app(self, file_data: bytes, filename: str) -> bool:
        """
        Otwiera plik w domyślnej aplikacji systemowej

        Args:
            file_data: Dane pliku
            filename: Nazwa pliku

        Returns:
            True jeśli sukces
        """
        try:
            # Zapisz do pliku tymczasowego
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=os.path.splitext(filename)[1],
                prefix=os.path.splitext(filename)[0] + "_"
            )
            temp_file.write(file_data)
            temp_file.close()

            # Otwórz w domyślnej aplikacji
            if platform.system() == 'Windows':
                os.startfile(temp_file.name)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(['open', temp_file.name])
            else:  # Linux
                subprocess.call(['xdg-open', temp_file.name])

            print(f"✅ Otwarto plik: {filename}")
            return True

        except Exception as e:
            print(f"❌ Nie udało się otworzyć pliku: {e}")
            return False

    def generate_thumbnail(
        self,
        file_data: bytes,
        filename: str,
        entity_type: str,
        entity_id: str,
        max_size: Tuple[int, int] = (200, 200)
    ) -> Optional[Dict[str, str]]:
        """
        Generuje thumbnail dla pliku graficznego

        Args:
            file_data: Dane pliku
            filename: Nazwa pliku
            entity_type: Typ encji
            entity_id: ID encji
            max_size: Maksymalny rozmiar thumbnail (szerokość, wysokość)

        Returns:
            Dict z URL-ami thumbnail lub None
        """
        try:
            from PIL import Image
            import io

            # Sprawdź czy to obraz
            ext = os.path.splitext(filename)[1].lower().lstrip('.')
            if ext not in ['png', 'jpg', 'jpeg', 'gif', 'bmp']:
                return None

            # Otwórz obraz
            image = Image.open(io.BytesIO(file_data))

            # Konwertuj do RGB jeśli potrzeba
            if image.mode not in ('RGB', 'RGBA'):
                image = image.convert('RGB')

            # Zmień rozmiar zachowując proporcje
            image.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Zapisz do bufora
            thumb_buffer = io.BytesIO()
            image.save(thumb_buffer, format='PNG', optimize=True)
            thumb_data = thumb_buffer.getvalue()

            # Upload thumbnail
            thumb_filename = f"thumb_{max_size[0]}x{max_size[1]}_{filename}"
            thumb_result = self.upload_file(
                file_data=thumb_data,
                filename=thumb_filename,
                entity_type=entity_type,
                entity_id=entity_id,
                file_category='thumbnails'
            )

            return thumb_result

        except Exception as e:
            print(f"⚠️ Nie udało się wygenerować thumbnail: {e}")
            return None

    def cleanup_entity_files(
        self,
        entity_type: str,
        entity_id: str
    ) -> int:
        """
        Usuwa wszystkie pliki związane z encją

        Args:
            entity_type: Typ encji
            entity_id: ID encji

        Returns:
            Liczba usuniętych plików
        """
        try:
            bucket = self.storage.from_(self.BUCKET_NAME)
            path = f"{entity_type}/{entity_id}"

            # Pobierz listę plików
            files = bucket.list(path=path)

            # Usuń wszystkie pliki
            if files:
                file_paths = [f"{path}/{f['name']}" for f in files]
                bucket.remove(file_paths)
                print(f"✅ Usunięto {len(file_paths)} plików dla {entity_type}/{entity_id}")
                return len(file_paths)

            return 0

        except Exception as e:
            print(f"❌ Błąd czyszczenia plików: {e}")
            return 0


# Funkcje pomocnicze

def format_file_size(size_bytes: int) -> str:
    """Formatuje rozmiar pliku do czytelnej formy"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def get_file_icon_by_extension(filename: str) -> str:
    """Zwraca emoji/ikonę dla typu pliku na podstawie rozszerzenia"""
    ext = os.path.splitext(filename)[1].lower().lstrip('.')

    icon_map = {
        # Dokumenty
        'pdf': '📄',
        'doc': '📝',
        'docx': '📝',
        'txt': '📃',
        'rtf': '📝',
        # Arkusze
        'xls': '📊',
        'xlsx': '📊',
        'csv': '📊',
        # Prezentacje
        'ppt': '📽️',
        'pptx': '📽️',
        # Obrazy
        'png': '🖼️',
        'jpg': '🖼️',
        'jpeg': '🖼️',
        'gif': '🖼️',
        'bmp': '🖼️',
        'svg': '🎨',
        # CAD
        'dxf': '📐',
        'dwg': '📐',
        'step': '⚙️',
        'stp': '⚙️',
        'igs': '⚙️',
        'iges': '⚙️',
        # Archiwa
        'zip': '🗜️',
        'rar': '🗜️',
        '7z': '🗜️',
        'tar': '🗜️',
        'gz': '🗜️',
        # Inne
        'xml': '📋',
        'json': '📋',
        'html': '🌐',
    }

    return icon_map.get(ext, '📎')


if __name__ == '__main__':
    print("AttachmentsStorage - Moduł integracji z Supabase Storage")
    print("=" * 60)
    print("Funkcjonalności:")
    print("- Upload plików do Supabase Storage")
    print("- Generowanie signed URLs dla prywatnych plików")
    print("- Sprawdzanie możliwości podglądu")
    print("- Generowanie thumbnails dla obrazów")
    print("- Zarządzanie plikami per encja")