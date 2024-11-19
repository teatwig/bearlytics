from datetime import timedelta
import os
import random
import string
from django.utils import timezone
from django.db.models import Q
import hashlib
import base64
import user_agents
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Count
from django.db.models.functions import RowNumber, TruncHour, TruncDay, TruncMonth, Concat
from django.db.models import Subquery, Min
from django.db.models import Window
from .models import PageView, Website

PIXEL = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")


SALT_SECRET = os.getenv("SALT_SECRET")
    

def extract_basic_language(lang_header):
    if not lang_header:
        return "unknown"
    lang_parts = lang_header.split(',')
    return lang_parts[0].split('-')[0]


def hit(request, website_id):
    website = get_object_or_404(Website, id=website_id)

    if request.method == "OPTIONS":
        response = HttpResponse()
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response
    
    # Set response headers
    response = HttpResponse(PIXEL, content_type='image/png')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS"

    # Parse User-Agent
    ua_string = request.META.get('HTTP_USER_AGENT', '')
    user_agent = user_agents.parse(ua_string)
    
    # Skip bots
    if (user_agent.is_bot or 
        any(bot_keyword in ua_string.lower() 
            for bot_keyword in ['bot', 'crawler', 'spider', 'headless', 'puppet'])):
        return response
        
    browser = user_agent.browser.family
    browser = browser.replace("Mobile", "").replace("iOS", "").replace("WebView", "").replace("UI/WK", "").strip()
    device = "Mobile" if user_agent.is_mobile else "Desktop"

    # Get country from CloudFlare header (if available)
    country = request.META.get('HTTP_CF_IPCOUNTRY', 'unknown')

    # Get the real IP address
    ip = request.META.get('HTTP_X_FORWARDED_FOR', '') or \
         request.META.get('HTTP_CF_CONNECTING_IP', '') or \
         request.META.get('REMOTE_ADDR', '')
    ip = ip.split(',')[0].strip()

    # Generate ID using IP, User Agent, current date, and secret
    date = timezone.now().strftime('%Y-%m-%d')
    data = f"{ip}|{ua_string}|{date}|{SALT_SECRET}"
    hash_id = hashlib.sha256(data.encode()).hexdigest()

    # Get path, ref, and project from query parameter
    path = request.GET.get('path', '/')
    if not path.startswith('/'):
        path = '/' + path

    referrer = request.GET.get('ref', 'direct')
    if referrer == "":
        referrer = "direct"
    referrer = referrer.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]

    # Extract basic language code
    language = extract_basic_language(request.META.get('HTTP_ACCEPT_LANGUAGE', ''))

    PageView.objects.create(
        website=website,
        hash_id=hash_id,
        path=path,
        referrer=referrer,
        device=device,
        browser=browser,
        country=country,
        language=language
    )

    return response


def all_hits(request):
    hits = PageView.objects.all().order_by('-timestamp')
    return render(request, 'all_hits.html', {'hits': hits})


def generate_website_id():
    # Generate a random 7-character string using uppercase letters
    return ''.join(random.choices(string.ascii_uppercase, k=7))

def websites(request):
    if request.method == 'POST':
        website_name = request.POST.get('website_name')
        if website_name:
            website_id = generate_website_id()
            # Create new website object
            Website.objects.create(
                name=website_name,
                id=website_id
            )
            messages.success(request, 'Website added successfully!')
            return redirect('websites')
        else:
            messages.error(request, 'Website name is required.')
    
    websites = Website.objects.all()
    return render(request, 'websites.html', {"websites": websites})


