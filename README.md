# 视频编辑效果批量评判程序

基于VLM模型的视频编辑效果批量评判工具，用于自动分类视频编辑结果。

## 功能特性

- **自动抽帧**：从视频中抽取代表性帧进行分析
- **VLM判断**：使用本地VLM模型（通过LM Studio）进行编辑效果评判
- **一致性检查**：通过位置交换进行两次判断，确保结果一致性
- **自动分类**：根据判断结果自动归档到对应目录
- **详细日志**：记录完整的判断过程和结果

## 项目结构

```
MP4AI/
├── config/
│   └── config.yaml          # 配置文件
├── src/
│   ├── __init__.py
│   ├── config.py            # 配置管理
│   ├── video_processor.py   # 视频处理
│   ├── image_processor.py   # 图像处理
│   ├── vlm_judge.py        # VLM判断
│   ├── result_classifier.py # 结果分类
│   ├── logger.py           # 日志记录
│   └── main.py             # 主程序
├── test_program.py          # 测试脚本
├── requirements.txt         # Python依赖
└── README.md               # 本文件
```

## 安装与配置

### 1. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 2. 配置LM Studio

1. 下载并安装 [LM Studio](https://lmstudio.ai/)
2. 下载支持的VLM模型（推荐 `qwen3-vl-30b`）
3. 在LM Studio中加载模型并启动本地服务（默认端口1234）

### 3. 修改配置文件

编辑 `config/config.yaml`：

```yaml
# 模型配置
model:
  api_url: "http://localhost:1234/v1/chat/completions"
  model_name: "qwen/qwen3-vl-30b"  # 根据LM Studio中显示的名称修改
  temperature: 0.2
  max_tokens: 2000
  timeout: 60

# 视频处理配置
video:
  input_dir: "E:\\Work_lyl\\concat_disagree"
  output_dir: "E:\\Work_lyl\\concat_disagree"
  video_extensions: [".mp4", ".avi", ".mov", ".mkv"]
  frame_position: "middle"
  frame_count: 1
```

## 使用方法

### 运行测试

```bash
python test_program.py
```

### 运行批量评判

```bash
# 使用默认配置
python src/main.py

# 指定输入目录
python src/main.py --input "D:\\path\\to\\videos"

# 指定配置文件
python src/main.py --config "config/custom_config.yaml"
```

## 输出目录结构

程序运行后会在输出目录下创建以下结构：

```
E:\Work_lyl\concat_disagree\
├── edit1\              # 高置信度判定为edit_1更好
├── edit2\              # 高置信度判定为edit_2更好
├── 平局\               # 高置信度判定为平局
├── _待人工复核\         # 低置信度样本，需要人工复核
└── _判断日志\
    ├── results.csv     # 判断结果CSV
    ├── *.json          # 详细判断结果
    └── report_*.txt    # 处理报告
```

## 工作流程

1. **抽帧**：从视频中抽取代表性帧（默认中间时间点）
2. **第一次判断**：将原始图像输入VLM模型进行评判
3. **位置交换**：交换edit_1和edit_2的位置
4. **第二次判断**：将交换后的图像输入模型进行评判
5. **一致性检查**：比较两次判断结果是否一致
6. **分类归档**：
   - 高置信度（一致）：自动归档到对应目录
   - 低置信度（不一致）：放入待人工复核目录
7. **日志记录**：保存判断过程和结果

## 注意事项

1. **LM Studio服务**：程序运行时需要LM Studio服务处于运行状态
2. **模型选择**：推荐使用 `qwen3-vl-30b`，对细微差异判断更准确
3. **视频格式**：支持MP4、AVI、MOV、MKV格式
4. **位置交换**：默认使用物理交换（图像处理），也可配置为仅交换标签
5. **人工复核**：低置信度样本需要人工复核，可配合AHK脚本使用

## 故障排除

### 无法连接LM Studio

- 检查LM Studio是否已启动本地服务
- 确认API地址和端口是否正确（默认http://localhost:1234）
- 检查防火墙设置

### 模型响应格式错误

- 检查模型是否支持视觉输入
- 确认模型名称是否与LM Studio中显示的一致
- 尝试降低temperature参数

### 视频抽帧失败

- 检查视频文件是否损坏
- 确认视频格式是否支持
- 检查文件权限

## 技术细节

- **抽帧策略**：支持单帧或多帧（首中尾），默认抽中间帧
- **位置交换**：支持物理交换（图像处理）和标签交换（prompt修改）
- **置信度判断**：基于两次判断的一致性，而非模型自评
- **结果解析**：使用正则表达式提取结构化结论

## 许可证

本项目仅用于内部使用。