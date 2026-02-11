# Student Results Viewing Web Application

A robust, scalable, and secure Django-based web application for viewing student academic results with a beautiful Tailwind CSS interface.

## Features

### Core Features
- ✅ Public result viewing with USN + DOB + Semester validation
- ✅ Google reCAPTCHA v2 integration for security
- ✅ PDF export of results with professional styling
- ✅ Dark mode support with smooth transitions
- ✅ Fully responsive design (mobile + desktop)
- ✅ Skeleton loader for responses > 1 second
- ✅ Session management with automatic expiration

### Admin Features
- ✅ Bulk Excel/CSV upload (Results & Metadata)
- ✅ Individual result editing
- ✅ Advanced analytics dashboard
- ✅ Semester-wise statistics
- ✅ Admission route analysis
- ✅ Top performers tracking
- ✅ Course-wise performance metrics
- ✅ Upload history tracking

### Security Features
- ✅ Django rate limiting
- ✅ Google reCAPTCHA validation
- ✅ Environment variable configuration
- ✅ CSRF protection
- ✅ SQL injection prevention
- ✅ XSS protection
- ✅ Secure session management

## Technology Stack

- **Backend**: Django 5.0.1
- **Frontend**: Tailwind CSS 3.x (CDN)
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **PDF Generation**: ReportLab
- **Data Processing**: Pandas, NumPy, OpenPyXL
- **Deployment**: Nginx + Gunicorn + WhiteNoise
- **Fonts**: Crimson Pro (headers) + Work Sans (body)

## Project Structure

```
student_results_system/
├── student_results/          # Main Django project
│   ├── __init__.py
│   ├── settings.py          # Project settings
│   ├── urls.py              # URL configuration
│   └── wsgi.py              # WSGI configuration
├── core/                     # Core app (home page)
│   ├── urls.py
│   └── ...
├── results/                  # Results app (main functionality)
│   ├── models.py            # Database models
│   ├── views.py             # View functions
│   ├── forms.py             # Form definitions
│   ├── admin.py             # Admin interface
│   ├── utils.py             # Excel processing utilities
│   ├── pdf_generator.py     # PDF generation
│   └── urls.py
├── accounts/                 # Authentication app
│   ├── views.py
│   └── urls.py
├── templates/               # HTML templates
│   ├── base/
│   │   └── base.html       # Base template with Tailwind
│   ├── results/
│   │   ├── home.html       # Result query page
│   │   └── result_view.html
│   ├── accounts/
│   │   └── login.html
│   └── admin_panel/
│       ├── dashboard.html
│       ├── bulk_upload.html
│       └── analytics.html
├── static/                  # Static files (CSS, JS, images)
├── media/                   # User uploads
├── requirements.txt         # Python dependencies
├── manage.py               # Django management script
├── .env.example            # Environment variables template
├── gunicorn_config.py      # Gunicorn configuration
├── nginx.conf              # Nginx configuration
└── student_results.service # Systemd service file
```

## Installation & Setup

### Prerequisites
- Python 3.10+
- pip
- virtualenv (recommended)
- PostgreSQL (for production)

### Local Development Setup

1. **Clone or extract the project**
```bash
cd student_results_system
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env file with your settings
```

Required environment variables:
- `SECRET_KEY`: Django secret key (generate new one for production)
- `DEBUG`: Set to `False` in production
- `RECAPTCHA_SITE_KEY`: Google reCAPTCHA site key
- `RECAPTCHA_SECRET_KEY`: Google reCAPTCHA secret key
- Database credentials (for PostgreSQL)

5. **Run migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Create superuser**
```bash
python manage.py createsuperuser
```

7. **Collect static files**
```bash
python manage.py collectstatic --noinput
```

8. **Run development server**
```bash
python manage.py runserver
```

Access the application at: http://localhost:8000

## Google reCAPTCHA Setup

