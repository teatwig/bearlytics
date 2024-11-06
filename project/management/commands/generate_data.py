from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from project.models import PageView, Website
import uuid

class Command(BaseCommand):
    help = 'Generates sample pageview data for the specified time period'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=365,
            help='Number of days to generate data for'
        )
        parser.add_argument(
            '--max-daily-views',
            type=int,
            default=40,
            help='Maximum number of daily views to generate'
        )

    def handle(self, *args, **kwargs):
        paths = ['/home', '/about', '/blog', '/contact', '/products']
        referrers = ['google.com', 'twitter.com', 'facebook.com', 'direct']
        devices = ['Desktop', 'Mobile', 'Tablet']
        browsers = ['Chrome', 'Firefox', 'Safari', 'Edge']
        languages = ['en', 'es', 'fr', 'de', 'zh']
        countries = ['US', 'GB', 'FR', 'DE', 'CA']

        website, _ = Website.objects.get_or_create(id="stress-test", name="Stress test")

        end_date = timezone.now()
        start_date = end_date - timedelta(days=kwargs['days'])
        current_date = start_date

        while current_date <= end_date:
            daily_views = random.randint(40, kwargs['max_daily_views'])
            
            for _ in range(daily_views):
                random_seconds = random.randint(0, 86400)
                timestamp = current_date + timedelta(seconds=random_seconds)
                
                pageview = PageView.objects.create(
                    website=website,
                    hash_id=str(uuid.uuid4())[:8],
                    path=random.choice(paths),
                    referrer=random.choice(referrers),
                    device=random.choice(devices),
                    browser=random.choice(browsers),
                    country=random.choice(countries),
                    language=random.choice(languages),
                )
                PageView.objects.filter(id=pageview.id).update(timestamp=timestamp)
            
            current_date += timedelta(days=1)
            if current_date.day == 1:
                self.stdout.write(f"Created data for {current_date.strftime('%B %Y')}")

        self.stdout.write(self.style.SUCCESS('Successfully generated pageview data'))