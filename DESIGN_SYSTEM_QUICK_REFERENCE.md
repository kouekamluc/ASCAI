# Design System Quick Reference Guide

## 🎨 Using the New Design System

### CSS Files to Include

```html
<!-- In your templates -->
<link rel="stylesheet" href="{% static 'css/design-system.css' %}">
<link rel="stylesheet" href="{% static 'css/sidebar.css' %}">
<link rel="stylesheet" href="{% static 'css/tables.css' %}">
<link rel="stylesheet" href="{% static 'css/dashboard-new.css' %}">
```

### Color Usage

```css
/* Primary Colors */
background-color: var(--color-white);
color: var(--color-text-primary);

/* Accent Color */
background-color: var(--color-accent);
color: var(--color-white);

/* Semantic Colors */
background-color: var(--color-success);
background-color: var(--color-warning);
background-color: var(--color-error);
background-color: var(--color-info);
```

### Button Classes

```html
<!-- Primary Button -->
<button class="btn btn-primary">Save</button>

<!-- Secondary Button -->
<button class="btn btn-secondary">Cancel</button>

<!-- Tertiary Button -->
<button class="btn btn-tertiary">Learn More</button>

<!-- Danger Button -->
<button class="btn btn-danger">Delete</button>

<!-- Sizes -->
<button class="btn btn-primary btn-sm">Small</button>
<button class="btn btn-primary">Default</button>
<button class="btn btn-primary btn-lg">Large</button>
```

### Card Component

```html
<div class="card">
    <div class="card-header">
        <h3 class="card-title">Card Title</h3>
    </div>
    <div class="card-body">
        <p>Card content goes here.</p>
    </div>
    <div class="card-footer">
        <button class="btn btn-primary">Action</button>
    </div>
</div>
```

### Badge Component

```html
<span class="badge badge-success">Active</span>
<span class="badge badge-warning">Pending</span>
<span class="badge badge-error">Inactive</span>
<span class="badge badge-info">Info</span>
<span class="badge badge-gray">Default</span>
```

### Form Controls

```html
<div class="form-group">
    <label for="email" class="form-label">
        Email <span class="required">*</span>
    </label>
    <input type="email" id="email" class="form-control" placeholder="Enter email">
    <small class="form-help">We'll never share your email.</small>
</div>

<!-- Error State -->
<div class="form-group">
    <label for="email" class="form-label">Email</label>
    <input type="email" id="email" class="form-control" aria-invalid="true">
    <div class="form-error">Please enter a valid email address.</div>
</div>
```

### Data Tables

```html
<div class="table-container">
    <div class="table-wrapper">
        <table class="data-table">
            <thead>
                <tr>
                    <th class="sortable">Name</th>
                    <th class="sortable">Email</th>
                    <th>Status</th>
                    <th class="actions">Actions</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>John Doe</td>
                    <td>john@example.com</td>
                    <td><span class="badge badge-success">Active</span></td>
                    <td class="actions">
                        <button class="btn btn-sm btn-primary">Edit</button>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
    <div class="table-pagination">
        <div class="pagination-info">Showing 1-10 of 50</div>
        <div class="pagination-controls">
            <button class="pagination-btn" disabled>Previous</button>
            <button class="pagination-btn active">1</button>
            <button class="pagination-btn">2</button>
            <button class="pagination-btn">3</button>
            <button class="pagination-btn">Next</button>
        </div>
    </div>
</div>
```

### KPI Cards

```html
<div class="kpi-grid">
    <div class="kpi-card">
        <div class="kpi-icon">👥</div>
        <div class="kpi-content">
            <div class="kpi-label">Total Members</div>
            <div class="kpi-value">1,234</div>
            <div class="kpi-change positive">+12% from last month</div>
        </div>
    </div>
</div>
```

### Dashboard Widgets

```html
<div class="dashboard-widget">
    <div class="widget-header">
        <h2>Recent Activity</h2>
        <a href="#" class="btn btn-sm btn-secondary">View All</a>
    </div>
    <div class="widget-content">
        <!-- Widget content -->
    </div>
</div>
```

### Alerts

```html
<div class="alert alert-success">
    <strong>Success!</strong> Your changes have been saved.
</div>

<div class="alert alert-error">
    <strong>Error!</strong> Something went wrong.
</div>

<div class="alert alert-warning">
    <strong>Warning!</strong> Please review your input.
</div>

<div class="alert alert-info">
    <strong>Info:</strong> This is an informational message.
</div>
```

### Spacing Utilities

```css
/* Use CSS variables for spacing */
padding: var(--spacing-4);      /* 16px */
margin: var(--spacing-6);        /* 24px */
gap: var(--spacing-2);          /* 8px */
```

### Typography

```html
<h1>Page Title (2.5rem, Bold)</h1>
<h2>Section Title (2rem, Semibold)</h2>
<h3>Subsection (1.5rem, Semibold)</h3>
<p class="text-primary">Primary text</p>
<p class="text-secondary">Secondary text</p>
<p class="text-tertiary">Tertiary text</p>
```

### Breadcrumbs

```html
{% block breadcrumbs %}
<nav class="breadcrumbs">
    <ol class="breadcrumbs-list">
        <li class="breadcrumbs-item">
            <a href="{% url 'dashboard:home' %}">Dashboard</a>
        </li>
        <li class="breadcrumbs-separator">/</li>
        <li class="breadcrumbs-item active">Current Page</li>
    </ol>
</nav>
{% endblock %}
```

### Page Title

```html
{% block page_title %}Dashboard{% endblock %}
```

### Responsive Grid

```html
<!-- Auto-responsive grid -->
<div class="content-grid">
    <div class="card">Item 1</div>
    <div class="card">Item 2</div>
    <div class="card">Item 3</div>
</div>
```

## 🎯 Best Practices

1. **Use CSS Variables**: Always use design system variables instead of hardcoded values
2. **Consistent Spacing**: Use the 8px spacing scale (var(--spacing-X))
3. **Color Hierarchy**: Follow the 60-30-10 rule (white, dark gray, blue)
4. **Touch Targets**: Minimum 44px height for interactive elements
5. **Accessibility**: Always include labels, ARIA attributes, and focus states

## 📱 Mobile Considerations

- Sidebar automatically becomes a drawer on mobile
- Tables stack vertically on small screens
- KPI cards stack in a single column
- Touch-friendly button sizes (44px minimum)

## 🔧 Customization

All design tokens are defined as CSS custom properties in `design-system.css`. You can override them:

```css
:root {
    --color-accent: #your-color;
    --spacing-4: 1.5rem;
    /* etc. */
}
```

## 📚 Full Documentation

See `UI_UX_REDESIGN_PLAN.md` for complete design specifications and rationale.

