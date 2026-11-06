# The Forwarded Seal — React Frontend Integration Guide

This guide is for the **Phase 1 React Frontend Developer**.

The FastAPI backend is fully operational and provides the exact REST API contract required for your admin dashboard, login screen, notice creation form, and public verification views.

---

## 1. Quick Connection Reference

- **Base URL:** `http://127.0.0.1:8000/api` (or `http://localhost:8000/api`)
- **Swagger Interactive Docs:** `http://localhost:8000/docs`
- **CORS Allowed Origins:** `http://localhost:3000`, `http://localhost:5173`, `http://127.0.0.1:3000`, `http://127.0.0.1:5173`
- **Default Test Admin Account:**
  - **Email:** `admin@gmu.edu`
  - **Password:** `AdminPass123!`

---

## 2. Authentication Pattern

All protected administrative endpoints require a JSON Web Token (JWT) sent via standard HTTP Authorization header:

```http
Authorization: Bearer <access_token>
```

When storing the token in your React application:
- Store `access_token` in memory (e.g. React Context / Zustand) or in `sessionStorage` / `localStorage`.
- Attach it to your Axios instance or Fetch wrapper request interceptors.

---

## 3. Endpoints Specification & Examples

### 3.1. Admin Login
Authenticate an administrator with email and password.

- **Endpoint:** `POST /api/admin/login`
- **Content-Type:** `application/json`
- **Auth Required:** No

#### Request Body:
```json
{
  "email": "admin@gmu.edu",
  "password": "AdminPass123!"
}
```

