# Video Editing Effect Batch Evaluation Tool

A batch evaluation tool for video editing effects based on VLM models, used to automatically classify video editing results.

## Features

- **Automatic Frame Extraction**: Extract representative frames from videos for analysis
- **VLM Judgment**: Use local VLM models (via LM Studio) for editing effect evaluation
- **Consistency Check**: Perform two judgments with position swapping to ensure result consistency
- **Automatic Classification**: Automatically archive results to corresponding directories based on judgment
- **Detailed Logging**: Record complete judgment process and results

## Project Structure

```
MP4AI/
├── config/
│   └── config.yaml          # Configuration file
├── src/
│   ├── __init__.py
│   ├── config.py            # Configuration management
│   ├── video_processor.py   # Video processing
│   ├── image_processor.py   # Image processing
│   ├── vlm_judge.py        # VLM judgment
│   ├── result_classifier.py # Result classification
│   ├── logger.py           # Logging
│   └── main.py             # Main program
├── test_program.py          # Test script
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Installation & Configuration

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure LM Studio

1. Download and install [LM Studio](https://lmstudio.ai/)
2. Download a supported VLM model (recommended: `qwen3-vl-30b`)
3. Load the model in LM Studio and start the local server (default port: 1234)

### 3. Modify Configuration File

Edit `config/config.yaml`:

```yaml
# Model configuration
model:
  api_url: "http://localhost:1234/v1/chat/completions"
  model_name: "qwen/qwen3-vl-30b"  # Modify according to LM Studio display name
  temperature: 0.2
  max_tokens: 2000
  timeout: 60

# Video processing configuration
video:
  input_dir: "E:/Work_lyl/concat_disagree"
  output_dir: "E:/Work_lyl/concat_disagree"
  video_extensions: [".mp4", ".avi", ".mov", ".mkv"]
  frame_position: "middle"
  frame_count: 1
```

## Usage

### Run Tests

```bash
python test_program.py
```

### Run Batch Evaluation

```bash
# Use default configuration
python src/main.py

# Specify input directory
python src/main.py --input "D:/path/to/videos"

# Specify configuration file
python src/main.py --config "config/custom_config.yaml"
```

## Output Directory Structure

After running the program, the following structure will be created in the output directory:

```
E:/Work_lyl/concat_disagree/
├── edit1/              # High confidence: edit_1 is better
├── edit2/              # High confidence: edit_2 is better
├── draw/               # High confidence: draw (tie)
├── _manual_review/     # Low confidence samples, need manual review
└── _judgment_logs/
    ├── results.csv     # Judgment results CSV
    ├── *.json          # Detailed judgment results
    └── report_*.txt    # Processing reports
```

## Workflow

1. **Frame Extraction**: Extract representative frames from video (default: middle time point)
2. **First Judgment**: Input original image to VLM model for evaluation
3. **Position Swap**: Swap the positions of edit_1 and edit_2
4. **Second Judgment**: Input swapped image to model for evaluation
5. **Consistency Check**: Compare if two judgment results are consistent
6. **Classification & Archival**:
   - High confidence (consistent): Automatically archive to corresponding directory
   - Low confidence (inconsistent): Place in manual review directory
7. **Logging**: Save judgment process and results

## Notes

1. **LM Studio Service**: LM Studio service must be running when the program executes
2. **Model Selection**: Recommended to use `qwen3-vl-30b` for more accurate judgment of subtle differences
3. **Video Formats**: Supports MP4, AVI, MOV, MKV formats
4. **Position Swapping**: Default uses physical swapping (image processing), can also be configured to only swap labels
5. **Manual Review**: Low confidence samples require manual review, can be used with AHK scripts

## Troubleshooting

### Cannot Connect to LM Studio

- Check if LM Studio local service is started
- Confirm API address and port are correct (default: http://localhost:1234)
- Check firewall settings

### Model Response Format Error

- Check if the model supports visual input
- Confirm model name matches the one displayed in LM Studio
- Try lowering the temperature parameter

### Video Frame Extraction Failed

- Check if video file is corrupted
- Confirm video format is supported
- Check file permissions

## Technical Details

- **Frame Extraction Strategy**: Supports single frame or multiple frames (start/middle/end), default is middle frame
- **Position Swapping**: Supports physical swapping (image processing) and label swapping (prompt modification)
- **Confidence Judgment**: Based on consistency of two judgments, not model self-evaluation
- **Result Parsing**: Uses regular expressions to extract structured conclusions

## License

This project is for internal use only.
