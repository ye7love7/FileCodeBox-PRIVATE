#!/usr/bin/env python3
"""
重置MySQL迁移记录脚本
用于清理migrates表，重新执行迁移
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def reset_migrations():
    """重置迁移记录"""
    print("重置MySQL迁移记录...")
    print("=" * 50)
    
    try:
        from core.settings import DATABASE_CONFIG
        from tortoise import Tortoise
        
        # 初始化数据库连接
        db_config = {
            "connections": {
                "default": {
                    "engine": "tortoise.backends.mysql",
                    "credentials": {
                        "host": DATABASE_CONFIG['host'],
                        "port": DATABASE_CONFIG['port'],
                        "user": DATABASE_CONFIG['user'],
                        "password": DATABASE_CONFIG['password'],
                        "database": DATABASE_CONFIG['database'],
                        "charset": DATABASE_CONFIG['charset'],
                        "echo": False
                    }
                }
            },
            "apps": {
                "models": {
                    "models": ["apps.base.models"],
                    "default_connection": "default",
                }
            },
            "use_tz": False,
            "timezone": "Asia/Shanghai"
        }
        
        await Tortoise.init(config=db_config)
        
        # 清理migrates表
        print("1. 清理migrates表...")
        await Tortoise.get_connection("default").execute_script("""
            DROP TABLE IF EXISTS migrates;
        """)
        print("✅ migrates表已删除")
        
        # 重新创建migrates表
        print("2. 重新创建migrates表...")
        await Tortoise.get_connection("default").execute_script("""
            CREATE TABLE migrates (
                id INT AUTO_INCREMENT PRIMARY KEY,
                migration_file VARCHAR(255) NOT NULL UNIQUE,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✅ migrates表已重新创建")
        
        # 删除可能存在的表（如果迁移失败留下的）
        print("3. 清理可能存在的表...")
        tables_to_drop = ['filecodes', 'keyvalue', 'uploadchunk']
        for table in tables_to_drop:
            try:
                await Tortoise.get_connection("default").execute_script(f"DROP TABLE IF EXISTS {table}")
                print(f"✅ 表 {table} 已清理")
            except Exception as e:
                print(f"⚠️  清理表 {table} 时出现警告: {e}")
        
        await Tortoise.close_connections()
        
        print("\n" + "=" * 50)
        print("🎉 迁移记录重置完成!")
        print("现在可以重新运行: python test_mysql_connection.py")
        
    except Exception as e:
        print(f"❌ 重置失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(reset_migrations())
