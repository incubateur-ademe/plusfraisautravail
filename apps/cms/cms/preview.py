"""Media of a preview (cms.settings.preview). A preview holds no bucket and no
key: what it writes (uploads, new renditions) goes to its own database, with the
storage of sites-conformes; what it does not hold, it reads from production's
public media. Only images are public there: a preview has no documents."""

import urllib.request
from urllib.error import HTTPError
from urllib.parse import urljoin

from django.core.files.base import ContentFile
from django.utils.deconstruct import deconstructible
from django.utils.encoding import filepath_to_uri
from sites_conformes.db_storage.storage import DatabaseStorage

TIMEOUT = 30  # seconds, per file read from production


@deconstructible
class PreviewStorage(DatabaseStorage):
    def __init__(self, production_url):
        self.production_url = production_url

    def _production(self, name):
        return urljoin(self.production_url, filepath_to_uri(name))

    def _fetch(self, name):
        with urllib.request.urlopen(self._production(name), timeout=TIMEOUT) as response:
            return response.read()

    def url(self, name):
        return super().url(name) if super().exists(name) else self._production(name)

    def exists(self, name):
        # A name production holds is taken: an upload must not cover its file.
        if super().exists(name):
            return True
        try:
            with urllib.request.urlopen(
                urllib.request.Request(self._production(name), method="HEAD"), timeout=TIMEOUT
            ):
                return True
        except HTTPError:
            return False

    # A new rendition reads its original. Not copied here: the database of a
    # preview sits on the production instance, and its disk.
    def _open(self, name, mode="rb"):
        try:
            return super()._open(name, mode)
        except FileNotFoundError:
            file = ContentFile(self._fetch(name))
            file.name = name
            return file

    def size(self, name):
        return super().size(name) if super().exists(name) else len(self._fetch(name))
