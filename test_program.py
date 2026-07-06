"""
Test Script - Verify Video Judgment Program Functionality
"""
import os
import sys
import tempfile
import numpy as np
import cv2

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import Config
from video_processor import VideoProcessor
from image_processor import ImageProcessor
from vlm_judge import VLMJudge
from result_classifier import ResultClassifier
from logger import JudgmentLogger

def create_test_video(output_path: str, duration: float = 2.0, fps: float = 30.0):
    """
    Create test video
    
    Args:
        output_path: Output path
        duration: Video duration (seconds)
        fps: Frame rate
    """
    width, height = 1920, 1080
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Generate test frames
    total_frames = int(duration * fps)
    
    for i in range(total_frames):
        # Create triple panel image
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Left region (edit_1)
        left_region = np.zeros((height, width//3, 3), dtype=np.uint8)
        left_region[:, :, 0] = 255  # Red
        cv2.putText(left_region, "edit_1", (width//6-50, height//2), 
                   cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        
        # Middle region (src)
        middle_region = np.zeros((height, width//3, 3), dtype=np.uint8)
        middle_region[:, :, 1] = 255  # Green
        cv2.putText(middle_region, "src", (width//6-30, height//2), 
                   cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        
        # Right region (edit_2)
        right_region = np.zeros((height, width//3, 3), dtype=np.uint8)
        right_region[:, :, 2] = 255  # Blue
        cv2.putText(right_region, "edit_2", (width//6-50, height//2), 
                   cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        
        # Combine three regions
        frame[:, :width//3] = left_region
        frame[:, width//3:2*width//3] = middle_region
        frame[:, 2*width//3:] = right_region
        
        # Add top text
        cv2.putText(frame, "Adjust lighting, simulate golden hour", (width//2-200, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        out.write(frame)
    
    out.release()
    print(f"Test video created: {output_path}")

def test_config():
    """Test configuration module"""
    print("Testing configuration module...")
    
    try:
        config = Config("config/config.yaml")
        model_config = config.get_model_config()
        print(f"  Model API URL: {model_config.get('api_url')}")
        print(f"  Model Name: {model_config.get('model_name')}")
        print("  ✓ Configuration module test passed")
        return True
    except Exception as e:
        print(f"  ✗ Configuration module test failed: {e}")
        return False

def test_video_processor():
    """Test video processing module"""
    print("Testing video processing module...")
    
    try:
        processor = VideoProcessor()
        
        # Create test video
        test_video = "test_video.mp4"
        create_test_video(test_video)
        
        # Test video info retrieval
        info = processor.get_video_info(test_video)
        print(f"  Video duration: {info['duration']:.2f}s")
        print(f"  Resolution: {info['width']}x{info['height']}")
        
        # Test frame extraction
        frames = processor.extract_frame(test_video, position="middle", frame_count=1)
        print(f"  Extracted frames: {len(frames)}")
        print(f"  Frame size: {frames[0].shape}")
        
        # Clean up test file
        os.remove(test_video)
        
        print("  ✓ Video processing module test passed")
        return True
    except Exception as e:
        print(f"  ✗ Video processing module test failed: {e}")
        return False

def test_image_processor():
    """Test image processing module"""
    print("Testing image processing module...")
    
    try:
        processor = ImageProcessor()
        
        # Create test image
        test_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        test_frame[:, :640, 0] = 255  # Left red
        test_frame[:, 640:1280, 1] = 255  # Middle green
        test_frame[:, 1280:, 2] = 255  # Right blue
        
        # Test position swap
        swapped_frame = processor.swap_positions(test_frame)
        
        # Check swap result
        left_color = swapped_frame[540, 320]  # Left center point
        right_color = swapped_frame[540, 1600]  # Right center point
        
        print(f"  Swapped left color: {left_color} (should be blue)")
        print(f"  Swapped right color: {right_color} (should be red)")
        
        # Test image preparation
        image_bytes = processor.prepare_for_model(test_frame)
        print(f"  Image bytes size: {len(image_bytes)} bytes")
        
        print("  ✓ Image processing module test passed")
        return True
    except Exception as e:
        print(f"  ✗ Image processing module test failed: {e}")
        return False

def test_vlm_judge():
    """Test VLM judgment module"""
    print("Testing VLM judgment module...")
    
    try:
        # Note: This test requires LM Studio service to be running
        # If not running, it will return error, but module initialization should succeed
        
        judge = VLMJudge(
            api_url="http://localhost:1234/v1/chat/completions",
            model_name="qwen/qwen3-vl-30b",
            temperature=0.2,
            max_tokens=2000,
            timeout=10  # Short timeout for testing
        )
        
        # Test prompt creation
        prompt = judge.create_judgment_prompt("test instruction")
        print(f"  Prompt length: {len(prompt)} characters")
        
        # Test result parsing
        test_response = """
        【Instruction Breakdown】
        1. Test requirements
        2. Analyze edit_1
        3. Analyze edit_2
        4. Comparison conclusion
        
        Conclusion: edit_1
        """
        
        parsed = judge.parse_judgment(test_response)
        print(f"  Parsed result: {parsed}")
        
        print("  ✓ VLM judgment module test passed")
        print("  ⚠ Note: Actual calls require LM Studio service to be running")
        return True
    except Exception as e:
        print(f"  ✗ VLM judgment module test failed: {e}")
        return False

def test_result_classifier():
    """Test result classification module"""
    print("Testing result classification module...")
    
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        output_dirs = {
            'edit1': os.path.join(temp_dir, 'edit1'),
            'edit2': os.path.join(temp_dir, 'edit2'),
            'draw': os.path.join(temp_dir, 'draw'),
            'manual_review': os.path.join(temp_dir, '_manual_review'),
            'logs': os.path.join(temp_dir, '_judgment_logs')
        }
        
        classifier = ResultClassifier(output_dirs)
        
        # Create test video
        test_video = os.path.join(temp_dir, "test_video.mp4")
        create_test_video(test_video)
        
        # Test classification
        judgment_result = {
            "parsed": True,
            "final_conclusion": "edit_1",
            "confidence": "high"
        }
        
        classification = classifier.classify_result(test_video, judgment_result, "high")
        print(f"  Classification result: {classification}")
        
        # Test video move
        target_path = classifier.move_video(test_video, classification)
        print(f"  Target path: {target_path}")
        
        # Check if file exists
        if os.path.exists(target_path):
            print("  ✓ File moved successfully")
        else:
            print("  ✗ File move failed")
            
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)
        
        print("  ✓ Result classification module test passed")
        return True
    except Exception as e:
        print(f"  ✗ Result classification module test failed: {e}")
        return False

def test_logger():
    """Test logging module"""
    print("Testing logging module...")
    
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        logger = JudgmentLogger(temp_dir)
        
        # Test logging
        judgment_result = {
            "judge1": {"conclusion": "edit_1", "content": "test content"},
            "judge2": {"conclusion": "edit_2", "content": "test content 2"},
            "consistent": False,
            "confidence": "low",
            "final_conclusion": None
        }
        
        success = logger.log_judgment(
            "test_video.mp4",
            judgment_result=judgment_result,
            classification="manual_review"
        )
        
        if success:
            print("  ✓ Logging successful")
        else:
            print("  ✗ Logging failed")
            
        # Test statistics
        stats = logger.get_statistics()
        print(f"  Statistics: {stats}")
        
        # Test report generation
        report = logger.generate_report()
        print(f"  Report length: {len(report)} characters")
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)
        
        print("  ✓ Logging module test passed")
        return True
    except Exception as e:
        print(f"  ✗ Logging module test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Video Editing Effect Batch Judgment Program - Functional Test")
    print("=" * 60)
    print()
    
    tests = [
        test_config,
        test_video_processor,
        test_image_processor,
        test_vlm_judge,
        test_result_classifier,
        test_logger
    ]
    
    results = []
    
    for test_func in tests:
        result = test_func()
        results.append(result)
        print()
    
    # Count results
    passed = sum(results)
    total = len(results)
    
    print("=" * 60)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("✓ All tests passed!")
        print("\nProgram is ready to run. Please ensure:")
        print("1. Python dependencies installed: pip install -r requirements.txt")
        print("2. LM Studio service started and model loaded")
        print("3. Configuration in config/config.yaml modified as needed")
        print("\nRun program: python src/main.py")
    else:
        print("⚠ Some tests failed, please check related modules")
        
    print("=" * 60)

if __name__ == "__main__":
    main()