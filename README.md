# 🏛️ CivicPulse (NagarVani) - Production Civic Complaint Reporting & Resolution Platform

A complete, production-ready, full-stack civic grievance reporting, intelligent auto-routing, and municipal field resolution platform built with **Python 3.12+**, **Streamlit**, **SQLAlchemy 2.0**, **PostgreSQL**, and **Pydantic**.

---

## 🌟 Key Features

1. **2-Minute Citizen Reporting Wizard**:
   - Dynamic Category Selection (Garbage, Sewage, Drainage, Water Leakage, Potholes, Streetlights, Flooding, Public Sanitation, Illegal Dumping, Damaged Infrastructure).
   - Problem Details & Severity estimation.
   - Multi-image & video upload validation with device camera capture support (`st.camera_input`).
   - Interactive Leaflet/Folium map with click-to-pin, search address, and automatic Indian reverse-geocoding.
   - Proactive geospatial duplicate detection alert before submission.
   - Formatted Unique Complaint ID: `CIV-2026-NNNNNN`.

2. **Decoupled 3-Tier Clean Architecture**:
   - **Presentation Layer**: Streamlit Multi-Page UI (`app.py`, `pages/`).
   - **Service & Domain Layer**: Pure Python services (`AuthService`, `ComplaintService`, `RoutingService`, `SLAService`, `DuplicateDetectionService`, `AIService`, `StorageService`, `LocationService`, `NotificationService`, `AnalyticsService`, `AuditService`, `MockGovernmentIntegrationService`). Can easily be wrapped with a FastAPI/React frontend without rewriting business logic!
   - **Data Layer**: SQLAlchemy 2.0 ORM with PostgreSQL and SQLite fallback support, repository patterns, Alembic migrations.

3. **Role-Based Access Control (RBAC)**:
   - `CITIZEN`: Self-registration, file complaints, track grievance timeline, add clarification messages, password reset via email OTP.
   - `OFFICER`: Department grievance queue, field triage workbench, photo evidence inspect, status transitions (`ACKNOWLEDGED` -> `IN_PROGRESS` -> `RESOLVED`), internal notes.
   - `DEPARTMENT_ADMIN`: Department oversight, officer assignment, SLA monitoring, escalation handling.
   - `SUPER_ADMIN`: System-wide governance, municipal wards & zones, departments, categories, routing rules, SLA configuration, audit trails.

4. **Dynamic Configurable Routing Engine**:
   - Database-backed rules matching Category + Ward/Zone + City to auto-route complaints directly to the responsible municipal department and local field engineer.

5. **SLA & Escalation Engine**:
   - Real-time SLA countdown badges (🟢 On Track, ⚠️ At Risk, 🚨 Overdue).
   - Automatic escalation logger for department supervisors.

6. **Civic AI Service Abstraction**:
   - Offline Heuristic NLP classifier & Google Gemini integration for category classification, severity estimation, officer briefing summaries, and geospatial duplicate detection.

7. **Public Transparency & Analytics**:
   - Open municipal data portal with Plotly charts: category breakdown, department workload, ward distribution, resolution velocity, and public resolved cases showcase.

---

## 🏗️ Project Architecture

