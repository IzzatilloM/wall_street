from django.http import Http404, HttpResponse

from .models import DBFile


def serve_db_file(request, name):
    """Bazada saqlangan media faylni qaytaradi (/media/<name>)."""
    try:
        obj = DBFile.objects.get(name=name)
    except DBFile.DoesNotExist:
        raise Http404('Fayl topilmadi')

    resp = HttpResponse(bytes(obj.content), content_type=obj.content_type)
    resp['Cache-Control'] = 'public, max-age=86400'
    return resp
