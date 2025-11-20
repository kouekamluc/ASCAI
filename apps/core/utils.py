"""
Core utility functions for ASCAI platform.
"""
import bleach
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys


def sanitize_html(content):
    """
    Sanitize HTML content from CKEditor to prevent XSS attacks.
    
    Args:
        content: HTML string to sanitize
        
    Returns:
        Sanitized HTML string
    """
    # Allowed HTML tags
    allowed_tags = [
        'p', 'br', 'strong', 'em', 'u', 's', 'strike',
        'a', 'ul', 'ol', 'li',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'blockquote', 'pre', 'code',
        'img', 'table', 'thead', 'tbody', 'tr', 'td', 'th',
        'div', 'span',
    ]
    
    # Allowed attributes per tag
    allowed_attributes = {
        'a': ['href', 'title', 'target'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
        'table': ['border', 'cellpadding', 'cellspacing'],
        'td': ['colspan', 'rowspan'],
        'th': ['colspan', 'rowspan'],
        'div': ['class'],
        'span': ['class'],
    }
    
    # Allowed CSS styles (optional, for more control)
    allowed_styles = []
    
    # Sanitize content
    cleaned = bleach.clean(
        content,
        tags=allowed_tags,
        attributes=allowed_attributes,
        styles=allowed_styles,
        strip=True,  # Strip disallowed tags
    )
    
    return cleaned


def optimize_image(image_field, max_size=(1200, 1200), quality=85, format='JPEG'):
    """
    Optimize uploaded image by resizing and compressing.
    
    Args:
        image_field: Django ImageField or file-like object
        max_size: Tuple of (max_width, max_height)
        quality: JPEG quality (1-100)
        format: Output format ('JPEG', 'PNG', 'WEBP')
        
    Returns:
        InMemoryUploadedFile with optimized image
    """
    try:
        # Open image
        img = Image.open(image_field)
        
        # Convert RGBA to RGB for JPEG
        if format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
            # Create white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize if image is larger than max_size
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save to BytesIO
        output = BytesIO()
        
        # Determine format
        if format == 'WEBP':
            img.save(output, format='WEBP', quality=quality, method=6)
            content_type = 'image/webp'
            ext = 'webp'
        elif format == 'PNG':
            img.save(output, format='PNG', optimize=True)
            content_type = 'image/png'
            ext = 'png'
        else:  # JPEG
            img.save(output, format='JPEG', quality=quality, optimize=True)
            content_type = 'image/jpeg'
            ext = 'jpg'
        
        output.seek(0)
        
        # Get original filename
        if hasattr(image_field, 'name'):
            original_name = image_field.name
            base_name = original_name.rsplit('.', 1)[0] if '.' in original_name else original_name
            filename = f"{base_name}.{ext}"
        else:
            filename = f"optimized.{ext}"
        
        # Create InMemoryUploadedFile
        return InMemoryUploadedFile(
            output,
            'ImageField',
            filename,
            content_type,
            sys.getsizeof(output),
            None
        )
    except Exception as e:
        # If optimization fails, return original
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Image optimization failed: {e}")
        return image_field

