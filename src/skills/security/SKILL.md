---
name: security
description: Security best practices, authentication, authorization, secrets.
triggers:
 - auth
 - login
 - password
 - token
 - jwt
 - oauth
 - secret
 - api key
 - encryption
 - secure
 - vulnerability
 - exploit
 - injection
 - xss
 - csrf
---

# Security Expertise

## Core Principles

1. **Never store secrets in code**
   - API keys, passwords, tokens → environment variables
   - Use secrets management (AWS Secrets Manager, etc.)

2. **Validate all input**
   - User input is untrusted
   - Sanitize before use in queries

3. **Principle of least privilege**
   - Only grant necessary permissions

4. **Use secure defaults**
   - HTTPS not HTTP
   - Strong passwords
   - Short-lived tokens

## Common Vulnerabilities

### SQL Injection
```python
# BAD - vulnerable to SQL injection
query = f"SELECT * FROM users WHERE id = {user_id}"

# GOOD - parameterized query
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

### XSS (Cross-Site Scripting)
```javascript
// BAD
element.innerHTML = userInput

// GOOD - escape HTML
element.textContent = userInput

// GOOD - use framework escaping
<div>{userInput}</div>  // React escapes automatically
```

### CSRF (Cross-Site Request Forgery)
- Use anti-CSRF tokens
- Same-site cookies

### Sensitive Data Exposure
- Always use HTTPS
- Don't log sensitive data
- Encrypt at rest

## Authentication

### Passwords
```python
import bcrypt

# Hash
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# Verify
bcrypt.checkpw(password.encode(), hashed)
```

### JWT
```python
import jwt

# Create
token = jwt.encode({"user_id": user.id}, secret, algorithm="HS256")

# Verify
payload = jwt.decode(token, secret, algorithms=["HS256"])
```

### Best Practices
- Short-lived access tokens (15 min)
- Long-lived refresh tokens (days)
- Store refresh securely (httpOnly cookies)

## Authorization

### Role-Based Access Control (RBAC)
```python
ROLES = {
    "user": ["read"],
    "editor": ["read", "write"],
    "admin": ["read", "write", "delete"],
}

def check_permission(user, action):
    return action in ROLES.get(user.role, [])
```

## Secrets Management

```bash
# Environment variables
export API_KEY="secret-value"  # Don't commit!

# .env file (add to .gitignore)
# API_KEY=secret-value
```

## Security Headers

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
```