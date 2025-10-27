# MySQL数据库迁移指南

## 概述

本指南详细说明了如何将FileCodeBox项目从SQLite数据库迁移到MySQL数据库。

## 数据库配置

### MySQL服务器信息
- **主机地址**: 192.168.9.56
- **端口**: 3306
- **用户名**: filebox
- **密码**: Yqga!123
- **数据库名**: filecodebox
- **字符集**: utf8mb4

### 配置文件位置
数据库配置已添加到 `core/settings.py` 文件中：

```python
DATABASE_CONFIG = {
    "host": "192.168.9.56",
    "port": 3306,
    "user": "filebox",
    "password": "Yqga!123",
    "database": "filecodebox",
    "charset": "utf8mb4"
}
```

## 迁移步骤

### 1. 安装MySQL驱动

首先安装新的依赖：

```bash
pip install -r requirements.txt
```

新添加的依赖：
- `aiomysql==0.2.0` - MySQL异步驱动

### 2. 创建MySQL数据库

执行以下命令创建数据库：

```bash
mysql -h 192.168.9.56 -u filebox -p < mysql_init.sql
```

或者手动执行：

```sql
-- 连接到MySQL服务器
mysql -h 192.168.9.56 -u filebox -p

-- 创建数据库
CREATE DATABASE filecodebox CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 验证数据库连接

启动应用程序前，先验证数据库连接：

```python
# 测试连接脚本 test_mysql_connection.py
import asyncio
import aiomysql
from core.settings import DATABASE_CONFIG

