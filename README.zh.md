# DeepSeek Vision MCP Server

基于 [FastMCP](https://gofastmcp.com) 封装的 DeepSeek 图像理解 MCP 服务器，按照官方
[图像理解指南](https://api-docs.deepseek.com/zh-cn/guides/vision) 实现三种传图接口，
供 opencode 等 MCP 客户端调用。

- 模型：`deepseek-v4-flash-vision-exp`
- API：OpenAI 兼容格式，`base_url = https://api.deepseek.com`

## 接口一览

| 工具 | 对应方式 | 说明 |
|------|----------|------|
| `analyze_local_image(image_path, prompt, detail)` | 1. Base64 内联 | 读取本地图片编码为 data URL 直接嵌入请求，单图 ≤ 32 MiB |
| `analyze_image_url(image_url, prompt, detail)` | 2. 外部 URL | 传入公开 http(s) 链接，服务端自动下载；URL ≤ 8192 字符 |
| `analyze_file_id(file_id, prompt)` | 3. Files API | 引用已上传文件的 file_id，单图最大 64 MiB，可跨请求复用 |
| `upload_image(image_path)` | Files API 辅助 | 上传本地图片（purpose=user_data），返回 `file-api-...` 格式 file_id |

`detail` 可选值：`low`（缩放到 512×512，更快更省 token）、`high`、`original`、`auto`。

## 安装

```powershell
mkdir %HOMEPATH%\mcp\DeepSeek
python -m venv %HOMEPATH%\mcp\DeepSeek\.venv
%HOMEPATH%\mcp\DeepSeek\.venv\Scripts\pip install -r %HOMEPATH%\mcp\DeepSeek\requirements.txt
```

依赖见 `requirements.txt`：`fastmcp==3.4.7`、`openai==3.3.1`。

## 配置

在 `~\.config\opencode\opencode.jsonc` 的 `mcp` 段添加：

```jsonc
"deepseek-vision": {
  "type": "local",
  "command": ["C:\\Users\\%USERNAME%\\mcp\\DeepSeek\\.venv\\Scripts\\python",
    "C:\\Users\\%USERNAME%\\mcp\\DeepSeek\\server.py"],
  "enabled": true,
  "environment": {
    "DEEPSEEK_API_KEY": "<你的 DeepSeek API Key>"
  }
}
```

API Key 从 [DeepSeek 开放平台](https://platform.deepseek.com/) 获取。

## 使用示例

配置生效后，可在对话中直接说：

- 「用 analyze_local_image 分析 D:\pics\screenshot.png 里有什么」
- 「用 analyze_image_url 看看 https://example.com/photo.jpg 描述一下画面内容」
- 「先用 upload_image 上传 big_photo.png，再用 analyze_file_id 识别里面的文字」

## 使用限制速查

| 限制项 | 数值 |
|--------|------|
| 支持格式 | JPEG、PNG、GIF、WebP |
| 请求体大小（内联） | 48 MiB |
| 单张图片（base64 / 外部 URL） | 32 MiB |
| 单张图片（Files API） | 64 MiB |
| 外部 URL 长度 | 8192 字符 |
| 单请求最大图片数 | 600 |

注意事项：

- 图片只能出现在 `user` 消息中，`system` / `assistant` 携带图片会返回 400。
- 仅视觉模型接受图片，其他模型返回 "This model does not support image"。
- 每张图片进入模型前会被缩放，单张最多消耗约 384 个 token。

## 运行验证

```powershell
%HOMEPATH%\mcp\DeepSeek\.venv\Scripts\python %HOMEPATH%\mcp\DeepSeek\server.py
```

无报错即表示服务器可正常以 stdio 方式启动（实际调用需要已配置 DEEPSEEK_API_KEY）。
