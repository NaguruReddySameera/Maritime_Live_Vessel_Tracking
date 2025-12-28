# JWT Authentication Documentation

## Infosys Virtual Internship 6.0

**Project Title:** Maritime Vessel Tracking, Port Analytics, and Safety Visualization Platform

**Group Members:**
- Sameera Reddy
- Tharuni
- Shweta

**Mentor:** Aishwarya

---

## Table of Contents
1. [Overview](#overview)
2. [What is JWT?](#what-is-jwt)
3. [System Architecture](#system-architecture)
4. [Authentication Flow](#authentication-flow)
5. [Implementation Details](#implementation-details)
6. [Security Features](#security-features)
7. [API Endpoints](#api-endpoints)
8. [Code Examples](#code-examples)
9. [Testing](#testing)

---

## Overview

JWT (JSON Web Token) Authentication is a secure, stateless authentication mechanism used in our Maritime Vessel Tracking Platform to verify user identity and authorize access to protected resources.

### Why JWT?
- **Stateless**: No need to store session data on the server
- **Scalable**: Works well with distributed systems
- **Secure**: Digitally signed tokens prevent tampering
- **Self-contained**: Carries all user information within the token
- **Cross-platform**: Works across web, mobile, and API clients

---

## What is JWT?

A JWT is a compact, URL-safe token composed of three parts:

```
header.payload.signature
```

### 1. Header
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```
- **alg**: Algorithm used for signing (HS256 = HMAC SHA-256)
- **typ**: Token type

### 2. Payload
```json
{
  "user_id": 123,
  "email": "user@example.com",
  "role": "operator",
  "exp": 1735000000,
  "iat": 1734996400
}
```
- **user_id**: Unique identifier for the user
- **email**: User's email address
- **role**: User role (operator, analyst, admin)
- **exp**: Expiration timestamp
- **iat**: Issued at timestamp

### 3. Signature
```
HMACSHA256(
  base64UrlEncode(header) + "." +
  base64UrlEncode(payload),
  secret_key
)
```
- Ensures token hasn't been tampered with
- Generated using server's secret key

---

## System Architecture

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Frontend  │  HTTP   │   Backend   │  Query  │  Database   │
│   (React)   │◄───────►│  (Django)   │◄───────►│  (SQLite3)  │
│             │   JWT   │             │         │             │
└─────────────┘         └─────────────┘         └─────────────┘
      │                       │
      │                       │
      ▼                       ▼
  localStorage          JWT Secret Key
  - access_token        - Signs tokens
  - refresh_token       - Verifies tokens
```

### Components:

1. **Frontend (React + TypeScript)**
   - Stores JWT tokens in localStorage
   - Sends tokens in Authorization header
   - Handles token expiration and refresh

2. **Backend (Django + Django REST Framework)**
   - Issues JWT tokens on login
   - Validates tokens on each request
   - Manages user roles and permissions

3. **Database (SQLite3)**
   - Stores user credentials (hashed passwords)
   - Stores user information and roles

---

## Authentication Flow

### 1. User Registration Flow
```
User fills form → Frontend sends data → Backend creates user
                                      → Hash password with bcrypt
                                      → Store in database
                                      → Return success message
```

**For Operators**: Auto-approved (is_active = True)
**For Analyst/Admin**: Requires admin approval (is_active = False)

### 2. Login Flow
```
User enters credentials → Frontend POST /api/auth/login/
                       ↓
                    Backend validates credentials
                       ↓
                    Generate JWT tokens:
                    - Access Token (15 min)
                    - Refresh Token (7 days)
                       ↓
                    Return tokens + user info
                       ↓
                    Frontend stores tokens
                    in localStorage
```

### 3. Authenticated Request Flow
```
User accesses protected page → Frontend reads access_token
                              → Add to Authorization header
                              → Backend validates token
                              → Check signature & expiration
                              → Extract user info
                              → Verify permissions
                              → Return requested data
```

### 4. Token Refresh Flow
```
Access token expires → Frontend detects 401 error
                     → Send refresh_token to /api/auth/refresh/
                     → Backend validates refresh token
                     → Issue new access token
                     → Frontend stores new token
                     → Retry original request
```

### 5. Logout Flow
```
User clicks logout → Frontend removes tokens from localStorage
                  → Redirect to login page
                  → Backend token becomes invalid
```

---

## Implementation Details

### Backend (Django)

#### 1. User Model
**File**: `backend/apps/authentication/models.py`

```python
class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    USERNAME_FIELD = 'email'
```

#### 2. JWT Settings
**File**: `backend/maritime_project/settings.py`

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}
```

#### 3. Login View
**File**: `backend/apps/authentication/views.py`

```python
class UserLoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        # Authenticate user
        user = authenticate(email=email, password=password)
        
        if user:
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'success': True,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                },
                'user': UserSerializer(user).data
            })
```

#### 4. Protected View Example
```python
class VesselListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # User is authenticated via JWT
        user = request.user
        vessels = Vessel.objects.all()
        return Response(VesselSerializer(vessels, many=True).data)
```

#### 5. Role-Based Permissions
**File**: `backend/apps/authentication/permissions.py`

```python
class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'

class IsOperator(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['operator', 'analyst', 'admin']
```

### Frontend (React + TypeScript)

#### 1. Auth Service
**File**: `frontend/src/services/authService.ts`

```typescript
const login = async (email: string, password: string) => {
  const response = await api.post('/auth/login/', { email, password });
  
  if (response.data.success) {
    // Store tokens in localStorage
    localStorage.setItem('access_token', response.data.tokens.access);
    localStorage.setItem('refresh_token', response.data.tokens.refresh);
    localStorage.setItem('user', JSON.stringify(response.data.user));
    
    return response.data;
  }
};

const logout = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
};
```

#### 2. API Interceptor
**File**: `frontend/src/services/api.ts`

```typescript
// Add token to all requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  }
);

// Handle token refresh on 401 errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token');
      
      if (refreshToken) {
        const response = await api.post('/auth/refresh/', {
          refresh: refreshToken
        });
        
        localStorage.setItem('access_token', response.data.access);
        
        // Retry original request
        error.config.headers.Authorization = `Bearer ${response.data.access}`;
        return api.request(error.config);
      }
    }
    return Promise.reject(error);
  }
);
```

#### 3. Protected Route
**File**: `frontend/src/App.tsx`

```typescript
import { Navigate } from 'react-router-dom';

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { user, loading } = useAuth();
  
  if (loading) return <div>Loading...</div>;
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
};

