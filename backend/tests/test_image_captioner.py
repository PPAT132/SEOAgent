#!/usr/bin/env python3
"""
Test script for ImageCaptioner
Tests the BLIP-based image captioning functionality
"""

import os
import sys

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.image_captioner import ImageCaptioner, caption_image


def test_image_captioner():
    """Test the ImageCaptioner with sample images"""
    
    print("=" * 60)
    print("Image Captioner Test")
    print("=" * 60)
    
    # Test URLs - using small images for faster processing
    test_images = [
        {
            "url": "https://images.unsplash.com/photo-1518717758536-85ae29035b6d?w=300",
            "description": "Dog photo"
        },
        {
            "url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=300", 
            "description": "Mountain landscape"
        },
        {
            "url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=300",
            "description": "Food photo"
        }
    ]
    
    # Test 1: Initialize captioner
    print("Test 1: Initializing ImageCaptioner...")
    try:
        captioner = ImageCaptioner()
        print("✓ ImageCaptioner initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize ImageCaptioner: {e}")
        return False
    
    # Test 2: Single image captioning
    print(f"\nTest 2: Single Image Captioning")
    print("-" * 40)
    
    success_count = 0
    
    for i, image_info in enumerate(test_images, 1):
        url = image_info["url"]
        description = image_info["description"]
        
        print(f"\nImage {i}: {description}")
        print(f"URL: {url}")
        
        try:
            # Test regular caption
            caption = captioner.generate_caption(url)
            if caption:
                print(f"Caption: {caption}")
                success_count += 1
            else:
                print("✗ Failed to generate caption")
            
            # Test short caption (for alt text)
            short_caption = captioner.generate_short_caption(url)
            if short_caption:
                print(f"Short caption: {short_caption}")
            else:
                print("✗ Failed to generate short caption")
                
        except Exception as e:
            print(f"✗ Error processing image: {e}")
    
    # Test 3: Batch processing
    print(f"\nTest 3: Batch Processing")
    print("-" * 40)
    
    try:
        urls = [img["url"] for img in test_images]
        results = captioner.batch_caption_images(urls, max_length=40)
        
        print(f"Batch results:")
        for url, caption in results.items():
            if caption:
                print(f"  ✓ {caption}")
            else:
                print(f"  ✗ Failed for {url}")
                
    except Exception as e:
        print(f"✗ Batch processing failed: {e}")
    
    # Test 4: Convenience function
    print(f"\nTest 4: Convenience Function")
    print("-" * 40)
    
    try:
        test_url = test_images[0]["url"]
        quick_caption = caption_image(test_url, short=True)
        if quick_caption:
            print(f"✓ Quick caption: {quick_caption}")
        else:
            print("✗ Quick caption failed")
    except Exception as e:
        print(f"✗ Convenience function failed: {e}")
    
    # Test 5: Error handling (invalid URL)
    print(f"\nTest 5: Error Handling")
    print("-" * 40)
    
    try:
        invalid_url = "https://example.com/nonexistent-image.jpg"
        result = captioner.generate_caption(invalid_url)
        if result is None:
            print("✓ Properly handled invalid URL")
        else:
            print(f"? Unexpected result for invalid URL: {result}")
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
    
    # Summary
    total_tests = len(test_images)
    success_rate = (success_count / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Images processed: {success_count}/{total_tests}")
    print(f"Success rate: {success_rate:.1f}%")
    
    if success_count > 0:
        print("✓ Image captioner is working!")
        return True
    else:
        print("✗ Image captioner failed all tests")
        return False


def test_caption_for_seo():
    """Test generating captions specifically for SEO alt text"""
    
    print(f"\n" + "=" * 60)
    print("SEO Alt Text Generation Test")
    print("=" * 60)
    
    # Test with images that might appear on websites
    seo_test_images = [
        "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=400",  # Shoes
        "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400",  # Office
        "https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=400",  # Food
    ]
    
    captioner = ImageCaptioner()
    
    print("Generating SEO-optimized alt text:")
    print("-" * 40)
    
    for i, url in enumerate(seo_test_images, 1):
        try:
            alt_text = captioner.generate_short_caption(url)
            if alt_text:
                print(f"{i}. {alt_text}")
                # Validate alt text properties
                if len(alt_text) <= 125:  # Good alt text length
                    print(f"   ✓ Good length ({len(alt_text)} chars)")
                else:
                    print(f"   ⚠ Too long ({len(alt_text)} chars)")
            else:
                print(f"{i}. ✗ Failed to generate alt text")
        except Exception as e:
            print(f"{i}. ✗ Error: {e}")


if __name__ == "__main__":
    # Run the tests
    print("Starting Image Captioner Tests...")
    
    # Check if we have the required dependencies
    try:
        import torch
        import transformers
        from PIL import Image
        print("✓ All required dependencies are available")
    except ImportError as e:
        print(f"✗ Missing dependencies: {e}")
        print("Please install with: pip install torch transformers pillow")
        sys.exit(1)
    
    # Run main test
    success = test_image_captioner()
    
    # Run SEO-specific test
    if success:
        test_caption_for_seo()
    
    print(f"\nTest completed. {'Success!' if success else 'Some tests failed.'}")
