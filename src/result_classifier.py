"""
Result Classification Module
Responsible for classifying judgment results and archiving to corresponding directories
"""
import os
import shutil
import json
import csv
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

class ResultClassifier:
    """Result Classifier"""
    
    def __init__(self, output_dirs: Dict[str, str], log_dir: str = None):
        """
        Initialize result classifier
        
        Args:
            output_dirs: Output directory configuration
            log_dir: Log directory
        """
        self.output_dirs = output_dirs
        self.log_dir = log_dir or output_dirs.get('logs', '_judgment_logs')
        self.logger = logging.getLogger(__name__)
        
    def classify_result(self, video_path: str, judgment_result: Dict[str, Any],
                       confidence: str) -> str:
        """
        Classify judgment result
        
        Args:
            video_path: Video file path
            judgment_result: Judgment result (with top-level fields like consistent, confidence, final_conclusion)
            confidence: Confidence level (high/low)
            
        Returns:
            Classification result (edit_1/edit_2/draw/manual_review)
        """
        # Check if manual review is needed
        if confidence == "low":
            return "manual_review"
            
        # Check if consistency check passed
        if not judgment_result.get("consistent", False):
            return "manual_review"
            
        # Get final conclusion
        conclusion = judgment_result.get("final_conclusion")
        if conclusion is None:
            return "manual_review"
            
        # Classify
        if conclusion == "edit_1":
            return "edit_1"
        elif conclusion == "edit_2":
            return "edit_2"
        elif conclusion == "平局":
            return "draw"
        else:
            return "manual_review"
            
    def move_video(self, video_path: str, classification: str) -> str:
        """
        Move video to corresponding classification directory
        
        Args:
            video_path: Video file path
            classification: Classification result
            
        Returns:
            Moved file path
        """
        # Get target directory
        if classification == "edit_1":
            target_dir = self.output_dirs.get('edit1', 'edit1')
        elif classification == "edit_2":
            target_dir = self.output_dirs.get('edit2', 'edit2')
        elif classification == "draw":
            target_dir = self.output_dirs.get('draw', 'draw')
        elif classification == "manual_review":
            target_dir = self.output_dirs.get('manual_review', '_manual_review')
        else:
            target_dir = self.output_dirs.get('manual_review', '_manual_review')
            
        # Ensure target directory exists
        os.makedirs(target_dir, exist_ok=True)
        
        # Get video filename
        video_filename = os.path.basename(video_path)
        target_path = os.path.join(target_dir, video_filename)
        
        # If target file already exists, add timestamp
        if os.path.exists(target_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(video_filename)
            target_path = os.path.join(target_dir, f"{name}_{timestamp}{ext}")
            
        try:
            shutil.move(video_path, target_path)
            self.logger.info(f"Moved video: {video_path} -> {target_path}")
            return target_path
        except Exception as e:
            self.logger.error(f"Failed to move video: {video_path}, Error: {str(e)}")
            return video_path
            
    def copy_video(self, video_path: str, classification: str) -> str:
        """
        Copy video to corresponding classification directory (keep original file)
        
        Args:
            video_path: Video file path
            classification: Classification result
            
        Returns:
            Copied file path
        """
        # Get target directory
        if classification == "edit_1":
            target_dir = self.output_dirs.get('edit1', 'edit1')
        elif classification == "edit_2":
            target_dir = self.output_dirs.get('edit2', 'edit2')
        elif classification == "draw":
            target_dir = self.output_dirs.get('draw', 'draw')
        elif classification == "manual_review":
            target_dir = self.output_dirs.get('manual_review', '_manual_review')
        else:
            target_dir = self.output_dirs.get('manual_review', '_manual_review')
            
        # Ensure target directory exists
        os.makedirs(target_dir, exist_ok=True)
        
        # Get video filename
        video_filename = os.path.basename(video_path)
        target_path = os.path.join(target_dir, video_filename)
        
        # If target file already exists, add timestamp
        if os.path.exists(target_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(video_filename)
            target_path = os.path.join(target_dir, f"{name}_{timestamp}{ext}")
            
        try:
            shutil.copy2(video_path, target_path)
            self.logger.info(f"Copied video: {video_path} -> {target_path}")
            return target_path
        except Exception as e:
            self.logger.error(f"Failed to copy video: {video_path}, Error: {str(e)}")
            return None
            
    def save_judgment_details(self, video_path: str, judgment_result: Dict[str, Any],
                             classification: str) -> str:
        """
        Save judgment details (JSON format)
        
        Args:
            video_path: Video file path
            judgment_result: Judgment result
            classification: Classification result
            
        Returns:
            Saved file path
        """
        # Create detailed result
        details = {
            "video_path": video_path,
            "video_filename": os.path.basename(video_path),
            "timestamp": datetime.now().isoformat(),
            "classification": classification,
            "judgment_result": judgment_result,
            "confidence": judgment_result.get("confidence", "unknown"),
            "consistent": judgment_result.get("consistent"),
            "conclusion1": judgment_result.get("conclusion1"),
            "conclusion2": judgment_result.get("conclusion2")
        }
        
        # Save to corresponding classification directory
        if classification == "edit_1":
            target_dir = self.output_dirs.get('edit1', 'edit1')
        elif classification == "edit_2":
            target_dir = self.output_dirs.get('edit2', 'edit2')
        elif classification == "draw":
            target_dir = self.output_dirs.get('draw', 'draw')
        elif classification == "manual_review":
            target_dir = self.output_dirs.get('manual_review', '_manual_review')
        else:
            target_dir = self.output_dirs.get('manual_review', '_manual_review')
            
        # Ensure target directory exists
        os.makedirs(target_dir, exist_ok=True)
        
        # Create JSON filename
        video_filename = os.path.basename(video_path)
        name, ext = os.path.splitext(video_filename)
        json_filename = f"{name}_judgment.json"
        json_path = os.path.join(target_dir, json_filename)
        
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(details, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"Saved judgment details: {json_path}")
            return json_path
        except Exception as e:
            self.logger.error(f"Failed to save judgment details: {json_path}, Error: {str(e)}")
            return None