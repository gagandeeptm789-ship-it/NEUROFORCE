# The Forwarded Seal — Phase 2: Backend & Admin Notice Platform

The Forwarded Seal is an institutional authenticity and verification platform for university documents and notices.

Phase 2 establishes the core backend foundation:
- **Secure Administrator Authentication** (bcrypt password hashing, JWT bearer tokens, role enforcement, active account status checks).
- **Official Notice Creation & Publishing** (multipart document upload, deep file inspection via magic bytes, institutional Notice ID generation).
- **Storage Abstraction** (local development storage with directory traversal defenses, extensible to Supabase Storage).
- **Phase 3 Cryptographic Readiness** (pre-planned database schema and modular service layer ready for SHA-256 document hashing and digital signatures).

---

## 1. Technology Stack

- **Python:** 3.10+
- **Framework:** FastAPI (high-performance asynchronous ASGI web framework)
- **Database:** PostgreSQL (with out-of-the-box SQLite support for local dev & testing)
- **ORM:** SQLAlchemy 2.0
- **Migrations:** Alembic
- **Data Validation & Schemas:** Pydantic v2
- **Authentication:** JSON Web Tokens (PyJWT / RFC 7519) + bcrypt (12 rounds)
- **File Validation:** Binary content header (magic bytes) inspection & extension validation

---

## 2. Project Architecture

```
backend/
├── .env                  # Local environment configuration
├── .env.example          # Environment variables template
├── README.md             # Complete backend engineering documentation
├── FRONTEND_INTEGRATION.md # Direct contract guide for React frontend developers
├── requirements.txt      # Python dependencies
├── alembic.ini           # Alembic database migration config
├── alembic/
│   ├── env.py            # Migration runtime context
│   ├── script.py.mako    # Migration template
│   └── versions/
│       └── 001_initial_schema.py # Initial database migration
├── scripts/
│   └── seed_admin.py     # Controlled administrative onboarding script
├── uploads/              # Local storage root for uploaded notice documents
├── tests/                # Automated test suite (32 unit & integration tests)
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_notices.py
│   └── test_storage_and_id.py
└── app/
    ├── main.py           # FastAPI entrypoint, CORS, lifespan, exception handlers
    ├── database.py       # SQLAlchemy engine, session maker, get_db dependency
    ├── core/
    │   ├── config.py     # Pydantic environment configuration & settings
    │   └── security.py   # bcrypt password hashing, JWT creation & decoding
    ├── models/
    │   ├── admin.py      # SQLAlchemy Admin entity
    │   └── notice.py     # SQLAlchemy Notice entity (with Phase 3 columns)
    ├── schemas/
    │   ├── admin.py      # Admin Pydantic schemas (AdminLogin, AdminResponse, etc.)
    │   └── notice.py     # Notice Pydantic schemas (NoticeResponse, NoticeListResponse)
    ├── routers/
    │   ├── auth.py       # POST /api/admin/login, GET /api/admin/me, POST /api/admin/register
    │   └── notices.py    # POST /api/notices, GET /api/notices, PATCH /api/notices/{id}/status
    ├── services/
    │   ├── auth_service.py    # Admin authentication, registration, dependency injection
    │   ├── notice_service.py  # Notice lifecycle, querying, pagination, status transitions
    │   ├── storage_service.py # Abstract StorageService, LocalStorageService, Supabase
    │   └── crypto_service.py  # Phase 3 readiness: SHA-256 calculation & signing stubs
    └── utils/
        ├── notice_id.py       # Cryptographically random Notice ID generator
        └── file_validator.py  # Magic byte validation, filename sanitization, size limits
```

---

## 3. Database Schema

