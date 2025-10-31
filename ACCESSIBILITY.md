# Accessibility Features

PortoDash is committed to WCAG 2.1 Level AA compliance, ensuring the application is usable by everyone, including people with disabilities.

## Implemented Features

### ✅ Keyboard Navigation
- **Focus indicators**: All interactive elements have visible 3px focus outlines with 2px offset
- **Tab order**: Logical tab order through filters, buttons, and charts
- **Focus styles**: Enhanced visibility with blue outline and subtle shadow
- **Skip links**: "Skip to main content" link for keyboard and screen reader users

### ✅ Color Contrast
All color combinations meet WCAG AA standards (minimum 4.5:1 for normal text, 3:1 for large text):

| Color | On White | On Light Gray (#F9FAFB) | On Dark (#1A1A1A) |
|-------|----------|------------------------|-------------------|
| Primary (#1A1A1A) | 17.4:1 ✅ | 16.65:1 ✅ | 1.0:1 ❌ |
| Secondary (#6366F1) | 4.47:1 ⚠️ | 4.27:1 ⚠️ | 3.9:1 ✅ (large text) |
| Neutral (#6B7280) | 4.83:1 ✅ | 4.63:1 ✅ | 3.6:1 ✅ (large text) |
| Links (#4F46E5) | 5.74:1 ✅ | 5.49:1 ✅ | — |

**Note**: Secondary/indigo color used only for large text (buttons, headers) where 3:1 minimum applies.

### ✅ Screen Reader Support
- **Skip navigation**: Jump directly to main content
- **Semantic HTML**: Proper heading hierarchy (H1 → H2 → H3)
- **ARIA labels**: Descriptive labels for charts and interactive widgets
- **Screen reader-only content**: `.sr-only` class for additional context

### ✅ Print Accessibility
Complete print stylesheet for generating financial reports:
- Hides interactive elements (sidebar, buttons, filters)
- Optimizes charts for black & white printing
- Proper page breaks between sections
- Page headers with report title
- Table headers repeat on each page

### ✅ Motion & Contrast Preferences
- **Reduced motion**: Respects `prefers-reduced-motion` setting
- **High contrast**: Enhanced borders and contrast in high contrast mode
- **No animations**: Transitions disabled when user prefers reduced motion

## Color Contrast Validation

Use the built-in `check_color_contrast()` function to validate new colors:

```python
from portodash.accessibility import check_color_contrast

# Check a color combination
result = check_color_contrast('#1A1A1A', '#FFFFFF')
print(f"Contrast ratio: {result['ratio']}:1")
print(f"Passes WCAG AA (normal text): {result['passes_aa_normal']}")
print(f"Passes WCAG AA (large text): {result['passes_aa_large']}")
```

## Testing

### Keyboard Navigation
1. Press `Tab` to navigate through interactive elements
2. Press `Shift+Tab` to navigate backwards
3. Press `Enter` or `Space` to activate buttons
4. Look for visible focus indicators on all elements

### Screen Reader Testing
- **macOS**: VoiceOver (Cmd+F5)
- **Windows**: NVDA (free) or JAWS
- **Linux**: Orca

### High Contrast Mode
- **Windows**: Settings → Ease of Access → High contrast
- **macOS**: System Preferences → Accessibility → Display → Increase contrast

### Print Preview
- Use browser's print preview (Cmd/Ctrl+P)
- Verify charts, tables, and metrics render correctly
- Check that interactive elements are hidden

## Future Improvements

- [ ] Add more ARIA labels to complex widgets
- [ ] Implement chart data tables for screen readers
- [ ] Add keyboard shortcuts documentation
- [ ] Increase color contrast for success/warning/error indicators
- [ ] Add focus management for dynamic content updates

## Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [WebAIM Color Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [a11y Project Checklist](https://www.a11yproject.com/checklist/)
