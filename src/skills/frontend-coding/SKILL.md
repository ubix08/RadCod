---
name: frontend-coding
description: Modern frontend development (React, Vue, etc). Use for web UIs.
triggers:
 - react
 - vue
 - frontend
 - css
 - javascript
 - typescript
 - vite
 - nextjs
---

# Frontend Coding Expertise

## Project Structure

```
myapp/
├── src/
│   ├── components/
│   ├── pages/
│   ├── hooks/
│   ├── utils/
│   ├── App.tsx
│   └── main.tsx
├── public/
├── package.json
├── vite.config.ts
└── tsconfig.json
```

## Stack Recommendations

- **Framework**: React + Vite (fast) or Next.js (full-stack)
- **Language**: TypeScript (required)
- **Styling**: TailwindCSS or CSS Modules
- **State**: Zustand or React Query

## Commands

```bash
# Create project
npm create vite@latest myapp -- --template react-ts

# Install deps
npm install

# Run dev
npm run dev

# Build
npm run build

# Test
npm test
```

## Component Patterns

### Functional Component
```tsx
interface Props {
  title: string;
  onSubmit: (data: Data) => void;
}

export function MyComponent({ title, onSubmit }: Props) {
  const [state, setState] = useState<string>('');
  
  return (
    <div>
      <h1>{title}</h1>
      <input value={state} onChange={e => setState(e.target.value)} />
    </div>
  );
}
```

### Custom Hook
```tsx
function useData() {
  const [data, setData] = useState<Type | null>(null);
  
  useEffect(() => {
    fetch('/api').then(res => res.json()).then(setData);
  }, []);
  
  return data;
}
```

## Testing

```bash
# Unit tests
npm test

# With coverage
npm test -- --coverage
```

## Common Tools

- `axios` / `fetch` - HTTP requests
- `react-router-dom` - Routing
- `zustand` - State management
- `@tanstack/react-query` - Server state