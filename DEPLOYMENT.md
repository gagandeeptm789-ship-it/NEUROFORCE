# The Forwarded Seal — Production Deployment Guide

This guide covers deployment procedures for **The Forwarded Seal** platform across containerized environments, cloud hosting providers (Render, Railway, Fly.io, Vercel), and managed databases (Supabase PostgreSQL).

---

## 1. Architecture Overview

- **Frontend:** React + Vite (Single Page Application, served statically or via Nginx).
- **Backend:** FastAPI (Python 3.10+, Uvicorn, OpenCV headless, Cryptography, SQLAlchemy).
- **Database:** PostgreSQL (Supabase or self-hosted PostgreSQL 15+).
- **Storage:** Local persistent disk volumes or Supabase Storage bucket (`notices`).

---

## 2. Docker & Docker Compose Deployment (Recommended)

The easiest and most reproducible deployment method uses Docker Compose.

### Prerequisites
- Docker Engine 24.0+ and Docker Compose 2.20+
- At least 2 GB RAM and 10 GB disk space on the host machine.

### Deployment Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/the-forwarded-seal.git
   cd the-forwarded-seal
   ```

2. **Configure environment variables:**
   Create `.env` based on `backend/.env.example`:
   ```bash
   cp backend/.env.example .env
   ```
   Generate secure random secrets:
   ```bash
   python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
   python -c "import secrets; print('ADMIN_REGISTRATION_SECRET=' + secrets.token_hex(24))"
   python -c "import secrets; print('POSTGRES_PASSWORD=' + secrets.token_hex(16))"
   ```
   Paste these generated values into `.env`.

3. **Build and start the multi-container stack:**
   ```bash
   docker compose up -d --build
   ```

4. **Verify running services:**
   ```bash
   docker compose ps
   docker compose logs -f backend
   ```
   Access:
   - Frontend UI: `http://localhost:3000`
   - Verification API & Swagger Docs: `http://localhost:8000/docs`
   - Healthcheck: `http://localhost:8000/health`

---

## 3. Supabase Integration Guide

The Forwarded Seal natively supports Supabase for PostgreSQL database hosting and object storage.

### A. Database Provisioning

1. Log in to [Supabase Console](https://app.supabase.com) and create a new project.
2. Under **Project Settings -> Database**, locate the **Connection string (URI)**.
   Format:
   ```text
   postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
   ```
3. Update your backend environment configuration:
   ```ini
   DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres"
   ```
4. Start the backend; tables (`admins`, `notices`) will automatically be verified and initialized via SQLAlchemy ORM.

### B. Supabase Storage Setup (Optional)

1. Under **Storage -> Buckets**, create a new bucket named `notices`.
2. Configure bucket access policies according to institutional privacy requirements:
   - **Public Read:** Enabled if public notices should be downloadable directly via CDN.
   - **Service Role Upload:** Restrict writes to backend service role key.
3. Configure backend environment:
   ```ini
   STORAGE_PROVIDER="supabase"
   SUPABASE_URL="https://[YOUR-PROJECT-REF].supabase.co"
   SUPABASE_SERVICE_ROLE_KEY="[YOUR-SUPABASE-SERVICE-ROLE-KEY]"
   SUPABASE_BUCKET_NAME="notices"
   ```

---

## 4. Cloud Deployment (Render / Railway / Fly.io)

### Deploying the Backend on Render
1. Create a **New Web Service** pointing to your Git repository.
2. Select **Docker** environment (Render detects `backend/Dockerfile`).
3. Set the Root Directory to `backend`.
4. Configure Environment Variables:
   - `ENVIRONMENT`: `production`
   - `DATABASE_URL`: Your Supabase or managed PostgreSQL URL.
   - `JWT_SECRET_KEY`: High-entropy secret key.
   - `ADMIN_REGISTRATION_SECRET`: High-entropy registration secret.
   - `ALLOWED_CORS_ORIGINS`: `["https://your-frontend-domain.com"]`
   - `AUTO_CREATE_DEFAULT_ADMIN`: `false`
5. Attach a persistent disk (size: 5 GB - 20 GB) mounted at `/app/uploads` and `/app/keys` to preserve cryptographic keys and notice originals.
6. Health Check Path: `/health`.

### Deploying the Frontend on Vercel
1. Import repository on [Vercel](https://vercel.com).
2. Framework Preset: **Vite**.
3. Build Command: `npm run build`.
4. Output Directory: `dist`.
5. Environment Variable:
   - `VITE_API_BASE_URL`: `https://your-backend-api.onrender.com`
6. Deploy!

---

## 5. Security & Production Hardening Checklist

| Security Control | Implementation | Verification Status |
| :--- | :--- | :--- |
| **Password Hashing** | Bcrypt with secure work factor (12 rounds) | Verified in `auth_service.py` |
| **JWT Access Tokens** | HS256 signed with 256-bit entropy, 60m expiry | Verified in `security.py` |
| **Key Isolation** | Ed25519 signing keys stored in restricted directory / HSM | Verified in `signature_service.py` |
| **MIME / Content Inspection** | File magic bytes verification (PDF `%PDF`, PNG, JPG `JFIF`) | Verified in `file_validator.py` |
| **Upload Size Limits** | 15 MB hard limit enforced at reverse proxy and API layer | Verified in `main.py` & Nginx |
| **Path Traversal Defense** | UUID-based / sanitized filenames, strictly validated paths | Verified in `storage_service.py` |
| **Non-Root Execution** | Docker container executes under unprivileged `appuser` | Enforced in `backend/Dockerfile` |
| **Information Leakage** | Global exception handler prevents Python traceback exposure | Verified in `main.py` |
| **CORS Origins** | Strict allow-list of approved institutional frontend domains | Configured via `ALLOWED_CORS_ORIGINS` |

---

## 6. Seed Initial Administrator

In production, automatic admin creation (`AUTO_CREATE_DEFAULT_ADMIN`) is disabled for security.
To register your initial administrator securely:

```bash
curl -X POST "https://your-backend-api.com/api/admin/register" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Registration-Secret: YOUR_ADMIN_REGISTRATION_SECRET" \
  -d '{
    "email": "registrar@gmu.edu",
    "password": "StrongPassword2026!#",
    "full_name": "Official University Registrar",
    "role": "super_admin"
  }'
```

