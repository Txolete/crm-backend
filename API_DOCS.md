# 📚 API Documentation - Authentication & User Management

**Version:** 0.1.0  
**Base URL:** `http://localhost:8000`

---

## 🔐 Authentication Endpoints

### 1. POST /auth/login

**Description:** Login with email and password

**Request:**
```json
POST /auth/login
Content-Type: application/json

{
  "email": "admin@crm.local",
  "password": "admin123456"
}
```

**Response (200 OK):**
```json
{
  "message": "Login successful",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Admin User",
    "email": "admin@crm.local",
    "role": "admin"
  }
}
```

**Response (401 Unauthorized - Invalid credentials):**
```json
{
  "detail": "Invalid email or password"
}
```

**Response (403 Forbidden - Inactive user):**
```json
{
  "detail": "User account is inactive"
}
```

**Notes:**
- Sets HttpOnly cookie `access_token` with JWT
- Updates `last_login_at` in database
- Creates audit log entry
- Cookie expires in 30 days

---

### 2. POST /auth/logout

**Description:** Logout by clearing the HttpOnly cookie

**Request:**
```json
POST /auth/logout
```

**Response (200 OK):**
```json
{
  "message": "Logout successful"
}
```

**Notes:**
- Deletes the `access_token` cookie

---

### 3. GET /auth/me

**Description:** Get current authenticated user information

**Authorization:** Requires JWT token in cookie

**Request:**
```json
GET /auth/me
Cookie: access_token=<jwt_token>
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Admin User",
  "email": "admin@crm.local",
  "role": "admin",
  "is_active": true,
  "last_login_at": "2026-01-07T18:30:00.000000Z"
}
```

**Response (401 Unauthorized - No token or invalid token):**
```json
{
  "detail": "Could not validate credentials"
}
```

**Response (403 Forbidden - User inactive):**
```json
{
  "detail": "User account is inactive"
}
```

---

## 👥 Admin - User Management Endpoints

### 4. GET /admin/users

**Description:** List all users

**Authorization:** Admin only

**Request:**
```json
GET /admin/users
Cookie: access_token=<jwt_token>
```

**Response (200 OK):**
```json
{
  "users": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Admin User",
      "email": "admin@crm.local",
      "role": "admin",
      "is_active": true,
      "last_login_at": "2026-01-07T18:30:00.000000Z",
      "created_at": "2026-01-07T10:00:00.000000Z",
      "updated_at": "2026-01-07T18:30:00.000000Z"
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "Sales User",
      "email": "sales@crm.local",
      "role": "sales",
      "is_active": true,
      "last_login_at": null,
      "created_at": "2026-01-07T11:00:00.000000Z",
      "updated_at": "2026-01-07T11:00:00.000000Z"
    }
  ],
  "total": 2
}
```

**Response (403 Forbidden - Not admin):**
```json
{
  "detail": "Access denied. Required role: admin"
}
```

---

### 5. POST /admin/users

**Description:** Create a new user

**Authorization:** Admin only

**Request:**
```json
POST /admin/users
Content-Type: application/json
Cookie: access_token=<jwt_token>

{
  "name": "New Sales User",
  "email": "newsales@crm.local",
  "password": "SecurePass123",
  "role": "sales"
}
```

**Response (201 Created):**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "name": "New Sales User",
  "email": "newsales@crm.local",
  "role": "sales",
  "is_active": true,
  "last_login_at": null,
  "created_at": "2026-01-07T19:00:00.000000Z",
  "updated_at": "2026-01-07T19:00:00.000000Z"
}
```

**Response (400 Bad Request - Email already exists):**
```json
{
  "detail": "Email already registered"
}
```

**Response (422 Unprocessable Entity - Validation error):**
```json
{
  "detail": [
    {
      "type": "string_pattern_mismatch",
      "loc": ["body", "role"],
      "msg": "String should match pattern '^(admin|sales|viewer)$'",
      "input": "invalid_role"
    }
  ]
}
```

**Notes:**
- Password must be at least 8 characters
- Role must be: admin, sales, or viewer
- User is created active by default
- Creates audit log entry

---

### 6. PUT /admin/users/{user_id}

**Description:** Update user information

**Authorization:** Admin only

**Request:**
```json
PUT /admin/users/770e8400-e29b-41d4-a716-446655440002
Content-Type: application/json
Cookie: access_token=<jwt_token>

{
  "name": "Updated Sales User",
  "role": "viewer",
  "is_active": true
}
```

**Response (200 OK):**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "name": "Updated Sales User",
  "email": "newsales@crm.local",
  "role": "viewer",
  "is_active": true,
  "last_login_at": null,
  "created_at": "2026-01-07T19:00:00.000000Z",
  "updated_at": "2026-01-07T19:15:00.000000Z"
}
```