// Usage
<Route 
  path="/dashboard" 
  element={
    <ProtectedRoute>
      <Dashboard />
    </ProtectedRoute>
  } 
/>
```

#### 4. Role-Based Access
```typescript
const AdminPanel = () => {
  const { user } = useAuth();
  
  useEffect(() => {
    if (user?.role !== 'admin') {
      navigate('/dashboard');
    }
  }, [user]);
  
  return <div>Admin Panel</div>;
};
```

---

## Security Features

### 1. Password Security
- **Hashing Algorithm**: PBKDF2 with SHA-256 (Django default)
- **Iterations**: 260,000 (configurable)
- **Salt**: Unique salt per password
- **Never store plain text passwords**

```python
from django.contrib.auth.hashers import make_password

hashed = make_password('user_password')
# Output: pbkdf2_sha256$260000$salt$hash
```

### 2. Token Security
- **Short-lived access tokens**: 15 minutes
- **Long-lived refresh tokens**: 7 days
- **Signature verification**: HMAC-SHA256
- **Secret key protection**: Environment variable

### 3. CORS Configuration
**File**: `backend/maritime_project/settings.py`

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React development server
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    'authorization',
    'content-type',
]
```

### 4. HTTPS (Production)
- All tokens transmitted over HTTPS only
- Secure cookie flags enabled
- HSTS headers configured

### 5. Token Storage
- **Frontend**: localStorage (or httpOnly cookies for enhanced security)
- **Backend**: No storage needed (stateless)
- **Never expose tokens in URLs**

### 6. Input Validation
```python
def validate_email(email):
    if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
        raise ValidationError('Invalid email format')

def validate_password(password):
    if len(password) < 8:
        raise ValidationError('Password must be at least 8 characters')
```

---

## API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register/` | Register new user | No |
| POST | `/api/auth/login/` | Login and get tokens | No |
| POST | `/api/auth/refresh/` | Refresh access token | Yes (Refresh Token) |
| GET | `/api/auth/me/` | Get current user info | Yes |
| POST | `/api/auth/logout/` | Logout user | Yes |
| GET | `/api/auth/demo-users/` | Get demo account credentials | No |

### Protected Endpoints (Require JWT)

| Method | Endpoint | Description | Role |
|--------|----------|-------------|------|
| GET | `/api/vessels/` | List all vessels | Operator+ |
| POST | `/api/vessels/` | Create vessel | Analyst+ |
| GET | `/api/ports/` | List all ports | Operator+ |
| GET | `/api/analytics/` | Get analytics data | Analyst+ |
| GET | `/api/admin/users/` | List all users | Admin |
| POST | `/api/admin/users/{id}/approve/` | Approve pending user | Admin |

---

## Code Examples

### 1. User Registration

**Frontend Request**:
```typescript
const handleRegister = async (formData) => {
  try {
    const response = await fetch('http://localhost:8000/api/auth/register/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: formData.email,
        password: formData.password,
        first_name: formData.firstName,
        last_name: formData.lastName,
        role: formData.role,
      }),
    });
    
    const data = await response.json();
    console.log('Registration success:', data);
  } catch (error) {
    console.error('Registration failed:', error);
  }
};
```

**Backend Response**:
```json
{
  "success": true,
  "message": "Operator registered successfully. You can now login.",
  "user": {
    "id": 15,
    "email": "operator@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "operator",
    "is_active": true
  }
}
```

