# 🎨 Scandinavian UI Design System

> A complete Nordic-inspired design system for Smart Fashion web application

---

## 📚 What's Included?

This design system provides everything needed to transform your UI into an authentic Scandinavian aesthetic:

### ✅ **Design Foundation**
- ✓ Color palette (muted blues, sage greens, warm neutrals)
- ✓ Typography system (Inter font, 8 sizes, 3 weights)
- ✓ Spacing system (8px base unit, consistent rhythm)
- ✓ Shadow system (soft, barely visible)
- ✓ Border radius specifications

### ✅ **Components Library**
- ✓ Navigation bar
- ✓ Buttons (primary, secondary, ghost)
- ✓ Cards with hover effects
- ✓ Form inputs & dropzones
- ✓ Tags & badges
- ✓ Statistics cards
- ✓ Gallery grid

### ✅ **Documentation**
- ✓ Design principles guide
- ✓ Implementation plan (6 phases)
- ✓ Quick start tutorial
- ✓ Component examples
- ✓ Troubleshooting tips

---

## 🚀 Quick Start (3 Steps)

### 1. Add CSS to Templates

Add this line to the `<head>` section of:
- `templates/index.html`
- `templates/gallery.html`
- `templates/product-detail.html`

```html
<link rel="stylesheet" href="/static/scandinavian.css?v={{ APP_VERSION }}">
```

### 2. Use Scandinavian Classes

Replace Tailwind classes with Scandinavian equivalents:

```html
<!-- Navigation -->
<nav class="scandi-nav">
  <div class="scandi-nav__container">
    <div class="scandi-nav__logo">Smart Fashion</div>
    <!-- ... -->
  </div>
</nav>

<!-- Buttons -->
<button class="btn btn-primary">Process Images</button>
<button class="btn btn-secondary">Download</button>

<!-- Cards -->
<div class="card">Content here</div>

<!-- Tags -->
<span class="tag">shirt</span>
```

### 3. Test

```bash
poetry run uvicorn main:app --reload
# Open http://localhost:8000
```

---

## 📖 Complete Documentation

| Document | Purpose | Quick Link |
|----------|---------|------------|
| **Design Guide** | Principles, colors, typography | [`docs/scandinavian_design_guide.md`](./scandinavian_design_guide.md) |
| **Implementation Plan** | Step-by-step with line numbers | [`docs/scandinavian_redesign_plan.md`](./scandinavian_redesign_plan.md) |
| **Quick Start** | 3-step tutorial + cheat sheet | [`docs/SCANDINAVIAN_QUICK_START.md`](./SCANDINAVIAN_QUICK_START.md) |
| **CSS Stylesheet** | Complete design system | [`static/scandinavian.css`](../static/scandinavian.css) |

---

## 🎨 Design Philosophy

### Scandinavian Design Principles

**1. Minimalism**
- Clean lines, uncluttered layouts
- Remove unnecessary elements
- "Less is more"

