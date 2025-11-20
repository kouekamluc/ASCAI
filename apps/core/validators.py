"""
File validation utilities for ASCAI platform.
"""
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


# Allowed MIME types for different file categories
ALLOWED_DOCUMENT_MIME_TYPES = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',  # .pptx
    'text/plain',
    'text/csv',
]

ALLOWED_IMAGE_MIME_TYPES = [
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
]

ALLOWED_RESUME_MIME_TYPES = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
]

# File size limits (in bytes)
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10MB
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_RESUME_SIZE = 5 * 1024 * 1024  # 5MB


def validate_file_type(file, allowed_types, file_type_name="file"):
    """
    Validate file type using MIME type detection.
    
    Args:
        file: Django UploadedFile object
        allowed_types: List of allowed MIME types
        file_type_name: Name of file type for error messages
        
    Raises:
        ValidationError if file type is not allowed
    """
    if MAGIC_AVAILABLE:
        try:
            # Read first 1024 bytes for MIME detection
            file.seek(0)
            file_content = file.read(1024)
            file.seek(0)  # Reset file pointer
            
            # Detect MIME type
            mime = magic.Magic(mime=True)
            detected_mime = mime.from_buffer(file_content)
            
            if detected_mime not in allowed_types:
                raise ValidationError(
                    _('File type "%(mime)s" is not allowed for %(file_type)s. Allowed types: %(allowed)s') % {
                        'mime': detected_mime,
                        'file_type': file_type_name,
                        'allowed': ', '.join(allowed_types)
                    }
                )
        except Exception as e:
            # If magic fails, fall back to extension-based validation
            import os
            allowed_extensions = {
                'application/pdf': ['.pdf'],
                'application/msword': ['.doc'],
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
                'application/vnd.ms-excel': ['.xls'],
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
                'application/vnd.ms-powerpoint': ['.ppt'],
                'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
                'text/plain': ['.txt'],
                'text/csv': ['.csv'],
                'image/jpeg': ['.jpg', '.jpeg'],
                'image/png': ['.png'],
                'image/gif': ['.gif'],
                'image/webp': ['.webp'],
            }
            
            ext = os.path.splitext(file.name)[1].lower()
            allowed_exts = []
            for mime in allowed_types:
                allowed_exts.extend(allowed_extensions.get(mime, []))
            
            if ext not in allowed_exts:
                raise ValidationError(
                    _('File extension "%(ext)s" is not allowed for %(file_type)s.') % {
                        'ext': ext,
                        'file_type': file_type_name
                    }
                )
    else:
        # python-magic not available, fall back to extension-based validation
        import os
        allowed_extensions = {
            'application/pdf': ['.pdf'],
            'application/msword': ['.doc'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
            'application/vnd.ms-excel': ['.xls'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
            'application/vnd.ms-powerpoint': ['.ppt'],
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
            'text/plain': ['.txt'],
            'text/csv': ['.csv'],
            'image/jpeg': ['.jpg', '.jpeg'],
            'image/png': ['.png'],
            'image/gif': ['.gif'],
            'image/webp': ['.webp'],
        }
        
        ext = os.path.splitext(file.name)[1].lower()
        allowed_exts = []
        for mime in allowed_types:
            allowed_exts.extend(allowed_extensions.get(mime, []))
        
        if ext not in allowed_exts:
            raise ValidationError(
                _('File extension "%(ext)s" is not allowed for %(file_type)s.') % {
                    'ext': ext,
                    'file_type': file_type_name
                }
            )


def validate_file_size(file, max_size, file_type_name="file"):
    """
    Validate file size.
    
    Args:
        file: Django UploadedFile object
        max_size: Maximum file size in bytes
        file_type_name: Name of file type for error messages
        
    Raises:
        ValidationError if file is too large
    """
    if file.size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        raise ValidationError(
            _('File size exceeds maximum allowed size of %(size).1f MB for %(file_type)s.') % {
                'size': max_size_mb,
                'file_type': file_type_name
            }
        )


def validate_document_file(file):
    """Validate document file (PDF, DOC, DOCX, etc.)."""
    validate_file_type(file, ALLOWED_DOCUMENT_MIME_TYPES, "document")
    validate_file_size(file, MAX_DOCUMENT_SIZE, "document")


def validate_image_file(file):
    """Validate image file (JPEG, PNG, GIF, WEBP)."""
    validate_file_type(file, ALLOWED_IMAGE_MIME_TYPES, "image")
    validate_file_size(file, MAX_IMAGE_SIZE, "image")


def validate_resume_file(file):
    """Validate resume file (PDF, DOC, DOCX)."""
    validate_file_type(file, ALLOWED_RESUME_MIME_TYPES, "resume")
    validate_file_size(file, MAX_RESUME_SIZE, "resume")

