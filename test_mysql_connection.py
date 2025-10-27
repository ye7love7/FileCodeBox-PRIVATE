#!/usr/bin/env python3
"""
MySQL连接测试脚本
用于验证数据库连接和配置是否正确
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_mysql_connection():
    """测试MySQL连接"""
    print("正在测试MySQL连接...")
    print("=" * 50)

    try:
        # 导入配置
        from core.settings import DATABASE_CONFIG
        print(f"数据库配置: {DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}")
        print(f"数据库名: {DATABASE_CONFIG['database']}")
        print(f"用户名: {DATABASE_CONFIG['user']}")

        # 测试数据库基础连接（使用PyMySQL）
        print("\n1. 测试数据库基础连接...")
        import pymysql

        try:
            conn = pymysql.connect(
                host=DATABASE_CONFIG['host'],
                port=DATABASE_CONFIG['port'],
                user=DATABASE_CONFIG['user'],
                password=DATABASE_CONFIG['password'],
                database=DATABASE_CONFIG['database'],
                charset=DATABASE_CONFIG['charset']
            )
            print("✅ PyMySQL连接成功!")

            # 测试查询
            with conn.cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()
                print(f"MySQL版本: {version[0]}")

            # 测试表是否存在
            with conn.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                print(f"现有表: {[table[0] for table in tables]}")

            conn.close()

        except Exception as e:
            print(f"❌ PyMySQL连接失败: {e}")
            # 如果PyMySQL失败，我们仍然继续测试Tortoise ORM

        # 测试Tortoise ORM连接
        print("\n2. 测试Tortoise ORM连接...")
        from tortoise import Tortoise
        from core.database import init_db

        # 初始化数据库
        await init_db()
        print("✅ Tortoise ORM连接成功!")
        print("✅ 数据库迁移执行成功!")

        # 测试模型操作
        print("\n3. 测试模型操作...")
        from apps.base.models import FileCodes, KeyValue

        # 检查表结构
        filecodes_count = await FileCodes.all().count()
        print(f"filecodes表记录数: {filecodes_count}")

        keyvalue_count = await KeyValue.all().count()
        print(f"keyvalue表记录数: {keyvalue_count}")

        # 测试插入和查询
        test_kv, created = await KeyValue.get_or_create(
            key="mysql_test",
            defaults={"value": {"status": "success", "timestamp": str(asyncio.get_event_loop().time())}}
        )
        if created:
            print("✅ 成功创建测试记录")
        else:
            print("✅ 测试记录已存在")

        # 清理测试数据
        await test_kv.delete()
        print("✅ 清理测试数据完成")

        # 关闭连接
        await Tortoise.close_connections()

        print("\n" + "=" * 50)
        print("🎉 所有测试通过! MySQL配置正确!")
        print("现在可以启动应用程序: python main.py")

    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保已安装所有依赖:")
        print("pip install -r requirements.txt")
        print("或者运行: python install_mysql_deps.py")
        return False
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("\n请检查以下配置:")
        print("1. MySQL服务器是否运行在 192.168.9.56:33306")
        print("2. 用户名和密码是否正确")
        print("3. 数据库 'filecodebox' 是否存在")
        print("4. 网络连接是否正常")
        return False

    return True


async def show_database_info():
    """显示数据库信息"""
    print("\n数据库信息:")
    print("-" * 30)

    try:
        from core.settings import DATABASE_CONFIG
        from tortoise import Tortoise

        # 使用正确的Tortoise MySQL连接格式
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
                        "charset": DATABASE_CONFIG['charset']
                    }
                }
            },
            "apps": {
                "models": {
                    "models": ["apps.base.models"],
                    "default_connection": "default",
                }
            }
        }

        # 初始化Tortoise
        await Tortoise.init(config=db_config)

        # 获取连接
        conn = Tortoise.get_connection("default")

        # 显示表信息
        async with conn.execute_query("SHOW TABLES") as result:
            tables = result[1]
            print(f"表数量: {len(tables)}")
            for table in tables:
                table_name = table[0]
                print(f"\n📋 表: {table_name}")

                # 获取表结构
                async with conn.execute_query(f"DESCRIBE {table_name}") as columns:
                    cols = columns[1]
                    print("   字段:")
                    for col in cols:
                        print(f"     - {col[0]} ({col[1]}) {col[2]} {col[3]} {col[4]}")

                # 获取记录数
                async with conn.execute_query(f"SELECT COUNT(*) FROM {table_name}") as count:
                    record_count = count[1][0][0]
                    print(f"   记录数: {record_count}")

        await Tortoise.close_connections()

    except Exception as e:
        print(f"获取数据库信息失败: {e}")


async def main():
    """主函数"""
    print("FileCodeBox MySQL连接测试工具")
    print("=" * 50)

    # 执行连接测试
    success = await test_mysql_connection()

    if success:
        # 显示数据库信息
        await show_database_info()

        print("\n" + "=" * 50)
        print("测试完成! 🎉")
        print("\n下一步:")
        print("1. 启动应用: python main.py")
        print("2. 访问: http://localhost:12345")
        print("3. 测试文件上传功能")
    else:
        print("\n" + "=" * 50)
        print("测试失败! 请检查配置后重试")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())