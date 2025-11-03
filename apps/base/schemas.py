from pydantic import BaseModel


class SelectFileModel(BaseModel):
    code: str


class InitChunkUploadModel(BaseModel):
    file_name: str
    chunk_size: int = 5 * 1024 * 1024
    file_size: int
    file_hash: str
    user_id: str = None


class CompleteUploadModel(BaseModel):
    expire_value: int
    expire_style: str
    user_id: str = None


class UserFileListRequest(BaseModel):
    user_id: str
    page: int = 1
    page_size: int = 20


class UserIDData(BaseModel):
    id: int
    user_id: str