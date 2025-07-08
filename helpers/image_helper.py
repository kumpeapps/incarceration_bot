"""Images Helper Functions"""

import base64
import requests # type: ignore


def image_url_to_base64(image_url):
    """
    Fetches an image from a URL and returns its Base64 representation.

    Args:
        image_url: The URL of the image.

    Returns:
        A string containing the Base64 encoded image data, or None if an error occurs.
    """
    try:
        # First check if the URL exists using HEAD request
        head_response = requests.head(image_url, timeout=30)
        head_response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        if head_response.status_code != 200:
            return None
        # If HEAD request succeeds, proceed with downloading the image
        response = requests.get(image_url, stream=True, timeout=30)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        image_data = response.content
        base64_encoded = base64.b64encode(image_data).decode("utf-8")
        return base64_encoded
    except requests.exceptions.RequestException as e:
        print(f"Error fetching image from URL: {e}")
        return None
    except (ValueError, TypeError, OSError) as e:
        print(f"An error occurred: {e}")
        return None