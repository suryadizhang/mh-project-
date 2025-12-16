---
applyTo: 'apps/customer/**,apps/admin/**'
---

# My Hibachi – React Performance & Re-rendering Prevention

**Priority: HIGH** – Prevent performance issues before they happen.

---

## 🔴 The #1 Rule: Avoid Re-render Loops

**Never create dependency chains that trigger themselves.**

### ❌ The Classic Mistake (ACTUAL BUG FIXED):

```tsx
// BAD - This creates a re-render loop!
const [retryCount, setRetryCount] = useState(0);

const connectWebSocket = useCallback(() => {
  ws.onclose = () => {
    setRetryCount((prev) => prev + 1); // Changes state
    if (retryCount < 3) {
      // Uses stale value!
      connectWebSocket(); // Recursive call
    }
  };
}, [retryCount]); // Re-creates callback on retryCount change

useEffect(() => {
  connectWebSocket();
}, [connectWebSocket]); // Re-runs when callback changes = LOOP!
```

**What happens:**

1. `retryCount` changes → `connectWebSocket` recreated
2. `useEffect` sees new `connectWebSocket` → re-runs
3. Connection closes → `retryCount` changes → LOOP!

### ✅ The Correct Pattern:

```tsx
// GOOD - Use ref to avoid re-render loops
const retryCountRef = useRef(0);

const connectWebSocket = useCallback(() => {
  ws.onclose = () => {
    retryCountRef.current += 1; // No re-render!
    if (retryCountRef.current < 3) {
      connectWebSocket();
    }
  };
}, []); // Empty deps - stable reference

useEffect(() => {
  if (isOpen) {
    connectWebSocket();
    retryCountRef.current = 0; // Reset on open
  }
}, [isOpen, connectWebSocket]);
```

---

## 📊 When to Use What

| Need                                   | Use              | Why                          |
| -------------------------------------- | ---------------- | ---------------------------- |
| Trigger re-render on change            | `useState`       | React tracks changes         |
| Store value without re-render          | `useRef`         | Mutable, no re-render        |
| Stable function reference              | `useCallback`    | Prevents child re-renders    |
| Expensive computation                  | `useMemo`        | Caches result                |
| Track value across renders (no render) | `useRef`         | Instance variable            |
| Derived state from props               | Compute directly | Don't duplicate in state     |

---

## 🚫 Common Anti-Patterns

### 1. State in Callback Dependencies

```tsx
// ❌ BAD - callback changes on every state change
const [count, setCount] = useState(0);
const handleClick = useCallback(() => {
  console.log(count);
}, [count]); // Recreated every time count changes!

// ✅ GOOD - use ref for values needed in callbacks
const countRef = useRef(count);
countRef.current = count; // Sync ref with state
const handleClick = useCallback(() => {
  console.log(countRef.current);
}, []); // Stable reference
```

### 2. Missing Dependencies in useCallback

```tsx
// ❌ BAD - uses function but doesn't list in deps
const connectWebSocket = useCallback(() => {
  ws.onmessage = () => {
    playNotificationSound(); // Used but not in deps!
  };
}, [retryCount]); // Missing playNotificationSound

// ✅ GOOD - include all used functions
const connectWebSocket = useCallback(() => {
  ws.onmessage = () => {
    playNotificationSound();
  };
}, [playNotificationSound]); // Correct deps
```

### 3. Object/Array in Dependencies

```tsx
// ❌ BAD - new object every render
useEffect(() => {
  fetchData(options);
}, [{ page: 1, limit: 10 }]); // New object = always runs!

// ✅ GOOD - primitive values or useMemo
const options = useMemo(() => ({ page: 1, limit: 10 }), []);
useEffect(() => {
  fetchData(options);
}, [options]);
```

### 4. Too Many useState Calls

```tsx
// ❌ BAD - 15+ useState calls in one component
const [name, setName] = useState('');
const [email, setEmail] = useState('');
const [phone, setPhone] = useState('');
// ... 12 more ...

// ✅ GOOD - group related state
const [formData, setFormData] = useState({
  name: '',
  email: '',
  phone: '',
});

// Or use useReducer for complex state
const [state, dispatch] = useReducer(formReducer, initialState);
```

---

## ✅ Best Practices

### 1. Use Refs for Mutable Values That Don't Need Renders

```tsx
// WebSocket connections, timers, previous values, counters
const wsRef = useRef<WebSocket | null>(null);
const timerRef = useRef<NodeJS.Timeout | null>(null);
const prevValueRef = useRef(value);
```

### 2. Stable Callbacks with Empty Deps + Refs

```tsx
const valueRef = useRef(value);
valueRef.current = value; // Keep in sync

const stableCallback = useCallback(() => {
  // Use valueRef.current instead of value
  doSomething(valueRef.current);
}, []); // Stable forever
```

### 3. Lazy Load Heavy Components

```tsx
// ❌ BAD - loads 1200-line component immediately
import ChatWidget from './ChatWidget';

// ✅ GOOD - loads only when needed
const ChatWidget = dynamic(() => import('./ChatWidget'), {
  ssr: false,
  loading: () => <ChatWidgetSkeleton />,
});
```

### 4. Memoize Expensive Computations

```tsx
// ❌ BAD - recalculates on every render
const sortedItems = items.sort((a, b) => a.name.localeCompare(b.name));

// ✅ GOOD - only recalculates when items change
const sortedItems = useMemo(
  () => [...items].sort((a, b) => a.name.localeCompare(b.name)),
  [items]
);
```

### 5. Split Large Components

```tsx
// If component has 10+ useState calls, split it:
// - Extract form state into custom hook
// - Extract WebSocket logic into custom hook
// - Extract complex UI into sub-components
```

---

## 🔍 Debugging Re-renders

### Add Render Counter (Dev Only):

```tsx
const renderCount = useRef(0);
renderCount.current += 1;
console.log(`[${componentName}] Render #${renderCount.current}`);
```

### Use React DevTools:

1. Install React DevTools browser extension
2. Enable "Highlight updates when components render"
3. Look for components flashing repeatedly

### Check Dependency Arrays:

```tsx
// Log when effect runs
useEffect(() => {
  console.log('Effect running because deps changed');
}, [dep1, dep2]); // Which dep is changing?
```

---

## 📋 Component Complexity Limits

| Metric             | Limit   | Action if Exceeded          |
| ------------------ | ------- | --------------------------- |
| useState calls     | 8       | Use useReducer or split     |
| useEffect calls    | 5       | Extract to custom hooks     |
| Component lines    | 300     | Split into sub-components   |
| Props count        | 10      | Use context or composition  |
| Render time        | 16ms    | Memoize or virtualize       |

---

## 🎯 Quick Checklist Before PR

- [ ] No state in useCallback deps that changes frequently
- [ ] All useCallback deps are listed (or documented why not)
- [ ] Large components lazy loaded with `dynamic()`
- [ ] Expensive computations wrapped in `useMemo()`
- [ ] Refs used for values that don't need re-renders
- [ ] No object/array literals in dependency arrays
- [ ] Components under 300 lines

---

## 🔗 Related Docs

- `10-COPILOT_PERFORMANCE.instructions.md` – General performance
- [React useCallback docs](https://react.dev/reference/react/useCallback)
- [React useMemo docs](https://react.dev/reference/react/useMemo)

