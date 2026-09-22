import base64
import os
from pathlib import Path

from fastmcp import FastMCP
from openai import OpenAI

MODEL = "deepseek-flash"
BASE_URL = "https://api.deepseek.com"
ALLOWED_SUFFIXES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}
INLINE_MAX_BYTES = 32 * 1024 * 1024
UPLOAD_MAX_BYTES = 64 * 1024 * 1024
DETAIL_LEVELS = {"low", "high", "original", "auto"}

mcp = FastMCP(
    "DeepSeek Vision",
    instructions="Wraps the DeepSeek vision API (deepseek-flash). "
    "Three ways to pass images: Base64 inline for local files, external http(s) URL, "
    "or Files API file_id reference; for large or reused images, upload first with upload_image.",
)


def _get_client() -> OpenAI:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError(
            "DEEPSEEK_API_KEY environment variable is not set. Please fill in your DeepSeek API key "
            "under deepseek-vision.environment in ~/.config/opencode/opencode.jsonc"
        )
    return OpenAI(api_key=api_key, base_url=BASE_URL)


def _validate_detail(detail: str) -> str:
    d = (detail or "auto").lower()
    if d not in DETAIL_LEVELS:
        raise ValueError(f"detail must be one of {'/'.join(sorted(DETAIL_LEVELS))}, got: {detail}")
    return d


def _check_suffix(path: Path) -> None:
    if path.suffix.lower() not in ALLOWED_SUFFIXES:
        raise ValueError(f"Unsupported image format {path.suffix}, only JPEG/PNG/GIF/WebP are allowed")


def _chat(content: list[dict]) -> str:
    response = _get_client().chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": content}],
    )
    return response.choices[0].message.content


@mcp.tool
def upload_image(image_path: str) -> str:
    """Upload a local image to the DeepSeek Files API (purpose=user_data) and return a file_id for analyze_file_id.

    Args:
        image_path: Local image path, JPEG/PNG/GIF/WebP, max 64 MiB per file.

    Returns:
        A file ID in the form of file-api-xxxxxxxxxxxxxxxx.
    """
    path = Path(image_path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"Image file not found: {path}")
    _check_suffix(path)
    if path.stat().st_size > UPLOAD_MAX_BYTES:
        raise ValueError(f"Image size {path.stat().st_size} bytes exceeds the Files API limit of 64 MiB")
    with open(path, "rb") as f:
        uploaded = _get_client().files.create(file=f, purpose="user_data")
    return uploaded.id


@mcp.tool
def analyze_local_image(image_path: str, prompt: str, detail: str = "auto") -> str:
    """Method 1 (Base64 inline): read a local image, encode it as a data URL, embed it directly in the request and send it to the DeepSeek vision model.

    Args:
        image_path: Local image path, JPEG/PNG/GIF/WebP, max 32 MiB inline per image.
        prompt: Question or instruction about the image, e.g. "What is in this image?".
        detail: Detail level, low=resized to 512x512 faster and cheaper, high/original=keep original, auto=automatic.

    Returns:
        The model's text answer.
    """
    d = _validate_detail(detail)
    path = Path(image_path).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"Image file not found: {path}")
    _check_suffix(path)
    data = path.read_bytes()
    if len(data) > INLINE_MAX_BYTES:
        raise ValueError(
            f"Image size {len(data)} bytes exceeds the 32 MiB inline limit; "
            "call upload_image first and then use analyze_file_id"
        )
    mime = ALLOWED_SUFFIXES[path.suffix.lower()]
    b64 = base64.b64encode(data).decode("utf-8")
    content = [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}", "detail": d}},
    ]
    return _chat(content)


@mcp.tool
def analyze_image_url(image_url: str, prompt: str, detail: str = "auto") -> str:
    """Method 2 (External URL): pass a publicly accessible http(s) image link, downloaded and analyzed by the DeepSeek service.

    Args:
        image_url: Publicly accessible image link, max 8192 characters, image max 32 MiB and downloadable within 60 seconds.
        prompt: Question or instruction about the image.
        detail: Detail level, low=resized to 512x512 faster and cheaper, high/original=keep original, auto=automatic.

    Returns:
        The model's text answer.
    """
    d = _validate_detail(detail)
    url = image_url.strip()
    if not url.lower().startswith(("http://", "https://")):
        raise ValueError("image_url must be a publicly accessible link starting with http:// or https://")
    if len(url) > 8192:
        raise ValueError("URL exceeds the 8192-character limit; use analyze_local_image or upload_image + analyze_file_id instead")
    content = [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": url, "detail": d}},
    ]
    return _chat(content)


@mcp.tool
def analyze_file_id(file_id: str, prompt: str) -> str:
    """Method 3 (Files API): reference a file_id previously uploaded via upload_image and send it to the DeepSeek vision model.

    Best for large images over the 32 MiB inline limit (Files API allows up to 64 MiB per image), or reusing one image across requests.

    Args:
        file_id: File ID returned by the Files API, in the form of file-api-xxxxxxxxxxxxxxxx.
        prompt: Question or instruction about the image.

    Returns:
        The model's text answer.
    """
    fid = file_id.strip()
    if not fid.startswith("file-api-"):
        raise ValueError("file_id should be an ID returned by the Files API (starting with file-api-); call upload_image first")
    content = [
        {"type": "text", "text": prompt},
        {"type": "file", "file_id": fid},
    ]
    return _chat(content)


if __name__ == "__main__":
    mcp.run()
