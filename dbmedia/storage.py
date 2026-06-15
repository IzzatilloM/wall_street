import mimetypes

from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.urls import reverse
from django.utils.deconstruct import deconstructible


@deconstructible
class DatabaseStorage(Storage):
    """
    Media fayllarni DBFile modeli (baza) orqali saqlaydigan storage backend.

    Django shu backend'ni `STORAGES['default']` sifatida ishlatadi —
    ImageField/FileField yuklamalari avtomatik bazaga yoziladi va
    `/media/<name>` URL orqali (dbmedia.views.serve_db_file) qaytariladi.
    """

    def _open(self, name, mode='rb'):
        from .models import DBFile
        obj = DBFile.objects.get(name=name)
        return ContentFile(bytes(obj.content), name=name)

    def _save(self, name, content):
        from .models import DBFile
        content.seek(0)
        data = content.read()
        ctype = (
            getattr(content, 'content_type', None)
            or mimetypes.guess_type(name)[0]
            or 'application/octet-stream'
        )
        DBFile.objects.update_or_create(
            name=name,
            defaults={'content': data, 'content_type': ctype, 'size': len(data)},
        )
        return name

    def exists(self, name):
        from .models import DBFile
        return DBFile.objects.filter(name=name).exists()

    def delete(self, name):
        from .models import DBFile
        DBFile.objects.filter(name=name).delete()

    def size(self, name):
        from .models import DBFile
        return DBFile.objects.get(name=name).size

    def url(self, name):
        return reverse('dbmedia_serve', kwargs={'name': name})
