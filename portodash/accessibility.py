"""Accessibility utilities for PortoDash.

Provides WCAG 2.1 compliance tools including color contrast validation,
ARIA label generation, and semantic HTML helpers.
"""
from typing import Tuple


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple.
    
    Args:
        hex_color: Hex color string (e.g., '#1A1A1A' or '1A1A1A')
    
    Returns:
        RGB tuple (r, g, b) with values 0-255
    """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def get_relative_luminance(rgb: Tuple[int, int, int]) -> float:
    """Calculate relative luminance for a color.
    
    Uses WCAG 2.1 formula for relative luminance.
    
    Args:
        rgb: RGB tuple (r, g, b) with values 0-255
    
    Returns:
        Relative luminance value between 0 and 1
    """
    def adjust_channel(channel: int) -> float:
        """Adjust RGB channel value per WCAG formula."""
        c = channel / 255.0
        if c <= 0.03928:
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4
    
    r, g, b = rgb
    r_adjusted = adjust_channel(r)
    g_adjusted = adjust_channel(g)
    b_adjusted = adjust_channel(b)
    
    return 0.2126 * r_adjusted + 0.7152 * g_adjusted + 0.0722 * b_adjusted


def check_color_contrast(foreground: str, background: str) -> dict:
    """Check color contrast ratio between foreground and background colors.
    
    Validates against WCAG 2.1 Level AA standards:
    - Normal text: 4.5:1 minimum
    - Large text (18pt+ or 14pt+ bold): 3:1 minimum
    - UI components: 3:1 minimum
    
    Args:
        foreground: Foreground color as hex string (e.g., '#1A1A1A')
        background: Background color as hex string (e.g., '#FFFFFF')
    
    Returns:
        Dict with contrast ratio and WCAG compliance status:
        {
            'ratio': float,
            'passes_aa_normal': bool,  # 4.5:1
            'passes_aa_large': bool,   # 3:1
            'passes_aaa_normal': bool, # 7:1
            'passes_aaa_large': bool   # 4.5:1
        }
    """
    fg_rgb = hex_to_rgb(foreground)
    bg_rgb = hex_to_rgb(background)
    
    fg_luminance = get_relative_luminance(fg_rgb)
    bg_luminance = get_relative_luminance(bg_rgb)
    
    # Ensure lighter color is in numerator
    lighter = max(fg_luminance, bg_luminance)
    darker = min(fg_luminance, bg_luminance)
    
    ratio = (lighter + 0.05) / (darker + 0.05)
    
    return {
        'ratio': round(ratio, 2),
        'passes_aa_normal': ratio >= 4.5,    # WCAG AA normal text
        'passes_aa_large': ratio >= 3.0,     # WCAG AA large text
        'passes_aaa_normal': ratio >= 7.0,   # WCAG AAA normal text
        'passes_aaa_large': ratio >= 4.5,    # WCAG AAA large text
    }


def validate_theme_colors(colors: dict) -> dict:
    """Validate all theme colors against white and dark backgrounds.
    
    Args:
        colors: Dict of color names to hex values
    
    Returns:
        Dict with validation results for each color combination
    """
    results = {}
    
    white_bg = '#FFFFFF'
    dark_bg = '#1A1A1A'
    light_bg = '#F9FAFB'
    
    for name, color in colors.items():
        results[name] = {
            'on_white': check_color_contrast(color, white_bg),
            'on_light': check_color_contrast(color, light_bg),
            'on_dark': check_color_contrast(color, dark_bg),
        }
    
    return results


def generate_aria_label(element_type: str, context: str) -> str:
    """Generate appropriate ARIA label for common dashboard elements.
    
    Args:
        element_type: Type of element ('chart', 'filter', 'button', 'metric')
        context: Specific context (e.g., 'Performance Chart', 'Account Filter')
    
    Returns:
        Formatted ARIA label string
    """
    templates = {
        'chart': f'{context} chart showing portfolio data',
        'filter': f'Filter portfolio by {context.lower()}',
        'button': f'{context} button',
        'metric': f'{context} metric card',
    }
    
    return templates.get(element_type, context)


# Pre-validate PortoDash theme colors
THEME_VALIDATION = validate_theme_colors({
    'primary': '#1A1A1A',
    'secondary': '#6366F1',
    'success': '#10B981',
    'warning': '#F59E0B',
    'error': '#EF4444',
    'neutral': '#6B7280',
})
