from django import template
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from urllib.parse import urlencode

register = template.Library()

@register.simple_tag(takes_context=True)
def sort_header(context, field, label, default_order='asc'):
    """
    Generates a sortable table header link
    """
    request = context['request']
    current_sort = request.GET.get('sort', '')
    current_order = request.GET.get('order', 'asc')
    
    # Determine if this field is currently being sorted
    is_active = current_sort == field
    
    # Determine the next order (toggle if active, use default if not)
    if is_active:
        next_order = 'desc' if current_order == 'asc' else 'asc'
    else:
        next_order = default_order
    
    # Build the query parameters
    params = request.GET.copy()
    params['sort'] = field
    params['order'] = next_order
    
    # Create the URL
    url = f"?{params.urlencode()}"
    
    # Determine the sort indicator icon
    if is_active:
        if current_order == 'asc':
            icon = '<i class="fas fa-sort-up ms-1"></i>'
        else:
            icon = '<i class="fas fa-sort-down ms-1"></i>'
    else:
        icon = '<i class="fas fa-sort ms-1 text-muted"></i>'
    
    # Generate the HTML
    html = format_html(
        '<a href="{}" class="text-decoration-none text-dark d-flex align-items-center justify-content-between">'
        '{}{}'
        '</a>',
        url,
        label,
        mark_safe(icon)
    )
    
    return html

@register.simple_tag(takes_context=True)
def sort_url(context, field, order='asc'):
    """
    Generates a sort URL for a given field and order
    """
    request = context['request']
    params = request.GET.copy()
    params['sort'] = field
    params['order'] = order
    return f"?{params.urlencode()}"