**Request (Deactivate user):**
```json
PUT /admin/users/770e8400-e29b-41d4-a716-446655440002
Content-Type: application/json
Cookie: access_token=<jwt_token>

{
  "is_active": false
}
```

**Response (200 OK):**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "name": "Updated Sales User",
  "email": "newsales@crm.local",
  "role": "viewer",
  "is_active": false,
  "last_login_at": null,
  "created_at": "2026-01-07T19:00:00.000000Z",
  "updated_at": "2026-01-07T19:20:00.000000Z"
}
```

**Response (404 Not Found):**
```json
{
  "detail": "User not found"
}
```

**Notes:**
- All fields are optional
- Can update: name, email, role, is_active
- Deactivating sets is_active=false (logical deletion)
- Never physically deletes users
- Creates audit log entry with before/after state

---

### 7. POST /admin/users/{user_id}/reset-password

**Description:** Reset user password

**Authorization:** Admin only

**Request:**
```json
POST /admin/users/770e8400-e29b-41d4-a716-446655440002/reset-password
Content-Type: application/json
Cookie: access_token=<jwt_token>

{
  "new_password": "NewSecurePass456"
}
```

**Response (200 OK):**
```json
{
  "message": "Password reset successfully",
  "user_id": "770e8400-e29b-41d4-a716-446655440002",
  "email": "newsales@crm.local"
}
```

**Response (404 Not Found):**
```json
{
  "detail": "User not found"
}
```

**Notes:**
- Password must be at least 8 characters
- Creates audit log entry
- User should be notified to change password on next login

---

## 🛡️ Authorization Matrix

| Endpoint | Admin | Sales | Viewer |
|----------|-------|-------|--------|
| POST /auth/login | ✅ | ✅ | ✅ |
| POST /auth/logout | ✅ | ✅ | ✅ |
| GET /auth/me | ✅ | ✅ | ✅ |
| GET /admin/users | ✅ | ❌ | ❌ |
| POST /admin/users | ✅ | ❌ | ❌ |
| PUT /admin/users/{id} | ✅ | ❌ | ❌ |
| POST /admin/users/{id}/reset-password | ✅ | ❌ | ❌ |

---

## 🔍 Testing with cURL

### Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@crm.local","password":"admin123456"}' \
  -c cookies.txt
```

### Get current user
```bash
curl -X GET http://localhost:8000/auth/me \
  -b cookies.txt
```

### List users (admin only)
```bash
curl -X GET http://localhost:8000/admin/users \
  -b cookies.txt
```

### Create user (admin only)
```bash
curl -X POST http://localhost:8000/admin/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@crm.local","password":"test12345","role":"viewer"}' \
  -b cookies.txt
```

### Logout
```bash
curl -X POST http://localhost:8000/auth/logout \
  -b cookies.txt \
  -c cookies.txt
```

---

## 📝 Audit Log Entries

All user management actions are logged in `audit_log` table:

**Login:**
```json
{
  "entity": "user",
  "entity_id": "550e8400-e29b-41d4-a716-446655440000",
  "action": "login",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "after_json": "{\"email\":\"admin@crm.local\",\"last_login_at\":\"2026-01-07T18:30:00Z\"}"
}
```

**User creation:**
```json
{
  "entity": "user",
  "entity_id": "770e8400-e29b-41d4-a716-446655440002",
  "action": "create",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "after_json": "{\"name\":\"New User\",\"email\":\"new@crm.local\",\"role\":\"sales\",\"is_active\":true}"
}
```

**User deactivation:**
```json
{
  "entity": "user",
  "entity_id": "770e8400-e29b-41d4-a716-446655440002",
  "action": "deactivate",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "before_json": "{\"name\":\"User\",\"email\":\"user@crm.local\",\"role\":\"sales\",\"is_active\":true}",
  "after_json": "{\"name\":\"User\",\"email\":\"user@crm.local\",\"role\":\"sales\",\"is_active\":false}"
}
```

---

## ⚠️ Important Notes

1. **Never delete users physically** - Use `is_active=false` for logical deletion
2. **Password security** - Passwords are hashed with bcrypt, never stored in plain text
3. **JWT expiration** - Tokens expire in 30 days (configurable in .env)
4. **HttpOnly cookies** - JWT is stored in HttpOnly cookie for security
5. **Audit trail** - All actions are logged in `audit_log` table
6. **Role enforcement** - Middleware checks role before allowing access
7. **Email uniqueness** - Email must be unique across all users

---

## 🚀 Next Steps

With authentication complete, the next features to implement are:
1. CRUD APIs for CRM entities (Accounts, Contacts, Opportunities, Tasks)
2. Dashboard with KPIs and Kanban
3. Excel Importer
4. Configuration module
