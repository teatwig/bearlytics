from datetime import timedelta
import os
from django.utils import timezone
from django.db.models import Q
import hashlib
import base64
import user_agents
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Count
from django.db.models.functions import TruncHour, TruncDay, Concat, ExtractHour
from django.db.models import Subquery, Min
from .models import PageView

PIXEL = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")


SALT_SECRET = os.getenv("SALT_SECRET")
    

def extract_basic_language(lang_header):
    if not lang_header:
        return "unknown"
    lang_parts = lang_header.split(',')
    return lang_parts[0].split('-')[0]


def hit(request):
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

    project = request.GET.get('project', 'default')

    # Extract basic language code
    language = extract_basic_language(request.META.get('HTTP_ACCEPT_LANGUAGE', ''))

    PageView.objects.create(
        project=project,
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


def projects(request):
    return HttpResponse("<a href='/justsketchme/dashboard/'>JustSketchMe</a> | <a href='/hermans-blog/dashboard/'>Herman's blog</a>")


def dashboard(request, project):
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
    
    # Create base query once for reuse
    base_query = PageView.objects.filter(
        project=project,
        timestamp__range=(start_time, end_time)
    )
    
    def get_top_metrics(column, limit=10):
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
    else:
        truncate_func = TruncDay
        date_format = '%Y-%m-%d'
    
    # Get time series data
    first_occurrences = (
        base_query
        .values('hash_id', 'path')
        .annotate(first_time=Min('timestamp'))
        .values('hash_id', 'path', 'first_time')
    )

    time_series = (
        base_query
        .annotate(period=truncate_func('timestamp'))
        .values('period')
        .annotate(
            views=Count('id'),
            visits=Count(
                'id',
                filter=Q(timestamp__in=Subquery(
                    first_occurrences.values('first_time')
                ))
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
    
    while current <= end_time_slots:
        time_labels.append(current.strftime(date_format))
        views_data.append(0)
        visits_data.append(0)
        if duration <= timedelta(hours=24):
            current += timedelta(hours=1)
        else:
            current += timedelta(days=1)
    
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
        'project': project,
        'stats': stats,
        'time_labels': time_labels,
        'views_data': views_data,
        'visits_data': visits_data,
        'top_pages': get_top_metrics('path'),
        'top_referrers': get_top_metrics('referrer'),
        'top_countries': get_top_metrics('country'),
        'top_devices': get_top_metrics('device'),
        'top_browsers': get_top_metrics('browser'),
        'selected_range': time_range,
    }
    
    return render(request, 'dashboard.html', context)