```text
civic_complaint_platform/
├── app.py                      # Main entrypoint & Streamlit router with RBAC session state
├── pages/                      # Multi-page Streamlit Views
│   ├── 01_Home.py              # Landing page, public stats, FAQs, CTA
│   ├── 02_Report_Problem.py    # 4-step wizard: Category, Details, Media, Location, Duplicate Check
│   ├── 03_Track_Complaint.py   # Complaint status timeline, map, media, and comments
│   ├── 04_My_Complaints.py     # Citizen dashboard & grievance management
│   ├── 05_Officer_Dashboard.py # Department queue, triage, assignment, status transition
│   ├── 06_Admin_Dashboard.py   # Wards, departments, SLA, routing rules, users & audit logs
│   ├── 07_Analytics.py         # Transparency portal, category charts, ward heatmaps, SLA metrics
│   ├── 08_Notifications.py    # User notification center
│   ├── 09_Profile.py          # User profile & credentials
│   └── 10_Auth.py             # Login, registration, forgot password via email OTP
├── backend/
│   ├── config.py               # Pydantic Settings & environment variables
│   ├── database.py             # SQLAlchemy 2.0 engine, SessionLocal, lifecycle
│   ├── models/                 # Normalized SQLAlchemy 2.0 models (17 entities)
│   ├── schemas/                # Pydantic validation schemas for all inputs/outputs
│   ├── repositories/           # Decoupled data access repositories
│   ├── services/               # Core business logic services
│   └── utils/                  # Security (Argon2), Logging, Formatting, Session, Email
├── migrations/                 # Alembic migrations (env.py, versions/)
├── scripts/
│   └── seed_database.py        # Realistic Indian civic dataset (Wards, Depts, Officers, Complaints)
├── tests/                      # Comprehensive pytest test suite (22 unit & integration tests)
├── uploads/                    # Local storage directory
├── Dockerfile                  # Production container
├── docker-compose.yml          # Streamlit app + PostgreSQL 16
├── alembic.ini                 # Alembic migration config
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable blueprint
└── README.md
```

---

## ⚡ Quick Start (Local Development)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
```
*(By default, SQLite is preconfigured for instant zero-setup local testing. For PostgreSQL, set `DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/civic_db`)*

### 3. Seed Realistic Indian Civic Dataset
```bash
python scripts/seed_database.py
```

### 4. Run the Test Suite
```bash
pytest tests/ -v
```

### 5. Launch the Web Application
```bash
streamlit run app.py
```
Open your browser at: **`http://localhost:8501`**

---

## 🔑 Demo Accounts (Pre-Seeded)

| Role | Email | Password | Description |
| :--- | :--- | :--- | :--- |
| **Super Admin** | `admin@civicpulse.gov.in` | `Admin@123` | Municipal Commissioner, BMC (Full Access) |
| **Dept Admin** | `admin.sanitation@civicpulse.gov.in` | `Admin@123` | Chief Engineer, Solid Waste Management (BMC) |
| **Field Officer** | `officer.roads@civicpulse.gov.in` | `Officer@123` | AE Roads (Andheri West Ward K/West) |
| **Field Officer** | `officer.sanitation@civicpulse.gov.in` | `Officer@123` | Sanitary Inspector (Bandra West Ward H/West) |
| **Field Officer** | `officer.water@civicpulse.gov.in` | `Officer@123` | Sub-Engineer Water Works (Colaba Ward A) |
| **Citizen** | `citizen.rahul@example.com` | `Citizen@123` | Amit Deshmukh (Resident, Bandra West, Mumbai) |
| **Citizen** | `citizen.priya@example.com` | `Citizen@123` | Neha Kulkarni (Resident, Andheri West, Mumbai) |

---

## 🔑 Forgot Password Feature Guide

For dedicated instructions on setting up and testing the **Forgot Password via Email OTP** feature, see [FORGOT_PASSWORD_README.md](file:///b:/SIH2026/civic-complaint-platform/FORGOT_PASSWORD_README.md).

---

## 🐳 Docker Deployment

To launch the full stack with **PostgreSQL 16** and **CivicPulse Streamlit Web App**:

```bash
docker compose up --build
```
The application will automatically initialize the database schema, seed demo data, and start on `http://localhost:8501`.

---

## 🔒 Security Practices

- **Password Hashing**: Industry-standard **Argon2id** (`argon2-cffi`) with memory and time cost tuning.
- **Input Sanitization**: HTML tag stripping and entity escaping to prevent stored XSS.
- **File Validation**: Image header magic byte inspection using PIL to prevent executable injection via upload spoofing.
- **Path Traversal Protection**: Uploaded files stored under verified, sandboxed relative paths.
- **Audit Logging**: Immutable system audit logs for authentication, complaint creation, and status modifications.