1. Go to [Google reCAPTCHA Admin](https://www.google.com/recaptcha/admin)
2. Register a new site with reCAPTCHA v2 (Checkbox)
3. Add your domain (use `localhost` for development)
4. Copy the Site Key and Secret Key
5. Add them to your `.env` file

## Database Models

### Student
- `usn` (Primary Key, 10 characters, alphanumeric)
- `name`
- `department`
- `semester`

### StudentMetadata
- `student` (One-to-One with Student)
- `dob` (Date of Birth, mandatory)
- `admission_route` (COMEDK/KCET/Management)

### Course
- `course_code` (Unique)
- `course_title`
- `semester`
- `credits`

### Result
- `student` (Foreign Key)
- `course` (Foreign Key)
- `final_cie_marks`
- `marks_in_words`
- `academic_year`
- `scheme`
- `semester`
- Unique constraint: (student, course)

### UploadHistory
- Tracks all Excel/CSV uploads
- Records: processed, created, updated, skipped
- Error logging

## Excel Upload Formats

### Results File Format
- **Skip first 7 rows** (Row 8 is header)
- **Required columns** (case-insensitive keyword matching):
  - USN (contains "usn")
  - Name (contains "name")
  - Course Title (contains "course")
- **Optional columns**:
  - Final CIE Marks (contains "final cie" or "cie")
  - Marks in Words (contains "words")

### Metadata File Format
- **Required columns**:
  - USN
  - DOB (Date of Birth)
- **Optional columns**:
  - Admission Route (COMEDK/KCET/Management)

### Upload Rules
- USN must be exactly 10 alphanumeric characters
- DOB format: YYYY-MM-DD or DD/MM/YYYY
- Missing metadata → auto-creates with default DOB (2006-01-01)
- Duplicate subjects → overwrites existing
- Metadata re-upload → replaces existing
- Max file size: 10MB

## User Roles

### Public Users
- View results by entering USN + DOB + Semester
- Download PDF of results
- No login required
- reCAPTCHA validation mandatory

### Admin/Professor (Superuser)
- Access admin dashboard
- Bulk upload Excel/CSV files
- Edit individual results
- View analytics and statistics
- Filter by semester, course, admission route
- Track upload history

## Production Deployment

### Using Nginx + Gunicorn

1. **Install system dependencies**
```bash
sudo apt update
sudo apt install python3-pip python3-venv nginx postgresql postgresql-contrib
```

2. **Setup PostgreSQL database**
```bash
sudo -u postgres createdb student_results_db
sudo -u postgres createuser student_results_user
sudo -u postgres psql
  ALTER USER student_results_user WITH PASSWORD 'admin123';
  GRANT ALL PRIVILEGES ON DATABASE student_results_db TO student_results_user;
  \q
```

3. **Configure .env for production**
```env
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DB_ENGINE=django.db.backends.postgresql
DB_NAME=student_results_db
DB_USER=student_results_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

4. **Install and configure Gunicorn**
```bash
pip install gunicorn
```

5. **Setup systemd service**
```bash
sudo cp student_results.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start student_results
sudo systemctl enable student_results
```

6. **Configure Nginx**
```bash
sudo cp nginx.conf /etc/nginx/sites-available/student_results
sudo ln -s /etc/nginx/sites-available/student_results /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

7. **Setup SSL with Let's Encrypt (recommended)**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

## Performance Optimization

- **WhiteNoise**: Serves static files efficiently
- **Database indexing**: Primary keys and foreign keys indexed
- **Query optimization**: select_related() and prefetch_related()
- **Rate limiting**: Prevents abuse
- **Compressed static files**: Gzip compression enabled
- **Target**: Page load < 1 second
- **Expected capacity**: ~4000 students

## Security Best Practices

1. **Never commit .env file** - Use .env.example template
2. **Use strong SECRET_KEY** - Generate new for production
3. **Enable HTTPS** - Use SSL certificates
4. **Set DEBUG=False** in production
5. **Configure ALLOWED_HOSTS** properly
6. **Use PostgreSQL** in production (not SQLite)
7. **Regular backups** of database
8. **Monitor logs** for suspicious activity
9. **Keep dependencies updated**
10. **Use environment variables** for all secrets

## API Endpoints

### Public
- `/` - Home page with result query form
- `/results/download/<usn>/<semester>/` - PDF download

### Admin (Login Required)
- `/accounts/login/` - Admin login
- `/accounts/logout/` - Logout
- `/admin-panel/` - Admin dashboard
- `/admin-panel/upload/` - Bulk upload
- `/admin-panel/analytics/` - Analytics
- `/admin-panel/edit/<id>/` - Edit result

## Customization

### Changing Colors
Edit the CSS variables in `templates/base/base.html`:
```css
:root {
    --color-primary: #1e3a8a;
    --color-secondary: #3b82f6;
    --color-accent: #f59e0b;
}
```

### Changing Fonts
Replace Google Fonts links in `templates/base/base.html`

### Modifying Validation Rules
Edit validators in `results/models.py` and `results/forms.py`

## Troubleshooting

### Common Issues

**Issue**: reCAPTCHA not working
- **Solution**: Check RECAPTCHA_SITE_KEY and RECAPTCHA_SECRET_KEY in .env

**Issue**: Excel upload fails
- **Solution**: Verify column names match keywords (case-insensitive)
- Check first 7 rows are being skipped for results file

**Issue**: PDF generation error
- **Solution**: Ensure reportlab is installed: `pip install reportlab`

**Issue**: Static files not loading
- **Solution**: Run `python manage.py collectstatic`
- Check STATIC_ROOT and STATIC_URL in settings.py

**Issue**: Database connection error
- **Solution**: Verify PostgreSQL credentials in .env
- Ensure PostgreSQL service is running

## Testing

### Manual Testing Checklist
- [ ] Result query with valid USN + DOB
- [ ] Result query with invalid USN
- [ ] Result query with wrong DOB
- [ ] PDF download functionality
- [ ] Dark mode toggle
- [ ] Admin login/logout
- [ ] Bulk Excel upload (Results)
- [ ] Bulk Excel upload (Metadata)
- [ ] Analytics filtering
- [ ] Mobile responsiveness

### Sample Data
Create sample students and results using Django admin:
1. Access `/admin/`
2. Add students manually
3. Add student metadata
4. Add courses
5. Add results

## Support & Maintenance

### Regular Maintenance Tasks
- Backup database regularly
- Monitor disk space (media/uploads)
- Review upload history for errors
- Update dependencies monthly
- Monitor server logs
- Clear old session data

### Logs Location
- Django logs: Check console or configure file logging
- Nginx access logs: `/var/log/nginx/access.log`
- Nginx error logs: `/var/log/nginx/error.log`
- Gunicorn logs: systemd journal (`journalctl -u student_results`)

## License

This project is for educational and institutional use.

## Credits

- **Django Framework**: Web framework
- **Tailwind CSS**: UI framework
- **ReportLab**: PDF generation
- **Pandas**: Data processing
- **Google Fonts**: Typography (Crimson Pro, Work Sans)
- **Google reCAPTCHA**: Security validation

---

**Built with ❤️ using Django & Tailwind CSS**   