def dashboard(request, website_id):
    website = get_object_or_404(Website, id=website_id)

    time_range = request.GET.get('range', '24h')
    end_time = timezone.now().replace(minute=59, second=59, microsecond=999999)
    
    ranges = {
        '24h': timedelta(hours=24),
        '7d': timedelta(days=7),
        '30d': timedelta(days=30),
        '90d': timedelta(days=90),
        '180d': timedelta(days=180),
        '365d': timedelta(days=365)
    }
    start_time = end_time - ranges.get(time_range, ranges['24h'])

    # Optimize base query by selecting only needed fields
    base_query = PageView.objects.filter(
        website=website,
        timestamp__range=(start_time, end_time)
    ).only('hash_id', 'path', 'referrer', 'browser', 'country', 'device', 'timestamp')
    
    # Add filters
    path_filter = request.GET.get('path')
    referrer_filter = request.GET.get('referrer')
    
    if path_filter:
        base_query = base_query.filter(path=path_filter)
    if referrer_filter:
        base_query = base_query.filter(referrer=referrer_filter)
    
    def get_top_metrics(column, limit=100):
        """Helper function to get top metrics for a given column"""
        return (base_query
            .values(column)
            .annotate(
                visits=Count('hash_id', distinct=True)
            )
            .order_by('-visits')[:limit])
    
    # Get overall stats
    stats = base_query.aggregate(
        views=Count('hash_id'),
        visits=Count(Concat('hash_id', 'path'), distinct=True),
        visitors=Count('hash_id', distinct=True),
        unique_pages=Count('path', distinct=True),
        unique_browsers=Count('browser', distinct=True),
        unique_countries=Count('country', distinct=True)
    )
    
    # Determine time grouping based on duration
    duration = end_time - start_time
    if duration <= timedelta(hours=24):
        truncate_func = TruncHour
        date_format = '%Y-%m-%d %H:00'
    elif duration <= timedelta(days=90):
        truncate_func = TruncDay
        date_format = '%Y-%m-%d'
    else:
        truncate_func = TruncMonth
        date_format = '%Y-%m'

    # Optimized time series query using Window function instead of subquery
    time_series = (
        base_query
        .annotate(period=truncate_func('timestamp'))
        .values('period')
        .annotate(
            views=Count('id'),
            visits=Count(
                'id',
                filter=Q(
                    id__in=Subquery(
                        base_query.annotate(
                            row_number=Window(
                                expression=RowNumber(),
                                partition_by=['hash_id', 'path'],
                                order_by='timestamp'
                            )
                        ).filter(row_number=1).values('id')
                    )
                )
            )
        )
        .order_by('period')
    )
    
    # Format time series data for the template
    time_labels = []
    views_data = []
    visits_data = []
    
    # Create time slots and initialize with zeros
    current = start_time
    end_time_slots = timezone.now() + timedelta(hours=1)
    
    total_time_series_visits = 0
    
    # Adjust the time slot creation for monthly grouping
    while current <= end_time_slots:
        time_labels.append(current.strftime(date_format))
        views_data.append(0)
        visits_data.append(0)
        if duration <= timedelta(hours=24):
            current += timedelta(hours=1)
        else:
            current += timedelta(days=1)
        # else:
        #     # Add one month
        #     if current.month == 12:
        #         current = current.replace(year=current.year + 1, month=1)
        #     else:
        #         current = current.replace(month=current.month + 1)
    
    # Fill in actual data
    time_data_map = {
        ts['period'].strftime(date_format): (ts['views'], ts['visits']) 
        for ts in time_series
    }
    
    for i, label in enumerate(time_labels):
        if label in time_data_map:
            views_data[i] = time_data_map[label][0]
            visits_data[i] = time_data_map[label][1]
            total_time_series_visits += time_data_map[label][1]
    
    context = {
        'website': website,
        'stats': stats,
        'time_labels': time_labels[1:],
        'views_data': views_data[1:],
        'visits_data': visits_data[1:],
        'top_pages': get_top_metrics('path'),
        'top_referrers': get_top_metrics('referrer'),
        'top_countries': get_top_metrics('country'),
        'top_devices': get_top_metrics('device'),
        'top_browsers': get_top_metrics('browser'),
        'selected_range': time_range,
        'path_filter': path_filter,
        'referrer_filter': referrer_filter,
    }
    
    return render(request, 'dashboard.html', context)