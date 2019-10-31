import io
import mimetypes
import os

from django.conf import settings
from django.core.files.storage import Storage
from google.cloud import storage
from google.cloud.storage import Blob


class GoogleCloudStorage(Storage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = storage.client.Client()
        self.bucket = self.client.bucket(settings.GOOGLE_CLOUD_STORAGE_BUCKET)
        self.root = settings.GOOGLE_CLOUD_STORAGE_ROOT
        self.url_base = settings.MEDIA_URL

    def _get_blob(self, name: str) -> Blob:
        return self.bucket.blob(self.generate_filename(f'{self.root}/{name}'))

    def _save(self, name, content):
        blob = self._get_blob(name)
        content.open()

        # Set content type only by `name`
        ext = os.path.splitext(name)[1]
        content_type = mimetypes.types_map.get(ext, None)

        blob.upload_from_file(
            content,
            content_type=content_type
        )
        return name

    def generate_filename(self, filename):
        return filename.replace('\\', '/')

    def delete(self, name):
        blob = self._get_blob(name)
        blob.delete()

    def exists(self, name):
        blob = self._get_blob(name)
        return blob.exists()

    def size(self, name):
        # TODO
        print("SIZE", name)
        assert False, name

    def url(self, name):
        return f'{self.url_base}{name}'

    def open(self, name, mode='rb'):
        return GoogleCloudStorageBlob(self._get_blob(name))


class GoogleCloudStorageBlob(io.BytesIO):
    def __init__(self, blob: Blob):
        super().__init__()
        self._blob = blob
        self._loaded = False
        self._is_write = False

    def write(self, b: bytes) -> int:
        self._is_write = True
        return super().write(b)

    def read(self, size=None) -> bytes:
        if not self._loaded:
            self._blob.download_to_file(self)
            self._is_write = False  # `write` may be executed
            self.seek(0)
            self._loaded = True
        return super().read(size)

    def close(self) -> None:
        if self._is_write:
            self._blob.upload_from_file(self)
        super().close()


