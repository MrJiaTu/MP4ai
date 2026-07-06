"""
Logging Module
Responsible for recording judgment process and results
"""
import csv
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

class JudgmentLogger:
    """Judgment Logger"""
    
    def __init__(self, log_dir: str, results_csv: str = "results.csv"):
        """
        Initialize judgment logger
        
        Args:
            log_dir: Log directory
            results_csv: Results CSV filename
        """
        self.log_dir = log_dir
        self.results_csv = os.path.join(log_dir, results_csv)
        self.logger = logging.getLogger(__name__)
        
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        
        # Initialize CSV file
        self._init_csv()
        
    def _init_csv(self):
        """Initialize CSV file (if not exists)"""
        if not os.path.exists(self.results_csv):
            # Create CSV file and write header
            headers = [
                "video_name",
                "instruction",
                "judge1_raw",
                "judge1_result",
                "judge2_raw", 
                "judge2_result",
                "consistent",
                "final_label",
                "confidence",
                "model_used",
                "timestamp",
                "elapsed_time_total",
                "classification"
            ]
            
            with open(self.results_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                
            self.logger.info(f"Created results CSV file: {self.results_csv}")
            
    def log_judgment(self, video_path: str, instruction: str = None,
                    judgment_result: Dict[str, Any] = None,
                    classification: str = None) -> bool:
        """
        Log judgment result to CSV
        
        Args:
            video_path: Video file path
            instruction: Editing instruction
            judgment_result: Judgment result
            classification: Classification result
            
        Returns:
            Whether successful
        """
        try:
            # Prepare data
            video_name = os.path.basename(video_path)
            
            if judgment_result is None:
                judgment_result = {}
                
            judge1 = judgment_result.get("judge1", {})
            judge2 = judgment_result.get("judge2", {})
            
            row = [
                video_name,
                instruction or "",
                judge1.get("content", ""),
                judge1.get("conclusion", ""),
                judge2.get("content", ""),
                judge2.get("conclusion", ""),
                judgment_result.get("consistent", ""),
                judgment_result.get("final_conclusion", ""),
                judgment_result.get("confidence", ""),
                judge1.get("model", ""),
                datetime.now().isoformat(),
                judge1.get("elapsed_time", 0) + judge2.get("elapsed_time", 0),
                classification or ""
            ]
            
            # Append to CSV file
            with open(self.results_csv, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row)
                
            self.logger.info(f"Logged judgment result: {video_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to log judgment result: {str(e)}")
            return False
            
    def log_detailed_result(self, video_path: str, judgment_result: Dict[str, Any],
                          classification: str) -> str:
        """
        Save detailed result to JSON file
        
        Args:
            video_path: Video file path
            judgment_result: Judgment result
            classification: Classification result
            
        Returns:
            Saved file path
        """
        # Prepare detailed result
        detailed_result = {
            "video_path": video_path,
            "video_filename": os.path.basename(video_path),
            "timestamp": datetime.now().isoformat(),
            "classification": classification,
            "judgment_result": judgment_result,
            "summary": {
                "confidence": judgment_result.get("confidence", "unknown"),
                "consistent": judgment_result.get("consistent"),
                "conclusion1": judgment_result.get("conclusion1"),
                "conclusion2": judgment_result.get("conclusion2"),
                "final_conclusion": judgment_result.get("final_conclusion")
            }
        }
        
        # Save JSON file
        video_filename = os.path.basename(video_path)
        name, ext = os.path.splitext(video_filename)
        json_filename = f"{name}_detailed.json"
        json_path = os.path.join(self.log_dir, json_filename)
        
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(detailed_result, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"Saved detailed result: {json_path}")
            return json_path
            
        except Exception as e:
            self.logger.error(f"Failed to save detailed result: {json_path}, Error: {str(e)}")
            return None
            
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics
        
        Returns:
            Statistics dictionary
        """
        stats = {
            "total_videos": 0,
            "high_confidence": 0,
            "low_confidence": 0,
            "edit1_count": 0,
            "edit2_count": 0,
            "draw_count": 0,
            "manual_review_count": 0,
            "consistency_rate": 0
        }
        
        if not os.path.exists(self.results_csv):
            return stats
            
        try:
            with open(self.results_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            stats["total_videos"] = len(rows)
            
            for row in rows:
                confidence = row.get("confidence", "")
                classification = row.get("classification", "")
                consistent = row.get("consistent", "")
                
                if confidence == "high":
                    stats["high_confidence"] += 1
                elif confidence == "low":
                    stats["low_confidence"] += 1
                    
                if classification == "edit_1":
                    stats["edit1_count"] += 1
                elif classification == "edit_2":
                    stats["edit2_count"] += 1
                elif classification == "draw":
                    stats["draw_count"] += 1
                elif classification == "manual_review":
                    stats["manual_review_count"] += 1
                    
            # Calculate consistency rate
            if stats["total_videos"] > 0:
                stats["consistency_rate"] = stats["high_confidence"] / stats["total_videos"]
                
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {str(e)}")
            return stats
            
    def generate_report(self) -> str:
        """
        Generate processing report
        
        Returns:
            Report text
        """
        stats = self.get_statistics()
        
        report = f"""
Video Editing Effect Batch Judgment Report
==========================================

Overall Statistics:
- Total videos processed: {stats['total_videos']}
- High confidence: {stats['high_confidence']} ({stats['consistency_rate']:.1%})
- Low confidence: {stats['low_confidence']}

Classification Results:
- edit_1 is better: {stats['edit1_count']}
- edit_2 is better: {stats['edit2_count']}
- Draw (tie): {stats['draw_count']}
- Need manual review: {stats['manual_review_count']}

Processing Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Save report
        report_path = os.path.join(self.log_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
                
            self.logger.info(f"Generated processing report: {report_path}")
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate report: {str(e)}")
            return report