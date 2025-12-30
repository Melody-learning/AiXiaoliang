# AiXiaoliang (AI-小亮)

AI-小亮是一个基于大模型的智能股票筛选与分析助手。

## 功能特点
- **智能研报阅读**: 结合本地知识库分析股票。
- **自动化工具**: 自动获取 Tushare 数据并进行分析。
- **灵活配置**: 支持通过环境变量配置模型和代理。
- **便携发布**: 支持 PyInstaller 打包为独立执行文件。

## 环境配置
参考 `.env.template` 创建 `.env` 文件并填入以下内容：
- `GOOGLE_API_KEY`: Gemini API Key
- `TUSHARE_TOKEN`: Tushare API Token
- `MODEL_NAME`: 使用的模型（推荐 `gemini-3-flash-preview`）

## 安装与运行
1. 安装依赖：`pip install -r requirements.txt`
2. 运行应用：`python aixiaoliang_agent/app.py`

## 本地打包
运行 `python package.py` 即可生成 `dist/AiXiaoliang` 可执行版本。
