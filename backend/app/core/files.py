import os
import re
import uuid
from fastapi import UploadFile, HTTPException, status
from pathlib import Path

# Setup directories relative to backend root
UPLOAD_DIR = Path("uploads")
DOCUMENTS_DIR = UPLOAD_DIR / "documents"
DRAWINGS_DIR = UPLOAD_DIR / "drawings"
SITE_IMAGES_DIR = UPLOAD_DIR / "site_images"

# Ensure upload directories exist on utility initialization
for directory in [DOCUMENTS_DIR, DRAWINGS_DIR, SITE_IMAGES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Whitelist definitions
ALLOWED_MIME_TYPES = {
    "document": {
        "application/pdf",
        "text/plain",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    },
    "drawing": {
        "application/pdf"
    },
    "image": {
        "image/png",
        "image/jpeg",
        "image/webp"
    }
}

ALLOWED_EXTENSIONS = {
    "document": {".pdf", ".txt", ".doc", ".docx", ".xls", ".xlsx"},
    "drawing": {".pdf"},
    "image": {".png", ".jpg", ".jpeg", ".webp"}
}

MAX_FILE_SIZES = {
    "document": 10 * 1024 * 1024, # 10MB
    "drawing": 10 * 1024 * 1024,  # 10MB
    "image": 5 * 1024 * 1024      # 5MB
}

def sanitize_filename(filename: str) -> str:
    """
    Sanitizes filename using regex to prevent directory traversal and special chars.
    Appends a unique uuid4 string to guarantee path uniqueness.
    """
    if not filename:
        filename = "unnamed_file"
    name, ext = os.path.splitext(filename)
    # Filter base name characters
    name = re.sub(r'[^a-zA-Z0-9_.-]', '_', name)
    ext = re.sub(r'[^a-zA-Z0-9.]', '', ext).lower()
    return f"{uuid.uuid4().hex}_{name}{ext}"

async def validate_and_save_file(
    file: UploadFile,
    file_category: str
) -> str:
    """
    Validates extension, MIME type, and size constraints.
    Saves file to directory and returns the relative file path.
    """
    if file_category not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file category: {file_category}"
        )

    # Validate file extension
    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ""
    if ext not in ALLOWED_EXTENSIONS[file_category]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{ext}' is not allowed for category '{file_category}'."
        )

    # Validate MIME type
    if file.content_type not in ALLOWED_MIME_TYPES[file_category]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"MIME type '{file.content_type}' is not allowed for category '{file_category}'."
        )

    # Read bytes to verify file size
    content = await file.read()
    file_size = len(content)
    await file.seek(0) # Reset pointer

    max_size = MAX_FILE_SIZES[file_category]
    if file_size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds the limit of {max_size_mb:.1f}MB."
        )

    # Map target path
    if file_category == "document":
        save_dir = DOCUMENTS_DIR
    elif file_category == "drawing":
        save_dir = DRAWINGS_DIR
    else:
        save_dir = SITE_IMAGES_DIR

    new_filename = sanitize_filename(file.filename)
    file_path = save_dir / new_filename

    # Save content to disk
    with open(file_path, "wb") as f:
        f.write(content)

    return str(file_path.as_posix())

def delete_physical_file(file_path: str):
    """
    Physically removes a file from disk if it exists.
    """
    if not file_path:
        return
    path = Path(file_path)
    if path.exists() and path.is_file():
        try:
            os.remove(path)
        except OSError:
            pass
