import hashlib
import uuid

from fastapi import APIRouter, Form, UploadFile, File, Depends, HTTPException
from starlette import status
from tortoise.functions import Sum

from apps.admin.dependencies import share_required_login
from apps.base.models import FileCodes, UploadChunk
from apps.base.schemas import SelectFileModel, InitChunkUploadModel, CompleteUploadModel, UserFileListRequest,UserIDData
from apps.base.utils import get_expire_info, get_file_path_name, ip_limit, get_chunk_file_path_name
from core.response import APIResponse
from core.settings import settings
from core.storage import storages, FileStorageInterface
from core.utils import get_select_token

from apps.admin.services import FileService
from apps.admin.dependencies import get_file_service
share_api = APIRouter(prefix="/share", tags=["分享"])


async def validate_file_size(file: UploadFile, max_size: int):
    if file.size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        raise HTTPException(
            status_code=403, detail=f"大小超过限制,最大为{max_size_mb:.2f} MB"
        )


async def create_file_code(code, **kwargs):
    return await FileCodes.create(code=code, **kwargs)


async def check_user_storage_limit(user_id: str, file_size: int) -> None:
    """
    检查用户存储容量限制
    :param user_id: 用户ID
    :param file_size: 本次上传的文件大小
    :raises HTTPException: 如果超过限制则抛出异常
    """
    if not user_id:
        return  # 如果没有user_id，则不检查（匿名上传）
    
    # 获取用户已上传的文件总容量
    result = await FileCodes.filter(user_id=user_id).aggregate(total_size=Sum('size'))
    user_upload_size = result.get('total_size') or 0
    
    # 检查总容量是否超过限制
    if user_upload_size + file_size > settings.uploadSize:
        raise HTTPException(
            status_code=400,
            detail=f"用户已上传的文件容量超过限制，已使用: {user_upload_size / (1024 * 1024):.2f} MB，限制: {settings.uploadSize / (1024 * 1024):.2f} MB"
        )


# @share_api.post("/text/", dependencies=[Depends(share_required_login)])
# async def share_text(
#         text: str = Form(...),
#         expire_value: int = Form(default=1, gt=0),
#         expire_style: str = Form(default="day"),
#         user_id: str = Form(default=None),
#         ip: str = Depends(ip_limit["upload"]),
# ):
#     text_size = len(text.encode("utf-8"))
#     max_txt_size = 222 * 1024
#     if text_size > max_txt_size:
#         raise HTTPException(status_code=403, detail="内容过多,建议采用文件形式")

#     expired_at, expired_count, used_count, code = await get_expire_info(
#         expire_value, expire_style
#     )
#     await create_file_code(
#         code=code,
#         text=text,
#         expired_at=expired_at,
#         expired_count=expired_count,
#         used_count=used_count,
#         size=len(text),
#         prefix="Text",
#         user_id=user_id,
#     )
#     ip_limit["upload"].add_ip(ip)
#     return APIResponse(detail={"code": code})


@share_api.post("/file/", dependencies=[Depends(share_required_login)])
async def share_file(
        expire_value: int = Form(default=1, gt=0),
        expire_style: str = Form(default="day"),
        file: UploadFile = File(...),
        user_id: str = Form(default=None),
        ip: str = Depends(ip_limit["upload"]),
):
    # 获取用户已上传的文件容量，如果加上本次上传的文件容量超过限制，则返回错误
    await validate_file_size(file, settings.uploadSize)
    # 检查用户存储容量限制
    await check_user_storage_limit(user_id, file.size)
    if expire_style not in settings.expireStyle:
        raise HTTPException(status_code=400, detail="过期时间类型错误")
    expired_at, expired_count, used_count, code = await get_expire_info(expire_value, expire_style)
    path, suffix, prefix, uuid_file_name, save_path = await get_file_path_name(file)
    file_storage: FileStorageInterface = storages[settings.file_storage]()
    await file_storage.save_file(file, save_path)
    await create_file_code(
        code=code,
        prefix=prefix,
        suffix=suffix,
        uuid_file_name=uuid_file_name,
        file_path=path,
        size=file.size,
        expired_at=expired_at,
        expired_count=expired_count,
        used_count=used_count,
        user_id=user_id,
    )
    ip_limit["upload"].add_ip(ip)
    return APIResponse(detail={"code": code, "name": file.filename})


