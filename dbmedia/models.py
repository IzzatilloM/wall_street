from django.db import models


class DBFile(models.Model):
    """
    Yuklangan media fayl bazada (Postgres bytea / SQLite BLOB) saqlanadi.

    Nima uchun: Render bepul disk EFEMERAL (redeploy/restart'da fayllar yo'qoladi),
    Cloudinary esa ba'zi davlatlarda (O'zbekiston) bloklangan. Postgres baza esa
    doimiy va har joydan ishlaydi — shuning uchun rasmlar shu yerda saqlanadi.
    """
    name         = models.CharField(max_length=500, unique=True, db_index=True)
    content      = models.BinaryField()
    content_type = models.CharField(max_length=120, default='application/octet-stream')
    size         = models.PositiveIntegerField(default=0)
    uploaded_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Media fayl (bazada)'
        verbose_name_plural = 'Media fayllar (bazada)'

    def __str__(self):
        return self.name
