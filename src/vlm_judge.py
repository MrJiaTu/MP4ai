"""
VLM Judgment Module
Responsible for calling VLM model to evaluate video editing effects
"""
import re
import base64
import requests
import json
from typing import Dict, Any, Optional, Tuple
import time
import logging

class VLMJudge:
    """VLM Judge"""
    
    def __init__(self, api_url: str, model_name: str, 
                 temperature: float = 0.2, max_tokens: int = 2000,
                 timeout: int = 60):
        """
        Initialize VLM judge
        
        Args:
            api_url: LM Studio API address
            model_name: Model name
            temperature: Temperature parameter
            max_tokens: Maximum token count
            timeout: Request timeout (seconds)
        """
        self.api_url = api_url
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    def create_judgment_prompt(self, instruction: str = None) -> str:
        """
        Create judgment prompt
        
        Args:
            instruction: Editing instruction (if None, OCR extract from image)
            
        Returns:
            Prompt text
        """
        # Note: The prompt is in Chinese for better VLM understanding
        prompt = """你是专业的图像编辑质量评审员。图片中包含三部分：
- 左侧标注"edit_1"的图像
- 中间标注"src"的原始图像
- 右侧标注"edit_2"的图像
- 顶部文字是编辑指令

"""
        
        if instruction:
            prompt += f"编辑指令：{instruction}\n\n"
        else:
            prompt += "编辑指令：请从图中顶部文字区域OCR提取编辑指令。\n\n"
            
        prompt += """请按以下步骤评审：

1. 【指令拆解】将指令拆解为具体的可验证要求（例如："金色时刻光影"可拆解为：暖色调、低角度光源、柔和阴影、天空颜色变化等）
2. 【edit_1分析】逐项对照上述要求，说明edit_1相对src的变化，以及是否达成、达成程度如何
3. 【edit_2分析】同上，分析edit_2
4. 【对比结论】直接比较两者：谁更贴合指令？是否存在其中一个过度编辑/编辑不足/引入了不该有的瑕疵（如失真、不自然的光斑、色偏过度）？

最后，另起一行，严格按以下格式输出结论（不要有多余文字）：
结论：edit_1
或
结论：edit_2
或
结论：平局"""
        
        return prompt
        
    def encode_image(self, image_bytes: bytes) -> str:
        """
        Encode image bytes to base64
        
        Args:
            image_bytes: Image byte data
            
        Returns:
            Base64 encoded string
        """
        return base64.b64encode(image_bytes).decode('utf-8')
        
    def call_model(self, image_bytes: bytes, prompt: str) -> Dict[str, Any]:
        """
        Call VLM model
        
        Args:
            image_bytes: Image byte data
            prompt: Prompt text
            
        Returns:
            Model response
        """
        # Encode image
        base64_image = self.encode_image(image_bytes)
        
        # Build request payload
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            self.logger.info(f"Calling model: {self.model_name}")
            start_time = time.time()
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            elapsed_time = time.time() - start_time
            self.logger.info(f"Model response time: {elapsed_time:.2f}s")
            
            if response.status_code != 200:
                error_msg = f"Model call failed: HTTP {response.status_code}"
                self.logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "raw_response": response.text
                }
                
            result = response.json()
            
            # Extract response content
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                
                return {
                    "success": True,
                    "content": content,
                    "usage": result.get('usage', {}),
                    "model": result.get('model', self.model_name),
                    "elapsed_time": elapsed_time
                }
            else:
                return {
                    "success": False,
                    "error": "Invalid model response format",
                    "raw_response": result
                }
                
        except requests.exceptions.Timeout:
            error_msg = f"Model call timeout ({self.timeout}s)"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        except requests.exceptions.RequestException as e:
            error_msg = f"Network request error: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        except Exception as e:
            error_msg = f"Unknown error: {str(e)}"
            self.logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
            
    def parse_judgment(self, response_content: str) -> Dict[str, Any]:
        """
        Parse model response and extract conclusion
        
        Args:
            response_content: Model response content
            
        Returns:
            Parsed result
        """
        # Use regex to extract conclusion
        pattern = r"结论[：:]\s*(edit_1|edit_2|平局)"
        matches = re.findall(pattern, response_content, re.IGNORECASE)
        
        if matches:
            # Take the last matched conclusion
            conclusion = matches[-1].lower()
            
            # Normalize
            if conclusion in ['edit_1', 'edit1']:
                normalized_conclusion = 'edit_1'
            elif conclusion in ['edit_2', 'edit2']:
                normalized_conclusion = 'edit_2'
            elif '平局' in conclusion or 'draw' in conclusion.lower():
                normalized_conclusion = '平局'
            else:
                normalized_conclusion = conclusion
                
            return {
                "parsed": True,
                "conclusion": normalized_conclusion,
                "raw_matches": matches
            }
        else:
            return {
                "parsed": False,
                "conclusion": None,
                "raw_matches": []
            }
            
    def judge_frame(self, image_bytes: bytes, instruction: str = None) -> Dict[str, Any]:
        """
        Judge a single frame
        
        Args:
            image_bytes: Image byte data
            instruction: Editing instruction
            
        Returns:
            Judgment result
        """
        # Create prompt
        prompt = self.create_judgment_prompt(instruction)
        
        # Call model
        model_response = self.call_model(image_bytes, prompt)
        
        if not model_response["success"]:
            return {
                "success": False,
                "error": model_response.get("error", "Model call failed"),
                "raw_response": model_response.get("raw_response", ""),
                "conclusion": None,
                "parsed": False
            }
            
        # Parse conclusion
        parsed_result = self.parse_judgment(model_response["content"])
        
        return {
            "success": True,
            "content": model_response["content"],
            "conclusion": parsed_result["conclusion"],
            "parsed": parsed_result["parsed"],
            "usage": model_response.get("usage", {}),
            "model": model_response.get("model", ""),
            "elapsed_time": model_response.get("elapsed_time", 0),
            "prompt": prompt
        }
        
    def judge_frame_with_consistency(self, image_bytes: bytes, 
                                    instruction: str = None,
                                    swapped_image_bytes: bytes = None) -> Dict[str, Any]:
        """
        Judge with consistency check
        
        Principle: Judge the same image twice, but swap the physical positions of edit_1 and edit_2.
        If the model judgment is stable (not affected by position), the two judgments should be consistent.
        
        Args:
            image_bytes: Original image bytes (edit_1 on left, edit_2 on right)
            instruction: Editing instruction
            swapped_image_bytes: Swapped image bytes (edit_2 on left, edit_1 on right)
            
        Returns:
            Judgment result with consistency check
        """
        # First judgment (original image)
        result1 = self.judge_frame(image_bytes, instruction)
        
        if swapped_image_bytes is None:
            # No swapped image, only one judgment
            return {
                "judge1": result1,
                "judge2": None,
                "consistent": None,
                "confidence": "low",
                "final_conclusion": result1.get("conclusion") if result1.get("parsed") else None
            }
            
        # Second judgment (swapped image)
        # Use same prompt, let model judge based on visual position
        result2 = self.judge_frame(swapped_image_bytes, instruction)
        
        # Check consistency
        # Note: Two judgments use same prompt but different image positions
        # If model is stable, two conclusions should be the same
        # If inconsistent, model is affected by position
        if result1.get("parsed") and result2.get("parsed"):
            conclusion1 = result1["conclusion"]
            conclusion2 = result2["conclusion"]
            
            # Directly compare two judgment conclusions
            # If consistent, model judgment is stable
            consistent = (conclusion1 == conclusion2)
        else:
            consistent = False
            
        # Determine confidence
        if consistent and result1.get("parsed") and result2.get("parsed"):
            confidence = "high"
            final_conclusion = result1["conclusion"]
        else:
            confidence = "low"
            final_conclusion = None
            
        return {
            "judge1": result1,
            "judge2": result2,
            "consistent": consistent,
            "confidence": confidence,
            "final_conclusion": final_conclusion,
            "conclusion1": result1.get("conclusion"),
            "conclusion2": result2.get("conclusion")
        }