"""
Utility functions for stroke type icons and formatting.
"""
import os


def get_stroke_icon_path(stroke_type: str) -> str:
    """
    Get image icon path for stroke type.
    
    Args:
        stroke_type: Stroke type string (freestyle, breaststroke, backstroke, butterfly, drill, mixed)
    
    Returns:
        Path to icon image file, or None if not found
    """
    if not stroke_type:
        stroke_type = 'freestyle'
    
    stroke_type = stroke_type.lower()
    
    # Map stroke types to possible filenames
    stroke_filenames = {
        'freestyle': ['freestyle', 'crawl', 'front_crawl'],
        'breaststroke': ['breaststroke', 'breast'],
        'backstroke': ['backstroke', 'back'],
        'butterfly': ['butterfly', 'fly'],
        'drill': ['drill', 'drills'],
        'mixed': ['mixed', 'im', 'individual_medley'],
    }
    
    # Look for icon files in icons/strokes directory
    icon_dir = 'icons/strokes'
    if not os.path.exists(icon_dir):
        icon_dir = 'icons'
    
    # Try to find matching icon file
    possible_names = stroke_filenames.get(stroke_type, [stroke_type])
    
    for name in possible_names:
        for ext in ['.png', '.jpg', '.jpeg', '.svg', '.avif']:
            icon_path = os.path.join(icon_dir, f"{name}{ext}")
            if os.path.exists(icon_path):
                return icon_path
    
    # Fallback: return None (will use default icon)
    return None


def get_stroke_icon_html(stroke_type: str, size: str = "32px") -> str:
    """
    Get HTML img tag for stroke icon.
    
    Args:
        stroke_type: Stroke type string
        size: Size of the icon (default: "32px")
    
    Returns:
        HTML img tag string
    """
    icon_path = get_stroke_icon_path(stroke_type)
    
    if icon_path:
        # Icons are copied to reports/icons/ directory
        # Use relative path from the HTML file location
        icon_filename = os.path.basename(icon_path)
        rel_path = f"icons/{icon_filename}"
        return f'<img src="{rel_path}" alt="{stroke_type}" style="width: {size}; height: {size}; object-fit: contain;" />'
    else:
        # Fallback to emoji if icon not found
        fallback_emojis = {
            'freestyle': '🏊',
            'breaststroke': '🏊‍♀️',
            'backstroke': '🏊‍♂️',
            'butterfly': '🦋',
            'drill': '🛠️',
            'mixed': '🔄',
        }
        emoji = fallback_emojis.get(stroke_type.lower() if stroke_type else 'freestyle', '🏊')
        return f'<span style="font-size: {size};">{emoji}</span>'


def get_stroke_icon(stroke_type: str) -> str:
    """
    Get icon path or fallback emoji for stroke type.
    For backward compatibility, returns path or emoji string.
    
    Args:
        stroke_type: Stroke type string
    
    Returns:
        Icon path or emoji string
    """
    icon_path = get_stroke_icon_path(stroke_type)
    if icon_path:
        return icon_path
    
    # Fallback emojis
    fallback_emojis = {
        'freestyle': '🏊',
        'breaststroke': '🏊‍♀️',
        'backstroke': '🏊‍♂️',
        'butterfly': '🦋',
        'drill': '🛠️',
        'mixed': '🔄',
    }
    return fallback_emojis.get(stroke_type.lower() if stroke_type else 'freestyle', '🏊')


def get_stroke_name(stroke_type: str) -> str:
    """
    Get formatted stroke name.
    
    Args:
        stroke_type: Stroke type string
    
    Returns:
        Formatted stroke name
    """
    if not stroke_type:
        return "Unknown"
    
    stroke_type = stroke_type.lower()
    
    # Capitalize first letter
    return stroke_type.capitalize()

