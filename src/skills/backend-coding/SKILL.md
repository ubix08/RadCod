---
name: backend-coding
description: Backend API development (FastAPI, Django, Express). Use for REST APIs.
triggers:
 - api
 - rest
 - fastapi
 - django
 - express
 - endpoint
 - backend
 - server
---

# Backend Coding Expertise

## Project Structure

```
myapi/
├── src/
│   ├── main.py
│   ├── api/
│   │   └── routes.py
│   ├── models/
│   ├── schemas/
│   └── database.py
├── tests/
├── pyproject.toml
└── README.md
```

## Framework Options

| Framework | Use Case | Fast | Full-Stack |
|-----------|---------|-----|------------|
| FastAPI | REST APIs, Microservices | ✅ | |
| Django | Full web apps | | ✅ |
| Express | Node APIs | ✅ | |

## FastAPI Example

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

@app.get("/items")
async def get_items():
    return items

@app.post("/items")
async def create_item(item: Item):
    items.append(item)
    return item
```

## Express Example

```javascript
const express = require('express');
const app = express();

app.use(express.json());

app.get('/api/items', (req, res) => {
  res.json(items);
});

app.post('/api/items', (req, res) => {
  const item = req.body;
  items.push(item);
  res.json(item);
});
```

## Commands

```bash
# FastAPI
pip install fastapi uvicorn
uvicorn main:app --reload

# Django
django-admin startproject myproject
python manage.py runserver

# Express
npm init -y
npm install express cors
node server.js
```

## Database

- **SQL**: PostgreSQL (recommended)
- **NoSQL**: MongoDB
- **ORM**: SQLAlchemy (Python), Prisma (JS)

## Testing

```bash
# Python
pytest

# JavaScript
npm test
```