"""
Image Processing Module
Responsible for image position swapping and related operations
"""
import cv2
import numpy as np
from typing import Tuple, Optional
from PIL import Image

class ImageProcessor:
    """Image Processor"""
    
    def __init__(self, swap_method: str = "physical", jpeg_quality: int = 95):
        """
        Initialize image processor
        
        Args:
            swap_method: Swap method - "physical" (physical swap) or "prompt" (only prompt swap)
            jpeg_quality: JPEG quality
        """
        self.swap_method = swap_method
        self.jpeg_quality = jpeg_quality
        
    def swap_positions(self, frame: np.ndarray) -> np.ndarray:
        """
        Swap positions of edit_1 and edit_2
        
        Args:
            frame: Original frame (OpenCV format, BGR)
            
        Returns:
            Frame with swapped positions
        """
        if self.swap_method == "physical":
            return self._physical_swap(frame)
        else:
            # Prompt method doesn't need image processing, return original
            return frame.copy()
            
    def _physical_swap(self, frame: np.ndarray) -> np.ndarray:
        """
        Physically swap positions of edit_1 and edit_2
        
        Image layout assumption:
        - Left: edit_1 (approximately 0-33% width)
        - Middle: src (approximately 33-66% width)
        - Right: edit_2 (approximately 66-100% width)
        
        After swap:
        - Left: edit_2
        - Middle: src
        - Right: edit_1
        """
        height, width = frame.shape[:2]
        
        # Define approximate boundaries for three regions (assuming uniform distribution)
        # Left region: edit_1
        left_end = width // 3
        # Middle region: src
        middle_start = width // 3
        middle_end = 2 * width // 3
        # Right region: edit_2
        right_start = 2 * width // 3
        
        # Extract three regions
        left_region = frame[:, :left_end].copy()
        middle_region = frame[:, middle_start:middle_end].copy()
        right_region = frame[:, right_start:].copy()
        
        # Create new frame
        new_frame = np.zeros_like(frame)
        
        # Swap positions: edit_2 to left, edit_1 to right
        # Left side: edit_2 (original right)
        new_frame[:, :left_end] = right_region
        # Middle: keep src
        new_frame[:, middle_start:middle_end] = middle_region
        # Right side: edit_1 (original left)
        new_frame[:, right_start:] = left_region
        
        # Handle potential boundary mismatch
        if left_end != middle_start or middle_end != right_start:
            # Use more precise swap
            new_frame = self._precise_swap(frame)
            
        return new_frame
        
    def _precise_swap(self, frame: np.ndarray) -> np.ndarray:
        """
        Precise swap, handling potential boundary issues
        """
        height, width = frame.shape[:2]
        
        # Calculate actual width for three regions
        third_width = width / 3
        
        # Create new frame
        new_frame = frame.copy()
        
        # Use sliding window method for swap
        # Actually, simple method is to create three equal-width slices
        slice_width = width // 3
        
        # Extract slices
        slice1 = frame[:, :slice_width].copy()  # edit_1
        slice2 = frame[:, slice_width:2*slice_width].copy()  # src
        slice3 = frame[:, 2*slice_width:].copy()  # edit_2
        
        # Recombine: edit_2, src, edit_1
        new_frame[:, :slice_width] = slice3
        new_frame[:, slice_width:2*slice_width] = slice2
        new_frame[:, 2*slice_width:] = slice1
        
        return new_frame
        
    def detect_text_regions(self, frame: np.ndarray) -> dict:
        """
        Detect text regions in image (simplified version)
        
        Args:
            frame: Input frame
            
        Returns:
            Text region information dictionary
        """
        # OCR can be integrated here to detect label text
        # Currently returns simplified position information
        height, width = frame.shape[:2]
        
        return {
            'edit1_label': {
                'position': 'left',
                'bbox': (0, 0, width//3, 50)  # Assuming label at top-left
            },
            'edit2_label': {
                'position': 'right', 
                'bbox': (2*width//3, 0, width, 50)
            },
            'instruction_area': {
                'position': 'top',
                'bbox': (0, 0, width, 100)
            }
        }
        
    def add_swap_labels(self, frame: np.ndarray, 
                       swap_applied: bool = False) -> np.ndarray:
        """
        Add swap marker to frame (for debugging)
        
        Args:
            frame: Input frame
            swap_applied: Whether swap was applied
            
        Returns:
            Frame with marker
        """
        if not swap_applied:
            return frame
            
        # Create copy
        marked_frame = frame.copy()
        
        # Add red border to indicate swap
        height, width = marked_frame.shape[:2]
        cv2.rectangle(marked_frame, (5, 5), (width-5, height-5), (0, 0, 255), 3)
        
        # Add text marker
        cv2.putText(marked_frame, "SWAPPED", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        return marked_frame
        
    def prepare_for_model(self, frame: np.ndarray) -> bytes:
        """
        Prepare frame for model input (JPEG bytes)
        
        Args:
            frame: Input frame (OpenCV format)
            
        Returns:
            JPEG byte data
        """
        # OpenCV uses BGR, need to convert to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(rgb_frame)
        
        # Save as JPEG bytes
        import io
        buffer = io.BytesIO()
        pil_image.save(buffer, format='JPEG', quality=self.jpeg_quality)
        
        return buffer.getvalue()
        
    def create_comparison_image(self, original: np.ndarray, 
                               swapped: np.ndarray) -> np.ndarray:
        """
        Create comparison image (side-by-side display of original and swapped)
        
        Args:
            original: Original frame
            swapped: Swapped frame
            
        Returns:
            Comparison image
        """
        # Ensure same size
        h1, w1 = original.shape[:2]
        h2, w2 = swapped.shape[:2]
        
        # Adjust size
        if h1 != h2 or w1 != w2:
            swapped = cv2.resize(swapped, (w1, h1))
            
        # Create side-by-side image
        comparison = np.hstack([original, swapped])
        
        return comparison