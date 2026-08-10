# Mobile Adaptation Patterns Reference

## 1. Viewport & Safe Area

### viewport meta (required)
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
```
- `viewport-fit=cover` is required for notch/Dynamic Island devices
- Without it, `env(safe-area-inset-*)` returns 0

### Safe area padding
```css
/* Bottom nav / fixed footer */
.bottom-bar {
  padding-bottom: env(safe-area-inset-bottom, 0px);
}

/* Top header on standalone PWA */
.top-bar {
  padding-top: env(safe-area-inset-top, 0px);
}

/* Full-bleed layout */
body {
  padding: env(safe-area-inset-top) env(safe-area-inset-right)
           env(safe-area-inset-bottom) env(safe-area-inset-left);
}
```

### Tailwind safe area plugin
```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      padding: {
        'safe-top': 'env(safe-area-inset-top)',
        'safe-bottom': 'env(safe-area-inset-bottom)',
        'safe-left': 'env(safe-area-inset-left)',
        'safe-right': 'env(safe-area-inset-right)',
      },
    },
  },
};
```

## 2. Viewport Height (100vh problem)

Mobile browsers have a dynamic address bar. `100vh` = viewport WITH address bar visible = content gets cut off when bar hides.

### Modern solution: dynamic viewport units
```css
.full-height {
  height: 100dvh; /* dynamic: adapts as browser chrome shows/hides */
}

/* Fallback for older browsers */
.full-height {
  height: 100vh;
  height: 100dvh;
}
```

| Unit | Behavior |
|------|----------|
| `100vh` | Legacy, equals large viewport, causes overflow |
| `100svh` | Small viewport (chrome visible) — stable but short |
| `100lvh` | Large viewport (chrome hidden) — matches old 100vh |
| `100dvh` | Dynamic — resizes with browser chrome |

### Tailwind v3.4+
```html
<div class="h-dvh">...</div>
<!-- or h-svh, h-lvh -->
```

## 3. Overflow Prevention

### Global overflow guard
```css
html, body {
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
}
```

### Text overflow
```css
.text-truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.text-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
```

### Table / wide content
```css
.table-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

table {
  min-width: 100%;
}
```

### Image overflow
```css
img, video, iframe {
  max-width: 100%;
  height: auto;
}
```

## 4. Touch Targets

Apple HIG: minimum 44x44pt
Material Design: minimum 48x48dp

```css
.touch-target {
  min-height: 44px;
  min-width: 44px;
  /* Or use padding to expand hit area */
  padding: 12px;
}

/* Invisible hit area expansion */
.small-icon-btn {
  position: relative;
}
.small-icon-btn::after {
  content: '';
  position: absolute;
  inset: -8px; /* expand by 8px in all directions */
}
```

## 5. Multi-Level Page Navigation (Mobile Stack Pattern)

### Pattern: slide-in page stack
Replace sidebar/tab navigation with a stack-based push/pop model on mobile.

```
Desktop:                    Mobile:
┌──────┬──────────┐        ┌──────────┐
│ Side │ Content  │        │ List     │ ← Level 1
│ bar  │          │   →    │          │
│      │          │        └──────────┘
└──────┴──────────┘        ┌──────────┐
                           │ ← Detail │ ← Level 2 (slides in)
                           │          │
                           └──────────┘
```

### React implementation pattern
```tsx
// Use a layout with conditional rendering based on breakpoint
function ResponsiveLayout({ children }) {
  const isMobile = useMediaQuery('(max-width: 768px)');

  if (isMobile) {
    return <MobileStack>{children}</MobileStack>;
  }
  return <DesktopSidebar>{children}</DesktopSidebar>;
}

// Mobile stack with back button
function MobileStack() {
  const [stack, setStack] = useState([{ id: 'list', component: ListView }]);

  const push = (page) => setStack(prev => [...prev, page]);
  const pop = () => setStack(prev => prev.slice(0, -1));

  const current = stack[stack.length - 1];

  return (
    <div className="relative h-dvh overflow-hidden">
      <current.component onNavigate={push} onBack={pop} />
    </div>
  );
}
```

### Next.js App Router pattern
Use intercepting routes + parallel routes for mobile stack:
```
app/
  @sidebar/        ← parallel route (desktop only)
  (mobile)/        ← route group
    layout.tsx     ← mobile layout with back button
    [id]/page.tsx  ← detail page
  layout.tsx       ← responsive switch
```

### CSS slide transition
```css
.page-enter {
  transform: translateX(100%);
}
.page-enter-active {
  transform: translateX(0);
  transition: transform 300ms ease-out;
}
.page-exit-active {
  transform: translateX(-30%);
  transition: transform 300ms ease-out;
}
```

## 6. Browser Chrome Adaptation

### Hide Safari address bar color (theme-color)
```html
<meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#1a1a1a" media="(prefers-color-scheme: dark)">
```

### Status bar style (PWA standalone)
```html
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
```

### Prevent pull-to-refresh interference
```css
body {
  overscroll-behavior-y: contain;
}
```

### Prevent zoom on input focus (iOS)
```css
input, select, textarea {
  font-size: 16px; /* iOS won't zoom if font-size >= 16px */
}
```

## 7. Responsive Layout Patterns

### Container queries (modern)
```css
.card-container {
  container-type: inline-size;
}

@container (max-width: 400px) {
  .card { flex-direction: column; }
}
```

### Standard breakpoints
```css
/* Mobile first */
.grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

@media (min-width: 640px) {  /* sm */
  .grid { grid-template-columns: repeat(2, 1fr); }
}

@media (min-width: 1024px) { /* lg */
  .grid { grid-template-columns: repeat(3, 1fr); }
}
```

### Tailwind responsive
```html
<div class="flex flex-col md:flex-row">
  <aside class="hidden md:block w-64">Sidebar</aside>
  <main class="flex-1">Content</main>
</div>
```

## 8. Common Framework-Specific Fixes

### Next.js
- Use `next/image` with `sizes` prop for responsive images
- Add viewport meta in `app/layout.tsx` via `metadata.viewport`

### Tailwind CSS
- Use `sm:` prefix for mobile-first responsive
- `h-dvh` replaces `h-screen`
- `overflow-x-auto` on scroll containers
- `touch-manipulation` for faster tap response

### Vue / Nuxt
- Use `useMediaQuery` from VueUse
- `<ClientOnly>` for breakpoint-dependent rendering