async def get_code_file_by_code(code, check=True):
    file_code = await FileCodes.filter(code=code).first()
    if not file_code:
        return False, "文件不存在"
    if await file_code.is_expired() and check:
        return False, "文件已过期"
    return True, file_code


async def update_file_usage(file_code):
    file_code.used_count += 1
    if file_code.expired_count > 0:
        file_code.expired_count -= 1
    await file_code.save()


@share_api.get("/select/")
async def get_code_file(code: str, ip: str = Depends(ip_limit["error"])):
    file_storage: FileStorageInterface = storages[settings.file_storage]()
    has, file_code = await get_code_file_by_code(code)
    if not has:
        ip_limit["error"].add_ip(ip)
        return APIResponse(code=404, detail=file_code)

    await update_file_usage(file_code)
    return await file_storage.get_file_response(file_code)


@share_api.post("/select/")
async def select_file(data: SelectFileModel, ip: str = Depends(ip_limit["error"])):
    file_storage: FileStorageInterface = storages[settings.file_storage]()
    has, file_code = await get_code_file_by_code(data.code)
    if not has:
        ip_limit["error"].add_ip(ip)
        return APIResponse(code=404, detail=file_code)

    await update_file_usage(file_code)
    return APIResponse(
        detail={
            "code": file_code.code,
            "name": file_code.prefix + file_code.suffix,
            "size": file_code.size,
            "text": (
                file_code.text
                if file_code.text is not None
                else await file_storage.get_file_url(file_code)
            ),
        }
    )


@share_api.get("/download")
async def download_file(key: str, code: str, ip: str = Depends(ip_limit["error"])):
    file_storage: FileStorageInterface = storages[settings.file_storage]()
    if await get_select_token(code) != key:
        ip_limit["error"].add_ip(ip)
    has, file_code = await get_code_file_by_code(code, False)
    if not has:
        return APIResponse(code=404, detail="文件不存在")
    return (
        APIResponse(detail=file_code.text)
        if file_code.text
        else await file_storage.get_file_response(file_code)
    )


chunk_api = APIRouter(prefix="/chunk", tags=["切片"])


@chunk_api.post("/upload/init/", dependencies=[Depends(share_required_login)])
async def init_chunk_upload(data: InitChunkUploadModel, ip: str = Depends(ip_limit["upload"])):
    # 检查文件大小限制
    if data.file_size > settings.uploadSize:
        max_size_mb = settings.uploadSize / (1024 * 1024)
        raise HTTPException(
            status_code=403, detail=f"大小超过限制,最大为{max_size_mb:.2f} MB"
        )
    
    # 检查用户存储容量限制
    await check_user_storage_limit(data.user_id, data.file_size)
    
    # # 秒传检查
    # existing = await FileCodes.filter(file_hash=data.file_hash).first()
    # if existing:
    #     if await existing.is_expired():
    #         file_storage: FileStorageInterface = storages[settings.file_storage](
    #         )
    #         await file_storage.delete_file(existing)
    #         await existing.delete()
    #     else:
    #         return APIResponse(detail={
    #             "code": existing.code,
    #             "existed": True,
    #             "name": f'{existing.prefix}{existing.suffix}'
    #         })

    # 创建上传会话
    upload_id = uuid.uuid4().hex
    total_chunks = (data.file_size + data.chunk_size - 1) // data.chunk_size
    await UploadChunk.create(
        upload_id=upload_id,
        chunk_index=-1,
        total_chunks=total_chunks,
        file_size=data.file_size,
        chunk_size=data.chunk_size,
        chunk_hash=data.file_hash,
        file_name=data.file_name,
        user_id=data.user_id,
    )
    # 获取已上传的分片列表
    uploaded_chunks = await UploadChunk.filter(
        upload_id=upload_id,
        completed=True
    ).values_list('chunk_index', flat=True)
    return APIResponse(detail={
        "existed": False,
        "upload_id": upload_id,
        "chunk_size": data.chunk_size,
        "total_chunks": total_chunks,
        "uploaded_chunks": uploaded_chunks
    })