### A. Admins Table (`admins`)
| Column | Type | Constraints / Description |
|---|---|---|
| `id` | String(36) | Primary Key (UUIDv4) |
| `full_name` | String(100) | Not null |
| `email` | String(255) | Unique, Indexed, Normalized lowercase |
| `password_hash` | String(255) | Not null (bcrypt hash) |
| `role` | String(50) | Default: `admin` (`super_admin`, `admin`, `exam_cell`) |
| `is_active` | Boolean | Default: `True` (only active admins can log in) |
| `created_at` | DateTime(UTC) | Timestamp |
| `updated_at` | DateTime(UTC) | Auto-updating timestamp |

### B. Notices Table (`notices`)
| Column | Type | Constraints / Description |
|---|---|---|
| `id` | String(36) | Primary Key (UUIDv4) |
| `notice_id` | String(64) | Unique, Indexed (e.g. `FS-GMU-2026-A8F29C`) |
| `title` | String(255) | Not null |
| `description` | Text | Nullable summary or full body |
| `category` | String(100) | Not null (e.g. `Academic`, `Examination`, `Admissions`) |
| `original_filename`| String(255) | Cleaned original upload filename |
| `stored_file_path` | String(512) | Normalized relative storage key |
| `mime_type` | String(100) | Validated MIME type (`application/pdf`, `image/png`, etc.) |
| `file_size` | Integer | Document size in bytes |
| `issuer_admin_id` | String(36) | Foreign Key -> `admins.id` |
| `publication_status`| String(20) | Default: `published` (`draft`, `published`, `archived`) |
| `created_at` | DateTime(UTC) | Timestamp |
| `updated_at` | DateTime(UTC) | Auto-updating timestamp |
| **Phase 3 Fields** | | |
| `sha256_hash` | String(64) | Nullable (64 hex characters) |
| `digital_signature`| Text | Nullable (asymmetric cryptographic signature) |
| `signing_key_id` | String(100) | Nullable (key identifier) |
| `signed_metadata` | Text | Nullable (JSON payload) |
| `revoked_at` | DateTime(UTC) | Nullable (revocation timestamp) |

---

## 4. Setup & Installation Instructions

### 1. Clone & Enter Directory
```bash
git clone <repo-url>
cd NEUROFORCE/backend
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Linux / macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment (.env)
Copy the template and modify secrets:
```bash
cp .env.example .env
```
Key settings in `.env`:
- `DATABASE_URL`: Set to your PostgreSQL / Supabase connection string, or keep `sqlite:///./forwarded_seal.db` for local testing.
- `SECRET_KEY`: Minimum 32-character secret key for signing JWTs.
- `ADMIN_REGISTRATION_SECRET`: Secret token used to protect administrative registration.
- `ALLOWED_CORS_ORIGINS`: Comma-separated list of allowed frontend origins (default includes `http://localhost:3000`, `http://localhost:5173`).

### 5. Seed Initial Administrator Account
Bootstrap the primary administrator without exposing open registration:
```bash
python scripts/seed_admin.py --email admin@gmu.edu --name "University Registrar" --password "Gmu@12345!" --role institutional_admin
```
In development, the same account is automatically created on backend startup when `AUTO_CREATE_DEFAULT_ADMIN=true`. The demo login is `admin@gmu.edu` / `Gmu@12345!`. To update an existing account with the seed script, include `--reset-password`. Set `AUTO_CREATE_DEFAULT_ADMIN=false` and provide real administrator credentials before production deployment; automatic demo provisioning is disabled by default outside development.

### 6. Run Migrations (Optional / Production)
```bash
alembic upgrade head
```
*(FastAPI also idempotently runs `init_db()` upon startup).*

### 7. Run the Application
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- Interactive Swagger UI documentation: `http://localhost:8000/docs`
- ReDoc documentation: `http://localhost:8000/redoc`
- Health check: `http://localhost:8000/health`

---

## 5. Security Engineering Implementation

1. **Password Security:**
   - Plaintext passwords are never stored. Passwords are hashed with bcrypt using automatically generated random salts with 12 rounds.
   - Enforces password complexity (minimum 8 characters, upper, lower, numbers, symbols).
   - Generic authentication failure messages prevent username/account enumeration.

