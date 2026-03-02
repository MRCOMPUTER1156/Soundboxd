from django import template

register = template.Library()

@register.filter
def format_number(value):
    """Format a number with dots as thousand separator (1.234.567)"""
    try:
        value = int(value)
        # Format with dots
        return "{:,}".format(value).replace(',', '.')
    except (ValueError, TypeError):
        return value
