from django.db import models

class PageView(models.Model):
    id = models.TextField(primary_key=True)
    path = models.TextField(db_index=True)
    referrer = models.TextField(null=True, blank=True)
    device = models.TextField()
    browser = models.TextField()
    country = models.TextField()
    language = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pageviews'

    def __str__(self):
        return f"{self.path} - {self.timestamp}" 