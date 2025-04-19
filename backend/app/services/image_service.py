import os
import logging
import requests
from typing import Optional
import tempfile
from urllib.parse import quote

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageService:
    """
    Service to fetch and manage images for presentations
    """
    
    def __init__(self):
        """
        Initialize the image service
        """
        # Create a temporary directory to store images
        self.temp_dir = tempfile.mkdtemp(prefix="ppt_images_")
        logger.info(f"Image service initialized. Temporary directory: {self.temp_dir}")
        
        # Get API key from environment or use a default
        self.api_key = os.getenv("UNSPLASH_API_KEY", "")
        self.use_mock = not self.api_key
        
        if self.use_mock:
            logger.warning("No Unsplash API key found. Using local placeholder images.")
        
        # Base URL for the Unsplash API
        self.api_base_url = "https://api.unsplash.com"
    
    def get_image_for_slide(self, description: str) -> Optional[str]:
        """
        Get an image path for a slide based on the description
        
        Args:
            description: Description of the image to fetch
            
        Returns:
            Path to the image file, or None if failed
        """
        try:
            logger.info(f"Fetching image for description: {description}")
            
            if self.use_mock:
                return self._get_placeholder_image()
            
            # Search for an image using the Unsplash API
            image_url = self._search_image(description)
            if not image_url:
                logger.warning(f"No image found for '{description}'. Using placeholder.")
                return self._get_placeholder_image()
            
            # Download the image
            image_path = self._download_image(image_url, description)
            if not image_path:
                logger.warning("Failed to download image. Using placeholder.")
                return self._get_placeholder_image()
            
            logger.info(f"Image successfully fetched and saved to {image_path}")
            return image_path
            
        except Exception as e:
            logger.error(f"Error fetching image: {str(e)}")
            return self._get_placeholder_image()
    
    def _search_image(self, query: str) -> Optional[str]:
        """
        Search for an image using the Unsplash API
        
        Args:
            query: Search query
            
        Returns:
            URL of the image, or None if not found
        """
        try:
            # Encode the query for URL
            encoded_query = quote(query)
            
            # Make request to Unsplash API
            url = f"{self.api_base_url}/search/photos?query={encoded_query}&per_page=1"
            headers = {"Authorization": f"Client-ID {self.api_key}"}
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Unsplash API error: {response.status_code} - {response.text}")
                return None
            
            data = response.json()
            
            if not data.get("results") or len(data["results"]) == 0:
                logger.warning(f"No images found for query: {query}")
                return None
            
            # Get the image URL
            image_url = data["results"][0]["urls"]["regular"]
            return image_url
            
        except Exception as e:
            logger.error(f"Error searching for image: {str(e)}")
            return None
    
    def _download_image(self, url: str, description: str) -> Optional[str]:
        """
        Download an image from a URL
        
        Args:
            url: URL of the image
            description: Description for naming
            
        Returns:
            Path to the downloaded image, or None if download failed
        """
        try:
            # Create a filename based on the description
            # Remove special characters and limit length
            filename = "".join(c for c in description if c.isalnum() or c.isspace())
            filename = filename.replace(" ", "_")
            filename = filename[:50] if len(filename) > 50 else filename
            
            # Add random suffix to avoid name collisions
            import random
            import string
            suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
            
            filepath = os.path.join(self.temp_dir, f"{filename}_{suffix}.jpg")
            
            # Download the image
            response = requests.get(url, stream=True, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Error downloading image: {response.status_code}")
                return None
            
            # Save the image
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Image saved to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
            return None
    
    def _get_placeholder_image(self) -> str:
        """
        Get a placeholder image when real images cannot be fetched
        
        Returns:
            Path to a placeholder image
        """
        try:
            # Check for existing template directory that might have placeholder images
            templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
            placeholder_path = os.path.join(templates_dir, "placeholder.jpg")
            
            # If the placeholder doesn't exist, create a simple colored rectangle
            if not os.path.exists(placeholder_path):
                try:
                    from PIL import Image, ImageDraw
                    
                    # Create a colored rectangle
                    img = Image.new('RGB', (800, 600), color=(41, 128, 185))
                    draw = ImageDraw.Draw(img)
                    draw.rectangle([(100, 100), (700, 500)], fill=(236, 240, 241))
                    
                    # Save the placeholder
                    os.makedirs(os.path.dirname(placeholder_path), exist_ok=True)
                    img.save(placeholder_path)
                    logger.info(f"Created placeholder image at {placeholder_path}")
                    
                except ImportError:
                    # If PIL is not available, create an empty file
                    logger.warning("PIL not available. Creating empty placeholder file.")
                    with open(placeholder_path, "w") as f:
                        f.write("")
            
            return placeholder_path
            
        except Exception as e:
            logger.error(f"Error creating placeholder: {str(e)}")
            # Return a path even if creation failed, PPT generator will handle missing files
            return os.path.join(tempfile.gettempdir(), "placeholder.jpg")
    
    def cleanup(self):
        """
        Clean up temporary files
        """
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
        except Exception as e:
            logger.error(f"Error cleaning up: {str(e)}") 