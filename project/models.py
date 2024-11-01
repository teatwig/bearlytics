from django.db import models

class PageView(models.Model):
    hash_id = models.CharField(max_length=64, db_index=True, blank=True)
    path = models.CharField(max_length=2048, db_index=True)
    referrer = models.CharField(max_length=2048, db_index=True, null=True, blank=True)
    device = models.CharField(max_length=100, db_index=True)
    browser = models.CharField(max_length=100, db_index=True)
    country = models.CharField(max_length=100, db_index=True)
    language = models.CharField(max_length=10, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'pageviews'

    def __str__(self):
        return f"{self.path} - {self.timestamp}" 