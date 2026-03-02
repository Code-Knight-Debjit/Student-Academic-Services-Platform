<div align="center">

# 🎓 Student Academic Services Platform

**A robust, scalable, and secure Django-based web application for managing and viewing student academic results.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0.1-green?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-3.x-38B2AC?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-Educational-purple)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen)]()
[![Run Tests](https://github.com/Code-Knight-Debjit/Student-Academic-Services-Platform/actions/workflows/test.yaml/badge.svg)](https://github.com/Code-Knight-Debjit/Student-Academic-Services-Platform/actions/workflows/test.yaml)
[![Deployment Automation](https://github.com/Code-Knight-Debjit/Student-Academic-Services-Platform/actions/workflows/deploy.yml/badge.svg)](https://github.com/Code-Knight-Debjit/Student-Academic-Services-Platform/actions/workflows/deploy.yml)

<img src="https://img.shields.io/badge/Database-SQLite%20%2F%20PostgreSQL-blue?logo=postgresql" />
<img src="https://img.shields.io/badge/Deployment-Nginx%20%2B%20Gunicorn-orange?logo=nginx" />
<img src="https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?logo=github-actions&logoColor=white" />
<img src="https://img.shields.io/badge/Containerized-Docker%20%2B%20Docker%20Compose-2496ED?logo=docker&logoColor=white" />

</div>

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Live Demo](#-live-demo)
- [Features](#-features)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Database Models](#-database-models)
- [API Endpoints](#-api-endpoints)
- [Installation & Setup](#-installation--setup)
- [Environment Variables](#-environment-variables)
- [Google reCAPTCHA Setup](#-google-recaptcha-setup)
- [Excel Upload Formats](#-excel-upload-formats)
- [User Roles & Permissions](#-user-roles--permissions)
- [🐳 Docker & Containerization](#-docker--containerization)
- [⚙️ CI/CD Pipeline — GitHub Actions](#%EF%B8%8F-cicd-pipeline--github-actions)
- [Production Deployment](#-production-deployment)
- [Performance Optimization](#-performance-optimization)
- [Security](#-security)
- [Customization](#-customization)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Maintenance](#-maintenance)
- [Contributing](#-contributing)
- [Credits](#-credits)
- [License](#-license)

---

## 🧭 Overview

The **Student Academic Services Platform** is a full-stack web application built for educational institutions to streamline the process of managing and displaying student academic results. It provides a clean, public-facing portal where students can look up their results using their USN (University Seat Number), Date of Birth, and Semester — all without needing an account. Behind the scenes, admins and professors can bulk-upload Excel/CSV data, track upload history, and dive into rich analytics.

The platform was built with scalability and security at the forefront — capable of handling approximately **4,000+ students** with sub-second page load times.

---

## 🌐 Live Demo

> *https://debjit-paul.me/*

---

## ✨ Features

### 🔓 Public Features
| Feature | Description |
|---|---|
| 🔍 Result Lookup | Students search using USN + Date of Birth + Semester |
| 📄 PDF Export | Professional PDF download of individual result cards |
| 🌙 Dark Mode | Smooth toggle between light and dark themes |
| 📱 Responsive Design | Fully optimized for mobile, tablet, and desktop |
| ⏳ Skeleton Loader | Loading placeholder shown for responses > 1 second |
| 🔒 reCAPTCHA v2 | Google reCAPTCHA integration to prevent bots |
| ⏰ Session Management | Automatic session expiration for security |

### 🛠️ Admin Features
| Feature | Description |
|---|---|
| 📤 Bulk Upload | Upload Results and Metadata via Excel/CSV files |
| ✏️ Individual Editing | Edit any student result record directly |
| 📊 Analytics Dashboard | Visual breakdown of academic performance |
| 📈 Semester Statistics | Aggregated stats by semester |
| 🛣️ Admission Route Analysis | COMEDK / KCET / Management breakdowns |
| 🏆 Top Performers | Track highest scorers per course/semester |
| 📚 Course-wise Metrics | Performance analysis per course |
| 🗂️ Upload History | Full log of all uploaded files with status |

### 🔐 Security Features
| Feature | Description |
|---|---|
| 🚦 Rate Limiting | Prevents brute force and API abuse |
| 🤖 reCAPTCHA | Bot protection on public queries |
| 🔑 Environment Variables | All secrets stored in `.env`, never in code |
| 🛡️ CSRF Protection | Django built-in CSRF tokens on all forms |
| 💉 SQL Injection Prevention | Django ORM parameterized queries |
| 🧱 XSS Protection | Template auto-escaping + secure headers |
| 🔐 Secure Sessions | HTTPOnly, SameSite cookie configuration |

---

## 🧰 Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Django 5.0.1 |
| **Frontend** | Tailwind CSS 3.x (via CDN) |
| **Database (Dev)** | SQLite |
| **Database (Prod)** | PostgreSQL 15 |
| **PDF Generation** | ReportLab |
| **Data Processing** | Pandas, NumPy, OpenPyXL |
| **Web Server** | Nginx |
| **WSGI Server** | Gunicorn (5 workers, 2 threads) |
| **Static Files** | WhiteNoise |
| **Containerization** | Docker + Docker Compose |
| **Tunnel / Ingress** | Cloudflare Tunnel (`cloudflared`) |
| **CI/CD** | GitHub Actions (2 workflows) |
| **Test Coverage** | `coverage.py` (≥ 70% enforced) |
| **Fonts** | Crimson Pro (headers) · Work Sans (body) via Google Fonts |
| **Security** | Google reCAPTCHA v2 |

---

## 📁 Project Structure

```
student_results_system/
│
├── student_results/              # 🏠 Main Django project config
│   ├── __init__.py
│   ├── settings.py               # Project settings (env-based)
│   ├── urls.py                   # Root URL configuration
│   └── wsgi.py                   # WSGI entry point
│
├── core/                         # 🌐 Core app — landing & home page
│   ├── urls.py
│   └── views.py
│
├── results/                      # 📋 Results app — core functionality
│   ├── models.py                 # Database models (Student, Result, etc.)
│   ├── views.py                  # View functions & logic
│   ├── forms.py                  # Form definitions & validation
│   ├── admin.py                  # Django admin customizations
│   ├── utils.py                  # Excel/CSV processing utilities
│   ├── pdf_generator.py          # PDF generation with ReportLab
│   └── urls.py                   # Results app URL routes
│
├── accounts/                     # 🔐 Authentication app
│   ├── views.py                  # Login/logout views
│   └── urls.py
│
├── templates/                    # 🎨 HTML templates
│   ├── base/
│   │   └── base.html             # Base layout with Tailwind + fonts
│   ├── results/
│   │   ├── home.html             # Result query form
│   │   └── result_view.html      # Result display page
│   ├── accounts/
│   │   └── login.html            # Admin login page
│   └── admin_panel/
│       ├── dashboard.html        # Admin overview
│       ├── bulk_upload.html      # File upload interface
│       └── analytics.html        # Analytics & charts
│
├── static/                       # 📦 Static assets (CSS, JS, images)
├── media/                        # 📂 User-uploaded files
│
├── requirements.txt              # Python dependencies
├── manage.py                     # Django management CLI
├── .env.example                  # Environment variable template
├── gunicorn_config.py            # Gunicorn WSGI configuration
├── nginx.conf                    # Nginx reverse proxy configuration
└── student_results.service       # Systemd service unit file
```

---

## 🗄️ Database Models

### `Student`
Stores core student identity information.

| Field | Type | Description |
|---|---|---|
| `usn` | CharField (PK, 10 chars) | University Seat Number |
| `name` | CharField | Full name of the student |
| `department` | CharField | Department/branch |
| `semester` | IntegerField | Current semester |

---

### `StudentMetadata`
Extended metadata linked to each student (one-to-one).

| Field | Type | Description |
|---|---|---|
| `student` | OneToOneField → Student | Links to Student |
| `dob` | DateField | Date of Birth (used for authentication) |
| `admission_route` | CharField | COMEDK / KCET / Management |

---

### `Course`
Represents individual courses/subjects.

| Field | Type | Description |
|---|---|---|
| `course_code` | CharField (Unique) | Unique subject code |
| `course_title` | CharField | Full name of the course |
| `semester` | IntegerField | Semester this course belongs to |
| `credits` | IntegerField | Credit weightage |

---

### `Result`
Stores individual student result per course.

| Field | Type | Description |
|---|---|---|
| `student` | ForeignKey → Student | Related student |
| `course` | ForeignKey → Course | Related course |
| `final_cie_marks` | FloatField | Continuous Internal Evaluation marks |
| `marks_in_words` | CharField | Verbal description of marks |
| `academic_year` | CharField | e.g., "2023-24" |
| `scheme` | CharField | Academic scheme |
| `semester` | IntegerField | Semester |

> **Constraint**: `(student, course)` pair must be unique.

---

### `UploadHistory`
Tracks all bulk upload events.

| Field | Type | Description |
|---|---|---|
| `file_name` | CharField | Name of the uploaded file |
| `uploaded_at` | DateTimeField | Timestamp |
| `processed` | IntegerField | Total rows processed |
| `created` | IntegerField | New records created |
| `updated` | IntegerField | Existing records updated |
| `skipped` | IntegerField | Rows skipped |
| `errors` | TextField | Error log (if any) |

---

## 🌐 API Endpoints

### Public Routes

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Home page with result query form |
| `POST` | `/` | Submit USN + DOB + Semester for result |
| `GET` | `/results/download/<usn>/<semester>/` | Download result as PDF |

### Admin Routes *(Login Required)*

| Method | Endpoint | Description |
|---|---|---|
| `GET/POST` | `/accounts/login/` | Admin login |
| `GET` | `/accounts/logout/` | Logout and end session |
| `GET` | `/admin-panel/` | Admin dashboard |
| `GET/POST` | `/admin-panel/upload/` | Bulk Excel/CSV upload |
| `GET` | `/admin-panel/analytics/` | Analytics and statistics view |
| `GET/POST` | `/admin-panel/edit/<id>/` | Edit individual result record |

---

## ⚙️ Installation & Setup

### Prerequisites

Make sure you have the following installed:

- **Python** 3.10+
- **pip**
- **virtualenv** (recommended)
- **PostgreSQL** (for production only)
- **Git**

---

### 🖥️ Local Development Setup

**Step 1 — Clone the repository**
```bash
git clone https://github.com/Code-Knight-Debjit/Student-Academic-Services-Platform.git
cd Student-Academic-Services-Platform
```

**Step 2 — Create and activate a virtual environment**
```bash
python3 -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

**Step 3 — Install dependencies**
```bash
pip install -r requirements.txt
```

**Step 4 — Configure environment variables**
```bash
cp .env.example .env
# Open .env and fill in your values
```

**Step 5 — Apply database migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

**Step 6 — Create a superuser (admin account)**
```bash
python manage.py createsuperuser
```

**Step 7 — Collect static files**
```bash
python manage.py collectstatic --noinput
```

**Step 8 — Start the development server**
```bash
python manage.py runserver
```

> 🌐 Open your browser and navigate to: **http://localhost:8000**

---

## 🔑 Environment Variables

Create a `.env` file based on `.env.example`. Here's a description of each variable:

```env
# Django Core
SECRET_KEY=your-very-secret-key-here
DEBUG=True                          # Set to False in production
ALLOWED_HOSTS=localhost,127.0.0.1   # Add your domain in production

# Google reCAPTCHA
RECAPTCHA_SITE_KEY=your-recaptcha-site-key
RECAPTCHA_SECRET_KEY=your-recaptcha-secret-key

# Database (SQLite by default for dev; PostgreSQL for prod)
DB_ENGINE=django.db.backends.sqlite3
# DB_ENGINE=django.db.backends.postgresql
DB_NAME=db.sqlite3
# DB_NAME=student_results_db
# DB_USER=student_results_user
# DB_PASSWORD=yourpassword
# DB_HOST=localhost
# DB_PORT=5432
```

> ⚠️ **Never commit your `.env` file to version control.** It is listed in `.gitignore` by default.

---

## 🤖 Google reCAPTCHA Setup

1. Visit the [Google reCAPTCHA Admin Console](https://www.google.com/recaptcha/admin)
2. Click **+ Create** and register a new site
3. Choose **reCAPTCHA v2** → "I'm not a robot" Checkbox
4. Add your domains:
   - `localhost` for local development
   - Your production domain for live deployment
5. Copy the **Site Key** and **Secret Key**
6. Paste them into your `.env` file:
   ```
   RECAPTCHA_SITE_KEY=xxxxxx
   RECAPTCHA_SECRET_KEY=xxxxxx
   ```

---

## 📊 Excel Upload Formats

### Results File

- **Skip first 7 rows** — Row 8 is treated as the header row.
- Column names are matched using **case-insensitive keyword matching**.

| Column | Keyword Match | Required |
|---|---|---|
| USN | contains `"usn"` | ✅ Yes |
| Student Name | contains `"name"` | ✅ Yes |
| Course Title | contains `"course"` | ✅ Yes |
| Final CIE Marks | contains `"final cie"` or `"cie"` | ❌ Optional |
| Marks in Words | contains `"words"` | ❌ Optional |

---

### Metadata File

| Column | Keyword Match | Required |
|---|---|---|
| USN | contains `"usn"` | ✅ Yes |
| Date of Birth | contains `"dob"` | ✅ Yes |
| Admission Route | contains `"route"` or `"admission"` | ❌ Optional |

---

### Upload Rules

| Rule | Details |
|---|---|
| **USN Format** | Exactly 10 alphanumeric characters |
| **DOB Format** | `YYYY-MM-DD` or `DD/MM/YYYY` |
| **Missing Metadata** | Auto-created with default DOB `2006-01-01` |
| **Duplicate Subjects** | Overwrites existing record |
| **Metadata Re-upload** | Replaces existing metadata |
| **Max File Size** | 10 MB |

---

## 👥 User Roles & Permissions

### 🧑‍🎓 Public Users (No Login Required)
- Search for results using **USN + Date of Birth + Semester**
- Must pass **Google reCAPTCHA** validation
- Download result as a **PDF**
- Sessions expire automatically

### 👨‍💼 Admin / Professor (Superuser Login Required)
- Access the **admin dashboard**
- **Bulk upload** Results and Metadata via Excel/CSV
- **Edit** individual student result records
- View **analytics** filtered by semester, course, and admission route
- Browse **upload history** with per-upload success/error breakdown

---

---

## 🐳 Docker & Containerization

This project is fully containerized using **Docker** and orchestrated with **Docker Compose**, enabling consistent environments across development, CI, and production.

### Container Architecture

The `docker-compose.yml` defines a **four-service stack**:

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose Stack                  │
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────┐  │
│  │ postgres │───▶│   web    │───▶│      nginx       │  │
│  │  :5432   │    │  :8000   │    │       :80        │  │
│  └──────────┘    └──────────┘    └──────────────────┘  │
│                                          │              │
│                                  ┌───────────────┐      │
│                                  │  cloudflared  │      │
│                                  │   (tunnel)    │      │
│                                  └───────────────┘      │
└─────────────────────────────────────────────────────────┘
```

| Service | Image | Role |
|---|---|---|
| `db` | `postgres:15` | PostgreSQL database with persistent volume |
| `web` | Custom (built from `Dockerfile`) | Django + Gunicorn WSGI server |
| `nginx` | `nginx:latest` | Reverse proxy + static file serving |
| `cloudflared` | `cloudflare/cloudflared:latest` | Cloudflare Tunnel for secure public access |

---

### Dockerfile

The application image is built from `python:3.12-slim`:

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client curl build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app/
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "student_results.wsgi:application"]
```

Key design decisions:
- Uses `python:3.12-slim` to minimize image size
- `PYTHONDONTWRITEBYTECODE` and `PYTHONUNBUFFERED` for clean container logging
- Static files collected at **build time** so Nginx can serve them directly
- Gunicorn runs as the WSGI server (not the Django dev server)

---

### Running with Docker Compose

**Start the full stack:**
```bash
docker compose up -d --build
```

**Check service health:**
```bash
docker compose ps
```

**View live logs:**
```bash
docker compose logs -f web
docker compose logs -f nginx
```

**Stop all services:**
```bash
docker compose down
```

**Tear down including volumes (⚠️ deletes database data):**
```bash
docker compose down -v
```

---

### Service Health Checks

All services include built-in health checks to ensure dependency ordering works correctly:

| Service | Health Check Command | Interval | Retries |
|---|---|---|---|
| `db` | `pg_isready -U ${DB_USER}` | 10s | 5 |
| `web` | `curl -f http://localhost:8000` | 15s | 5 |
| `nginx` | `curl -f http://localhost` | 15s | 5 |
| `cloudflared` | `cloudflared tunnel info <id>` | 30s | 3 |

The `web` service waits for `db` to be **healthy** before starting — preventing startup race conditions.

---

### Superuser Auto-Creation

The `web` container automatically creates a superuser on first boot using environment variables:

```env
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=yourpassword
DJANGO_SUPERUSER_EMAIL=admin@example.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD=yourpassword
ADMIN_EMAIL=admin@example.com
```

> The `|| true` ensures the container doesn't fail if the superuser already exists on subsequent deploys.

---

### Cloudflare Tunnel

The stack includes a **Cloudflare Tunnel** (`cloudflared`) service that exposes the application to the public internet **without requiring open firewall ports**. This provides:

- Zero-trust network access
- Automatic HTTPS without managing SSL certificates separately
- DDoS protection via Cloudflare's network

The tunnel connects through the Nginx proxy, so the full request path is:

```
Internet → Cloudflare Edge → cloudflared tunnel → nginx:80 → web:8000 → Django
```

---

## ⚙️ CI/CD Pipeline — GitHub Actions

This project implements a **fully automated CI/CD pipeline** using GitHub Actions with two distinct workflows that run in parallel on every push to `master`.

### Pipeline Overview

```
┌──────────────────────────────────────────────────────────────┐
│                   git push → master                          │
└───────────────────────┬──────────────────────────────────────┘
                        │ triggers both workflows simultaneously
          ┌─────────────┴─────────────┐
          ▼                           ▼
┌─────────────────┐         ┌──────────────────────┐
│   Run Tests     │         │ Deployment Automation │
│  (test.yaml)    │         │   (deploy.yml)        │
│                 │         │                       │
│ ubuntu-latest   │         │   self-hosted runner  │
│                 │         │  (production server)  │
│ ~1 min          │         │  ~3-5 min             │
└─────────────────┘         └──────────────────────┘
```

---

### Workflow 1 — Run Tests (`test.yaml`)

**Trigger:** Push to `master` or `develop`, or any Pull Request targeting `master`

**Runner:** `ubuntu-latest` (GitHub-hosted)

**Purpose:** Validate code correctness, run the Django test suite, and enforce a minimum code coverage threshold before any merge or deploy.

#### Full Workflow

```yaml
name: Run Tests

on:
  push:
    branches:
      - master
      - develop
  pull_request:
    branches:
      - master

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    env:
      DB_NAME: test_db
      DB_USER: test_user
      DB_PASSWORD: test_password
      DB_HOST: localhost
      DB_PORT: 5432
      SECRET_KEY: test-secret-key-for-ci-only
      DEBUG: "True"
      RAZORPAY_KEY_ID: dummy_key
      RAZORPAY_KEY_SECRET: dummy_secret

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Wait for PostgreSQL
        run: |
          until pg_isready -h localhost -p 5432 -U test_user; do
            echo "Waiting for postgres..."
            sleep 2
          done

      - name: Run migrations
        run: python manage.py migrate

      - name: Run tests with coverage
        run: |
          pip install coverage
          coverage run manage.py test results.tests --verbosity=2
          coverage report --fail-under=70

      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: coverage-report
          path: coverage.xml

      - name: Notify on failure
        if: failure()
        run: echo "::error::Tests failed! Check the logs above."
```

#### Step-by-Step Breakdown

| Step | What It Does |
|---|---|
| **Checkout code** | Pulls the latest commit into the runner |
| **Set up Python 3.11** | Installs Python with `pip` caching for speed |
| **Install dependencies** | Installs all packages from `requirements.txt` |
| **Wait for PostgreSQL** | Polls `pg_isready` until the test DB service is accepting connections |
| **Run migrations** | Applies all Django migrations against the ephemeral test PostgreSQL instance |
| **Run tests with coverage** | Executes `results.tests` with `--verbosity=2` and enforces **≥ 70% code coverage** |
| **Upload coverage report** | Saves `coverage.xml` as a GitHub Actions artifact (even on failure) |
| **Notify on failure** | Emits a GitHub Actions error annotation if any step fails |

#### Key CI Design Decisions

- **Ephemeral PostgreSQL service container** — Tests run against a real Postgres 15 instance, not SQLite, matching the production database engine. This prevents false positives from SQLite-specific behavior.
- **Health-checked DB startup** — The workflow polls `pg_isready` in a loop before running migrations, preventing flaky failures from race conditions at container startup.
- **Coverage threshold enforcement** — `coverage report --fail-under=70` causes the CI job to fail if coverage drops below 70%, acting as a quality gate.
- **Artifact upload with `if: always()`** — The coverage XML is uploaded regardless of whether tests pass or fail, so coverage data is always available for investigation.
- **Pip caching** — `cache: "pip"` on the Python setup step significantly reduces install time on repeated runs.
- **Dummy secrets for third-party services** — `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` are stubbed out with dummy values so tests don't require real payment credentials.

#### Coverage Configuration (`.coveragerc`)

```ini
[run]
source = results

[report]
omit =
    results/admin.py
    results/views_backup.py
    results/pdf_generator.py
    results/utils.py
    results/services/*
    results/signals.py
    results/views.py
    results/forms.py
```

Coverage is scoped to the `results` app and deliberately omits backup files, utility modules, and complex view/form logic — focusing coverage measurement on core business logic in the models and test suite.

---

### Workflow 2 — Deployment Automation (`deploy.yml`)

**Trigger:** Push to `master` only

**Runner:** `self-hosted` (the production server itself acts as the runner)

**Purpose:** Automatically deploy the latest code to the production server by SSHing in, pulling the new code, and rebuilding the Docker Compose stack — all without any manual intervention.

#### Full Workflow

```yaml
name: Deployment Automation

on:
  push:
    branches:
      - master

jobs:
  deploy:
    runs-on: self-hosted

    steps:
      - name: Checkout
        uses: actions/checkout@v3

      - name: Setup SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_ed25519
          chmod 600 ~/.ssh/id_ed25519
          ssh-keyscan -H ${{ secrets.SERVER_HOST }} >> ~/.ssh/known_hosts

      - name: Ensure Docker Compose v2
        run: |
          docker --version
          docker compose version || (sudo apt-get update && sudo apt-get install -y docker-compose-plugin)

      - name: Deploy
        run: |
          ssh ${{ secrets.SERVER_USER }}@${{ secrets.SERVER_HOST }} << 'EOF'
          set -e
          cd /home/code_knight_debjit/Student-Academic-Services-Platform

          echo "Pulling latest code..."
          git pull origin master

          echo "Rebuilding containers..."
          docker compose up -d --build --force-recreate

          echo "Checking container health..."
          sleep 10
          docker compose ps

          echo "Cleaning unused images..."
          docker system prune -f
          EOF

      - name: Notify on failure
        if: failure()
        run: echo "Deployment failed! Check logs in the local server."
```

#### Step-by-Step Breakdown

| Step | What It Does |
|---|---|
| **Checkout** | Checks out the repository on the self-hosted runner |
| **Setup SSH** | Writes the private key from GitHub Secrets to `~/.ssh/id_ed25519` and adds the server to `known_hosts` to avoid host verification prompts |
| **Ensure Docker Compose v2** | Verifies Docker Compose v2 (`docker compose`) is installed; installs it if missing |
| **Deploy via SSH** | Opens an SSH session into the production server and runs the full deployment sequence |
| **git pull** | Fetches the latest `master` from GitHub |
| **docker compose up --build** | Rebuilds all Docker images and recreates all containers with `--force-recreate` to ensure no stale state |
| **docker compose ps** | Prints container health status after a 10-second warm-up period |
| **docker system prune** | Cleans up unused images and dangling layers to reclaim disk space |
| **Notify on failure** | Logs an error annotation if any step fails |

#### Key CD Design Decisions

- **Self-hosted runner on the production server** — By using `runs-on: self-hosted`, the deployment job executes directly on the production machine. This eliminates the need for a separate deployment server or cloud-provider-specific deploy action.
- **SSH with secrets** — `SSH_PRIVATE_KEY`, `SERVER_HOST`, and `SERVER_USER` are stored as GitHub repository secrets and never hardcoded. The private key is written with `chmod 600` to satisfy SSH security requirements.
- **`set -e` in the SSH heredoc** — Causes the entire remote script to exit immediately on any error, ensuring partial deployments don't leave the application in a broken state.
- **`--force-recreate`** — Guarantees all containers are torn down and rebuilt fresh, even if the image hash hasn't changed. This ensures environment variables, volumes, and configs are always up to date.
- **Automatic Docker cleanup** — `docker system prune -f` runs post-deploy to prevent disk exhaustion on long-running servers.
- **Cloudflare Tunnel remains active during deploy** — Since `cloudflared` is a separate container managed by Docker Compose, it stays running during the app container rebuild, providing near-zero-downtime deploys.

---

### Required GitHub Secrets

Navigate to **Settings → Secrets and variables → Actions** in your repository and add:

| Secret Name | Description |
|---|---|
| `SSH_PRIVATE_KEY` | Private SSH key (ed25519) with access to the production server |
| `SERVER_HOST` | IP address or hostname of the production server |
| `SERVER_USER` | SSH username on the production server |

> Generate a dedicated deploy key: `ssh-keygen -t ed25519 -C "github-actions-deploy"` and add the public key to `~/.ssh/authorized_keys` on the server.

---

### Setting Up the Self-Hosted Runner

On your production server:

```bash
# 1. Go to: GitHub Repo → Settings → Actions → Runners → New self-hosted runner
# 2. Select: Linux / x64
# 3. Follow the GitHub-provided instructions, then:

# Run as a background service
sudo ./svc.sh install
sudo ./svc.sh start

# Verify it's online
sudo ./svc.sh status
```

The runner will appear as **Online** in your repository's Actions settings once registered.

---

### Complete CI/CD Flow (End to End)

```
Developer pushes to master
         │
         ▼
┌─────────────────────────────────┐
│  GitHub receives the push event │
└─────────────┬───────────────────┘
              │ triggers
    ┌─────────┴──────────┐
    ▼                    ▼
Run Tests            Deployment Automation
(ubuntu-latest)      (self-hosted runner)
    │                    │
    │ Spin up             │ Checkout repo
    │ postgres:15         │ Setup SSH keys
    │ service             │ Verify Docker
    │                    │ Compose v2
    │ pip install         │
    │ requirements        │ SSH into server
    │                    │ git pull master
    │ migrate             │
    │                    │ docker compose up
    │ coverage run        │ --build
    │ tests               │ --force-recreate
    │                    │
    │ coverage ≥ 70%?     │ docker compose ps
    │                    │
    │ upload artifact     │ docker system prune
    │                    │
    ▼                    ▼
  ✅ Pass or ❌ Fail    ✅ Deployed or ❌ Error
```

Both workflows run **concurrently** — tests validate correctness in a clean environment while deployment proceeds to production. If the deployment job fails, the `Notify on failure` step logs the error and the runner surfaces it in the GitHub Actions UI.

---

## 🚀 Production Deployment

### Using Nginx + Gunicorn on Ubuntu

**Step 1 — Install system dependencies**
```bash
sudo apt update
sudo apt install python3-pip python3-venv nginx postgresql postgresql-contrib -y
```

**Step 2 — Set up PostgreSQL**
```bash
sudo -u postgres createdb student_results_db
sudo -u postgres createuser student_results_user
sudo -u postgres psql

# Inside psql prompt:
ALTER USER student_results_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE student_results_db TO student_results_user;
\q
```

**Step 3 — Configure production `.env`**
```env
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DB_ENGINE=django.db.backends.postgresql
DB_NAME=student_results_db
DB_USER=student_results_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432
```

**Step 4 — Install and run Gunicorn**
```bash
pip install gunicorn
gunicorn --config gunicorn_config.py student_results.wsgi:application
```

**Step 5 — Set up systemd service**
```bash
sudo cp student_results.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start student_results
sudo systemctl enable student_results
```

**Step 6 — Configure Nginx**
```bash
sudo cp nginx.conf /etc/nginx/sites-available/student_results
sudo ln -s /etc/nginx/sites-available/student_results /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**Step 7 — Enable HTTPS with Let's Encrypt (Recommended)**
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

---

## ⚡ Performance Optimization

| Optimization | Detail |
|---|---|
| **WhiteNoise** | Efficient static file serving without Nginx overhead |
| **Database Indexing** | Primary keys and foreign keys are indexed |
| **Query Optimization** | `select_related()` and `prefetch_related()` used throughout |
| **Rate Limiting** | Prevents spamming and reduces server load |
| **Gzip Compression** | Enabled for static file delivery |
| **Target Load Time** | < 1 second per page |
| **Expected Capacity** | ~4,000 students |

---

## 🔒 Security

This project follows Django security best practices:

1. **Never commit `.env`** — Use `.env.example` as a template only
2. **Generate a strong `SECRET_KEY`** for production using:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
3. **Set `DEBUG=False`** in production
4. **Configure `ALLOWED_HOSTS`** with only your actual domains
5. **Use PostgreSQL** instead of SQLite in production
6. **Enable HTTPS** using SSL/TLS certificates (Let's Encrypt recommended)
7. **Monitor logs** for suspicious activity patterns
8. **Keep dependencies updated** regularly:
   ```bash
   pip list --outdated
   pip install --upgrade <package>
   ```
9. **Back up the database** regularly (daily recommended)
10. **Clear old sessions** periodically:
    ```bash
    python manage.py clearsessions
    ```

---

## 🎨 Customization

### Changing Brand Colors

Edit the CSS variables in `templates/base/base.html`:

```css
:root {
    --color-primary:   #1e3a8a;   /* Deep blue — headers, buttons */
    --color-secondary: #3b82f6;   /* Medium blue — links, accents */
    --color-accent:    #f59e0b;   /* Amber — highlights, badges */
}
```

### Changing Fonts

Replace the Google Fonts `<link>` tags in `templates/base/base.html` with your preferred font family URLs from [fonts.google.com](https://fonts.google.com).

### Modifying Validation Rules

- **Model-level** validation: `results/models.py`
- **Form-level** validation: `results/forms.py`
- **USN format**, **DOB rules**, and **semester ranges** can all be adjusted here.

### Adjusting Upload Behavior

Edit `results/utils.py` to modify:
- Row-skip logic (currently 7 rows)
- Column keyword matching patterns
- Duplicate handling behavior
- File size limits

---

## 🧪 Testing

### ✅ Manual Testing Checklist

**Public Functionality**
- [ ] Result query with valid USN + DOB + Semester
- [ ] Result query with invalid USN (error handling)
- [ ] Result query with incorrect DOB (auth failure)
- [ ] PDF download of results
- [ ] Dark mode toggle
- [ ] Mobile responsiveness (check on 375px viewport)
- [ ] Skeleton loader appears for slow responses
- [ ] reCAPTCHA challenge works correctly

**Admin Functionality**
- [ ] Admin login with valid credentials
- [ ] Admin login with invalid credentials (error handling)
- [ ] Bulk Excel upload — Results file
- [ ] Bulk Excel upload — Metadata file
- [ ] Viewing upload history
- [ ] Editing an individual result
- [ ] Analytics page filtering by semester
- [ ] Analytics page filtering by course
- [ ] Analytics page filtering by admission route
- [ ] Admin logout

---

### 📂 Loading Sample Data

You can add sample data through Django Admin:

1. Navigate to `/admin/`
2. Log in with your superuser credentials
3. Add entries for:
   - **Students** → USN, Name, Department, Semester
   - **Student Metadata** → DOB, Admission Route
   - **Courses** → Code, Title, Semester, Credits
   - **Results** → Student + Course + CIE Marks

---

## 🔧 Troubleshooting

| Problem | Likely Cause | Solution |
|---|---|---|
| reCAPTCHA not working | Wrong keys in `.env` | Verify `RECAPTCHA_SITE_KEY` and `RECAPTCHA_SECRET_KEY` |
| Excel upload fails | Column name mismatch | Check keywords (case-insensitive) match expected patterns |
| PDF generation error | Missing ReportLab | Run `pip install reportlab` |
| Static files not loading | `collectstatic` not run | Run `python manage.py collectstatic` |
| Database connection error | Wrong PostgreSQL config | Verify credentials in `.env` and ensure PostgreSQL is running |
| `ALLOWED_HOSTS` error | Host not in list | Add your domain/IP to `ALLOWED_HOSTS` in `.env` |
| Migrations not applying | Out-of-sync migrations | Run `makemigrations` then `migrate` |

---

## 🛠️ Maintenance

### Regular Tasks

| Frequency | Task |
|---|---|
| Daily | Database backup |
| Weekly | Review upload history for errors |
| Monthly | Update Python dependencies |
| Monthly | Monitor disk usage in `media/` directory |
| As needed | Clear expired sessions: `python manage.py clearsessions` |

### Log Locations

| Log | Path |
|---|---|
| Django | Console output or configured file logger |
| Nginx Access | `/var/log/nginx/access.log` |
| Nginx Error | `/var/log/nginx/error.log` |
| Gunicorn | `journalctl -u student_results` |

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository
2. **Create a branch** for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Commit** your changes with clear messages:
   ```bash
   git commit -m "feat: add export to CSV functionality"
   ```
4. **Push** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
5. Open a **Pull Request** on GitHub

### Commit Message Convention
This project follows [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` — A new feature
- `fix:` — A bug fix
- `docs:` — Documentation changes
- `style:` — Formatting, no logic change
- `refactor:` — Code restructuring
- `test:` — Adding/updating tests
- `chore:` — Build process or dependency updates

---

## 🙏 Credits

| Library / Tool | Purpose |
|---|---|
| [Django](https://www.djangoproject.com/) | Web framework |
| [Tailwind CSS](https://tailwindcss.com/) | Utility-first CSS framework |
| [ReportLab](https://www.reportlab.com/) | PDF generation |
| [Pandas](https://pandas.pydata.org/) | Excel/CSV data processing |
| [NumPy](https://numpy.org/) | Numerical operations |
| [OpenPyXL](https://openpyxl.readthedocs.io/) | Excel file reading |
| [WhiteNoise](http://whitenoise.evans.io/) | Static file serving |
| [Gunicorn](https://gunicorn.org/) | Python WSGI HTTP Server |
| [Nginx](https://nginx.org/) | High-performance reverse proxy |
| [Docker](https://www.docker.com/) | Application containerization |
| [Docker Compose](https://docs.docker.com/compose/) | Multi-container orchestration |
| [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) | Zero-trust secure public ingress |
| [GitHub Actions](https://github.com/features/actions) | CI/CD automation (test + deploy) |
| [coverage.py](https://coverage.readthedocs.io/) | Python test coverage measurement |
| [Google Fonts](https://fonts.google.com/) | Crimson Pro + Work Sans typography |
| [Google reCAPTCHA](https://www.google.com/recaptcha/) | Bot protection |

---

## 📄 License

This project is intended for **educational and institutional use**.  
Please refer to your institution's policies before deploying in a production environment.

---

<div align="center">

**Built with ❤️ using Django & Tailwind CSS**

[![GitHub](https://img.shields.io/badge/GitHub-Code--Knight--Debjit-black?logo=github)](https://github.com/Code-Knight-Debjit/Student-Academic-Services-Platform)

</div>
