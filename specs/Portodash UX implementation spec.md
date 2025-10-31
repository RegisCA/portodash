# PortoDash UX Implementation Spec for GitHub Copilot (GPT-5-Codex)

## Targeted improvements

Core fintech UX principles: replacing emoji icons with professional alternatives, fixing the problematic bright green styling, implementing intelligent refresh behavior, and enhancing table readability.

The roadmaps is focused on these critical improvements:

1. **Professional icon system** - Replace emoji icons with proper UI elements
2. **Color palette overhaul** - Move away from overwhelming bright green
3. **Smart refresh logic** - Context-aware refresh button behavior
4. **Enhanced table design** - Better headers, company names, visual hierarchy
5. **Streamlit-first approach** - Maintain current framework for Copilot compatibility
6. **Component-based development** - Structure for AI pair programming efficiency

## Portodash Design Configuration

### Color Palette: Modern dark-accent approach

```css
Primary: #1A1A1A (Near black)
Secondary: #6366F1 (Indigo action)  
Success: #10B981 (Emerald gains)
Warning: #F59E0B (Amber alerts)
```

### Typography: Larger, prominent metrics

- Portfolio Value: **2.5rem, weight 700**
- Section Headers: **1.75rem, weight 600**

### Filter Sidebar: Neutral gray with enhanced organization

- Neutral gray backgrounds
- Collapsible filter groups with count badges

## GitHub Copilot Implementation Prompts

### Phase 1: Foundation (Core Styling)

#### Prompt 1.1 - Modern Dark-Accent Color System

```bash
Create a Streamlit custom CSS injection function called inject_modern_fintech_css() that implements a modern dark-accent color palette. Use these CSS variables: --primary: #1A1A1A; --secondary: #6366F1; --success: #10B981; --warning: #F59E0B; --error: #EF4444; --neutral: #6B7280; --background: #FFFFFF; --card-bg: #F9FAFB. Include styles for buttons, metrics, and table elements. Use st.markdown() with unsafe_allow_html=True.
```

#### Prompt 1.2 - Professional Icon Replacement

```bash
Replace all emoji icons in a Streamlit sidebar with clean text labels and Unicode symbols. Create a function get_professional_icon(icon_type) that maps: "analytics" → "📊" → "Analytics ▼", "date" → "📅" → "Date Range", "filter" → "🔍" → "Filters ⚙", "account" → "📁" → "● Account", "holder" → "👤" → "● Holder", "type" → "🏦" → "● Type". Return professional text alternatives.
```

#### Prompt 1.3 - Prominent Typography Hierarchy

```bash
Create Streamlit CSS injection for enhanced typography hierarchy in a financial dashboard. Define styles: .portfolio-value {font-size: 2.5rem; font-weight: 700; color: #1A1A1A}, .section-header {font-size: 1.75rem; font-weight: 600; margin: 1.5rem 0 1rem}, .metric-label {font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; color: #6B7280}, .data-table {font-size: 0.875rem}. Use system font stack.
```

### Phase 2: Smart Components

#### Prompt 2.1 - Context-Aware Refresh Logic

```bash
Create a Streamlit component that shows intelligent refresh status. When data timestamp is <30 minutes old, display st.success("✓ Data is current") with timestamp. When stale, show st.button("Update Data", type="primary"). Add rate limiting: after refresh, show st.info with countdown timer "Next update available in X minutes". Use datetime comparison and st.session_state for cooldown tracking.
```

#### Prompt 2.2 - Enhanced Holdings Table with Company Names

```bash
Improve a pandas DataFrame display in Streamlit for stock holdings. Add a "Company" column showing "TICKER - Company Name" format. Implement color-coded gain_pct column using conditional formatting with subtle background colors (green tint for gains, red tint for losses). Add CSS for zebra striping and responsive column hiding. Use st.dataframe with custom styling and column configuration.
```

#### Prompt 2.3 - Collapsible Filter Sidebar with Count Badges

