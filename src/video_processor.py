"""
Video Processing Module
Responsible for extracting representative frames from videos
"""
import os
import cv2
import numpy as np
from typing import List, Optional, Tuple
from pathlib import Path

class VideoProcessor:
    """Video Processor"""
    
    def __init__(self, video_extensions: List[str] = None):
        """
        Initialize video processor
        
        Args:
            video_extensions: List of supported video file extensions
        """
        self.video_extensions = video_extensions or ['.mp4', '.avi', '.mov', '.mkv']
        
    def get_video_files(self, directory: str) -> List[str]:
        """
        Get all video files in directory
        
        Args:
            directory: Video directory
            
        Returns:
            List of video file paths
        """
        video_files = []
        
        for file in os.listdir(directory):
            if any(file.lower().endswith(ext) for ext in self.video_extensions):
                video_files.append(os.path.join(directory, file))
                
        return video_files
        
    def extract_frame(self, video_path: str, position: str = "middle", 
                     frame_count: int = 1) -> List[np.ndarray]:
        """
        Extract frames from video
        
        Args:
            video_path: Video file path
            position: Frame position - "middle", "start", "end", 
                     or specific seconds like "5.0"
            frame_count: Number of frames to extract (1 or 3)
            
        Returns:
            List of extracted frames (OpenCV format, BGR)
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {video_path}")
            
        try:
            # Get video info
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count_total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count_total / fps if fps > 0 else 0
            
            if frame_count == 1:
                # Extract single frame
                frame_idx = self._calculate_frame_index(position, duration, fps)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                
                if not ret:
                    raise ValueError(f"Cannot read video frame: {video_path}")
                    
                return [frame]
                
            elif frame_count == 3:
                # Extract start, middle, end frames
                frames = []
                positions = ["start", "middle", "end"]
                
                for pos in positions:
                    frame_idx = self._calculate_frame_index(pos, duration, fps)
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                    ret, frame = cap.read()
                    
                    if ret:
                        frames.append(frame)
                    else:
                        # If cannot read, use previous frame
                        if frames:
                            frames.append(frames[-1])
                        else:
                            # Create blank frame
                            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            frames.append(np.zeros((height, width, 3), dtype=np.uint8))
                            
                return frames
            else:
                raise ValueError(f"Unsupported frame count: {frame_count}")
                
        finally:
            cap.release()
            
    def _calculate_frame_index(self, position: str, duration: float, 
                              fps: float) -> int:
        """
        Calculate frame index
        
        Args:
            position: Frame position
            duration: Video duration (seconds)
            fps: Frame rate
            
        Returns:
            Frame index
        """
        if position == "start":
            time_seconds = 0.0
        elif position == "middle":
            time_seconds = duration / 2
        elif position == "end":
            time_seconds = max(0, duration - 0.1)  # Avoid boundary issues
        else:
            # Try to parse as number
            try:
                time_seconds = float(position)
                time_seconds = min(max(0, time_seconds), duration)
            except ValueError:
                # Default to middle position
                time_seconds = duration / 2
                
        return int(time_seconds * fps)
        
    def save_frame(self, frame: np.ndarray, output_path: str, 
                   quality: int = 95) -> str:
        """
        Save frame to file
        
        Args:
            frame: Frame data (OpenCV format)
            output_path: Output path
            quality: JPEG quality (1-100)
            
        Returns:
            Saved file path
        """
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save image
        encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
        cv2.imwrite(output_path, frame, encode_params)
        
        return output_path
        
    def get_video_info(self, video_path: str) -> dict:
        """
        Get video information
        
        Args:
            video_path: Video file path
            
        Returns:
            Video information dictionary
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Cannot open video file: {video_path}")
            
        try:
            info = {
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'duration': 0
            }
            
            if info['fps'] > 0:
                info['duration'] = info['frame_count'] / info['fps']
                
            return info
            
        finally:
            cap.release()