### 2. User Login

**Frontend Request**:
```typescript
const handleLogin = async (email, password) => {
  const response = await fetch('http://localhost:8000/api/auth/login/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });
  
  const data = await response.json();
  
  // Store tokens
  localStorage.setItem('access_token', data.tokens.access);
  localStorage.setItem('refresh_token', data.tokens.refresh);
  localStorage.setItem('user', JSON.stringify(data.user));
};
```

**Backend Response**:
```json
{
  "success": true,
  "tokens": {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  },
  "user": {
    "id": 1,
    "email": "sameerareddy583@gmail.com",
    "first_name": "Sameera",
    "last_name": "Reddy",
    "role": "admin",
    "full_name": "Sameera Reddy"
  }
}
```

### 3. Authenticated API Request

**Frontend Request**:
```typescript
const fetchVessels = async () => {
  const token = localStorage.getItem('access_token');
  
  const response = await fetch('http://localhost:8000/api/vessels/', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
  
  const data = await response.json();
  return data;
};
```

**Request Headers**:
```
GET /api/vessels/ HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

### 4. Token Refresh

**Frontend Request**:
```typescript
const refreshAccessToken = async () => {
  const refreshToken = localStorage.getItem('refresh_token');
  
  const response = await fetch('http://localhost:8000/api/auth/refresh/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      refresh: refreshToken,
    }),
  });
  
  const data = await response.json();
  localStorage.setItem('access_token', data.access);
  
  return data.access;
};
```

---

## Testing

### 1. Manual Testing with cURL

**Register User**:
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "first_name": "Test",
    "last_name": "User",
    "role": "operator"
  }'
```

**Login**:
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

**Access Protected Endpoint**:
```bash
curl -X GET http://localhost:8000/api/vessels/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 2. Testing in Browser Console

```javascript
// Login
const login = async () => {
  const response = await fetch('http://localhost:8000/api/auth/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: 'sameerareddy583@gmail.com',
      password: 'admin'
    })
  });
  const data = await response.json();
  console.log('Access Token:', data.tokens.access);
  localStorage.setItem('access_token', data.tokens.access);
};

// Test authenticated request
const testAuth = async () => {
  const token = localStorage.getItem('access_token');
  const response = await fetch('http://localhost:8000/api/vessels/', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const data = await response.json();
  console.log('Vessels:', data);
};
```

### 3. JWT Token Decoder

Visit [jwt.io](https://jwt.io) to decode and inspect JWT tokens:

**Example Decoded Token**:
```json
{
  "token_type": "access",
  "exp": 1735000000,
  "iat": 1734996400,
  "jti": "abc123",
  "user_id": 1,
  "email": "sameerareddy583@gmail.com",
  "role": "admin"
}
```

---

## Demo Accounts

Test the authentication system with these pre-configured accounts:

| Role | Email | Password |
|------|-------|----------|
| Admin | sameerareddy583@gmail.com | admin |
| Analyst | analyst@maritimetracking.com | analyst |
| Operator | operator@maritimetracking.com | operator |

---

## Common Issues & Solutions

### Issue 1: "Invalid token" error
**Solution**: Token may have expired. Use refresh token to get new access token.

### Issue 2: "User is not active"
**Solution**: Admin needs to approve the user registration (for analyst/admin roles).

### Issue 3: CORS errors
**Solution**: Ensure frontend URL is added to `CORS_ALLOWED_ORIGINS` in Django settings.

### Issue 4: Token not sent with request
**Solution**: Check that token is stored in localStorage and added to Authorization header.

---

## Best Practices

1. **Never expose secret keys**: Use environment variables
2. **Use HTTPS in production**: Always encrypt token transmission
3. **Implement token refresh**: Don't make users login repeatedly
4. **Validate all inputs**: Prevent injection attacks
5. **Use short-lived access tokens**: Minimize security risks
6. **Implement rate limiting**: Prevent brute force attacks
7. **Log authentication events**: Monitor suspicious activity
8. **Handle token expiration gracefully**: Automatic refresh or clear error messages

---

## Conclusion

JWT Authentication provides a secure, scalable solution for our Maritime Vessel Tracking Platform. It enables:

✅ Secure user authentication  
✅ Stateless session management  
✅ Role-based access control  
✅ Cross-platform compatibility  
✅ Easy integration with microservices  

The implementation follows industry best practices and provides a solid foundation for enterprise-level security.

---

## References

- [JWT Official Documentation](https://jwt.io/introduction)
- [Django REST Framework JWT](https://django-rest-framework-simplejwt.readthedocs.io/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [RFC 7519 - JSON Web Token (JWT)](https://tools.ietf.org/html/rfc7519)

---

**Document Version**: 1.0  
**Last Updated**: December 18, 2025  
**Prepared by**: Sameera Reddy, Tharuni, Shweta  
**Mentor**: Aishwarya  
**Program**: Infosys Virtual Internship 6.0
