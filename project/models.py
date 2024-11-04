from django.db import models

class Website(models.Model):
    id = models.CharField(max_length=20, primary_key=True, db_index=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} ({self.id})"


class PageView(models.Model):
    website = models.ForeignKey(Website, on_delete=models.CASCADE, blank=True, null=True)
    project = models.CharField(max_length=255, default="default", db_index=True)
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