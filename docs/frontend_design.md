# Frontend Design Guide - Smart Fashion

> **Comprehensive frontend architecture, design system, and coding standards**

**Last Updated:** 2025-12-25
**Version:** 2.0.0
**Status:** Production Ready

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Design System](#design-system)
3. [Component Library](#component-library)
4. [JavaScript Architecture](#javascript-architecture)
5. [Template Structure](#template-structure)
6. [Coding Standards](#coding-standards)
7. [File Organization](#file-organization)
8. [Best Practices](#best-practices)

---

## 🏗️ Architecture Overview

### Technology Stack

**Core Technologies:**
- **Templates:** Jinja2 with inheritance and macros
- **Styling:** Global CSS design system + Tailwind CSS (utility)
- **JavaScript:** ES Modules (native browser support)
- **Fonts:** Newsreader (serif) + Manrope (sans-serif)

**No Framework Dependencies:**
- ✅ No React/Vue/Angular
- ✅ No jQuery
- ✅ No build tools required
- ✅ Browser-native ES modules

### Directory Structure

```
smart-fashion/
├── static/
│   ├── global.css                    # Main design system
│   └── js/
│       ├── main.js                   # Entry point & router
│       ├── utils/                    # Shared utilities
│       │   ├── api.js               # API calls
│       │   ├── constants.js         # App constants
│       │   ├── dom.js               # DOM helpers
│       │   └── formatters.js        # Data formatters
│       └── modules/                  # Feature modules (flat)
│           ├── canvasModal.js       # Canvas modal manager
│           ├── canvasRenderer.js    # Base canvas class
│           ├── fileHandler.js       # File validation
│           ├── galleryPage.js       # Gallery logic
│           ├── imageProcessor.js    # Image processing
│           ├── productCanvas.js     # Product canvas (extends base)
│           ├── productPage.js       # Product detail logic
│           └── uploadPage.js        # Upload page logic
│
├── templates/
│   ├── layouts/
│   │   └── base.html                # Master layout
│   ├── macros/                       # Reusable components
│   │   ├── navigation.html          # Nav with active state
│   │   ├── pagination.html          # Pagination controls
│   │   └── stats.html               # Stat cards
│   ├── components/                   # Includes (flat)
│   │   ├── canvas_modal.html        # Canvas editor modal
│   │   ├── gallery_item.html        # Gallery card macro
│   │   └── upload_zone.html         # File upload zone
│   └── pages/                        # Page templates
│       ├── index.html               # Upload page
│       ├── gallery.html             # Gallery page
│       └── product_detail.html      # Product detail
```

---

## 🎨 Design System

### Design Philosophy

**Scandinavian Principles:**
1. **Minimalism** - Clean, uncluttered layouts
2. **Natural Colors** - Muted palette, no bright saturation
3. **Generous Whitespace** - Breathing room, 8px base unit
4. **Functional Beauty** - Form follows function
5. **Soft Shadows** - Barely visible, natural depth
6. **Tactile Quality** - Organic, human-centered

### Color Palette

#### Primary Colors
```css
--scandi-white: #FAFAFA;           /* Card backgrounds */
--scandi-off-white: #F5F5F5;       /* Page background */
--scandi-light-gray: #E8E8E8;      /* Borders, dividers */
--scandi-medium-gray: #9E9E9E;     /* Muted text, placeholders */
--scandi-dark-gray: #4A4A4A;       /* Body text */
--scandi-charcoal: #2E2E2E;        /* Headings */
```

#### Accent Colors
```css
--scandi-dusty-blue: #6B8E9E;      /* Primary actions, links */
--scandi-dusty-blue-hover: #5A7D8C;
--scandi-sage-green: #9CAF88;      /* Secondary actions */
--scandi-sage-green-hover: #88A073;
--scandi-warm-beige: #E8DCC4;      /* Tags, soft accents */
--scandi-terracotta: #D4A59A;      /* Hover states */
--scandi-wood: #BF9B6F;            /* Natural elements */
```

#### Semantic Colors
```css
--scandi-primary: var(--scandi-dusty-blue);
--scandi-secondary: var(--scandi-sage-green);
--scandi-success: var(--scandi-sage-green);
--scandi-error: #C8997B;           /* Muted orange */
--scandi-warning: var(--scandi-warm-beige);
--scandi-info: var(--scandi-dusty-blue);
```

### Typography

#### Font Family
```css
/* Serif for headings */
font-family: 'Newsreader', Georgia, serif;

/* Sans-serif for body */
font-family: 'Manrope', -apple-system, BlinkMacSystemFont, sans-serif;
```

#### Font Scale
```css
--text-xs: 0.75rem;     /* 12px - Captions */
--text-sm: 0.875rem;    /* 14px - Small text */
--text-base: 1rem;      /* 16px - Body */
--text-lg: 1.125rem;    /* 18px - Large text */
--text-xl: 1.25rem;     /* 20px - Small headings */
--text-2xl: 1.5rem;     /* 24px - Section headings */
--text-3xl: 1.875rem;   /* 30px - Page headings */
--text-4xl: 2.25rem;    /* 36px - Hero headings */
```

#### Line Heights
```css
--leading-tight: 1.25;    /* Headings */
--leading-normal: 1.5;    /* Body text */
--leading-relaxed: 1.75;  /* Paragraphs */
```

### Spacing System

**8px Base Unit:**
```css
--space-1: 0.5rem;   /* 8px */
--space-2: 1rem;     /* 16px */
--space-3: 1.5rem;   /* 24px */
--space-4: 2rem;     /* 32px */
--space-5: 2.5rem;   /* 40px */
--space-6: 3rem;     /* 48px */
--space-8: 4rem;     /* 64px */
--space-12: 6rem;    /* 96px */
```

### Shadows

**Soft, Subtle Depths:**
```css
--shadow-xs: 0 1px 3px rgba(0, 0, 0, 0.03);
--shadow-sm: 0 2px 6px rgba(0, 0, 0, 0.04);
--shadow-md: 0 4px 12px rgba(0, 0, 0, 0.06);
--shadow-lg: 0 8px 20px rgba(0, 0, 0, 0.08);
--shadow-xl: 0 12px 28px rgba(0, 0, 0, 0.10);
```

### Border Radius

```css
--radius-sm: 4px;
--radius-md: 8px;
--radius-lg: 12px;
--radius-full: 9999px;
```

### Transitions

```css
--transition-fast: 150ms ease;
--transition-base: 250ms ease;
--transition-slow: 350ms ease;
```

---

## 📦 Component Library

### Navigation

**Class:** `.scandi-nav`

```html
<nav class="scandi-nav">
  <div class="scandi-nav__container">
    <div class="scandi-nav__logo">FASHION AI</div>
    <div>
      <a href="/" class="scandi-nav__link scandi-nav__link--active">Upload</a>
      <a href="/gallery" class="scandi-nav__link">Gallery</a>
      <a href="/docs" class="scandi-nav__link">Docs</a>
    </div>
  </div>
</nav>
```

**Features:**
- Fixed top, full width
- Active state with bottom border
- Generous padding (24px vertical)
- Clean typography

### Buttons

**Classes:** `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-ghost`, `.btn-large`

```html
<!-- Primary action (dusty blue) -->
<button class="btn btn-primary">Process Images</button>

<!-- Secondary action (sage green) -->
<button class="btn btn-secondary">Download</button>

<!-- Tertiary action (outlined) -->
<button class="btn btn-ghost">Clear</button>

<!-- Large CTA -->
<button class="btn btn-primary btn-large">Get Started</button>
```

**Styling:**
- Uppercase text, 0.5px letter-spacing
- Padding: 12px 32px (large: 16px 48px)
- Border-radius: 4px
- Hover: Lift 2px + subtle shadow

### Cards

**Class:** `.card`

```html
<div class="card">
  <div class="card__title">Card Title</div>
  <div class="card__content">Content goes here...</div>
</div>
```

**Features:**
- White background (#FAFAFA)
- Soft shadow (shadow-sm)
- Padding: 32px
- Hover: Enhanced shadow + lift 4px

### Tags

**Classes:** `.tag`, `.tag--primary`, `.tag--secondary`

```html
<span class="tag">shirt</span>
<span class="tag tag--primary">Featured</span>
<span class="tag tag--secondary">New</span>
```

**Styling:**
- Warm beige background (#E8DCC4)
- Dark gray text (#4A4A4A)
- Padding: 8px 16px
- Border-radius: 4px
- Hover: Terracotta + scale 1.05

### Statistics Cards

**Classes:** `.stat-card`, `.stat-card--primary`, `.stat-card--secondary`

```html
<div class="stat-card stat-card--primary">
  <p class="stat-card__label">Objects Detected</p>
  <p class="stat-card__value">42</p>
</div>
```

**Features:**
- Off-white background
- Left border accent (4px)
- Hover: Shadow + translate-x

### Drop Zone

**Class:** `.drop-zone`

```html
<div class="drop-zone">
  <div class="drop-zone__icon">
    <!-- SVG icon -->
  </div>
  <div class="drop-zone__title">Drop images here</div>
  <div class="drop-zone__subtitle">or click to browse</div>
  <div class="drop-zone__info">Max 100 files, 500KB each</div>
</div>
```

**Features:**
- Dashed border (light gray)
- Off-white background
- Generous padding (64px)
- Hover: Border color change + shadow

### Gallery Grid

**Class:** `.gallery-grid`

```html
<div class="gallery-grid">
  <div class="gallery-item">
    <img src="..." class="gallery-item__image" alt="">
    <div class="gallery-item__content">
      <!-- Metadata, tags, actions -->
    </div>
  </div>
</div>
```

**Features:**
- Auto-fill grid (min 320px)
- Gap: 32px
- Hover: Lift 6px + enhanced shadow
- Image scale 1.02 on hover

### Inputs

**Class:** `.input`

```html
<input type="text" class="input" placeholder="Search...">
```

**Styling:**
- Off-white background
- Light gray border
- Focus: Dusty blue border + white background
- Ring shadow on focus

---

## 💻 JavaScript Architecture

### Module System

**ES Modules Pattern:**
```javascript
// Import
import { functionName } from "./path/to/module.js";

// Export
export function functionName() { }
export class ClassName { }
```

**No Bundler Required:**
- Relative paths with `.js` extension
- Browser-native module support
- Type: `<script type="module">`

### Entry Point: `main.js`

**Router Pattern:**
```javascript
import { initUploadPage } from "./modules/uploadPage.js";
import { initGalleryPage } from "./modules/galleryPage.js";
import { initProductPage } from "./modules/productPage.js";
import { initCanvasModal } from "./modules/canvasModal.js";

document.addEventListener("DOMContentLoaded", () => {
  const currentPage = document.body.dataset.page;

  switch (currentPage) {
    case "upload":
      initUploadPage();
      initCanvasModal();
      break;
    case "gallery":
      initGalleryPage();
      break;
    case "product":
      initProductPage();
      break;
  }

  applyDynamicStyling();
});
```

**Page Detection:**
```html
<body data-page="upload">
```

### Utils Layer

#### `utils/constants.js`
```javascript
export const MAX_FILES = 100;
export const MAX_FILE_SIZE_KB = 500;

export const TAG_COLORS = {
  "short sleeve top": "#FF6B6B",
  "long sleeve top": "#4ECDC4",
  // ... 13 clothing categories
};

export const CANVAS_COLORS = [
  "#FF6B6B", "#4ECDC4", "#45B7D1", // ... 10 colors
];
```

#### `utils/api.js`
```javascript
export async function segmentImages(files) {
  const formData = new FormData();
  files.forEach(file => formData.append("files", file));
  const response = await fetch("/api/segment", {
    method: "POST",
    body: formData
  });
  if (!response.ok) throw new Error("Processing failed");
  return response.json();
}

export async function deleteImage(fileId) { }
export async function getImageDetails(imageId) { }
```

#### `utils/dom.js`
```javascript
export function show(element) {
  if (element) element.classList.remove("hidden");
}

export function hide(element) {
  if (element) element.classList.add("hidden");
}

export function clearElement(element) {
  if (element) element.innerHTML = "";
}
```

#### `utils/formatters.js`
```javascript
export function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
}

export function formatDate(dateString) { }
export function formatConfidence(confidence) { }
```

### Class-Based Architecture

#### Base Class: `CanvasRenderer`
```javascript
export class CanvasRenderer {
  constructor(canvasElement) {
    this.canvas = canvasElement;
    this.ctx = canvasElement?.getContext("2d");
    this.currentImage = null;
  }

  loadImage(imageUrl) { /* Returns Promise */ }
  drawDetections(objects) { }
  drawObject(obj, index) { }
  clear() { }
  redrawImage() { }
  download(filename) { }
  renderObjectsList(objects, container) { }
}
```

#### Extended Class: `ProductCanvas`
```javascript
import { CanvasRenderer } from "./canvasRenderer.js";

export class ProductCanvas extends CanvasRenderer {
  constructor(canvasElement, detectionsData) {
    super(canvasElement);
    this.detections = detectionsData;
    this.displayMode = "polygon";
  }

  setDisplayMode(mode) {
    this.displayMode = mode;
    this.redraw();
  }

  redraw() { }
  drawDetectionPolygon(detection) { }
  drawDetectionRectangle(detection) { }
}
```

#### Validation Class: `FileHandler`
```javascript
export class FileHandler {
  constructor() {
    this.selectedFiles = [];
  }

  validateFiles(files) {
    const result = { valid: [], errors: [] };
    // Validation logic
    return result;
  }

  addFiles(newFiles) { }
  removeFile(index) { }
  getFiles() { return this.selectedFiles; }
  hasFiles() { return this.selectedFiles.length > 0; }
}
```

### Module Pattern Example

**Upload Page Module:**
```javascript
import { FileHandler } from "./fileHandler.js";
import { processImages } from "./imageProcessor.js";
import { formatFileSize } from "../utils/formatters.js";
import { show, hide, clearElement } from "../utils/dom.js";

export function initUploadPage() {
  const fileHandler = new FileHandler();

  setupDropZoneEvents(fileHandler);
  setupFileInputEvents(fileHandler);
  setupProcessButton(fileHandler);
}

function setupDropZoneEvents(fileHandler) { }
function setupFileInputEvents(fileHandler) { }
function setupProcessButton(fileHandler) { }
function updateFilePreview(fileHandler) { }
```

---

## 🏛️ Template Structure

### Jinja2 Inheritance

**Base Layout:**
```jinja2
<!-- templates/layouts/base.html -->
<!DOCTYPE html>
<html lang="en">
  <head>
    <title>{% block title %}Fashion AI{% endblock %}</title>
    <link rel="stylesheet" href="/static/global.css?v={{ APP_VERSION }}">
    {% block extra_head %}{% endblock %}
  </head>
  <body data-page="{% block page_identifier %}{% endblock %}">
    {% block navigation %}{% endblock %}
    <main class="pt-24">
      {% block content %}{% endblock %}
    </main>
    {% block modals %}{% endblock %}
    {% block scripts %}{% endblock %}
  </body>
</html>
```

**Page Template:**
```jinja2
<!-- templates/pages/index.html -->
{% extends "layouts/base.html" %}
{% from "macros/navigation.html" import render_nav %}

{% block title %}Upload — Fashion AI{% endblock %}
{% block page_identifier %}upload{% endblock %}

{% block navigation %}
  {{ render_nav('upload') }}
{% endblock %}

{% block content %}
  <!-- Page content -->
  {% include 'components/upload_zone.html' %}
{% endblock %}

{% block modals %}
  {% include 'components/canvas_modal.html' %}
{% endblock %}

{% block scripts %}
  <script type="module" src="/static/js/main.js?v={{ APP_VERSION }}"></script>
{% endblock %}
```

### Macros (Reusable Components)

**Navigation Macro:**
```jinja2
<!-- templates/macros/navigation.html -->
{% macro render_nav(active_page='') %}
<nav class="scandi-nav">
  <div class="scandi-nav__container">
    <div class="scandi-nav__logo">FASHION AI</div>
    <div>
      <a href="/" class="scandi-nav__link {% if active_page == 'upload' %}scandi-nav__link--active{% endif %}">
        Upload
      </a>
      <a href="/gallery" class="scandi-nav__link {% if active_page == 'gallery' %}scandi-nav__link--active{% endif %}">
        Gallery
      </a>
    </div>
  </div>
</nav>
{% endmacro %}
```

**Pagination Macro:**
```jinja2
<!-- templates/macros/pagination.html -->
{% macro render_pagination(current_page, total_pages, base_url, current_tag=None) %}
<div class="pagination">
  <!-- Previous button -->
  <a href="{{ base_url }}?page={{ current_page - 1 }}{% if current_tag %}&tag={{ current_tag }}{% endif %}"
     class="btn btn-ghost {% if current_page <= 1 %}disabled{% endif %}">
    Previous
  </a>

  <!-- Page numbers -->
  {% for page in range(1, total_pages + 1) %}
    <a href="{{ base_url }}?page={{ page }}{% if current_tag %}&tag={{ current_tag }}{% endif %}"
       class="btn {% if page == current_page %}btn-primary{% else %}btn-ghost{% endif %}">
      {{ page }}
    </a>
  {% endfor %}

  <!-- Next button -->
  <a href="{{ base_url }}?page={{ current_page + 1 }}{% if current_tag %}&tag={{ current_tag }}{% endif %}"
     class="btn btn-ghost {% if current_page >= total_pages %}disabled{% endif %}">
    Next
  </a>
</div>
{% endmacro %}
```

**Stats Card Macro:**
```jinja2
<!-- templates/macros/stats.html -->
{% macro stat_card(label, value, variant='primary') %}
<div class="stat-card stat-card--{{ variant }}">
  <p class="stat-card__label">{{ label }}</p>
  <p class="stat-card__value">{{ value }}</p>
</div>
{% endmacro %}
```

**Gallery Item Macro:**
```jinja2
<!-- templates/components/gallery_item.html -->
{% macro gallery_card(image) %}
<div class="gallery-item">
  <a href="/product/{{ image.file_id }}">
    <img src="{{ image.image_url }}" class="gallery-item__image" alt="">
  </a>
  <div class="gallery-item__content">
    <p><strong>{{ image.object_count }}</strong> objects detected</p>
    <div class="tags">
      {% for cls in image.classes %}
        <span class="tag">{{ cls }}</span>
      {% endfor %}
    </div>
    <div class="actions">
      <a href="{{ image.image_url }}" download class="btn btn-secondary">Download</a>
      <button data-delete-image="{{ image.file_id }}" class="btn btn-ghost">Delete</button>
    </div>
  </div>
</div>
{% endmacro %}
```

### Include Components

**Canvas Modal:**
```jinja2
<!-- templates/components/canvas_modal.html -->
<div id="canvasModal" class="modal-overlay hidden">
  <div class="modal-content">
    <div class="modal-header">
      <h3>Canvas Editor</h3>
      <button id="closeCanvasBtn">×</button>
    </div>
    <div class="modal-body">
      <canvas id="drawCanvas"></canvas>
      <div id="objectsList"></div>
    </div>
    <div class="modal-footer">
      <button id="downloadCanvasBtn" class="btn btn-primary">Download</button>
    </div>
  </div>
</div>
```

**Upload Zone:**
```jinja2
<!-- templates/components/upload_zone.html -->
<div id="dropZone" class="drop-zone">
  <input type="file" id="fileInput" multiple accept="image/*" class="hidden">
  <div class="drop-zone__icon">
    <!-- SVG icon -->
  </div>
  <div class="drop-zone__title">Drop images here</div>
  <div class="drop-zone__subtitle">or click to browse</div>
  <div class="drop-zone__info">Max {{ MAX_FILES }} files, {{ MAX_FILE_SIZE_KB }}KB each</div>
</div>

<div id="fileList" class="space-y-3"></div>

<div id="loadingIndicator" class="hidden">
  <div class="loader"></div>
  <p>Processing images...</p>
</div>

<button id="processBtn" class="btn btn-primary btn-large">
  Process Images
</button>
```

---

## 📏 Coding Standards

### HTML Standards

**DO:**
```html
✅ Use semantic HTML5 tags
✅ Include alt text for images
✅ Use data-* attributes for JS hooks
✅ Maintain consistent indentation (2 spaces)
✅ Close all tags properly
✅ Use kebab-case for IDs and classes
```

**DON'T:**
```html
❌ Inline JavaScript (use ES modules)
❌ Inline styles (use CSS classes)
❌ Generic div soup (use semantic tags)
❌ Missing form labels
❌ Non-descriptive IDs
```

### CSS Standards

**DO:**
```css
✅ Use CSS custom properties
✅ Follow BEM naming convention
✅ Group related styles together
✅ Use mobile-first approach
✅ Prefer classes over IDs for styling
```

**Example:**
```css
/* BEM: Block__Element--Modifier */
.card { }
.card__title { }
.card__content { }
.card--featured { }
```

**DON'T:**
```css
❌ !important (unless absolutely necessary)
❌ Overly specific selectors
❌ Magic numbers (use CSS variables)
❌ Inline styles
❌ Browser-specific hacks without fallbacks
```

### JavaScript Standards

**DO:**
```javascript
✅ Use ES6+ syntax
✅ Export/import for modularity
✅ Use const/let (not var)
✅ Add JSDoc comments for functions
✅ Handle errors with try/catch
✅ Use async/await for promises
```

**Example:**
```javascript
/**
 * Process images through segmentation API
 * @param {FileHandler} fileHandler - File handler instance
 * @param {HTMLElement} resultsContainer - Results container
 * @returns {Promise<void>}
 */
export async function processImages(fileHandler, resultsContainer) {
  try {
    const files = fileHandler.getFiles();
    const response = await segmentImages(files);
    displayResults(response.results, resultsContainer);
  } catch (error) {
    console.error("Processing failed:", error);
    alert("Failed to process images. Please try again.");
  }
}
```

**DON'T:**
```javascript
❌ Global variables
❌ var keyword
❌ Callbacks (use promises/async-await)
❌ Magic numbers (use constants)
❌ Nested ternaries
❌ Silent error swallowing
```

### Jinja2 Standards

**DO:**
```jinja2
✅ Use {% block %} for extensibility
✅ Use {% macro %} for reusable components
✅ Use {% include %} for shared partials
✅ Use filters for formatting: {{ value|upper }}
✅ Add whitespace control: {%- if -%}
```

**DON'T:**
```jinja2
❌ Complex logic in templates (use Python)
❌ Hardcoded URLs (use url_for or route names)
❌ Duplicate code (use macros)
❌ Missing {% endblock %}, {% endmacro %}
```

---

## 🗂️ File Organization

### Naming Conventions

**Files:**
- HTML templates: `kebab-case.html` (e.g., `product_detail.html`)
- JavaScript: `camelCase.js` (e.g., `uploadPage.js`)
- CSS: `kebab-case.css` (e.g., `global.css`)

**CSS Classes:**
- BEM: `.block__element--modifier`
- Utilities: `.text-center`, `.mb-4`

**JavaScript:**
- Functions: `camelCase` (e.g., `initUploadPage`)
- Classes: `PascalCase` (e.g., `FileHandler`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_FILES`)

**Jinja2:**
- Macros: `snake_case` (e.g., `render_nav`)
- Blocks: `snake_case` (e.g., `page_identifier`)

### Import Paths

**JavaScript:**
```javascript
// Relative imports with .js extension
import { func } from "./module.js";       // Same directory
import { func } from "../utils/api.js";   // Parent directory
```

**Jinja2:**
```jinja2
{# Relative to templates/ directory #}
{% extends "layouts/base.html" %}
{% from "macros/navigation.html" import render_nav %}
{% include 'components/canvas_modal.html' %}
```

### Version Control

**Cache Busting:**
```html
<link rel="stylesheet" href="/static/global.css?v={{ APP_VERSION }}">
<script type="module" src="/static/js/main.js?v={{ APP_VERSION }}"></script>
```

---

## ✅ Best Practices

### Performance

1. **Lazy Loading:**
   ```javascript
   // Dynamic imports for code splitting (if needed)
   const module = await import("./heavy-module.js");
   ```

2. **Event Delegation:**
   ```javascript
   // Instead of multiple listeners
   document.addEventListener("click", (e) => {
     if (e.target.matches("[data-delete-image]")) {
       handleDelete(e.target.dataset.deleteImage);
     }
   });
   ```

3. **Debouncing:**
   ```javascript
   function debounce(func, wait) {
     let timeout;
     return function(...args) {
       clearTimeout(timeout);
       timeout = setTimeout(() => func.apply(this, args), wait);
     };
   }
   ```

### Accessibility

1. **Keyboard Navigation:**
   ```html
   <button tabindex="0" aria-label="Close modal">×</button>
   ```

2. **ARIA Attributes:**
   ```html
   <div role="alert" aria-live="polite">Processing complete!</div>
   ```

3. **Focus Management:**
   ```javascript
   function openModal(modal) {
     modal.classList.remove("hidden");
     modal.querySelector("button").focus();
   }
   ```

### Security

1. **Input Validation:**
   ```javascript
   function validateFile(file) {
     const allowedTypes = ["image/jpeg", "image/png", "image/webp"];
     if (!allowedTypes.includes(file.type)) {
       throw new Error("Invalid file type");
     }
   }
   ```

2. **XSS Prevention:**
   ```javascript
   // Don't use innerHTML with user input
   element.textContent = userInput;  // ✅ Safe
   element.innerHTML = userInput;    // ❌ Dangerous
   ```

3. **CSRF Protection:**
   ```python
   # Backend handles CSRF tokens
   # Frontend just needs to pass them
   ```

### Error Handling

1. **User-Friendly Messages:**
   ```javascript
   try {
     await apiCall();
   } catch (error) {
     console.error("API Error:", error);
     alert("Something went wrong. Please try again.");
   }
   ```

2. **Graceful Degradation:**
   ```javascript
   if (!canvas.getContext) {
     alert("Your browser doesn't support canvas.");
     return;
   }
   ```

### Testing

1. **Manual Testing Checklist:**
   - [ ] All pages load without errors
   - [ ] All ES modules resolve correctly
   - [ ] Buttons and interactions work
   - [ ] Forms validate properly
   - [ ] Responsive design works
   - [ ] Browser console has no errors

2. **Browser Testing:**
   - Chrome 61+ ✅
   - Firefox 60+ ✅
   - Safari 10.1+ ✅
   - Edge 16+ ✅

---

## 🚫 Anti-Patterns to Avoid

### HTML
- ❌ Deeply nested divs (max 4 levels)
- ❌ Non-semantic class names (`.div1`, `.box123`)
- ❌ Missing form labels
- ❌ Hardcoded text (use i18n if needed)

### CSS
- ❌ Bright saturated colors (#0000FF, #00FF00)
- ❌ Heavy drop shadows (blur > 20px)
- ❌ Magic numbers (use CSS variables)
- ❌ !important spam
- ❌ Overly specific selectors (#id .class div span)

### JavaScript
- ❌ Callback hell (use async/await)
- ❌ Global pollution
- ❌ Premature optimization
- ❌ Silent errors
- ❌ Mixing concerns (DOM + API logic)

### Jinja2
- ❌ Business logic in templates
- ❌ Duplicate markup (use macros)
- ❌ Missing error handling
- ❌ Hardcoded URLs

---

## 📚 Quick Reference

### Commonly Used Classes

| Component | Classes |
|-----------|---------|
| Container | `.container` |
| Section | `.section`, `.section--large` |
| Card | `.card`, `.card__title`, `.card__content` |
| Button | `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-ghost` |
| Tag | `.tag`, `.tag--primary`, `.tag--secondary` |
| Input | `.input` |
| Drop Zone | `.drop-zone` |
| Gallery | `.gallery-grid`, `.gallery-item` |
| Stat Card | `.stat-card`, `.stat-card--primary` |
| Loader | `.loader` |
| Hidden | `.hidden` |

### Common Import Patterns

```javascript
// Utils
import { MAX_FILES } from "../utils/constants.js";
import { formatFileSize } from "../utils/formatters.js";
import { show, hide } from "../utils/dom.js";
import { segmentImages } from "../utils/api.js";

// Modules
import { FileHandler } from "./fileHandler.js";
import { CanvasRenderer } from "./canvasRenderer.js";
```

### Common Macro Calls

```jinja2
{{ render_nav('upload') }}
{{ render_pagination(current_page, total_pages, '/gallery') }}
{{ stat_card('Objects', count, 'primary') }}
{{ gallery_card(image) }}
```

---

## 🔄 Migration from Old Architecture

### Before (Nested)
```
modules/upload/uploadPage.js
modules/canvas/canvasModal.js
components/modals/canvas_modal.html
```

### After (Flat)
```
modules/uploadPage.js
modules/canvasModal.js
components/canvas_modal.html
```

### Import Path Changes

**Before:**
```javascript
import { func } from "../../utils/api.js";
import { CanvasRenderer } from "../canvas/canvasRenderer.js";
```

**After:**
```javascript
import { func } from "../utils/api.js";
import { CanvasRenderer } from "./canvasRenderer.js";
```

---

## 📞 Contact & Support

**Documentation:**
- Design Guide: `docs/scandinavian_design_guide.md`
- Implementation Plan: `docs/scandinavian_redesign_plan.md`
- Quick Start: `docs/SCANDINAVIAN_QUICK_START.md`

**Codebase:**
- Frontend: `static/`, `templates/`
- Backend: `app/`, `main.py`

---

**Made with ♥ using modern web standards**

**Version:** 2.0.0
**Last Updated:** 2025-12-25
**Status:** Production Ready ✅
