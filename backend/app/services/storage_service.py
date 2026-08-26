import os
import uuid
import hashlib
from typing import Tuple
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings

class StorageService:
    def __init__(self, base_dir: str = settings.STORAGE_LOCAL_DIR):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def validate_file(self, file: UploadFile) -> str:
        """Validate filename, extension, and MIME type."""
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file must have a valid filename"
            )
        
        ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '{ext}' is not supported. Supported: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        return ext

    def save_upload(self, file: UploadFile, workspace_id: str, project_id: str) -> Tuple[str, str, int, str]:
        """
        Saves uploaded file securely into partitioned storage.
        Returns: (relative_storage_path, original_filename, file_size_bytes, sha256_checksum)
        """
        ext = self.validate_file(file)
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        
        target_dir = os.path.join(self.base_dir, workspace_id, project_id)
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, unique_name)

        hasher = hashlib.sha256()
        file_size = 0

        # Read file contents and save
        file.file.seek(0)
        with open(target_path, "wb") as f:
            while chunk := file.file.read(8192):
                hasher.update(chunk)
                file_size += len(chunk)
                if file_size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                    # Clean up file on size exceed
                    f.close()
                    if os.path.exists(target_path):
                        os.remove(target_path)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB"
                    )
                f.write(chunk)
        
        rel_path = os.path.relpath(target_path, self.base_dir)
        return rel_path, file.filename, file_size, hasher.hexdigest()

    def get_file_bytes(self, relative_path: str) -> bytes:
        """Retrieve original uploaded file content securely."""
        full_path = os.path.join(self.base_dir, relative_path)
        # Directory traversal prevention
        normalized = os.path.normpath(full_path)
        if not normalized.startswith(os.path.normpath(self.base_dir)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insecure path traversal detected"
            )
        if not os.path.exists(normalized):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Stored file not found"
            )
        with open(normalized, "rb") as f:
            return f.read()

storage_service = StorageService()
