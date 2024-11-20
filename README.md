# ʕ•ᴥ•ʔ⌕ Bearlytics

A privacy-first, no-nonsense web analytics platform.

## What is this?

Bearlytics is exactly what it says on the tin - a straightforward web analytics tool that helps you understand your website traffic without selling your soul to the tracking gods. No cookies, no personal data collection, just the basics:

- Page views
- Referrers
- Country
- Device type
- Browser

## Why?

Because sometimes you just want to know how many people visited your blog post about artisanal toast without signing up for an enterprise-grade solution.

After struggling to self-host popular open-source analytics platforms like Plausible and Umami (which require multiple services and complex setups), I decided to build something simpler and self-contained with Django and SQLite.

![Screenshot](screenshot.png)
## Features

- 🔒 Privacy-focused: No cookies, no personal data collection
- 🚀 As many websites as your server can handle
- 📊 Clean, intuitive dashboard
- 🔍 Filter by date range, page path, and referrer
- 📱 Responsive design that won't make your eyes bleed
- 💾 Self-hosted, because your data belongs to you

### Configuration

Bearlytics uses a straightforward Django configuration with SQLite as the database backend. Key settings include:

- **Database**: SQLite with WAL journal mode and optimized cache settings for better performance
- **Environment Variables**:
  - `SECRET_KEY`: Django secret key
  - `DEBUG`: Set to False in production
  - `DB_PATH`: SQLite database location (default: /app/db/db.sqlite3)
  - `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
  - `CSRF_TRUSTED_ORIGINS`: Comma-separated list of trusted origins

The SQLite database is configured with performance optimizations:
- Increased cache size
- Write-Ahead Logging (WAL) journal mode
- Normal synchronization mode

## Self-hosting Guide

This is a basic Django app that can be deployed to any platform that supports Django. I've chosen Dokku because it's easy to set up and manage, and because I'm familiar with it.

### Prerequisites

- A Dokku server (or the willingness to set one up)
- Basic knowledge of terminal commands
- A cup of coffee

### Step 1: Dokku Setup 

```bash
# Create the app
dokku apps:create analytics

# Create persistent storage for SQLite
dokku storage:ensure-directory analytics
dokku storage:mount analytics /var/lib/dokku/data/storage/analytics:/app/data

# Set environment variables
dokku config:set analytics SECRET_KEY=your_very_secret_key_here
dokku config:set analytics DB_PATH=/app/data/analytics.db
dokku config:set DISABLE_COLLECTSTATIC=1
dokku config:set DEBUG=False
```

### Step 2: Deploy

Add Dokku as a remote and commit and push your code
```bash
git remote add dokku dokku@your-server:analytics
git push dokku main
```

### Step 3: Add Your First Website

1. Visit `https://your-analytics-domain.com`
2. Create an account (if no user exists, the first user will be automatically promoted to admin)
3. Add your website
4. Copy the tracking script
5. Add it to your website's `<head>` section
6. Watch those sweet, sweet analytics roll in

## Tracking Script

<script async defer src="https://your-analytics-domain.com/tracker.js" data-website-id="your-website-id"></script>

## FAQ

**Q: Is this better than Google Analytics?**  
A: For tracking your cat blog? Probably. For enterprise-level analytics needs? I'd recommend something more robust like [Fathom](https://usefathom.com/ref/GMAGWL).

**Q: Will this make me rich and famous?**  
A: No, but it will tell you how many people read your blog post about getting rich and famous.

**Q: Is it production-ready?**  
A: I've been running it in production on my [personal blog](https://herman.bearblog.dev), and [JustSketchMe](https://justsketch.me) since November 2024. So far, nothing has exploded.

## License

AGPL-3.0 - This license ensures that:
- You can self-host and modify Bearlytics for your own use, no strings attached
- Commercial hosting of Bearlytics as a service is restricted to the original copyright holder (me)

For the full license text, see [LICENSE](LICENSE.md)

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## Acknowledgments

- Coffee ☕
- The internet 🌐
- That one Stack Overflow answer that saved my life 🙏
- SQLite (you're doing great!)

---

Made with ❤️ and probably too much caffeine by [Herman](https://herman.bearblog.dev)