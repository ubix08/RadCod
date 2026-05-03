---
name: databases
description: Database design, SQL, PostgreSQL, MongoDB. Use for data persistence.
triggers:
 - database
 - sql
 - postgresql
 - mysql
 - mongodb
 - query
 - db
 - migrate
 - migration
 - orm
 - alembic
 - prisma
---

# Database Expertise

## Database Types

| Database | Use Case |
|----------|--------|
| PostgreSQL | Relational, complex queries |
| MySQL | Web apps, simple |
| MongoDB | Documents, flexible |
| Redis | Caching, sessions |

## SQL Basics

### Common Queries
```sql
-- Select
SELECT * FROM users WHERE active = true;

-- Insert
INSERT INTO users (name, email) VALUES ('John', 'john@email.com');

-- Update
UPDATE users SET updated_at = NOW() WHERE id = 1;

-- Delete
DELETE FROM users WHERE id = 1;
```

### Joins
```sql
SELECT u.name, o.total
FROM users u
JOIN orders o ON u.id = o.user_id
WHERE o.status = 'completed';
```

## PostgreSQL

### Common Operations
```bash
# Connect
psql -U user -d database

# List tables
\dt

# Describe table
\d users

# Run SQL file
psql -U user -d database -f query.sql
```

### Python with psycopg
```python
import psycopg

conn = psycopg.connect("postgresql://user:pass@localhost/db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM users")
result = cursor.fetchall()
```

## ORM (SQLAlchemy)

### Model Definition
```python
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(100), unique=True)
```

### Queries
```python
# Create
user = User(name="John", email="john@email.com")
session.add(user)
session.commit()

# Read
user = session.query(User).filter_by(email="john@email.com").first()

# Update
user.name = "Jane"
session.commit()

# Delete
session.delete(user)
session.commit()
```

## Migrations

### Alembic (Python)
```bash
# Create migration
alembic revision -m "add column"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Prisma (JavaScript)
```bash
# Create migration
npx prisma migrate dev --name init

# Apply
npx prisma migrate deploy
```

## Best Practices

1. **Indexes** - Add for frequently queried columns
2. **Constraints** - NOT NULL, unique, foreign keys
3. **Transactions** - Group related changes
4. **Backups** - Regular automated backups
5. **Connection Pooling** - Use for web apps