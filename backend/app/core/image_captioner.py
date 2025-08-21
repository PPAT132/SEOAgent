#!/usr/bin/env python3
"""
Image Captioner using BLIP model
Generates short captions for images from URLs using local BLIP model
"""

import requests
import torch
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
from typing import Optional
import logging
from io import BytesIO
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageCaptioner:
    """
    Image captioner using BLIP model for generating short, descriptive captions
    """
    
    def __init__(self, model_name: str = "Salesforce/blip-image-captioning-base"):
        """
        Initialize the image captioner with BLIP model
        
        Args:
            model_name: Hugging Face model name for BLIP
        """
        self.model_name = model_name
        self.processor = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        logger.info(f"Initializing ImageCaptioner with device: {self.device}")
        self._load_model()
    
    def _load_model(self):
        """Load the BLIP model and processor"""
        try:
            logger.info(f"Loading BLIP model: {self.model_name}")
            start_time = time.time()
            
            # Load processor and model
            self.processor = BlipProcessor.from_pretrained(self.model_name)
            self.model = BlipForConditionalGeneration.from_pretrained(self.model_name)
            
            # Move model to appropriate device
            self.model.to(self.device)
            self.model.eval()  # Set to evaluation mode
            
            load_time = time.time() - start_time
            logger.info(f"Model loaded successfully in {load_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Failed to load BLIP model: {str(e)}")
            raise
    
    def _download_image(self, image_url: str, timeout: int = 10) -> Optional[Image.Image]:
        """
        Download image from URL and convert to PIL Image
        
        Args:
            image_url: URL of the image to download
            timeout: Request timeout in seconds
            
        Returns:
            PIL Image object or None if download fails
        """
        try:
            logger.info(f"Downloading image from: {image_url}")
            
            # Set headers to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(image_url, headers=headers, timeout=timeout, stream=True)
            response.raise_for_status()
            
            # Check if the content is actually an image
            content_type = response.headers.get('content-type', '').lower()
            if not content_type.startswith('image/'):
                logger.warning(f"URL does not point to an image. Content-Type: {content_type}")
                return None
            
            # Load image from response content
            image = Image.open(BytesIO(response.content))
            
            # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            logger.info(f"Image downloaded successfully. Size: {image.size}")
            return image
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download image from {image_url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Failed to process image from {image_url}: {str(e)}")
            return None
    
    def generate_caption(self, image_url: str, max_length: int = 50, min_length: int = 10) -> Optional[str]:
        """
        Generate a caption for an image from URL
        
        Args:
            image_url: URL of the image to caption
            max_length: Maximum length of the generated caption
            min_length: Minimum length of the generated caption
            
        Returns:
            Generated caption string or None if processing fails
        """
        if not self.model or not self.processor:
            logger.error("Model not properly initialized")
            return None
        
        # Download the image
        image = self._download_image(image_url)
        if image is None:
            return None
        
        try:
            logger.info("Generating caption...")
            start_time = time.time()
            
            # Process the image
            inputs = self.processor(image, return_tensors="pt").to(self.device)
            
            # Generate caption
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    min_length=min_length,
                    num_beams=5,  # Use beam search for better quality
                    early_stopping=True,
                    do_sample=False  # Deterministic generation
                )
            
            # Decode the generated caption
            caption = self.processor.decode(generated_ids[0], skip_special_tokens=True)
            
            generation_time = time.time() - start_time
            logger.info(f"Caption generated in {generation_time:.2f} seconds: '{caption}'")
            
            return caption
            
        except Exception as e:
            logger.error(f"Failed to generate caption: {str(e)}")
            return None
    
    def generate_short_caption(self, image_url: str) -> Optional[str]:
        """
        Generate a short caption (optimized for alt text)
        
        Args:
            image_url: URL of the image to caption
            
        Returns:
            Short caption string or None if processing fails
        """
        caption = self.generate_caption(image_url, max_length=30, min_length=5)
        
        if caption:
            # Clean up the caption for use as alt text
            caption = caption.strip()
            
            # Remove common prefixes that BLIP sometimes adds
            prefixes_to_remove = [
                "a picture of ",
                "an image of ",
                "a photo of ",
                "this is ",
                "there is ",
                "here is "
            ]
            
            for prefix in prefixes_to_remove:
                if caption.lower().startswith(prefix):
                    caption = caption[len(prefix):]
                    break
            
            # Capitalize first letter
            caption = caption[0].upper() + caption[1:] if caption else ""
            
            # Ensure it ends with proper punctuation (for accessibility)
            if caption and not caption.endswith(('.', '!', '?')):
                caption += '.'
        
        return caption
    
    def batch_caption_images(self, image_urls: list, max_length: int = 50) -> dict:
        """
        Generate captions for multiple images
        
        Args:
            image_urls: List of image URLs
            max_length: Maximum length for captions
            
        Returns:
            Dictionary mapping URLs to their captions
        """
        results = {}
        
        logger.info(f"Processing {len(image_urls)} images...")
        
        for i, url in enumerate(image_urls, 1):
            logger.info(f"Processing image {i}/{len(image_urls)}")
            caption = self.generate_caption(url, max_length=max_length)
            results[url] = caption
        
        successful_captions = sum(1 for caption in results.values() if caption is not None)
        logger.info(f"Successfully generated captions for {successful_captions}/{len(image_urls)} images")
        
        return results


# Convenience function for quick usage
def caption_image(image_url: str, short: bool = True) -> Optional[str]:
    """
    Quick function to caption a single image
    
    Args:
        image_url: URL of the image to caption
        short: Whether to generate a short caption optimized for alt text
        
    Returns:
        Generated caption or None if failed
    """
    captioner = ImageCaptioner()
    
    if short:
        return captioner.generate_short_caption(image_url)
    else:
        return captioner.generate_caption(image_url)


# Example usage and testing
if __name__ == "__main__":
    # Test the image captioner
    test_urls = [
        "https://images.unsplash.com/photo-1518717758536-85ae29035b6d?w=300",  # Dog
        "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=300",  # Mountain landscape
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=300",  # Food
    ]
    
    captioner = ImageCaptioner()
    
    print("Testing Image Captioner")
    print("=" * 50)
    
    for i, url in enumerate(test_urls, 1):
        print(f"\nImage {i}: {url}")
        
        # Generate regular caption
        caption = captioner.generate_caption(url)
        print(f"Caption: {caption}")
        
        # Generate short caption
        short_caption = captioner.generate_short_caption(url)
        print(f"Short caption: {short_caption}")
        
        print("-" * 30)