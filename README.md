# THE FORWARDED SEAL — Production Frontend Architecture

> **Don't Trust the Forward. Verify the Source.**  
> A cybersecurity SaaS platform engineered to help university students and academic communities distinguish genuine college circulars from forged, manipulated, or altered notices.

---

## 1. Project Overview

**The Forwarded Seal** protects academic integrity against malicious circulars circulating through unofficial channels (such as forwarded WhatsApp images, Telegram channels, and student forums).

The frontend interface is connected directly to backend API contracts with **zero mock, placeholder, or simulated data**. When the Python FastAPI backend is offline or unreachable, the application gracefully presents informative connection-pending and empty states with retry capabilities.

---

## 2. Technology Stack

- **Framework**: React 18
- **Build Tool**: Vite 6
- **Routing**: React Router DOM (v6)
- **Styling**: Tailwind CSS (Custom Cybersecurity midnight & electric cyan palette)
- **Icons**: Lucide React
- **HTTP Client**: Axios (preconfigured with interceptors, authorization bearer headers & environment-aware base URL)
- **Language**: JavaScript (ESM)

---

## 3. Project Structure

```text
c:/Users/LEENA S TOTAD/NEUROFORCE/
├── .env                       # Local environment variables
├── .env.example               # Backend API connection template
├── .gitignore                 # Standard Node/Vite git ignore rules
├── build.bat                  # One-click Windows production build script
├── dev.bat                    # One-click Windows dev server launcher
├── index.html                 # HTML entry with security shield favicon & typography
├── package.json               # NPM scripts and dependencies
├── postcss.config.js          # PostCSS configuration
├── tailwind.config.js         # Custom cybersecurity theme & tokens
├── vite.config.js             # Vite development server configuration
├── README.md                  # Comprehensive documentation
├── src/
│   ├── assets/
│   │   └── logo.svg           # High-resolution vector security seal logo
│   ├── components/
│   │   ├── Navbar.jsx             # Responsive navigation with dynamic auth status
│   │   ├── Footer.jsx             # Security footer with platform architecture status
│   │   ├── FileUpload.jsx         # Drag-and-drop zone with type & size validation
│   │   ├── VerificationResult.jsx # Forensic result card for authentic/tampered states
│   │   ├── FeatureCard.jsx        # Reusable cybersecurity feature card
│   │   └── QRScannerModal.jsx     # Optical QR watermark camera viewfinder
│   ├── layouts/
│   │   ├── MainLayout.jsx         # Public layout (Navbar, Page Outlet, Footer)
│   │   └── AdminLayout.jsx        # Admin layout (Topbar, User Profile, Outlet, Footer)
│   ├── pages/
│   │   ├── Home.jsx               # Landing page (Hero, 3 Features, 3-Step Guide)
│   │   ├── VerifyNotice.jsx       # Student verification portal (Upload, ID, QR)
│   │   ├── HowItWorks.jsx         # 7-step security architecture breakdown
│   │   ├── About.jsx              # Mission, dangers of forgery, 3 pillars
│   │   ├── AdminLogin.jsx         # Institutional admin login & validation
│   │   └── AdminDashboard.jsx     # Overview metrics, notice ledger & publication
│   ├── services/
│   │   ├── api.js                 # Axios API contract with FastAPI endpoints
│   │   └── noticeService.js       # Live backend service layer with structured error handling
│   ├── App.jsx                    # React Router DOM route hierarchy
│   ├── index.css                  # Custom cyber cards, glows, and Tailwind directives
│   └── main.jsx                   # React root entry point
```

---

## 4. Key Functional Pages

### A. Home / Landing Page (`/`)
- Brand identity with document security shield icon.
- Hero headline: *"Don't Trust the Forward. Verify the Source."*
- Problem description explaining student risk from forged college circulars.
- Dual CTAs: *Verify a Notice* and *How It Works*.
- Three core architectural layers: Cryptographic Authentication, Digital Watermarking, and Image Forensics.
- Three-step workflow explanation: **Upload → Analyze → Verify**.

### B. Student Verification Page (`/verify`)
- Drag-and-drop file upload zone supporting **PDF**, **PNG**, and **JPG/JPEG**.
- Strict file validation for format types and maximum file size (15 MB).
- Real-time file name, size display, image thumbnail preview, and removal option.
- Alternative Notice ID text search with instant clear button.
- Optical QR Code Watermark Scanner modal with viewfinder and direct code entry.
- When submitted, queries the live backend verification engine. If the backend is offline, an informative "Service Temporarily Unavailable / Backend Pending" message is displayed with zero fake positive or negative claims.

