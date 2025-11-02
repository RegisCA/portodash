# Contributing to PortoDash

Thank you for your interest in contributing to PortoDash! This document provides
guidelines for contributing to the project.

## Welcome Contributions

We especially welcome contributions in these areas:

- **UX polish**: Interface improvements that maintain clarity-first design
- **Caching strategies**: Performance optimizations for data fetching
- **Data modeling**: Enhanced portfolio analytics and calculations
- **Multi-currency analytics**: Richer FX impact analysis
- **Accessibility**: Improvements to WCAG compliance
- **Documentation**: Corrections, clarifications, and examples

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git for version control
- Familiarity with Streamlit (for UI changes)

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/RegisCA/portodash.git
cd portodash

# Create virtual environment (Option A)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Or use Conda (Option B - recommended for Apple Silicon)
conda env create -f environment.yml
conda activate portodash

# Run the application
streamlit run app.py
```

## How to Contribute

### Reporting Issues

Before creating an issue:

- Check existing issues to avoid duplicates
- Use the issue template if available
- Provide clear reproduction steps for bugs
- Include your Python and Streamlit versions

### Suggesting Features

Feature requests should include:

- Clear use case and problem statement
- How it maintains the clarity-first philosophy
- Consideration for multi-currency complexity
- Mockups or examples (if applicable)

### Submitting Pull Requests

1. **Create an issue first** to discuss significant changes
2. **Fork the repository** and create a feature branch
3. **Follow existing code style**:
   - Use type hints where appropriate
   - Add docstrings for new functions
   - Keep functions focused and single-purpose
4. **Test your changes**:
   - Run the app with demo mode: `python scripts/demo_mode.py`
   - Verify all features still work
   - Test with different portfolio configurations
5. **Update documentation**:
   - Update relevant markdown files
   - Add code comments for complex logic
   - Include examples in docstrings
6. **Commit with clear messages**:
   - Use conventional commits format
   - Examples: `feat:`, `fix:`, `docs:`, `refactor:`
7. **Submit PR with context**:
   - Reference related issue numbers
   - Explain UX rationale for interface changes
   - Note any edge cases or limitations

## Code Style Guidelines

### Python

- Follow PEP 8 conventions
- Use meaningful variable names
- Prefer explicit over implicit
- Keep functions under 50 lines when possible

### Streamlit UI

- Maintain accessibility standards (WCAG 2.1 Level AA)
- Use semantic section headers
- Preserve responsive layout
- Test keyboard navigation

### Documentation

- Use markdown for all documentation
- Keep line length under 120 characters for readability
- Use proper heading hierarchy (## H2, ### H3)
- Include code examples with syntax highlighting

## Accessibility Requirements

All UI contributions must maintain WCAG 2.1 Level AA compliance:

- **Color contrast**: Minimum 4.5:1 for normal text
- **Keyboard navigation**: All features accessible without mouse
- **Screen readers**: Proper ARIA labels on charts and controls
- **Focus indicators**: Visible focus states on interactive elements

See [ACCESSIBILITY.md](ACCESSIBILITY.md) for detailed guidelines.

## Design System

Follow the established design system when making UI changes:

- **Color palette**: Defined in `.streamlit/config.toml`
- **Typography**: System font stack with consistent hierarchy
- **Spacing**: 8px grid system for consistency
- **Components**: Use theme utilities from `portodash/theme.py`

See [UX_DESIGN.md](UX_DESIGN.md) for complete design system documentation.

## Testing

### Manual Testing Checklist

- [ ] Test with demo mode (`python scripts/demo_mode.py`)
- [ ] Verify all account filtering works
- [ ] Check performance chart displays correctly
- [ ] Test refresh functionality and rate limiting
- [ ] Verify accessibility (keyboard navigation, screen reader)
- [ ] Test responsive layout on different screen sizes

### Demo Mode

Use demo mode for safe testing without exposing personal data:

```bash
# Toggle demo mode on/off
python scripts/demo_mode.py

# Check status
python scripts/demo_mode.py --status

# Run app with demo data
streamlit run app.py
```

## Documentation Standards

### Markdown Files

When updating documentation:

- Use ## for main sections (no H1)
- Keep line length under 400 characters
- Use code blocks with language specifiers
- Include examples for complex features
- Add links to related documentation

### Code Comments

- Add docstrings to all functions
- Explain "why" not "what" in comments
- Document edge cases and assumptions
- Include type hints for function parameters

## Review Process

### What Reviewers Look For

- **Code quality**: Readable, maintainable, well-structured
- **Testing**: Changes have been manually tested
- **Documentation**: Relevant docs updated
- **Accessibility**: WCAG standards maintained
- **UX consistency**: Follows design system
- **Edge cases**: Handles errors gracefully

### Response Time

- Issues: Triaged within 3-5 business days
- PRs: Initial review within 1 week
- Follow-ups: Responded to within 3-5 business days

## Community Guidelines

- Be respectful and constructive
- Focus on the code, not the person
- Assume good intentions
- Help newcomers get started
- Share knowledge and learn together

## Questions?

- Open an issue with the "question" label
- Check existing documentation in the repository
- Review [DEVELOPMENT.md](DEVELOPMENT.md) for technical context

## License

By contributing, you agree that your contributions will be licensed under
the MIT License, same as the project.