async def test_connection():
    try:
        conn = await aiomysql.connect(
            host=DATABASE_CONFIG['host'],
            port=DATABASE_CONFIG['port'],
            user=DATABASE_CONFIG['user'],
            password=DATABASE_CONFIG['password'],
            db=DATABASE_CONFIG['database'],
            charset=DATABASE_CONFIG['charset']
        )
        print("✅ MySQL连接成功!")
        await conn.ensure_closed()
    except Exception as e:
        print(f"❌ MySQL连接失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
```

### 4. 启动应用程序

```bash
python main.py
```

应用程序启动时会自动：
1. 连接到MySQL数据库
2. 创建所有必要的表结构
3. 执行所有迁移脚本
4. 创建索引

## 主要修改内容

### 1. 配置文件更新

**core/settings.py**
```python
# 新增MySQL配置
DATABASE_CONFIG = {
    "host": "192.168.9.56",
    "port": 3306,
    "user": "filebox",
    "password": "Yqga!123",
    "database": "filecodebox",
    "charset": "utf8mb4"
}
```

**core/database.py**
```python
# 构建MySQL连接字符串
db_url = f"mysql+aiomysql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}?charset={DATABASE_CONFIG['charset']}"
```

**main.py**
```python
# 更新Tortoise配置使用MySQL
db_url = f"mysql+aiomysql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}?charset={DATABASE_CONFIG['charset']}"
```

### 2. 依赖更新

**requirements.txt**
```
aiomysql==0.2.0  # 新增MySQL驱动
```

### 3. 迁移脚本更新

所有迁移脚本都已更新为MySQL语法：

- `migrations_001.py` - 创建基础表结构
- `migrations_002.py` - 添加分片上传支持
- `migrations_003.py` - 添加用户ID支持

## 数据库表结构

### filecodes表
```sql
CREATE TABLE filecodes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(255) NOT NULL UNIQUE,
    prefix VARCHAR(255) DEFAULT '' NOT NULL,
    suffix VARCHAR(255) DEFAULT '' NOT NULL,
    uuid_file_name VARCHAR(255),
    file_path VARCHAR(255),
    size INT DEFAULT 0 NOT NULL,
    text TEXT,
    expired_at TIMESTAMP NULL,
    expired_count INT DEFAULT 0 NOT NULL,
    used_count INT DEFAULT 0 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    file_hash VARCHAR(128),
    is_chunked BOOLEAN NOT NULL DEFAULT FALSE,
    upload_id VARCHAR(128),
    user_id VARCHAR(255),
    INDEX idx_filecodes_code (code),
    INDEX idx_filecodes_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### uploadchunk表
```sql
CREATE TABLE uploadchunk (
    id INT AUTO_INCREMENT PRIMARY KEY,
    upload_id VARCHAR(36) NOT NULL,
    chunk_index INT NOT NULL,
    chunk_hash VARCHAR(128) NOT NULL,
    total_chunks INT NOT NULL,
    file_size BIGINT NOT NULL,
    chunk_size INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    file_name VARCHAR(255) NOT NULL,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    user_id VARCHAR(255),
    INDEX idx_uploadchunk_upload_id (upload_id),
    INDEX idx_uploadchunk_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### keyvalue表
```sql
CREATE TABLE keyvalue (
    id INT AUTO_INCREMENT PRIMARY KEY,
    key VARCHAR(255) NOT NULL UNIQUE,
    value JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    INDEX idx_keyvalue_key (key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### migrates表
```sql
CREATE TABLE migrates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    migration_file VARCHAR(255) NOT NULL UNIQUE,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

## 性能优化

### 1. 索引优化
- `filecodes.code` - 唯一索引，用于快速查找文件
- `filecodes.user_id` - 普通索引，用于用户文件查询
- `uploadchunk.upload_id` - 普通索引，用于分片上传查询
- `keyvalue.key` - 唯一索引，用于配置快速查找

### 2. 存储引擎
使用InnoDB存储引擎，支持：
- 事务处理
- 外键约束
- 行级锁定
- 崩溃恢复

### 3. 字符集
使用utf8mb4字符集，支持：
- 完整的Unicode字符集
- 表情符号
- 特殊字符

## 故障排除

### 1. 连接失败
```bash
# 检查MySQL服务器是否运行
telnet 192.168.9.56 3306

# 检查用户权限
mysql -h 192.168.9.56 -u filebox -p -e "SHOW DATABASES;"
```

### 2. 权限问题
确保filebox用户有足够权限：
```sql
GRANT ALL PRIVILEGES ON filecodebox.* TO 'filebox'@'%';
FLUSH PRIVILEGES;
```

### 3. 字符集问题
检查字符集设置：
```sql
SHOW VARIABLES LIKE 'character_set%';
SHOW VARIABLES LIKE 'collation%';
```

### 4. 表已存在错误
如果表已存在，可以手动删除重新创建：
```sql
DROP TABLE IF EXISTS filecodes;
DROP TABLE IF EXISTS uploadchunk;
DROP TABLE IF EXISTS keyvalue;
DROP TABLE IF EXISTS migrates;
```

## 数据迁移（可选）

如果需要从SQLite迁移现有数据：

1. 导出SQLite数据
2. 转换数据格式
3. 导入到MySQL

注意：这个过程需要根据实际数据情况进行调整。

## 备份策略

### 1. 自动备份
```bash
# 创建备份脚本
mysqldump -h 192.168.9.56 -u filebox -p filecodebox > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 2. 定期备份
建议设置定时任务进行定期备份：

```bash
# 添加到crontab
0 2 * * * /usr/bin/mysqldump -h 192.168.9.56 -u filebox -pYqga!123 filecodebox > /backup/filecodebox_$(date +\%Y\%m\%d).sql
```

## 监控

### 1. 连接数监控
```sql
SHOW STATUS LIKE 'Threads_connected';
```

### 2. 查询性能监控
```sql
SHOW PROCESSLIST;
```

### 3. 慢查询日志
确保MySQL开启了慢查询日志功能。

## 安全建议

1. 使用强密码
2. 限制数据库用户权限
3. 定期更新密码
4. 使用SSL连接（如果可能）
5. 定期备份数据

## 总结

完成以上步骤后，FileCodeBox项目将成功从SQLite迁移到MySQL数据库。新的MySQL配置提供了更好的性能、可扩展性和数据安全性。