# 注意，以下内容由AI生成，还未校对核实，如不明白如何使用，请等待下次修改描述

# 哔哩哔哩视频转写工具

## 项目描述

这是一个全栈应用程序，用于将哔哩哔哩（Bilibili）视频的音频内容转写为文本。它提供了一个用户友好的界面，允许用户输入视频的 BV 号，选择转写服务，并获取转写结果。该工具支持多种转写服务，包括本地 Faster Whisper、OpenAI Whisper 和云端 Faster Whisper。

## 功能特性

- 支持通过 BV 号提取哔哩哔哩视频音频
- 多种转写服务选项
  - 本地 Faster Whisper
  - OpenAI Whisper
  - 云端 Faster Whisper
- 实时转写进度显示
- 转写历史记录管理
- 导出 SRT 字幕文件
- 响应式设计，支持移动设备
- 深色/浅色主题切换

## 使用的技术

### 前端
- React.js
- Material-UI
- React Hooks
- localStorage 用于客户端存储

### 后端
- Python
- Flask
- yt-dlp 用于视频处理
- Faster Whisper
- OpenAI API（用于 Whisper 服务）

## 环境要求

- Node.js (v14+)
- Python (v3.8+)
- pip (Python 包管理器)
- FFmpeg (用于音频处理)

## 安装步骤

1. 克隆仓库：
   ```
   git clone https://github.com/yourusername/bilibili-transcription-tool.git
   cd bilibili-transcription-tool
   ```

2. 安装前端依赖：
   ```
   cd frontend
   npm install
   ```

3. 安装后端依赖：
   ```
   cd ../backend
   pip install -r requirements.txt
   ```

## 配置

1. 设置环境变量：
   在 `backend` 目录中创建一个 `.env` 文件，内容如下：
   ```
   OPENAI_API_KEY=your_openai_api_key
   CLOUD_WHISPER_URL=your_cloud_whisper_url
   ```

2. 配置 Faster Whisper 模型路径：
   在 `services.py` 中，更新 `FASTER_WHISPER_MODEL_PATH` 变量为你本地 Faster Whisper 模型的路径。

## 使用说明

1. 启动后端服务器：
   ```
   cd backend
   python app.py
   ```

2. 启动前端开发服务器：
   ```
   cd frontend
   npm start
   ```

3. 打开浏览器并访问 `http://localhost:3000`

4. 输入哔哩哔哩视频的 BV 号，选择转写服务，然后点击"获取字幕"开始转写过程。

## API 端点

- `POST /api/transcribe`: 开始转写任务
- `GET /api/progress`: 获取转写任务的进度
- `POST /api/export_srt`: 将转写结果导出为 SRT 文件

## 前端结构

- `App.js`: 包含应用程序主要逻辑的主组件
- `TranscriptSentence.js`: 用于渲染单个转写句子的组件
- `index.js`: React 应用程序的入口点

## 后端结构

- `app.py`: Flask 应用程序设置和初始化
- `routes.py`: API 路由定义
- `services.py`: 音频提取和转写的核心业务逻辑
- `transcription_service.py`: 转写服务实现
- `utils.py`: 实用函数
- `subtitle_utils.py`: 字幕处理函数
- `cloud_faster_whisper.py`: 云端 Faster Whisper 实现

## 贡献指南

欢迎贡献！请随时提交 Pull Request。

## 许可证

本项目采用 MIT 许可证。

## 致谢

- [Faster Whisper](https://github.com/guillaumekln/faster-whisper) 用于本地转写
- [OpenAI Whisper](https://github.com/openai/whisper) 用于云端转写
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) 用于视频处理
- [Material-UI](https://material-ui.com/) 用于 React 组件

## 安全注意事项

1. 确保 `.env` 文件包含在 `.gitignore` 中，以防止暴露敏感的 API 密钥。
2. 建议在生产部署中使用 HTTPS 以确保数据传输的安全性。
3. 建议用户在生产环境中为 API 端点设置适当的身份验证和速率限制。
4. 建议在前端和后端都实施输入验证，以防止潜在的注入攻击。
5. 建议定期更新依赖项以修复任何已知的漏洞。

## 常见问题解答

1. Q: 如何更改转写服务？
   A: 在用户界面中，您可以在提交 BV 号之前选择所需的转写服务。

2. Q: 支持哪些视频格式？
   A: 该工具支持哔哩哔哩平台上的所有常见视频格式。

3. Q: 如何处理长视频？
   A: 对于较长的视频，转写过程可能需要更多时间。请耐心等待，进度条会显示实时进度。

4. Q: 转写结果的准确性如何？
   A: 转写准确性取决于所选的服务和原始音频的质量。通常情况下，对于清晰的普通话音频，准确率较高。

5. Q: 如果转写过程中断，如何恢复？
   A: 目前，如果转写过程中断，您需要重新开始转写过程。我们计划在未来版本中添加断点续传功能。

## 故障排除

1. 如果遇到 "无法连接到服务器" 错误，请检查您的网络连接，并确保后端服务器正在运行。

2. 如果转写过程卡在某个阶段，尝试刷新页面并重新开始转写过程。

3. 如果导出 SRT 文件失败，请确保您有足够的磁盘空间，并且对输出目录有写入权限。

4. 如果遇到 Python 依赖相关的错误，尝试更新您的 pip 和所有依赖：
   ```
   pip install --upgrade pip
   pip install -r requirements.txt --upgrade
   ```

5. 如果前端无法加载，请检查 Node.js 版本是否兼容，并尝试清除 npm 缓存：
   ```
   npm cache clean --force
   npm install
   ```

## 未来计划

1. 添加更多转写服务选项
2. 实现用户认证系统
3. 提供批量转写功能
4. 改进转写准确性的后处理
5. 添加更多字幕格式的导出选项
6. 实现实时字幕生成功能

我们欢迎社区成员为这些计划做出贡献或提供建议！
