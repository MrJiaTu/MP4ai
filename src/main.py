"""
Video Editing Effect Batch Judgment Main Program
"""
import os
import sys
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any

# Calculate project root directory (parent of src)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Add src directory to Python path
sys.path.insert(0, SCRIPT_DIR)

from config import Config
from video_processor import VideoProcessor
from image_processor import ImageProcessor
from vlm_judge import VLMJudge
from result_classifier import ResultClassifier
from logger import JudgmentLogger

class VideoJudgmentPipeline:
    """Video Judgment Pipeline"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize judgment pipeline
        
        Args:
            config_path: Configuration file path
        """
        # Load configuration
        self.config = Config(config_path)
        
        # Initialize modules
        self.video_processor = VideoProcessor(
            video_extensions=self.config.get('video.video_extensions', ['.mp4', '.avi', '.mov', '.mkv'])
        )
        
        self.image_processor = ImageProcessor(
            swap_method=self.config.get('image.swap_method', 'physical'),
            jpeg_quality=self.config.get('image.jpeg_quality', 95)
        )
        
        model_config = self.config.get_model_config()
        self.vlm_judge = VLMJudge(
            api_url=model_config.get('api_url', 'http://localhost:1234/v1/chat/completions'),
            model_name=model_config.get('model_name', 'qwen/qwen3-vl-30b'),
            temperature=model_config.get('temperature', 0.2),
            max_tokens=model_config.get('max_tokens', 2000),
            timeout=model_config.get('timeout', 60)
        )
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
    def _setup_logging(self):
        """Setup logging"""
        logging_config = self.config.get_logging_config()
        log_level = getattr(logging, logging_config.get('level', 'INFO'))
        log_file = logging_config.get('log_file', 'video_judgment.log')
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
    def process_single_video(self, video_path: str) -> Dict[str, Any]:
        """
        Process single video
        
        Args:
            video_path: Video file path
            
        Returns:
            Processing result
        """
        video_filename = os.path.basename(video_path)
        self.logger.info(f"Processing video: {video_filename}")
        
        try:
            # Get video info
            video_info = self.video_processor.get_video_info(video_path)
            self.logger.info(f"Video info: duration={video_info['duration']:.2f}s, "
                           f"resolution={video_info['width']}x{video_info['height']}")
            
            # Extract frame
            video_config = self.config.get_video_config()
            frames = self.video_processor.extract_frame(
                video_path,
                position=video_config.get('frame_position', 'middle'),
                frame_count=video_config.get('frame_count', 1)
            )
            
            if not frames:
                return {
                    "success": False,
                    "error": "Cannot extract frame from video",
                    "video_path": video_path
                }
                
            # Use first frame for judgment (if multiple frames extracted)
            frame = frames[0]
            
            # Prepare image bytes
            original_image_bytes = self.image_processor.prepare_for_model(frame)
            
            # Perform judgment with consistency check
            judgment_config = self.config.get_judgment_config()
            
            # Check if position swap is needed
            if judgment_config.get('confidence_method') == 'consistency':
                # Physical position swap
                swapped_frame = self.image_processor.swap_positions(frame)
                swapped_image_bytes = self.image_processor.prepare_for_model(swapped_frame)
                
                judgment_result = self.vlm_judge.judge_frame_with_consistency(
                    original_image_bytes,
                    swapped_image_bytes=swapped_image_bytes
                )
            else:
                # Single judgment only
                judgment_result = {
                    "judge1": self.vlm_judge.judge_frame(original_image_bytes),
                    "judge2": None,
                    "consistent": None,
                    "confidence": "unknown",
                    "final_conclusion": None
                }
                
            # Get confidence level
            confidence = judgment_result.get("confidence", "low")
            
            # Initialize result classifier
            output_dirs = self.config.get_output_dirs()
            # Convert relative paths to absolute paths (based on output directory)
            base_dir = self.config.get('video.output_dir', '.')
            abs_output_dirs = {}
            for name, subdir in output_dirs.items():
                abs_output_dirs[name] = os.path.join(base_dir, subdir)
                
            classifier = ResultClassifier(abs_output_dirs)
            
            # Classify result
            classification = classifier.classify_result(video_path, judgment_result, confidence)
            
            # Move video to corresponding directory
            target_path = classifier.move_video(video_path, classification)
            
            # Save judgment details
            classifier.save_judgment_details(video_path, judgment_result, classification)
            
            # Log results
            log_dir = os.path.join(base_dir, output_dirs.get('logs', '_judgment_logs'))
            judgment_logger = JudgmentLogger(log_dir)
            judgment_logger.log_judgment(video_path, judgment_result=judgment_result, classification=classification)
            judgment_logger.log_detailed_result(video_path, judgment_result, classification)
            
            self.logger.info(f"Video processing complete: {video_filename} -> {classification}")
            
            return {
                "success": True,
                "video_path": video_path,
                "target_path": target_path,
                "classification": classification,
                "confidence": confidence,
                "judgment_result": judgment_result,
                "video_info": video_info
            }
            
        except Exception as e:
            self.logger.error(f"Failed to process video: {video_path}, Error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "video_path": video_path
            }
            
    def process_batch(self, input_dir: str = None) -> Dict[str, Any]:
        """
        Batch process videos
        
        Args:
            input_dir: Input directory (if None, use configured directory)
            
        Returns:
            Batch processing result
        """
        if input_dir is None:
            input_dir = self.config.get('video.input_dir')
            
        self.logger.info(f"Starting batch video processing, input directory: {input_dir}")
        
        # Check if directory exists
        if not os.path.exists(input_dir):
            return {
                "success": False,
                "error": f"Input directory does not exist: {input_dir}"
            }
            
        # Get all video files
        video_files = self.video_processor.get_video_files(input_dir)
        
        if not video_files:
            return {
                "success": False,
                "error": "No video files found in input directory"
            }
            
        self.logger.info(f"Found {len(video_files)} video files")
        
        # Process each video
        results = []
        success_count = 0
        fail_count = 0
        
        for i, video_path in enumerate(video_files, 1):
            self.logger.info(f"Processing progress: {i}/{len(video_files)}")
            
            result = self.process_single_video(video_path)
            results.append(result)
            
            if result.get("success"):
                success_count += 1
            else:
                fail_count += 1
                
        # Generate statistics
        base_dir = self.config.get('video.output_dir', '.')
        output_dirs = self.config.get_output_dirs()
        log_dir = os.path.join(base_dir, output_dirs.get('logs', '_judgment_logs'))
        judgment_logger = JudgmentLogger(log_dir)
        statistics = judgment_logger.get_statistics()
        
        # Generate report
        report = judgment_logger.generate_report()
        
        batch_result = {
            "success": True,
            "total_videos": len(video_files),
            "success_count": success_count,
            "fail_count": fail_count,
            "statistics": statistics,
            "results": results,
            "report": report
        }
        
        self.logger.info(f"Batch processing complete: success={success_count}, failed={fail_count}")
        
        return batch_result
        
    def run(self, input_dir: str = None):
        """
        Run judgment pipeline
        
        Args:
            input_dir: Input directory (optional)
        """
        self.logger.info("=" * 50)
        self.logger.info("Video Editing Effect Batch Judgment Program Started")
        self.logger.info("=" * 50)
        
        try:
            result = self.process_batch(input_dir)
            
            if result.get("success"):
                self.logger.info("Processing complete!")
                self.logger.info(f"Statistics: {result['statistics']}")
                print("\n" + result.get("report", ""))
            else:
                self.logger.error(f"Processing failed: {result.get('error', 'Unknown error')}")
                print(f"Processing failed: {result.get('error', 'Unknown error')}")
                
        except KeyboardInterrupt:
            self.logger.info("User interrupted processing")
            print("User interrupted processing")
        except Exception as e:
            self.logger.error(f"Program exception: {str(e)}")
            print(f"Program exception: {str(e)}")
            raise

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Video Editing Effect Batch Judgment Program")
    parser.add_argument("--config", default="config/config.yaml", 
                       help="Configuration file path (default: config/config.yaml)")
    parser.add_argument("--input", default=None, 
                       help="Input video directory (overrides configuration file setting)")
    
    args = parser.parse_args()
    
    # If config path is relative, resolve based on project root
    config_path = args.config
    if not os.path.isabs(config_path):
        config_path = os.path.join(PROJECT_ROOT, config_path)
    
    # Create and run pipeline
    pipeline = VideoJudgmentPipeline(config_path)
    pipeline.run(args.input)

if __name__ == "__main__":
    main()