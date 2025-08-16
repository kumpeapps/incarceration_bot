"""
Shared password format utilities for consistent password handling across backend and plugins.
"""

import re
import logging

logger = logging.getLogger(__name__)

class PasswordFormatError(Exception):
    """Exception raised for invalid password formats."""

def detect_password_format(password: str) -> str:
    """
    Detect password format based on hash pattern.
    
    Args:
        password: The password hash to analyze
        
    Returns:
        str: The detected password format
        
    Raises:
        PasswordFormatError: If password format cannot be determined
    """
    if not password:
        raise PasswordFormatError("Empty password provided")
    
    # aMember/WordPress phpass format
    if re.match(r'^\$P\$', password):
        return 'phpass'
    
    # bcrypt format
    if re.match(r'^\$2[aby]\$', password):
        return 'bcrypt'
    
    # Argon2 format
    if re.match(r'^\$argon2', password):
        return 'argon2'
    
    # Unix crypt format
    if re.match(r'^\$[1-6]\$', password):
        return 'crypt'
    
    # MD5 format (32 hex chars) - DEPRECATED, only for legacy support
    if re.match(r'^[a-fA-F0-9]{32}$', password):
        logger.warning("MD5 password format detected - this is insecure and deprecated")
        return 'md5'
    
    # SHA1 format (40 hex chars) - DEPRECATED, only for legacy support
    if re.match(r'^[a-fA-F0-9]{40}$', password):
        logger.warning("SHA1 password format detected - this is insecure and deprecated")
        return 'sha1'
    
    # If no pattern matches, this is likely a plaintext password or unknown format
    raise PasswordFormatError(f"Unable to determine password format for hash: {password[:10]}...")

def validate_password_format(password_hash: str, expected_format: str) -> bool:
    """
    Validate that a password hash matches the expected format.
    
    Args:
        password_hash: The password hash to validate
        expected_format: The expected password format
        
    Returns:
        bool: True if hash matches expected format
        
    Raises:
        PasswordFormatError: If validation fails
    """
    detected_format = detect_password_format(password_hash)
    if detected_format != expected_format:
        raise PasswordFormatError(
            f"Password hash format mismatch: expected {expected_format}, "
            f"but detected {detected_format}"
        )
    return True

def get_format_requirements() -> dict:
    """
    Get requirements for each password format.
    
    Returns:
        dict: Format requirements including patterns and security notes
    """
    return {
        'bcrypt': {
            'pattern': r'^\$2[aby]\$\d+\$.{53}$',
            'description': 'bcrypt with salt and cost factor',
            'secure': True,
            'recommended': True
        },
        'phpass': {
            'pattern': r'^\$P\$.{30}$',
            'description': 'Portable PHP password hash (phpass)',
            'secure': True,
            'recommended': False,
            'note': 'Common in WordPress/aMember'
        },
        'argon2': {
            'pattern': r'^\$argon2[id]*\$',
            'description': 'Argon2 password hash',
            'secure': True,
            'recommended': True
        },
        'crypt': {
            'pattern': r'^\$[1-6]\$',
            'description': 'Unix crypt formats (DES, MD5, SHA)',
            'secure': False,
            'recommended': False,
            'note': 'Legacy support only'
        },
        'md5': {
            'pattern': r'^[a-fA-F0-9]{32}$',
            'description': 'Plain MD5 hash',
            'secure': False,
            'recommended': False,
            'note': 'DEPRECATED - insecure, legacy support only'
        },
        'sha1': {
            'pattern': r'^[a-fA-F0-9]{40}$',
            'description': 'Plain SHA1 hash',
            'secure': False,
            'recommended': False,
            'note': 'DEPRECATED - insecure, legacy support only'
        }
    }

def is_secure_format(password_format: str) -> bool:
    """
    Check if a password format is considered secure.
    
    Args:
        password_format: The password format to check
        
    Returns:
        bool: True if format is secure
    """
    requirements = get_format_requirements()
    return requirements.get(password_format, {}).get('secure', False)

def get_recommended_format() -> str:
    """
    Get the recommended password format for new passwords.
    
    Returns:
        str: The recommended format ('bcrypt')
    """
    return 'bcrypt'
