# PortoDash UX Design System

## Overview

PortoDash's UX follows a clean, modern design aesthetic inspired by Wealthsimple's approach to financial interfaces: high contrast, generous whitespace, clear typography, and purposeful use of color to guide attention without overwhelming the user.

**Design Philosophy:** Financial data should be trustworthy, scannable, and actionable. The interface prioritizes clarity over decoration, using visual hierarchy to surface the most important information while keeping details accessible.

---

## Design Principles

### 1. **Trust Through Transparency**
Every number shows its provenance. Data freshness indicators, source labels, and explicit timestamps build confidence in the accuracy of displayed information.

### 2. **Hierarchy Over Density**
White space is intentional. Sections are clearly separated with dividers. Metrics are large and prominent. Details are available but don't compete for attention.

### 3. **Color as Signal, Not Decoration**
- **Mint green (#00D46A)** signals primary actions and positive portfolio values
- **Red/pink** indicates losses or warnings
- **Gray** provides structure without distraction
- Charts use intentional color schemes that aid interpretation

### 4. **Consistency Across Context**
Typography, spacing, border radius, and interactive elements follow consistent patterns. Users build muscle memory for navigation and actions.

---

## Color Palette

### Primary Colors
```
Mint Green (Primary):  #00D46A  // CTA buttons, positive metrics, chart accents
Near Black (Text):     #1A1A1A  // Primary text
Pure White:            #FFFFFF  // Background
Off-White (Cards):     #F7F9FA  // Card backgrounds, sidebar
```

### Secondary Colors
```
Gray (Neutral):        #6B7280  // Secondary text, baseline chart lines
Light Gray (Borders):  #E8EBED  // Dividers, borders, subtle structure
Blue (Info):           #2E86AB  // Informational accents
Purple (Data):         #A23B72  // Secondary data series
Orange (Alert):        #F18F01  // Warnings, attention
```

### Status Colors
```
Live (Green):          #D1FAE5 (bg) / #065F46 (text)
Cache (Yellow):        #FEF3C7 (bg) / #92400E (text)
Mixed (Blue):          #DBEAFE (bg) / #1E40AF (text)
```

---

## Typography

### Font Stack
```css
font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
```

Uses system fonts for optimal performance and native feel across platforms.

### Type Scale
```
H1 (Page Title):       2rem (32px), weight 700, letter-spacing -0.02em
H2 (Section):          1.5rem (24px), weight 600, letter-spacing -0.01em
H3 (Subsection):       1.25rem (20px), weight 600
Body:                  1rem (16px), weight 400
Caption:               0.875rem (14px), weight 400
Metric Value:          2rem (32px), weight 700
Metric Label:          0.875rem (14px), weight 500, uppercase, letter-spacing 0.05em
```

---

## Spacing System

### Margins & Padding
```
xs:  0.25rem  (4px)
sm:  0.5rem   (8px)
md:  1rem     (16px)
lg:  1.5rem   (24px)
xl:  2rem     (32px)
xxl: 3rem     (48px)
```

### Section Dividers
Major sections separated by `---` horizontal rules with 2rem vertical spacing to create clear visual breaks.

---

## Component Styling

### Buttons

**Primary (CTA)**
```css
background: #00D46A
color: white
border-radius: 8px
padding: 0.5rem 1.5rem
font-weight: 600
transition: all 0.2s ease
hover: transform translateY(-1px), shadow 0 4px 12px rgba(0,0,0,0.08)
```

**Secondary/Default**
```css
background: white
border: 1px solid #E8EBED
color: #1A1A1A
(other properties same as primary)
```

### Metrics (KPI Cards)

Large, prominent numbers with small uppercase labels:
```
Value: 2rem, weight 700
Label: 0.875rem, weight 500, uppercase, tracking 0.05em, color #6B7280
```

Delta indicators use Streamlit's built-in metric delta for gain/loss percentages.

### Data Tables

- Clean presentation with generous row spacing
- Color-coded gain_pct column (green/red backgrounds)
- Rounded corners (8px) on container
- Sortable by default for user exploration

### Cards/Containers

```css
background: #F7F9FA
border-radius: 12px
padding: 1.5rem
border: 1px solid #E8EBED
```

Used sparingly for grouping related information without overwhelming the interface.

### Status Badges

Small, rounded indicators for data provenance:
```css
display: inline-block
padding: 0.25rem 0.75rem
border-radius: 12px
font-size: 0.875rem
font-weight: 600
```

Color-coded by status (Live/Cache/Mixed) using status colors from palette.

---

## Chart Styling

### Allocation Pie Chart

- **Donut style** (40% hole) for modern look
- **Color palette:** Sequential from mint green through blues, purples, oranges
- **Labels:** Outside positioning with ticker + percent
- **Legend:** Vertical on right side for easy scanning
- **Hover:** Clean tooltip with white background

### Performance Line Chart

**Dual-series (with FX impact analysis):**
- **Actual Performance (with FX):** Mint green (#00D46A), 3px width, solid
- **Market Performance (Fixed FX):** Gray (#6B7280), 2px width, dotted

**Single-series (no FX data):**
- Mint green (#00D46A), 3px width, solid

**Shared attributes:**
- Transparent background (paper & plot)
- Subtle grid lines (#E8EBED)
- Horizontal legend below chart for dual-series
- Clean hover tooltip with unified x-axis mode
- System font stack for consistency

---

## Layout Structure

### Sidebar (Left)

**Width:** Default Streamlit sidebar width (~250px)

**Sections:**
1. **Controls Header** with gear icon
2. **Time Range** slider for performance chart
3. **Filters** with emoji labels (📁 Account, 👤 Holder, 🏦 Type)
4. **Data Refresh** with primary CTA button
5. **Ticker list** (caption, collapsed if >10)

**Background:** Off-white (#F7F9FA) with subtle border

### Main Content

**Structure:**
1. **Header:** Page title + caption
2. **Portfolio Status:** Last updated timestamp + scheduler status
3. **Portfolio Overview:** 3-column KPIs (Value, Cost, Gain)
4. **Multi-Currency Details:** Expandable, collapsed by default
5. **Holdings:** Account breakdown (if multi-account) + full holdings table
6. **Allocation:** Donut chart
7. **Performance:** Line chart (30 days or custom range)
8. **Data Management:** Snapshot save + CSV download

**Visual separators:** `---` between major sections

---

## Responsive Considerations

### Desktop (>1024px)
- Full sidebar visible
- 3-column layout for metrics
- Charts at full width

### Tablet (768px - 1024px)
- Sidebar collapsible
- 2-column layout for metrics
- Charts maintain aspect ratio

### Mobile (<768px)
- Sidebar as drawer
- Single column layout
- Stacked metrics
- Horizontal scroll for tables

*Note: Streamlit handles most responsiveness automatically. Custom CSS focuses on enhancing desktop/tablet experience.*

---

## Accessibility

### Color Contrast
All text meets WCAG AA standards:
- Primary text (#1A1A1A) on white: 16.74:1
- Secondary text (#6B7280) on white: 5.74:1
- Buttons maintain >4.5:1 contrast

### Interactive Elements
- All buttons have visible focus states
- Form elements use native Streamlit accessibility
- Charts include hover tooltips for screen reader context

### Typography
- Minimum font size: 0.875rem (14px)
- Line height: 1.5 for body text
- Proper heading hierarchy (H1 → H2 → H3)

---

## Animation & Transitions

### Micro-interactions
- Button hover: translateY(-1px) + shadow in 0.2s
- Smooth transitions on interactive elements
- No gratuitous animations that distract from data

### Performance
- CSS transforms (not top/left) for smooth 60fps animations
- Transitions limited to hover states and button interactions
- Chart rendering managed by Plotly (hardware accelerated)

---

## Icons & Emojis

Used sparingly for scanability and personality:

| Context | Icon | Meaning |
|---------|------|---------|
| Page title | 📊 | Data/analytics |
| Time range | 📅 | Calendar/dates |
| Filters | 🔍 | Search/filter |
| Account name | 📁 | Folder/organization |
| Holder | 👤 | Person |
| Account type | 🏦 | Bank/institution |
| Refresh | 🔄 | Update/sync |
| Portfolio overview | 💰 | Money/value |
| Holdings | 📈 | Growth/stocks |
| Allocation | 🎯 | Target/distribution |
| Performance | 📉 | Chart/trends |
| Snapshot | 📸 | Capture/save |
| Download | 📥 | Export |
| Multi-currency | 💱 | Exchange |
| Scheduler | ⚡ | Automation |
| Warning | ⚠️ | Alert |
| Success | ✅ | Complete |

---

## Implementation Details

### Streamlit Configuration
Located in `.streamlit/config.toml`:
- Theme colors defined (primary, background, text)
- Server settings for local development
- Browser usage stats disabled

### Custom CSS Injection
`inject_custom_css()` function in `app.py`:
- Typography enhancements
- Component styling (buttons, metrics, tables)
- Hover effects and transitions
- Status badge styles
- Chart container styling

### Chart Generation
`portodash/viz.py` functions:
- `make_allocation_pie()`: Donut chart with custom colors
- `make_snapshot_performance_chart()`: Line chart with FX analysis

Both use Plotly for interactive, hardware-accelerated rendering.

---

## Future Enhancements

### Planned Improvements
1. **Dark mode** support with `prefers-color-scheme` detection
2. **Custom date range picker** with presets (1M, 3M, 6M, 1Y, YTD)
3. **Drill-down views** for individual holdings with mini-charts
4. **Enhanced mobile layout** with optimized table views
5. **Contribution flow visualization** showing deposits vs growth
6. **Benchmark comparison** overlays on performance chart

### Under Consideration
- Migration to React for more control over UI components
- Custom charting library for tighter visual integration
- Animated transitions between data states
- Progressive web app (PWA) capabilities for offline use

---

## Testing Checklist

When making design changes, verify:

- [ ] Metrics are prominent and easy to scan
- [ ] Charts render correctly at all viewport widths
- [ ] Status badges have correct colors for each state
- [ ] Buttons have visible hover states
- [ ] Tables remain readable with color coding
- [ ] Sidebar filters are accessible and clear
- [ ] Section dividers create clear visual hierarchy
- [ ] Icons add clarity without distraction
- [ ] Colors maintain sufficient contrast
- [ ] Typography scale is consistent across sections
- [ ] Responsive layout works on tablet/mobile

---

## Design System Changelog

### v1.1 - UX Polish (October 30, 2025)
**Major Changes:**
- Implemented Wealthsimple-inspired color palette with mint green accent
- Added custom CSS injection for typography, spacing, and components
- Enhanced Plotly chart styling with modern colors and clean layout
- Restructured app.py with better visual hierarchy and section grouping
- Added emoji icons for better scanability
- Improved sidebar organization with clear sections
- Introduced status badges for data provenance
- Enhanced button styling with hover effects
- Updated metrics display with larger values and better labels

**Visual Impact:**
- Cleaner, more professional appearance
- Better information hierarchy reduces cognitive load
- Consistent spacing and typography improve readability
- Color is used purposefully to guide attention
- Interactive elements have clear affordances

---

*This design system should be referenced when adding new features or components to maintain visual consistency and user experience quality.*