### C. How It Works Page (`/how-it-works`)
- Visual system schematic showing the 3 phases (Institutional Issuance, Uncontrolled Transit, Student Verification).
- 7-step verification lifecycle breakdown.

### D. About Page (`/about`)
- Comprehensive exploration of why fake circulars cause academic panic, fee fraud, and campus distress.
- Foundational mission of The Forwarded Seal.
- The Three Architectural Pillars: **Authenticity**, **Integrity**, and **Survivability**.

### E. Admin Login Page (`/admin/login`)
- Clean credential form starting with empty inputs (no hardcoded credentials).
- Client-side email format and password length validation.
- Show/hide password visibility toggle.
- Institutional login via `POST /api/admin/login` with JWT session persistence.

### F. Admin Dashboard (`/admin/dashboard`)
- Institutional administration portal with dedicated layout and session-aware user profile.
- Overview stat cards displaying real counts (defaults to `0` when no records exist).
- Notice management table with search by title/ID/dept and status filtering.
- Proper empty states:
  - Table: Displays *"No notices available"* when the registry has no records.
  - History: Displays *"No verification history yet"* when audit logs are empty.
  - Offline banner with *"Retry Connection"* button when the backend API is offline.
- Real publication modal connecting to `POST /api/notices` with multipart file upload.

---

## 5. Verification Result States

The verification result component (`VerificationResult.jsx`) presents 4 distinct forensic states rendered strictly when returned by the backend:

| Status | Color Coding | Meaning |
| :--- | :--- | :--- |
| **`VERIFIED`** | Emerald Green / Cyan | Authentic notice. Cryptographic signature and anti-tamper watermark match university ledger records. |
| **`TAMPERING_DETECTED`** | Crimson Red | Suspicious modifications found. Pixel noise or font splicing detected in deadline/fee sections. |
| **`AUTHENTIC_TRANSFORMED`** | Amber Gold | Document content is authentic and matches records, but has undergone lossy messaging re-compression or screenshot formatting. |
| **`UNVERIFIABLE`** | Slate Gray | Insufficient evidence. Notice ID or watermark not recognized in institutional database. |

---

## 6. Backend Integration Contract (FastAPI)

All API communication is isolated in `src/services/api.js`. The backend endpoints are:

| Endpoint | Method | Payload / Params | Service Method | Description |
| :--- | :--- | :--- | :--- | :--- |
| `/api/admin/login` | `POST` | `{ email, password }` | `authApi.login()` | Admin token authentication |
| `/api/notices` | `POST` | `FormData` (title, dept, file) | `noticeApi.createNotice()` | Publish notice & sign cryptographically |
| `/api/notices` | `GET` | `{ search, status, page }` | `noticeApi.getNotices()` | Query notices in administration ledger |
| `/api/notices/{notice_id}` | `GET` | `notice_id` (path param) | `noticeApi.getNoticeById()` | Retrieve notice metadata & signature |
| `/api/verify` | `POST` | `FormData` (file or notice ID) | `noticeApi.verifyDocument()` | Run forensic & cryptographic analysis |

Configuration in `.env`:
```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

---

## 7. Setup & Run Instructions

### Prerequisites
- Node.js (v18+ recommended; tested on v24)
- npm or pnpm
- Python 3.10+

### Run Local Development Server

#### Option A (Recommended for Windows PowerShell):
Create a backend virtual environment and install its dependencies once:
```powershell
python -m venv backend\venv
.\backend\venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

Then start both the FastAPI backend and Vite frontend:
```powershell
.\dev.bat
```
The demo admin is created automatically on backend startup:
- Email: `admin@gmu.edu`
- Password: `Gmu@12345!`

To start only the frontend (with the backend already running):
```powershell
npm.cmd run dev
```

#### Option B (Standard npm):
```bash
npm run dev
```

Open **[http://localhost:3000](http://localhost:3000)** in your browser.

### Build for Production
```powershell
npm.cmd run build
```
*(Or `.\build.bat`)*

### Preview Production Build
```powershell
npm.cmd run preview
```
