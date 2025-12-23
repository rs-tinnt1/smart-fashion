# Scandinavian Design Guide for Smart Fashion

## 📐 Scandinavian Design Principles

Scandinavian design (also called Nordic design) emphasizes:

### 1️⃣ **Minimalism & Simplicity**
- Clean lines, uncluttered layouts
- Removal of unnecessary elements
- Focus on functionality first

### 2️⃣ **Natural Colors & Light**
- **Whites & Off-Whites:** #FFFFFF, #F7F7F7, #FAFAFA
- **Soft Grays:** #E5E5E5, #9E9E9E, #757575
- **Warm Wood Tones:** #D4A574, #BF9B6F, #A0826D
- **Muted Accent Colors:** 
  - Dusty Blue: #6B8E9E, #8FA3AD
  - Sage Green: #9CAF88, #B5C4A1
  - Soft Terracotta: #D4A59A, #C8997B
  - Warm Beige: #E8DCC4, #D9CBAE

### 3️⃣ **Typography**
- Sans-serif fonts: Inter, Roboto, Helvetica
- Clean, readable, generous line-height
- Limited font weights (Regular 400, Medium 500, Bold 600)

### 4️⃣ **Whitespace (Negative Space)**
- Generous padding and margins
- Breathing room between elements
- Not afraid of empty space

### 5️⃣ **Natural Materials & Textures**
- Wood grain textures
- Linen, cotton textures
- Soft shadows (not harsh drop shadows)

### 6️⃣ **Functional Beauty**
- Every element serves a purpose
- Beautiful AND usable
- Form follows function

---

## 🎨 Color Palette for Smart Fashion

### Primary Colors
```css
--scandi-white: #FAFAFA;
--scandi-off-white: #F5F5F5;
--scandi-light-gray: #E8E8E8;
--scandi-medium-gray: #9E9E9E;
--scandi-dark-gray: #4A4A4A;
--scandi-charcoal: #2E2E2E;
```

### Accent Colors
```css
--scandi-dusty-blue: #6B8E9E;
--scandi-sage-green: #9CAF88;
--scandi-warm-beige: #E8DCC4;
--scandi-terracotta: #D4A59A;
--scandi-wood: #BF9B6F;
```

### Semantic Colors
```css
--scandi-success: #9CAF88;  /* Sage green */
--scandi-error: #C8997B;    /* Muted orange */
--scandi-warning: #E8DCC4;  /* Warm beige */
--scandi-info: #6B8E9E;     /* Dusty blue */
```

---

## 🖋️ Typography System

### Font Family
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
```

### Font Sizes
```css
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--text-3xl: 1.875rem;  /* 30px */
--text-4xl: 2.25rem;   /* 36px */
```

### Line Heights
```css
--leading-tight: 1.25;
--leading-normal: 1.5;
--leading-relaxed: 1.75;
```

---

## 📦 Spacing System

Use an 8px base unit:

```css
--space-1: 0.5rem;   /* 8px */
--space-2: 1rem;     /* 16px */
--space-3: 1.5rem;   /* 24px */
--space-4: 2rem;     /* 32px */
--space-6: 3rem;     /* 48px */
--space-8: 4rem;     /* 64px */
--space-12: 6rem;    /* 96px */
```

---

## 🌟 UI Components in Scandinavian Style

### Buttons
```css
/* Primary Button */
.btn-primary {
  background: var(--scandi-dusty-blue);
  color: var(--scandi-white);
  padding: 12px 32px;
  border-radius: 4px;  /* Subtle rounded corners */
  font-weight: 500;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  font-size: 0.875rem;
  transition: all 0.2s ease;
}

.btn-primary:hover {
  background: #5A7D8C;
  box-shadow: 0 4px 12px rgba(107, 142, 158, 0.25);
}

/* Secondary Button */
.btn-secondary {
  background: transparent;
  color: var(--scandi-dark-gray);
  border: 1.5px solid var(--scandi-light-gray);
  padding: 12px 32px;
  border-radius: 4px;
}
```

### Cards
```css
.card {
  background: var(--scandi-white);
  border-radius: 8px;
  padding: var(--space-4);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);  /* Very soft shadow */
  transition: box-shadow 0.3s ease;
}

.card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}
```

### Inputs
```css
.input {
  background: var(--scandi-off-white);
  border: 1px solid var(--scandi-light-gray);
  padding: 12px 16px;
  border-radius: 4px;
  font-size: 1rem;
  transition: border-color 0.2s ease;
}

.input:focus {
  outline: none;
  border-color: var(--scandi-dusty-blue);
  background: var(--scandi-white);
}
```

---

## 🖼️ Layout Guidelines

### Navigation
- Clean, horizontal navigation
- Minimal items (3-4 max)
- Generous padding: 16px-24px vertical

### Content Grid
- Use 12-column grid with generous gutters (24px-32px)
- Max content width: 1200px-1400px
- Center-aligned

### Cards & Images
- Aspect ratios: 3:4 (portrait), 16:9 (landscape)
- Subtle hover effects (scale 1.02, not 1.1)
- Soft border-radius: 4px-8px

---

## ✨ Interaction Patterns

### Hover States
```css
/* Subtle lift */
.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
}
```

### Focus States
```css
*:focus {
  outline: 2px solid var(--scandi-dusty-blue);
  outline-offset: 2px;
}
```

### Loading States
- Use skeleton screens (not spinners)
- Soft pulsing animation

---

## 🚫 What to Avoid

❌ Bright, saturated colors (blue-600, green-500, etc.)  
❌ Heavy drop shadows  
❌ Excessive gradients  
❌ Multiple accent colors at once  
❌ Cluttered layouts  
❌ Tiny spacing  
❌ Aggressive animations  

---

## ✅ Scandinavian Design Checklist

- [ ] Color palette: whites, grays, muted accents
- [ ] Typography: Inter or similar sans-serif
- [ ] Generous whitespace (padding, margins)
- [ ] Soft shadows (0-8px blur, low opacity)
- [ ] Subtle border-radius (4-8px)
- [ ] Minimal UI chrome
- [ ] Natural, organic feel
- [ ] Functional first, beautiful second

---

## 📚 References

- **Inspiration Sites:**
  - IKEA: https://www.ikea.com
  - Muuto: https://www.muuto.com
  - Hay: https://hay.dk
  - &Tradition: https://www.andtradition.com

- **Design Systems:**
  - Norwegian Design System: https://design.nav.no
  - Swedish Design System: https://designsystemet.se

---

**Next Step:** Apply these principles to the Smart Fashion templates!
