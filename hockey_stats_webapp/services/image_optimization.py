"""
Image Optimization Service for Mobile Performance

This service provides image optimization, lazy loading, and responsive image handling
to improve mobile performance and reduce bandwidth usage.
"""

import base64
import io
import logging
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse
import hashlib

logger = logging.getLogger(__name__)

class ImageOptimizationService:
    """
    Service for optimizing images for mobile clients.
    Provides lazy loading, responsive images, and bandwidth optimization.
    """
    
    def __init__(self):
        """Initialize the image optimization service."""
        self.lazy_loading_enabled = True
        self.responsive_images_enabled = True
        self.placeholder_cache = {}
        
        # Image optimization settings
        self.mobile_max_width = 800
        self.tablet_max_width = 1200
        self.desktop_max_width = 1920
        
        # Supported image formats
        self.supported_formats = ['jpg', 'jpeg', 'png', 'webp', 'svg']
        
        # Placeholder SVG template
        self.placeholder_template = '''
        <svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
            <rect width="100%" height="100%" fill="#f0f0f0"/>
            <text x="50%" y="50%" text-anchor="middle" dy=".3em" 
                  font-family="Arial, sans-serif" font-size="14" fill="#999">
                {text}
            </text>
        </svg>
        '''
    
    def create_lazy_loading_config(self, src: str, alt: str = "", 
                                 width: Optional[int] = None, 
                                 height: Optional[int] = None) -> Dict[str, Any]:
        """
        Create lazy loading configuration for an image.
        
        Args:
            src: Image source URL
            alt: Alt text for the image
            width: Image width (optional)
            height: Image height (optional)
            
        Returns:
            Dictionary with lazy loading configuration
        """
        try:
            # Generate placeholder
            placeholder = self.generate_placeholder(width or 300, height or 200, alt or "Loading...")
            
            # Create responsive srcset if width is provided
            srcset = self.generate_responsive_srcset(src, width) if width else None
            
            config = {
                'src': src,
                'alt': alt,
                'loading': 'lazy',
                'placeholder': placeholder,
                'lazy_enabled': self.lazy_loading_enabled
            }
            
            if width:
                config['width'] = width
            if height:
                config['height'] = height
            if srcset:
                config['srcset'] = srcset
                config['sizes'] = self.generate_sizes_attribute()
            
            # Add intersection observer config
            config['intersection_config'] = {
                'root': None,
                'rootMargin': '50px',
                'threshold': 0.1
            }
            
            return config
            
        except Exception as e:
            logger.error(f"Error creating lazy loading config: {e}")
            return {
                'src': src,
                'alt': alt,
                'error': str(e)
            }
    
    def generate_placeholder(self, width: int, height: int, text: str = "Loading...") -> str:
        """
        Generate a placeholder SVG for lazy loading.
        
        Args:
            width: Placeholder width
            height: Placeholder height
            text: Placeholder text
            
        Returns:
            Base64 encoded SVG placeholder
        """
        try:
            # Check cache first
            cache_key = f"{width}x{height}:{text}"
            if cache_key in self.placeholder_cache:
                return self.placeholder_cache[cache_key]
            
            # Generate SVG
            svg_content = self.placeholder_template.format(
                width=width,
                height=height,
                text=text
            ).strip()
            
            # Encode as base64 data URL
            svg_bytes = svg_content.encode('utf-8')
            svg_b64 = base64.b64encode(svg_bytes).decode('utf-8')
            placeholder = f"data:image/svg+xml;base64,{svg_b64}"
            
            # Cache the result
            self.placeholder_cache[cache_key] = placeholder
            
            return placeholder
            
        except Exception as e:
            logger.error(f"Error generating placeholder: {e}")
            # Return a simple gray placeholder
            return "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjBmMGYwIi8+PC9zdmc+"
    
    def generate_responsive_srcset(self, base_src: str, original_width: int) -> str:
        """
        Generate responsive srcset for different screen sizes.
        
        Args:
            base_src: Base image source URL
            original_width: Original image width
            
        Returns:
            Srcset string for responsive images
        """
        try:
            # Parse the URL to modify it
            parsed_url = urlparse(base_src)
            base_path = parsed_url.path
            
            # Generate different sizes
            sizes = []
            
            # Mobile size (if original is larger)
            if original_width > self.mobile_max_width:
                mobile_src = self.modify_image_url(base_src, self.mobile_max_width)
                sizes.append(f"{mobile_src} {self.mobile_max_width}w")
            
            # Tablet size (if original is larger)
            if original_width > self.tablet_max_width:
                tablet_src = self.modify_image_url(base_src, self.tablet_max_width)
                sizes.append(f"{tablet_src} {self.tablet_max_width}w")
            
            # Original size
            sizes.append(f"{base_src} {original_width}w")
            
            return ", ".join(sizes)
            
        except Exception as e:
            logger.error(f"Error generating responsive srcset: {e}")
            return f"{base_src} {original_width}w"
    
    def modify_image_url(self, url: str, width: int) -> str:
        """
        Modify image URL to request a specific width.
        This is a placeholder implementation - in a real app, you'd integrate
        with an image CDN or processing service.
        
        Args:
            url: Original image URL
            width: Desired width
            
        Returns:
            Modified URL for the specified width
        """
        # For now, just return the original URL with a width parameter
        # In a real implementation, you'd integrate with services like:
        # - Cloudinary: url + f"?w_{width}"
        # - ImageKit: url + f"?tr=w-{width}"
        # - AWS CloudFront with Lambda@Edge
        
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}w={width}"
    
    def generate_sizes_attribute(self) -> str:
        """
        Generate the sizes attribute for responsive images.
        
        Returns:
            Sizes attribute string
        """
        return (
            f"(max-width: {self.mobile_max_width}px) 100vw, "
            f"(max-width: {self.tablet_max_width}px) 100vw, "
            f"{self.desktop_max_width}px"
        )
    
    def optimize_background_image(self, image_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize background image configuration for mobile.
        
        Args:
            image_config: Background image configuration
            
        Returns:
            Optimized background image configuration
        """
        try:
            optimized = image_config.copy()
            
            # Add mobile-optimized background properties
            optimized.update({
                'backgroundSize': 'cover',
                'backgroundPosition': 'center',
                'backgroundRepeat': 'no-repeat',
                'backgroundAttachment': 'scroll'  # Better for mobile performance
            })
            
            # Add responsive background images if supported
            if 'src' in optimized:
                src = optimized['src']
                
                # Create media queries for different screen sizes
                optimized['responsive_backgrounds'] = {
                    'mobile': {
                        'media': f'(max-width: {self.mobile_max_width}px)',
                        'src': self.modify_image_url(src, self.mobile_max_width)
                    },
                    'tablet': {
                        'media': f'(max-width: {self.tablet_max_width}px)',
                        'src': self.modify_image_url(src, self.tablet_max_width)
                    },
                    'desktop': {
                        'media': f'(min-width: {self.tablet_max_width + 1}px)',
                        'src': src
                    }
                }
            
            return optimized
            
        except Exception as e:
            logger.error(f"Error optimizing background image: {e}")
            return image_config
    
    def create_progressive_image_loader(self, images: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a progressive image loader configuration.
        
        Args:
            images: List of image configurations
            
        Returns:
            Progressive loader configuration
        """
        try:
            # Prioritize images based on their importance
            prioritized_images = self.prioritize_images(images)
            
            # Create loading batches
            batches = self.create_loading_batches(prioritized_images)
            
            return {
                'batches': batches,
                'loading_strategy': 'progressive',
                'batch_delay': 100,  # ms between batches
                'max_concurrent': 3,  # max concurrent image loads
                'retry_attempts': 2,
                'timeout': 10000  # 10 second timeout
            }
            
        except Exception as e:
            logger.error(f"Error creating progressive image loader: {e}")
            return {
                'batches': [images],
                'error': str(e)
            }
    
    def prioritize_images(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prioritize images based on their importance and visibility.
        
        Args:
            images: List of image configurations
            
        Returns:
            Prioritized list of images
        """
        try:
            # Sort images by priority
            def get_priority(img):
                # Higher priority for above-the-fold images
                if img.get('above_fold', False):
                    return 1
                # Medium priority for visible images
                elif img.get('visible', True):
                    return 2
                # Lower priority for below-the-fold images
                else:
                    return 3
            
            return sorted(images, key=get_priority)
            
        except Exception as e:
            logger.error(f"Error prioritizing images: {e}")
            return images
    
    def create_loading_batches(self, images: List[Dict[str, Any]], batch_size: int = 3) -> List[List[Dict[str, Any]]]:
        """
        Create batches of images for progressive loading.
        
        Args:
            images: Prioritized list of images
            batch_size: Number of images per batch
            
        Returns:
            List of image batches
        """
        try:
            batches = []
            for i in range(0, len(images), batch_size):
                batch = images[i:i + batch_size]
                batches.append(batch)
            
            return batches
            
        except Exception as e:
            logger.error(f"Error creating loading batches: {e}")
            return [images]
    
    def get_image_optimization_stats(self) -> Dict[str, Any]:
        """
        Get image optimization statistics and configuration.
        
        Returns:
            Dictionary with optimization statistics
        """
        return {
            'lazy_loading_enabled': self.lazy_loading_enabled,
            'responsive_images_enabled': self.responsive_images_enabled,
            'mobile_max_width': self.mobile_max_width,
            'tablet_max_width': self.tablet_max_width,
            'desktop_max_width': self.desktop_max_width,
            'supported_formats': self.supported_formats,
            'placeholder_cache_size': len(self.placeholder_cache),
            'optimization_features': [
                'lazy_loading',
                'responsive_srcset',
                'progressive_loading',
                'placeholder_generation',
                'background_optimization'
            ]
        }
    
    def estimate_image_savings(self, original_images: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Estimate bandwidth savings from image optimization.
        
        Args:
            original_images: List of original image configurations
            
        Returns:
            Dictionary with estimated savings
        """
        try:
            total_original_size = 0
            total_optimized_size = 0
            
            for img in original_images:
                # Estimate original size (placeholder values)
                original_size = img.get('size', 500 * 1024)  # 500KB default
                
                # Estimate optimized size based on responsive loading
                width = img.get('width', 1200)
                if width > self.mobile_max_width:
                    # Assume 60% size reduction for mobile
                    optimized_size = original_size * 0.4
                else:
                    optimized_size = original_size
                
                total_original_size += original_size
                total_optimized_size += optimized_size
            
            savings = total_original_size - total_optimized_size
            savings_percentage = (savings / total_original_size * 100) if total_original_size > 0 else 0
            
            return {
                'total_images': len(original_images),
                'original_size_bytes': total_original_size,
                'optimized_size_bytes': total_optimized_size,
                'savings_bytes': savings,
                'savings_percentage': round(savings_percentage, 2),
                'lazy_loading_benefit': 'Reduces initial page load by deferring off-screen images',
                'responsive_benefit': 'Serves appropriately sized images for device'
            }
            
        except Exception as e:
            logger.error(f"Error estimating image savings: {e}")
            return {
                'error': str(e),
                'total_images': len(original_images)
            }