#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Attachments Manager Module
Zarządzanie załącznikami przechowywanymi jako archiwa ZIP w bazie danych
"""

import os
import io
import zipfile
import json
import tempfile
import mimetypes
from typing import List, Dict, Optional, Tuple, BinaryIO
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class FileMetadata:
    """Metadane pojedynczego pliku w archiwum"""
    filename: str
    size: int  # Rozmiar w bajtach
    type: str  # MIME type
    added_at: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'FileMetadata':
        return cls(**data)


@dataclass
class AttachmentInfo:
    """Informacje o załączniku"""
    id: str
    entity_type: str  # 'order' lub 'quotation'
    entity_id: str
    files_metadata: List[FileMetadata]
    total_size: int
    compressed_size: int
    files_count: int
    created_at: str
    created_by: Optional[str] = None
    notes: Optional[str] = None


class AttachmentsManager:
    """Manager do obsługi załączników jako archiwa ZIP w bazie danych"""

    def __init__(self, db_client):
        """
        Inicjalizacja managera załączników

        Args:
            db_client: Klient Supabase
        """
        self.client = db_client

    def add_files(
        self,
        entity_type: str,
        entity_id: str,
        file_paths: List[str],
        created_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Dodaje pliki jako załącznik (spakowane do ZIP)

        Args:
            entity_type: Typ encji ('order' lub 'quotation')
            entity_id: ID zamówienia lub oferty
            file_paths: Lista ścieżek do plików
            created_by: Użytkownik tworzący załącznik
            notes: Dodatkowe notatki

        Returns:
            Dict z informacjami o utworzonym załączniku lub None w przypadku błędu
        """
        try:
            # Walidacja
            if entity_type not in ['order', 'quotation']:
                raise ValueError(f"Nieprawidłowy entity_type: {entity_type}")

            if not file_paths:
                raise ValueError("Lista plików nie może być pusta")

            # Sprawdź czy pliki istnieją
            for file_path in file_paths:
                if not os.path.exists(file_path):
                    raise FileNotFoundError(f"Plik nie istnieje: {file_path}")

            # Twórz archiwum ZIP w pamięci
            zip_buffer = io.BytesIO()
            files_metadata = []
            total_size = 0

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file_path in file_paths:
                    # Pobierz informacje o pliku
                    file_stat = os.stat(file_path)
                    file_size = file_stat.st_size
                    filename = os.path.basename(file_path)

                    # Określ MIME type
                    mime_type, _ = mimetypes.guess_type(filename)
                    if not mime_type:
                        mime_type = 'application/octet-stream'

                    # Dodaj plik do archiwum
                    zip_file.write(file_path, arcname=filename)

                    # Zapisz metadane
                    metadata = FileMetadata(
                        filename=filename,
                        size=file_size,
                        type=mime_type,
                        added_at=datetime.now().isoformat()
                    )
                    files_metadata.append(metadata)
                    total_size += file_size

            # Pobierz dane ZIP
            zip_data = zip_buffer.getvalue()
            compressed_size = len(zip_data)

            # Konwertuj metadane do JSON
            metadata_json = [m.to_dict() for m in files_metadata]

            # Zapisz do bazy danych
            attachment_data = {
                'entity_type': entity_type,
                'entity_id': entity_id,
                'archive_data': zip_data,
                'files_metadata': json.dumps(metadata_json),
                'total_size': total_size,
                'compressed_size': compressed_size,
                'files_count': len(file_paths),
                'created_by': created_by,
                'notes': notes
            }

            response = self.client.table('attachments').insert(attachment_data).execute()

            if response.data:
                print(f"✅ Dodano załącznik: {len(file_paths)} plików, "
                      f"rozmiar: {self._format_size(total_size)}, "
                      f"skompresowany: {self._format_size(compressed_size)} "
                      f"({compressed_size / total_size * 100:.1f}% kompresji)")
                return response.data[0]

            return None

        except Exception as e:
            print(f"❌ Błąd dodawania załączników: {e}")
            return None

    def get_attachments_list(
        self,
        entity_type: str,
        entity_id: str
    ) -> List[AttachmentInfo]:
        """
        Pobiera listę załączników dla encji

        Args:
            entity_type: Typ encji ('order' lub 'quotation')
            entity_id: ID zamówienia lub oferty

        Returns:
            Lista AttachmentInfo
        """
        try:
            response = self.client.table('attachments').select('*').eq(
                'entity_type', entity_type
            ).eq('entity_id', entity_id).order('created_at', desc=True).execute()

            attachments = []
            for data in response.data:
                # Parsuj metadane plików z JSON
                files_metadata_raw = data.get('files_metadata', '[]')
                if isinstance(files_metadata_raw, str):
                    files_metadata_list = json.loads(files_metadata_raw)
                else:
                    files_metadata_list = files_metadata_raw

                files_metadata = [
                    FileMetadata.from_dict(m) for m in files_metadata_list
                ]

                attachment = AttachmentInfo(
                    id=data['id'],
                    entity_type=data['entity_type'],
                    entity_id=data['entity_id'],
                    files_metadata=files_metadata,
                    total_size=data['total_size'],
                    compressed_size=data.get('compressed_size', 0),
                    files_count=data['files_count'],
                    created_at=data['created_at'],
                    created_by=data.get('created_by'),
                    notes=data.get('notes')
                )
                attachments.append(attachment)

            return attachments

        except Exception as e:
            print(f"❌ Błąd pobierania listy załączników: {e}")
            return []

    def get_files_list(self, attachment_id: str) -> List[FileMetadata]:
        """
        Pobiera listę plików w załączniku (bez pobierania danych ZIP)

        Args:
            attachment_id: ID załącznika

        Returns:
            Lista FileMetadata
        """
        try:
            response = self.client.table('attachments').select(
                'files_metadata'
            ).eq('id', attachment_id).execute()

            if not response.data:
                return []

            files_metadata_raw = response.data[0].get('files_metadata', '[]')
            if isinstance(files_metadata_raw, str):
                files_metadata_list = json.loads(files_metadata_raw)
            else:
                files_metadata_list = files_metadata_raw

            return [FileMetadata.from_dict(m) for m in files_metadata_list]

        except Exception as e:
            print(f"❌ Błąd pobierania listy plików: {e}")
            return []

    def extract_file(
        self,
        attachment_id: str,
        filename: str
    ) -> Optional[bytes]:
        """
        Wyodrębnia pojedynczy plik z archiwum ZIP

        Args:
            attachment_id: ID załącznika
            filename: Nazwa pliku do wyodrębnienia

        Returns:
            Dane pliku jako bytes lub None
        """
        try:
            # Pobierz archiwum ZIP z bazy
            response = self.client.table('attachments').select(
                'archive_data'
            ).eq('id', attachment_id).execute()

            if not response.data:
                print(f"❌ Załącznik {attachment_id} nie został znaleziony")
                return None

            archive_data = response.data[0].get('archive_data')
            if not archive_data:
                print(f"❌ Brak danych archiwum")
                return None

            # Rozpakuj plik z archiwum
            zip_buffer = io.BytesIO(archive_data)
            with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
                if filename not in zip_file.namelist():
                    print(f"❌ Plik {filename} nie znaleziony w archiwum")
                    return None

                file_data = zip_file.read(filename)
                print(f"✅ Wyodrębniono plik: {filename} ({len(file_data)} bajtów)")
                return file_data

        except Exception as e:
            print(f"❌ Błąd wyodrębniania pliku: {e}")
            return None

    def extract_all_to_temp(
        self,
        attachment_id: str
    ) -> Optional[str]:
        """
        Rozpakowuje wszystkie pliki do folderu tymczasowego

        Args:
            attachment_id: ID załącznika

        Returns:
            Ścieżka do folderu tymczasowego lub None
        """
        try:
            # Pobierz archiwum ZIP z bazy
            response = self.client.table('attachments').select(
                'archive_data'
            ).eq('id', attachment_id).execute()

            if not response.data:
                print(f"❌ Załącznik {attachment_id} nie został znaleziony")
                return None

            archive_data = response.data[0].get('archive_data')
            if not archive_data:
                print(f"❌ Brak danych archiwum")
                return None

            # Utwórz folder tymczasowy
            temp_dir = tempfile.mkdtemp(prefix='attachments_')

            # Rozpakuj wszystkie pliki
            zip_buffer = io.BytesIO(archive_data)
            with zipfile.ZipFile(zip_buffer, 'r') as zip_file:
                zip_file.extractall(temp_dir)

            print(f"✅ Rozpakowano załącznik do: {temp_dir}")
            return temp_dir

        except Exception as e:
            print(f"❌ Błąd rozpakowywania załącznika: {e}")
            return None

    def delete_attachment(self, attachment_id: str) -> bool:
        """
        Usuwa załącznik

        Args:
            attachment_id: ID załącznika do usunięcia

        Returns:
            True jeśli usunięto, False w przypadku błędu
        """
        try:
            self.client.table('attachments').delete().eq('id', attachment_id).execute()
            print(f"✅ Usunięto załącznik {attachment_id}")
            return True

        except Exception as e:
            print(f"❌ Błąd usuwania załącznika: {e}")
            return False

    def copy_attachments(
        self,
        source_entity_type: str,
        source_entity_id: str,
        target_entity_type: str,
        target_entity_id: str,
        created_by: Optional[str] = None
    ) -> int:
        """
        Kopiuje wszystkie załączniki z jednej encji do drugiej
        (używane przy konwersji ofert na zamówienia)

        Args:
            source_entity_type: Typ encji źródłowej ('order' lub 'quotation')
            source_entity_id: ID encji źródłowej
            target_entity_type: Typ encji docelowej
            target_entity_id: ID encji docelowej
            created_by: Użytkownik tworzący kopię

        Returns:
            Liczba skopiowanych załączników
        """
        try:
            # Pobierz wszystkie załączniki źródłowe
            response = self.client.table('attachments').select('*').eq(
                'entity_type', source_entity_type
            ).eq('entity_id', source_entity_id).execute()

            if not response.data:
                print(f"ℹ️ Brak załączników do skopiowania")
                return 0

            copied_count = 0
            for attachment in response.data:
                # Utwórz kopię załącznika
                new_attachment = {
                    'entity_type': target_entity_type,
                    'entity_id': target_entity_id,
                    'archive_data': attachment['archive_data'],
                    'files_metadata': attachment['files_metadata'],
                    'total_size': attachment['total_size'],
                    'compressed_size': attachment.get('compressed_size'),
                    'files_count': attachment['files_count'],
                    'created_by': created_by,
                    'notes': f"Skopiowane z {source_entity_type} {source_entity_id}"
                }

                result = self.client.table('attachments').insert(new_attachment).execute()
                if result.data:
                    copied_count += 1

            print(f"✅ Skopiowano {copied_count} załączników")
            return copied_count

        except Exception as e:
            print(f"❌ Błąd kopiowania załączników: {e}")
            return 0

    def get_attachment_size_summary(
        self,
        entity_type: str,
        entity_id: str
    ) -> Dict[str, int]:
        """
        Pobiera podsumowanie rozmiaru załączników

        Args:
            entity_type: Typ encji ('order' lub 'quotation')
            entity_id: ID zamówienia lub oferty

        Returns:
            Dict z kluczami: total_size, compressed_size, files_count, attachments_count
        """
        try:
            response = self.client.table('attachments').select(
                'total_size, compressed_size, files_count'
            ).eq('entity_type', entity_type).eq('entity_id', entity_id).execute()

            if not response.data:
                return {
                    'total_size': 0,
                    'compressed_size': 0,
                    'files_count': 0,
                    'attachments_count': 0
                }

            total_size = sum(a['total_size'] for a in response.data)
            compressed_size = sum(a.get('compressed_size', 0) for a in response.data)
            files_count = sum(a['files_count'] for a in response.data)
            attachments_count = len(response.data)

            return {
                'total_size': total_size,
                'compressed_size': compressed_size,
                'files_count': files_count,
                'attachments_count': attachments_count
            }

        except Exception as e:
            print(f"❌ Błąd pobierania podsumowania: {e}")
            return {
                'total_size': 0,
                'compressed_size': 0,
                'files_count': 0,
                'attachments_count': 0
            }

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """
        Formatuje rozmiar w bajtach do czytelnej formy

        Args:
            size_bytes: Rozmiar w bajtach

        Returns:
            Sformatowany string (np. "1.5 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"


# Funkcje pomocnicze dla łatwego użycia

def format_file_size(size_bytes: int) -> str:
    """Formatuje rozmiar pliku do czytelnej formy"""
    return AttachmentsManager._format_size(size_bytes)


def get_file_icon_by_type(mime_type: str) -> str:
    """Zwraca emoji/ikonę dla typu pliku"""
    icon_map = {
        'application/pdf': '📄',
        'application/msword': '📝',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '📝',
        'application/vnd.ms-excel': '📊',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '📊',
        'image/png': '🖼️',
        'image/jpeg': '🖼️',
        'image/jpg': '🖼️',
        'image/gif': '🖼️',
        'application/zip': '🗜️',
        'application/x-rar': '🗜️',
        'text/plain': '📃',
        'application/dxf': '📐',
        'application/dwg': '📐',
        'application/step': '⚙️',
        'application/stp': '⚙️',
    }

    return icon_map.get(mime_type, '📎')


# Przykład użycia
if __name__ == '__main__':
    # Ten kod służy tylko do testów
    print("AttachmentsManager - Moduł zarządzania załącznikami")
    print("=" * 50)
    print("Funkcjonalności:")
    print("- Dodawanie wielu plików jako spakowane archiwum ZIP")
    print("- Przechowywanie w bazie danych jako BYTEA")
    print("- Rozpakowywanie w locie do podglądu")
    print("- Kopiowanie załączników (np. oferta → zamówienie)")
    print("- Metadane w formacie JSON")
