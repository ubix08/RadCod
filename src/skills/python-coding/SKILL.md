---
name: python-coding
description: Python best practices, patterns, and idioms. Use for any Python development.
triggers:
 - python
 - pip
 - pytest
 - virtualenv
 - venv
---

# Python Coding Expertise

## Project Structure

```
myproject/
├── src/                   # Source code
│   └── myproject/
│       ├── __init__.py
│       ├── main.py
│       └── models.py
├── tests/                 # Test files
│   ├── __init__.py
│   ├── test_main.py
│   └── conftest.py
├── pyproject.toml         # Project config
├── README.md
└── LICENSE
```

## Dependencies

- Use `pyproject.toml` with modern `uv` or `pip`
- Pin versions: `package>=1.0.0`
- Dev deps: `pytest`, `ruff`, `black`

## Type Safety

- Always use type hints: `def foo(x: int) -> str:`
- Avoid `# type: ignore`
- Use `pydantic` for data validation

## Testing

- Use `pytest`: `pytest tests/`
- Fixtures in `conftest.py`
- Unit tests + integration tests

## Common Patterns

### Logging
```python
import logging
logger = logging.getLogger(__name__)
```

### Config
```python
from pydantic_settings import BaseSettings
class Config(BaseSettings):
    debug: bool = False
```

### HTTP
```python
import httpx
async with httpx.AsyncClient() as client:
    response = await client.get(url)
```

## Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate   # Windows

# or use uv
uv venv
uv sync
```