@chunk_api.post("/upload/chunk/{upload_id}/{chunk_index}", dependencies=[Depends(share_required_login)])
async def upload_chunk(
        upload_id: str,
        chunk_index: int,
        chunk: UploadFile = File(...),
):
    # 获取上传会话信息
    chunk_info = await UploadChunk.filter(upload_id=upload_id, chunk_index=-1).first()
    if not chunk_info:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="上传会话不存在")

    # 检查分片索引有效性
    if chunk_index < 0 or chunk_index >= chunk_info.total_chunks:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="无效的分片索引")

    # 读取分片数据并计算哈希
    chunk_data = await chunk.read()
    chunk_hash = hashlib.sha256(chunk_data).hexdigest()

    # 更新或创建分片记录
    await UploadChunk.update_or_create(
        upload_id=upload_id,
        chunk_index=chunk_index,
        defaults={
            'chunk_hash': chunk_hash,
            'completed': True,
            'file_size': chunk_info.file_size,
            'total_chunks': chunk_info.total_chunks,
            'chunk_size': chunk_info.chunk_size,
            'file_name': chunk_info.file_name
        }
    )
    # 获取文件路径
    _, _, _, _, save_path = await get_chunk_file_path_name(chunk_info.file_name, upload_id)
    # 保存分片到存储
    storage = storages[settings.file_storage]()
    await storage.save_chunk(upload_id, chunk_index, chunk_data, chunk_hash, save_path)
    return APIResponse(detail={"chunk_hash": chunk_hash})


@chunk_api.post("/upload/complete/{upload_id}", dependencies=[Depends(share_required_login)])
async def complete_upload(upload_id: str, data: CompleteUploadModel, ip: str = Depends(ip_limit["upload"])):
    # 获取上传基本信息
    chunk_info = await UploadChunk.filter(upload_id=upload_id, chunk_index=-1).first()
    if not chunk_info:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="上传会话不存在")

    # 再次检查用户存储容量限制（防止在分片上传过程中容量被其他上传占用）
    user_id = chunk_info.user_id or data.user_id
    await check_user_storage_limit(user_id, chunk_info.file_size)

    storage = storages[settings.file_storage]()
    # 验证所有分片
    completed_chunks = await UploadChunk.filter(
        upload_id=upload_id,
        completed=True
    ).count()
    if completed_chunks != chunk_info.total_chunks:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="分片不完整")
    # 获取文件路径
    path, suffix, prefix, _, save_path = await get_chunk_file_path_name(chunk_info.file_name, upload_id)
    # 合并文件并计算哈希
    await storage.merge_chunks(upload_id, chunk_info, save_path)
    # 创建文件记录
    expired_at, expired_count, used_count, code = await get_expire_info(data.expire_value, data.expire_style)
    await FileCodes.create(
        code=code,
        file_hash=chunk_info.chunk_hash,
        is_chunked=True,
        upload_id=upload_id,
        size=chunk_info.file_size,
        expired_at=expired_at,
        expired_count=expired_count,
        used_count=used_count,
        file_path=path,
        uuid_file_name=f"{prefix}{suffix}",
        prefix=prefix,
        suffix=suffix,
        user_id=chunk_info.user_id or data.user_id,
    )
    # 清理临时文件
    await storage.clean_chunks(upload_id, save_path)
    return APIResponse(detail={"code": code, "name": chunk_info.file_name})


@share_api.delete("/file/user_delete")
async def file_delete(
        data: UserIDData,
        file_service: FileService = Depends(get_file_service)
):
    await file_service.delete_user_file(data.id,data.user_id)
    return APIResponse()

@share_api.post("/user/files/", dependencies=[Depends(share_required_login)])
async def get_user_files(data: UserFileListRequest):
    # 计算分页
    offset = (data.page - 1) * data.page_size

    # 查询用户上传的文件列表
    query = FileCodes.filter(user_id=data.user_id).order_by("-created_at")

    # 获取总数
    total = await query.count()

    # 获取分页数据
    files = await query.offset(offset).limit(data.page_size).all()

    # 构建返回数据
    file_list = []
    for file_obj in files:
        file_info = {
            "code": file_obj.code,
            "name": file_obj.prefix + file_obj.suffix if file_obj.prefix and file_obj.suffix else "Text",
            "size": file_obj.size,
            "created_at": file_obj.created_at.isoformat() if file_obj.created_at else None,
            "expired_at": file_obj.expired_at.isoformat() if file_obj.expired_at else None,
            "is_text": file_obj.text is not None,
            "expired_count": file_obj.expired_count,
            "used_count": file_obj.used_count,
            "id": file_obj.id,
        }
        file_list.append(file_info)

    return APIResponse(detail={
        "files": file_list,
        "pagination": {
            "page": data.page,
            "page_size": data.page_size,
            "total": total,
            "pages": (total + data.page_size - 1) // data.page_size
        }
    })
