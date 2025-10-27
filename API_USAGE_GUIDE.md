# 用户ID功能集成指南

## 功能概述

本项目已成功集成用户ID功能，支持以下特性：
1. 文件上传时关联用户ID
2. 文本分享时关联用户ID
3. 分片上传时关联用户ID
4. 查询用户上传历史列表

## 修改内容

### 1. 数据库变更
- `filecodes` 表添加 `user_id` 字段
- `uploadchunk` 表添加 `user_id` 字段
- 新增迁移文件：`apps/base/migrations/migrations_003.py`

### 2. 模型变更
- `FileCodes` 模型添加 `user_id` 字段
- `UploadChunk` 模型添加 `user_id` 字段

### 3. 接口变更

#### 3.1 文本上传接口
**URL**: `POST /share/text/`

**请求参数**:
```form-data
text: string (required) - 文本内容
expire_value: int (optional, default=1) - 过期时间值
expire_style: string (optional, default="day") - 过期时间类型
user_id: string (optional) - 用户ID
```

**响应示例**:
```json
{
  "code": 200,
  "detail": {
    "code": "abc12"  // 5位取件码
  }
}
```

#### 3.2 文件上传接口
**URL**: `POST /share/file/`

**请求参数**:
```form-data
file: file (required) - 上传的文件
expire_value: int (optional, default=1) - 过期时间值
expire_style: string (optional, default="day") - 过期时间类型
user_id: string (optional) - 用户ID
```

**响应示例**:
```json
{
  "code": 200,
  "detail": {
    "code": "def34",  // 5位取件码
    "name": "filename.ext"  // 原始文件名
  }
}
```

#### 3.3 分片上传初始化接口
**URL**: `POST /chunk/upload/init/`

**请求参数**:
```json
{
  "file_name": "example.zip",
  "chunk_size": 5242880,  // 5MB
  "file_size": 10485760,  // 10MB
  "file_hash": "sha256_hash...",
  "user_id": "user123"    // 用户ID
}
```

**响应示例**:
```json
{
  "code": 200,
  "detail": {
    "existed": false,
    "upload_id": "uuid_string",
    "chunk_size": 5242880,
    "total_chunks": 2,
    "uploaded_chunks": []
  }
}
```

#### 3.4 分片上传完成接口
**URL**: `POST /chunk/upload/complete/{upload_id}`

**请求参数**:
```json
{
  "expire_value": 7,
  "expire_style": "day",
  "user_id": "user123"    // 用户ID
}
```

**响应示例**:
```json
{
  "code": 200,
  "detail": {
    "code": "ghi56",  // 5位取件码
    "name": "example.zip"
  }
}
```

#### 3.5 用户文件列表查询接口（新增）
**URL**: `POST /share/user/files/`

**请求参数**:
```json
{
  "user_id": "user123",     // 必需 - 用户ID
  "page": 1,               // 可选 - 页码，默认1
  "page_size": 20          // 可选 - 每页数量，默认20
}
```

**响应示例**:
```json
{
  "code": 200,
  "detail": {
    "files": [
      {
        "code": "abc12",                    // 5位取件码
        "name": "document.pdf",            // 文件名
        "size": 1048576,                   // 文件大小（字节）
        "created_at": "2023-08-20T10:30:00", // 创建时间
        "expired_at": "2023-08-27T10:30:00", // 过期时间
        "is_text": false,                  // 是否为文本
        "expired_count": 10,               // 剩余下载次数
        "used_count": 2                    // 已使用次数
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 5,        // 总文件数
      "pages": 1         // 总页数
    }
  }
}
```

## 使用示例

### 代理项目集成

在另一个项目（用户认证项目）中，您可以这样调用：

```python
import httpx

# 代理文件上传
async def proxy_upload_file(user_id, file_data, expire_value=1, expire_style="day"):
    files = {"file": file_data}
    data = {
        "expire_value": expire_value,
        "expire_style": expire_style,
        "user_id": user_id
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://41.218.128.131:12345/share/file/",
            files=files,
            data=data
        )
        return response.json()

# 查询用户文件列表
async def get_user_files(user_id, page=1, page_size=20):
    data = {
        "user_id": user_id,
        "page": page,
        "page_size": page_size
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://41.218.128.131:12345/share/user/files/",
            json=data
        )
        return response.json()
```

### 前端调用示例

#### 文件上传
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('expire_value', 7);
formData.append('expire_style', 'day');
formData.append('user_id', 'current_user_id');

fetch('/share/file/', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    console.log('上传成功，取件码:', data.detail.code);
});
```

#### 查询文件列表
```javascript
fetch('/share/user/files/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        user_id: 'current_user_id',
        page: 1,
        page_size: 10
    })
})
.then(response => response.json())
.then(data => {
    console.log('用户文件列表:', data.detail.files);
});
```

## 数据库迁移

项目启动时会自动执行数据库迁移。如果需要手动执行迁移：

```python
from apps.base.migrations.migrations_003 import migrate

await migrate()
```

## 注意事项

1. 所有上传接口的 `user_id` 参数都是可选的，不传则为 `null`
2. 用户文件列表查询需要提供 `user_id`
3. 分片上传时，`user_id` 会在初始化时保存，并在完成时自动关联到最终文件记录
4. 所有接口都需要通过 `share_required_login` 依赖验证（根据您的认证逻辑）
5. 返回的取件码都是5位长度，用于文件下载

## 测试

可以使用项目根目录的 `test_user_functionality.py` 脚本来测试新功能：

```bash
# 启动服务
python main.py

# 在另一个终端运行测试
python test_user_functionality.py
```

## 向后兼容性

- 所有现有接口保持向后兼容
- 不传 `user_id` 参数时行为与之前完全一致
- 数据库自动迁移，不会影响现有数据