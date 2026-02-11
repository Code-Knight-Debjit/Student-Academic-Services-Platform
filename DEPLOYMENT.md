# Deployment Guide - Student Results System

## Quick Start Deployment

### Step 1: Server Preparation (Ubuntu 22.04+)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-pip python3-venv python3-dev \
    postgresql postgresql-contrib nginx supervisor git

# Install build tools for some Python packages
sudo apt install -y build-essential libpq-dev
```

### Step 2: Database Setup

```bash
# Access PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE student_results_db;
CREATE USER student_results_user WITH PASSWORD 'your_secure_password_here';
ALTER ROLE student_results_user SET client_encoding TO 'utf8';
ALTER ROLE student_results_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE student_results_user SET timezone TO 'Asia/Kolkata';
GRANT ALL PRIVILEGES ON DATABASE student_results_db TO student_results_user;
\q
```

### Step 3: Application Setup

```bash
# Create application directory
sudo mkdir -p /var/www/student_results
sudo chown $USER:$USER /var/www/student_results
cd /var/www/student_results

# Clone or copy your project files here
# (Copy the entire student_results_system directory)

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Environment Configuration

```bash
# Create .env file
nano .env
```

Add the following (replace with your actual values):

```env
# Django Settings
SECRET_KEY=your-very-long-random-secret-key-generate-new-one
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,your-server-ip

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=student_results_db
DB_USER=student_results_user
DB_PASSWORD=your_secure_password_here
DB_HOST=localhost
DB_PORT=5432

# Google reCAPTCHA
RECAPTCHA_SITE_KEY=your-recaptcha-site-key
RECAPTCHA_SECRET_KEY=your-recaptcha-secret-key
```

Generate a new SECRET_KEY:
```python
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### Step 5: Django Setup

```bash
# Activate virtual environment
source venv/bin/activate

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Set proper permissions
sudo chown -R www-data:www-data /var/www/student_results
sudo chmod -R 755 /var/www/student_results
```

### Step 6: Gunicorn Setup with Systemd

```bash
# Copy service file
sudo nano /etc/systemd/system/student_results.service
```

Paste this content (adjust paths):

```ini
[Unit]
Description=Student Results System Gunicorn Daemon
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/student_results
Environment="PATH=/var/www/student_results/venv/bin"
ExecStart=/var/www/student_results/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/var/www/student_results/student_results.sock \
          --timeout 30 \
          student_results.wsgi:application

[Install]
WantedBy=multi-user.target
```

Start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl start student_results
sudo systemctl enable student_results
sudo systemctl status student_results
```

### Step 7: Nginx Configuration

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/student_results
```

Paste this content (adjust domain and paths):

```nginx
upstream student_results_app {
    server unix:/var/www/student_results/student_results.sock fail_timeout=0;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    client_max_body_size 10M;
    
    access_log /var/log/nginx/student_results_access.log;
    error_log /var/log/nginx/student_results_error.log;
    
    location /static/ {
        alias /var/www/student_results/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /var/www/student_results/media/;
        expires 7d;
    }
    
    location / {
        proxy_pass http://student_results_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # WebSocket support (if needed in future)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/student_results /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 8: SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Certbot will automatically configure Nginx for SSL
# Test auto-renewal
sudo certbot renew --dry-run
```

### Step 9: Firewall Configuration

```bash
# Allow HTTP and HTTPS
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### Step 10: Verify Deployment

1. Visit `https://your-domain.com`
2. Test result query functionality
3. Login to admin panel
4. Test bulk upload
5. Generate PDF
6. Check analytics

## Post-Deployment Tasks

### Database Backup Script

Create `/var/www/student_results/backup_db.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/student_results"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

pg_dump -U student_results_user student_results_db > $BACKUP_DIR/db_backup_$DATE.sql

# Keep only last 30 days of backups
find $BACKUP_DIR -name "db_backup_*.sql" -mtime +30 -delete
```

Make executable and add to cron:

```bash
chmod +x /var/www/student_results/backup_db.sh
sudo crontab -e
# Add: 0 2 * * * /var/www/student_results/backup_db.sh
```

### Monitoring Setup

```bash
# View application logs
sudo journalctl -u student_results -f

# View Nginx access logs
sudo tail -f /var/log/nginx/student_results_access.log

# View Nginx error logs
sudo tail -f /var/log/nginx/student_results_error.log
```

### Maintenance Commands

```bash
# Restart application
sudo systemctl restart student_results

# Restart Nginx
sudo systemctl restart nginx

# Update application
cd /var/www/student_results
source venv/bin/activate
git pull  # if using git
pip install -r requirements.txt --upgrade
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart student_results

# Clear sessions
python manage.py clearsessions
```

## Performance Tuning

### PostgreSQL Optimization

Edit `/etc/postgresql/14/main/postgresql.conf`:

```
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
work_mem = 4MB
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

### Nginx Caching

Add to Nginx config for better performance:

```nginx
# Cache zone
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=student_results_cache:10m inactive=60m;

# In location /
proxy_cache student_results_cache;
proxy_cache_valid 200 10m;
proxy_cache_bypass $http_pragma $http_authorization;
```

## Troubleshooting

### Application won't start
```bash
# Check service status
sudo systemctl status student_results

# Check logs
sudo journalctl -u student_results -n 50

# Common fixes
sudo chown -R www-data:www-data /var/www/student_results
source venv/bin/activate
python manage.py check
```

### 502 Bad Gateway
```bash
# Check if Gunicorn socket exists
ls -la /var/www/student_results/*.sock

# Restart service
sudo systemctl restart student_results
```

### Static files not loading
```bash
python manage.py collectstatic --noinput
sudo systemctl restart student_results
sudo systemctl restart nginx
```

### Database connection issues
```bash
# Test database connection
sudo -u postgres psql -d student_results_db

# Check database credentials in .env file
```

## Security Checklist

- [ ] DEBUG=False in production
- [ ] Strong SECRET_KEY generated
- [ ] ALLOWED_HOSTS configured
- [ ] SSL certificate installed
- [ ] Firewall enabled
- [ ] Database password is strong
- [ ] Regular backups enabled
- [ ] File permissions set correctly
- [ ] reCAPTCHA configured
- [ ] Rate limiting enabled

## Monitoring & Maintenance Schedule

**Daily:**
- Check application logs
- Monitor disk space

**Weekly:**
- Review upload history
- Check for failed uploads
- Review error logs

**Monthly:**
- Update dependencies
- Review and clean old media files
- Database vacuum/analyze
- Security updates

**Quarterly:**
- Full database backup
- Performance review
- Security audit

---

## Support

For issues or questions:
1. Check logs first
2. Review this deployment guide
3. Check README.md for configuration details
4. Test in development environment first