#### Response (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "admin": {
    "id": "7440d92c-a112-4e38-a8b7-6ab56e1f6d35",
    "full_name": "University Registrar",
    "email": "admin@gmu.edu",
    "role": "super_admin",
    "is_active": true,
    "created_at": "2026-11-06T10:00:00Z"
  }
}
```

#### Error Responses:
- `401 Unauthorized`: `{"detail": "Invalid email or password."}`
- `403 Forbidden`: `{"detail": "Account is inactive. Please contact the system administrator."}`
- `422 Unprocessable Entity`: Field validation error (e.g. invalid email format).

---

### 3.2. Current Administrator Profile
Retrieve the authenticated administrator's profile.

- **Endpoint:** `GET /api/admin/me`
- **Auth Required:** Yes (`Bearer <access_token>`)

#### Request Headers:
```http
Authorization: Bearer <access_token>
```

#### Response (200 OK):
```json
{
  "id": "7440d92c-a112-4e38-a8b7-6ab56e1f6d35",
  "full_name": "University Registrar",
  "email": "admin@gmu.edu",
  "role": "super_admin",
  "is_active": true,
  "created_at": "2026-11-06T10:00:00Z"
}
```

---

### 3.3. Create Official Notice (with File Upload)
Upload an official document (PDF, PNG, JPG) and publish a college notice.

- **Endpoint:** `POST /api/notices`
- **Content-Type:** `multipart/form-data`
- **Auth Required:** Yes (`Bearer <access_token>`)

#### Form Data Fields:
| Field Name | Type | Required | Description |
|---|---|---|---|
| `title` | string | Yes | Title/Headline of notice (3–255 characters) |
| `description` | string | No | Full description or summary |
| `category` | string | Yes | e.g. `Academic`, `Examination`, `Admissions`, `Events`, `General` |
| `publication_status` | string | No | `published` (default) or `draft` |
| `file` | File / Blob | Yes | PDF, PNG, or JPEG file (max 10 MB). Disguised files or fake extensions are rejected by deep binary header inspection. |

#### Response (201 Created):
```json
{
  "id": "9bc2e118-2435-4428-b805-4c07db95f2a1",
  "notice_id": "FS-GMU-2026-A8F29C",
  "title": "Fall 2026 Final Examination Schedule",
  "description": "Comprehensive schedule for all undergraduate courses.",
  "category": "Examination",
  "original_filename": "exam_schedule.pdf",
  "mime_type": "application/pdf",
  "file_size": 245812,
  "publication_status": "published",
  "issuer_admin_id": "7440d92c-a112-4e38-a8b7-6ab56e1f6d35",
  "created_at": "2026-11-06T10:15:00Z",
  "updated_at": "2026-11-06T10:15:00Z",
  "file_download_url": "/api/notices/FS-GMU-2026-A8F29C/file",
  "issuer_admin": {
    "id": "7440d92c-a112-4e38-a8b7-6ab56e1f6d35",
    "full_name": "University Registrar",
    "email": "admin@gmu.edu",
    "role": "super_admin"
  },
  "sha256_hash": null,
  "digital_signature": null,
  "signing_key_id": null,
  "signed_metadata": null,
  "revoked_at": null
}
```

---

### 3.4. List Notices (with Pagination & Filters)
Retrieve notices with support for filtering and text search.

- **Endpoint:** `GET /api/notices`
- **Auth Required:** Optional (authenticated admins can view drafts; public requests default to published)
- **Query Parameters:**
  - `page` (integer, default: `1`): 1-indexed page number.
  - `page_size` (integer, default: `20`, max: `100`): Items per page.
  - `category` (string, optional): e.g. `Academic`, `Examination`.
  - `status` (string, optional): `published`, `draft`, `archived`, or `all`.
  - `search` (string, optional): Search term matched against title, description, or Notice ID.

#### Example Request:
```http
GET /api/notices?page=1&page_size=10&category=Academic&search=schedule HTTP/1.1
Authorization: Bearer <access_token>
```

#### Response (200 OK):
```json
{
  "items": [
    {
      "id": "9bc2e118-2435-4428-b805-4c07db95f2a1",
      "notice_id": "FS-GMU-2026-A8F29C",
      "title": "Fall 2026 Final Examination Schedule",
      "description": "Comprehensive schedule for all undergraduate courses.",
      "category": "Examination",
      "original_filename": "exam_schedule.pdf",
      "mime_type": "application/pdf",
      "file_size": 245812,
      "publication_status": "published",
      "issuer_admin_id": "7440d92c-a112-4e38-a8b7-6ab56e1f6d35",
      "created_at": "2026-11-06T10:15:00Z",
      "updated_at": "2026-11-06T10:15:00Z",
      "file_download_url": "/api/notices/FS-GMU-2026-A8F29C/file",
      "issuer_admin": {
        "id": "7440d92c-a112-4e38-a8b7-6ab56e1f6d35",
        "full_name": "University Registrar",
        "email": "admin@gmu.edu",
        "role": "super_admin"
      }
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10,
  "total_pages": 1
}
```

---

### 3.5. Get Notice Details (Public Verification View)
Retrieve a notice's full metadata using its unique institutional Notice ID (e.g. from a QR code or student search).

- **Endpoint:** `GET /api/notices/{notice_id}`
- **Auth Required:** No

#### Example:
`GET /api/notices/FS-GMU-2026-A8F29C`

#### Response (200 OK):
Returns the complete Notice object (same structure as 3.3).

#### Error (404 Not Found):
```json
{
  "detail": "Notice 'FS-GMU-2026-A8F29C' was not found."
}
```

---

### 3.6. Update Notice Status
Change a notice's state between `draft`, `published`, and `archived`.

- **Endpoint:** `PATCH /api/notices/{notice_id}/status`
- **Content-Type:** `application/json`
- **Auth Required:** Yes (`Bearer <access_token>`)

#### Request Body:
```json
{
  "publication_status": "archived"
}
```

#### Response (200 OK):
Returns the updated Notice object with `publication_status: "archived"`.

---

### 3.7. Download / View Notice Document
Direct stream of the uploaded document (PDF or image).

- **Endpoint:** `GET /api/notices/{notice_id}/file`
- **Auth Required:** No

You can embed this URL directly in React `<iframe src="http://localhost:8000/api/notices/FS-GMU-2026-A8F29C/file"></iframe>` or `<img src="http://localhost:8000/api/notices/FS-GMU-2026-A8F29C/file" />`.

---

## 4. Frontend React Integration Code Snippets

### A. Axios Client Configuration
```javascript
// src/api/client.js
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Automatically inject JWT Bearer token into outgoing requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

### B. Admin Login Component Flow
```javascript
// src/services/auth.js
import api from '../api/client';

export async function loginAdmin(email, password) {
  try {
    const response = await api.post('/admin/login', { email, password });
    const { access_token, admin } = response.data;
    localStorage.setItem('token', access_token);
    localStorage.setItem('admin', JSON.stringify(admin));
    return { success: true, admin };
  } catch (error) {
    const message = error.response?.data?.detail || 'Authentication failed.';
    return { success: false, message };
  }
}
```

### C. Create Notice Form Submission (Multipart Form-Data)
```javascript
// src/services/notices.js
import api from '../api/client';

export async function createNotice({ title, description, category, publicationStatus, file }) {
  const formData = new FormData();
  formData.append('title', title);
  if (description) formData.append('description', description);
  formData.append('category', category);
  formData.append('publication_status', publicationStatus || 'published');
  formData.append('file', file); // The File object from <input type="file" />

  try {
    const response = await api.post('/notices', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return { success: true, notice: response.data };
  } catch (error) {
    const message = error.response?.data?.detail || 'Failed to create notice.';
    return { success: false, message };
  }
}
```

### D. Notice List & Search Component
```javascript
export async function fetchNotices({ page = 1, category, status, search }) {
  const params = { page, page_size: 10 };
  if (category && category !== 'All') params.category = category;
  if (status && status !== 'All') params.status = status;
  if (search) params.search = search;

  const response = await api.get('/notices', { params });
  return response.data; // { items, total, page, page_size, total_pages }
}
```

---

## 5. Security & Verification Checklist for Frontend

1. **Token Expiry (401 Handling):** If any API call returns `401 Unauthorized`, clear `localStorage.removeItem('token')` and redirect the administrator to the login page.
2. **File Restrictions:** Before sending files from React, advise users that:
   - Permitted formats: `.pdf`, `.png`, `.jpg`, `.jpeg`.
   - Maximum upload size: 10 MB.
3. **Notice ID Display:** Always display the official `notice_id` (e.g. `FS-GMU-2026-A8F29C`) prominently alongside the notice so students and authorities can verify it.

