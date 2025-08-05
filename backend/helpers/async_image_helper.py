"""Async Images Helper Functions"""

import base64
import aiohttp
import asyncio
from loguru import logger

async def async_image_url_to_base64(session: aiohttp.ClientSession, image_url: str, timeout: int = 10):
    """
    Asynchronously fetches an image from a URL and returns its Base64 representation.

    Args:
        session: aiohttp ClientSession for making the request
        image_url: The URL of the image
        timeout: Timeout in seconds for the request

    Returns:
        A string containing the Base64 encoded image data, or None if an error occurs
    """
    try:
        # Use a HEAD request first to check if the image exists
        async with session.head(
            image_url, 
            timeout=aiohttp.ClientTimeout(total=timeout)
        ) as head_response:
            if head_response.status != 200:
                logger.warning(f"Image not found at {image_url}: HTTP {head_response.status}")
                return None
        
        # If HEAD request succeeds, get the image
        async with session.get(
            image_url, 
            timeout=aiohttp.ClientTimeout(total=timeout)
        ) as response:
            if response.status != 200:
                logger.warning(f"Failed to fetch image from {image_url}: HTTP {response.status}")
                return None
            
            # Read the image data
            image_data = await response.read()
            
            # Encode to base64
            base64_encoded = base64.b64encode(image_data).decode("utf-8")
            return base64_encoded
            
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        logger.error(f"Error fetching image from {image_url}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing image from {image_url}: {str(e)}")
        return None

# Cache to store already fetched mugshots to avoid duplicate downloads
mugshot_cache = {}

async def cached_async_image_url_to_base64(session: aiohttp.ClientSession, image_url: str, timeout: int = 10):
    """
    Version of async_image_url_to_base64 with caching to prevent duplicate downloads.
    
    Args:
        session: aiohttp ClientSession for making the request
        image_url: The URL of the image
        timeout: Timeout in seconds for the request
        
    Returns:
        A string containing the Base64 encoded image data, or None if an error occurs
    """
    # Check if we've already fetched this image
    if image_url in mugshot_cache:
        return mugshot_cache[image_url]
    
    # If not, fetch it and cache the result
    result = await async_image_url_to_base64(session, image_url, timeout)
    if result:
        mugshot_cache[image_url] = result
    
    return result
