# Generated by Django 5.1.2 on 2024-11-19 09:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0008_alter_pageview_browser_alter_pageview_country_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='pageview',
            index=models.Index(fields=['website', 'timestamp'], name='pageviews_website_53b17f_idx'),
        ),
    ]