2. **Access Control & JWT:**
   - HS256-signed JWT access tokens with strict expiration (`ACCESS_TOKEN_EXPIRE_MINUTES`).
   - All notice creation, status changes, and administrator profile endpoints require `Authorization: Bearer <token>`.
   - Inactive administrators (`is_active = False`) are blocked immediately (HTTP 403) even with valid passwords.

3. **Controlled Registration:**
   - Public self-registration is strictly disallowed.
   - Initial administrators are provisioned via `scripts/seed_admin.py`.
   - The `/api/admin/register` endpoint requires the `X-Admin-Registration-Secret` HTTP header matching `.env`.

4. **Deep File Validation (Magic Bytes & Anti-Malware):**
   - Filenames and extensions are never trusted. Uploaded files undergo binary inspection of their first 16 bytes:
     - PDF: Magic signature `%PDF-` (`0x25 0x50 0x44 0x46`)
     - PNG: Magic signature `\x89PNG\r\n\x1a\n` (`0x89 0x50 0x4E 0x47`)
     - JPEG: Magic signature `\xff\xd8\xff` (`0xFF 0xD8 0xFF`)
   - Empty files (0 bytes) and oversized uploads exceeding `MAX_UPLOAD_SIZE_BYTES` (default 10 MB) are rejected with HTTP 400.
   - Executable extensions (`.exe`, `.sh`, `.bat`, `.py`) are rejected.

5. **Path Traversal Protection (CWE-22):**
   - Filenames are sanitized via `sanitize_filename` (removing path components, null bytes, and non-alphanumeric characters).
   - `LocalStorageService` resolves absolute canonical paths and verifies `commonpath([base_dir, target_path]) == base_dir`.
   - Any path traversal escape attempts immediately throw an access violation error.

6. **Information Leakage Prevention:**
   - Password hashes are completely excluded from all Pydantic response models (`AdminResponse`).
   - Unhandled exceptions are caught by global middleware, returning a standardized generic HTTP 500 error without exposing stack traces.

---

## 6. Phase 3 Cryptographic Compatibility

The architecture prepares for Phase 3 (SHA-256 document hashing and digital signatures):
1. **Schema Extensibility:** The `notices` table contains pre-migrated nullable columns: `sha256_hash`, `digital_signature`, `signing_key_id`, `signed_metadata`, and `revoked_at`.
2. **Service Layer Separation:** Cryptographic algorithms are strictly kept out of HTTP route handlers. `app/services/crypto_service.py` provides the `ICryptoService` interface and `Phase3PreparedCryptoService` with `calculate_sha256` and canonical metadata payload formatting.
3. **Prepared Hook:** `notice_service.prepare_phase3_signing_payload()` is ready to be invoked upon notice creation or batch signing.

---

## 7. Automated Test Suite

Run all automated unit and integration tests:
```bash
pytest -v
```

### Test Coverage Highlights:
- **32 Automated Tests:**
  - `test_auth.py`: Admin login with valid credentials, invalid password rejection, nonexistent email generic rejection, deactivated account rejection, `/api/admin/me` profile retrieval, JWT bearer validation, missing token handling, tampered JWT rejection, expired JWT rejection, protected registration without secret (403), registration with valid secret (201), weak password rejection (400), duplicate email rejection (400).
  - `test_notices.py`: PDF document notice creation, PNG image notice creation, JPEG image notice creation, unauthorized notice creation rejection, disallowed file extension rejection, spoofed magic bytes rejection, empty file rejection, oversized file rejection, notice retrieval by Notice ID, 404 nonexistent notice handling, notice listing with category filtering and keyword search, notice publication status updates (draft -> published -> archived), original document file streaming.
  - `test_storage_and_id.py`: Notice ID format and collision resistance across 100 iterations, directory traversal defense (`../../etc/passwd`), file save/retrieve/delete lifecycle, filename sanitization, Phase 3 SHA-256 calculation verification, Phase 3 canonical metadata formatting.