**2. Natural Colors**
- Whites and off-whites (#FAFAFA, #F5F5F5)
- Soft grays (#E8E8E8, #9E9E9E)
- Muted accents (dusty blue, sage green, warm beige)

**3. Generous Whitespace**
- Breathing room between elements
- 8px base spacing unit
- Not afraid of empty space

**4. Functional Beauty**
- Form follows function
- Every element serves a purpose
- Beautiful AND usable

---

## 🎨 Color Palette

### Primary Colors
```css
--scandi-dusty-blue: #6B8E9E       /* Primary actions */
--scandi-sage-green: #9CAF88       /* Secondary actions */
```

### Neutrals
```css
--scandi-white: #FAFAFA            /* Cards */
--scandi-off-white: #F5F5F5        /* Background */
--scandi-light-gray: #E8E8E8       /* Borders */
--scandi-medium-gray: #9E9E9E      /* Muted text */
--scandi-dark-gray: #4A4A4A        /* Body text */
--scandi-charcoal: #2E2E2E         /* Headings */
```

### Accents
```css
--scandi-warm-beige: #E8DCC4       /* Tags */
--scandi-terracotta: #D4A59A       /* Hover states */
--scandi-wood: #BF9B6F             /* Natural elements */
```

---

## 📐 Typography

### Font Family
```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
```

### Font Sizes
```css
--text-sm: 0.875rem;    /* 14px - Small text */
--text-base: 1rem;      /* 16px - Body text */
--text-lg: 1.125rem;    /* 18px - Large text */
--text-xl: 1.25rem;     /* 20px - Small headings */
--text-2xl: 1.5rem;     /* 24px - Section headings */
--text-3xl: 1.875rem;   /* 30px - Page headings */
--text-4xl: 2.25rem;    /* 36px - Hero headings */
```

---

## 📦 Component Library

### Buttons

```html
<!-- Primary button (dusty blue) -->
<button class="btn btn-primary">Primary Action</button>

<!-- Secondary button (sage green) -->
<button class="btn btn-secondary">Secondary Action</button>

<!-- Ghost button (outlined) -->
<button class="btn btn-ghost">Tertiary Action</button>

<!-- Large button -->
<button class="btn btn-primary btn-large">Large CTA</button>
```

### Cards

```html
<!-- Basic card -->
<div class="card">
  <div class="card__title">Card Title</div>
  <div class="card__content">Card content goes here...</div>
</div>
```

### Tags

```html
<!-- Basic tag (warm beige) -->
<span class="tag">shirt</span>

<!-- Colored tags -->
<span class="tag tag--primary">Category</span>
<span class="tag tag--secondary">Tag</span>
```

### Statistics

```html
<!-- Primary stat card (dusty blue accent) -->
<div class="stat-card stat-card--primary">
  <div class="stat-card__label">Objects Detected</div>
  <div class="stat-card__value">42</div>
</div>

<!-- Secondary stat card (sage green accent) -->
<div class="stat-card stat-card--secondary">
  <div class="stat-card__label">Unique Classes</div>
  <div class="stat-card__value">8</div>
</div>
```

### Gallery Grid

```html
<div class="gallery-grid">
  <div class="gallery-item">
    <img src="..." class="gallery-item__image" alt="">
    <div class="gallery-item__content">
      <!-- Content -->
    </div>
  </div>
  <!-- More items -->
</div>
```

---

## 🛠️ Migration Guide

### Tailwind → Scandinavian Mapping

| Tailwind | Scandinavian | Notes |
|----------|--------------|-------|
| `bg-blue-600` | `var(--scandi-dusty-blue)` | Muted blue |
| `bg-green-600` | `var(--scandi-sage-green)` | Muted green |
| `bg-white` | `var(--scandi-white)` | Off-white |
| `bg-gray-50` | `var(--scandi-off-white)` | Background |
| `text-gray-900` | `var(--scandi-charcoal)` | Dark text |
| `border-gray-300` | `var(--scandi-light-gray)` | Borders |
| `shadow-lg` | `var(--shadow-md)` | Softer shadow |
| `rounded-lg` | `border-radius: var(--radius-md)` | 8px |
| `px-8 py-3` | `padding: 12px 32px` | Button padding |

---

## ✨ Before & After

### Navigation
```html
<!-- BEFORE (Tailwind) -->
<nav class="bg-white shadow-md">
  <div class="max-w-7xl mx-auto px-4">
    <div class="flex justify-between items-center h-16">
      <!-- content -->
    </div>
  </div>
</nav>

<!-- AFTER (Scandinavian) -->
<nav class="scandi-nav">
  <div class="scandi-nav__container">
    <!-- content -->
  </div>
</nav>
```

### Buttons
```html
<!-- BEFORE -->
<button class="bg-green-600 text-white px-8 py-3 rounded-lg hover:bg-green-700 shadow-lg">
  Process Images
</button>

<!-- AFTER -->
<button class="btn btn-secondary">
  Process Images
</button>
```

### Tags
```html
<!-- BEFORE -->
<span class="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
  shirt
</span>

<!-- AFTER -->
<span class="tag">shirt</span>
```

---

## 🎯 Implementation Checklist

### Phase 1: Foundation ✓
- [x] Create `scandinavian.css`
- [x] Define custom properties
- [x] Import Inter font
- [ ] Link CSS in templates

### Phase 2: Navigation
- [ ] Update navigation markup
- [ ] Apply Scandinavian classes
- [ ] Test responsive behavior

### Phase 3: Buttons
- [ ] Replace all button classes
- [ ] Test hover states
- [ ] Verify accessibility

### Phase 4: Cards & Content
- [ ] Update card components
- [ ] Apply gallery grid classes
- [ ] Update tag styles

### Phase 5: Fine-Tuning
- [ ] Adjust spacing
- [ ] Test responsive breakpoints
- [ ] Verify color contrast
- [ ] Polish interactions

---

## 🔧 Customization

Want to adjust colors or spacing? Edit CSS custom properties:

```css
:root {
  /* Change primary color */
  --scandi-dusty-blue: #5A7D8C;  /* Darker */
  
  /* Adjust spacing */
  --space-4: 2.5rem;  /* Increase from 2rem */
  
  /* Softer shadows */
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.02);
}
```

---

## 📸 Visual Examples

### Navigation Bar
**Style:** Clean, minimal, text-only logo
**Colors:** White background, dusty blue highlights
**Spacing:** Generous (24px vertical padding)

### Buttons
**Style:** Subtle rounded corners (4px), uppercase text
**Colors:** Dusty blue (primary), sage green (secondary)
**Hover:** Soft lift effect (2px), subtle shadow

### Cards
**Style:** Soft shadows, generous padding
**Hover:** Lift effect (4px), enhanced shadow
**Spacing:** 32px grid gap

### Tags
**Style:** Warm beige background, dark gray text
**Hover:** Terracotta background, scale 1.05

---

## 🚫 Common Mistakes to Avoid

❌ **Don't:**
- Use bright saturated colors (blue-600, green-500)
- Add heavy drop shadows
- Over-use gradients
- Clutter the layout with too many elements
- Use tiny spacing

✅ **Do:**
- Embrace whitespace
- Use muted accent colors
- Keep shadows soft and subtle
- Remove unnecessary elements
- Follow the 8px spacing grid

---

## 📚 Resources

### Inspiration
- [IKEA](https://www.ikea.com) - Functional minimalism
- [HAY](https://hay.dk) - Nordic furniture
- [Muuto](https://www.muuto.com) - Modern design
- [Norwegian Design System](https://design.nav.no)

### Tools
- [Coolors Palette](https://coolors.co/fafafa-6b8e9e-9caf88-e8dcc4-d4a59a)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Google Fonts - Inter](https://fonts.google.com/specimen/Inter)

---

## 💬 Questions?

- **Design principles:** Read [`scandinavian_design_guide.md`](./scandinavian_design_guide.md)
- **Step-by-step guide:** See [`scandinavian_redesign_plan.md`](./scandinavian_redesign_plan.md)
- **Quick reference:** Check [`SCANDINAVIAN_QUICK_START.md`](./SCANDINAVIAN_QUICK_START.md)

---

**Made with ♥ using Scandinavian design principles**

**Version:** 2.0.0  
**Last Updated:** 2025-12-23
