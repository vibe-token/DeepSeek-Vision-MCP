# DeepSeek Vision MCP Server

A DeepSeek vision MCP server built with [FastMCP](https://gofastmcp.com), implementing
the three image-input interfaces from the official
[vision guide](https://api-docs.deepseek.com/guides/vision) for MCP clients such as opencode.

- Model: `deepseek-flash`
- API: OpenAI-compatible format, `base_url = https://api.deepseek.com`

> 中文文档请参见 [README.zh.md](README.zh.md)。

## Interfaces

| Tool | Method | Description |
|------|--------|-------------|
| `analyze_local_image(image_path, prompt, detail)` | 1. Base64 inline | Reads a local image, encodes it as a data URL embedded in the request; max 32 MiB per image |
| `analyze_image_url(image_url, prompt, detail)` | 2. External URL | Passes a public http(s) link downloaded by the server; URL ≤ 8192 chars |
| `analyze_file_id(file_id, prompt)` | 3. Files API | References an uploaded file's file_id; up to 64 MiB per image, reusable across requests |
| `upload_image(image_path)` | Files API helper | Uploads a local image (purpose=user_data), returns a `file-api-...` file_id |

`detail` options: `low` (resized to 512×512, faster and cheaper), `high`, `original`, `auto`.

## Installation

```powershell
mkdir %HOMEPATH%\mcp\DeepSeek
python -m venv %HOMEPATH%\mcp\DeepSeek\.venv
%HOMEPATH%\mcp\DeepSeek\.venv\Scripts\pip install -r %HOMEPATH%\mcp\DeepSeek\requirements.txt
```

Dependencies are pinned in `requirements.txt`: `fastmcp==3.4.7`, `openai==3.3.1`.

## Configuration

Add the following to the `mcp` section of `%HOMEPATH%\.config\opencode\opencode.jsonc`:

```jsonc
"deepseek-vision": {
  "type": "local",
  "command": ["C:\\Users\\%USERNAME%\\mcp\\DeepSeek\\.venv\\Scripts\\python",
    "C:\\Users\\%USERNAME%\\mcp\\DeepSeek\\server.py"],
  "enabled": true,
  "environment": {
    "DEEPSEEK_API_KEY": "<your DeepSeek API key>"
  }
}
```

Get your API key from the [DeepSeek Platform](https://platform.deepseek.com/).

## Usage Examples

Once configured, you can simply ask in conversation:

- "Use analyze_local_image to describe what's in D:\pics\screenshot.png"
- "Use analyze_image_url to look at https://example.com/photo.jpg and describe the scene"
- "First upload big_photo.png with upload_image, then use analyze_file_id to read the text in it"

## Limits Cheat Sheet

| Limit | Value |
|-------|-------|
| Supported formats | JPEG, PNG, GIF, WebP |
| Request body size (inline) | 48 MiB |
| Single image (base64 / external URL) | 32 MiB |
| Single image (Files API) | 64 MiB |
| External URL length | 8192 characters |
| Max images per request | 600 |

Notes:

- Images may only appear in `user` messages; images in `system` / `assistant` messages return 400.
- Only the vision model accepts images; other models return "This model does not support image".
- Every image is resized before entering the model; a single image consumes at most ~384 tokens.

## Verification

```powershell
%HOMEPATH%\mcp\DeepSeek\.venv\Scripts\python %HOMEPATH%\mcp\DeepSeek\server.py
```

No errors means the server starts fine in stdio mode (actual calls require DEEPSEEK_API_KEY configured).