```bash
Create a Streamlit sidebar with collapsible filter groups using st.expander. For each filter group (Accounts, Holders, Types), show count badges like "Accounts (3)" in the expander header. Use st.multiselect inside each expander with neutral gray styling. Add a "Reset All Filters" button at bottom. Include custom CSS for subtle borders and hover states matching --neutral color variable.
```

### Phase 3: Professional Enhancement

#### Prompt 3.1 - Elevated KPI Cards

```bash
Create professional KPI metric cards for Streamlit showing portfolio value, cost basis, and gains. Use st.columns(3) with custom CSS cards having subtle shadows (box-shadow: 0 1px 3px rgba(0,0,0,0.1)). Show large values (2.5rem font) with delta indicators using st.metric. Include percentage changes in smaller secondary text with success/error colors from the modern palette. Make responsive to single column on mobile.
```

#### Prompt 3.2 - Data Provenance Status Badges

```bash
Add data freshness indicators to Streamlit interface using colored status badges. Create function render_status_badge(status, timestamp) that returns HTML badges: Live (green background), Cache (amber background), Mixed (neutral background). Use pill-shaped styling with appropriate text colors for accessibility. Include hover tooltips using st.help explaining "Live: Real-time API", "Cache: Stored data", "Mixed: Combination of sources".
```

#### Prompt 3.3 - Modern Chart Styling Integration

```bash
Enhance Plotly charts in Streamlit with modern dark-accent theme. Create custom plotly theme using the color palette: primary #1A1A1A, secondary #6366F1, success #10B981. Add hover tooltips showing company names + ticker symbols. Set responsive sizing, clean grid lines, and system font family. Use plotly.graph_objects with layout template and fig.update_layout for consistent theming across pie and line charts.
```

### Phase 4: Polish \& Optimization

#### Prompt 4.1 - Responsive Grid Layout

```bash
Create a responsive layout system for Streamlit financial dashboard. Use st.columns with different ratios for desktop ([2,1,1] for KPIs, [1,1] for charts) and implement CSS media queries to stack columns on mobile (<768px). Add container classes with max-width and centered alignment. Include breakpoint-specific spacing and font scaling using CSS clamp() functions.
```

#### Prompt 4.2 - Loading States \& Transitions

```bash
Add professional loading states to Streamlit components. Create spinner overlays for data refresh operations using st.spinner with custom CSS. Add smooth CSS transitions (0.2s ease) for hover states on buttons and cards. Implement skeleton loading placeholders for tables and charts while data loads. Use CSS transforms instead of position changes for 60fps animations.
```

#### Prompt 4.3 - Accessibility \& Polish

```bash
Enhance Streamlit financial dashboard accessibility. Add proper ARIA labels, ensure 4.5:1 color contrast ratios for all text, implement keyboard navigation focus styles. Create function check_color_contrast() to validate palette combinations. Add skip links for screen readers and proper semantic HTML structure in custom components. Include print stylesheet for financial reports.
```

## Copilot Execution Strategy

**Sequential Implementation:** Run prompts in phase order - foundation styling enables component enhancements which enable advanced features.

**Test After Each Prompt:** Use `streamlit run app.py` to verify each component works before proceeding to next prompt.

**Iterative Refinement:** After implementing a prompt, use follow-up requests like "Make the card shadows more subtle" or "Increase button padding slightly" for fine-tuning.

**Component Isolation:** Test each component separately using `if st.checkbox("Test Component"):` blocks during development.

### Quality Checkpoints

After completing each phase, verify these fintech UX standards:

#### Phase 1 Complete

- [ ] Professional appearance without emoji distractions
- [ ] Consistent modern color palette throughout
- [ ] Prominent typography hierarchy for quick scanning

#### Phase 2 Complete

- [ ] Smart refresh behavior based on data freshness
- [ ] Clear company names visible in holdings table
- [ ] Organized filter sidebar with count indicators

#### Phase 3 Complete

- [ ] KPI cards pass 5-second comprehension test
- [ ] Data provenance clearly indicated with status badges
- [ ] Charts match overall design system aesthetics

#### Phase 4 Complete

- [ ] Responsive layout works on tablet and mobile
- [ ] Professional loading states during data operations
- [ ] Accessibility standards met for financial interface
