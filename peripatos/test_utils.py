import tempfile

from .storage import private_storage


class TemporaryPrivateStorage:
    """Evita que los tests escriban en el volumen privado real."""

    def setUp(self):
        super().setUp()
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        storage = private_storage()
        # location y base_location son cached_property: basta con sustituir la caché
        previous = {"base_location": storage.base_location, "location": storage.location}
        self.addCleanup(storage.__dict__.update, previous)
        storage.__dict__.update(base_location=directory.name, location=directory.name)
