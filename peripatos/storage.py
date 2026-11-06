from django.core.files.storage import storages


def private_storage():
    """Ficheros fuera de /media: nginx no los sirve y solo se descargan a través de la API."""
    return storages["private"]
