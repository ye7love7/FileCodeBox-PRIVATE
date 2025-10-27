#!/usr/bin/env python3
"""
简化版MySQL连接测试脚本
只使用Tortoise ORM进行测试，确保与项目配置一致
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_mysql_connection():
    """测试MySQL连接"""
    print("FileCodeBox MySQL连接测试")
    print("=" * 50)

    try:
        # 导入配置
        from core.settings import DATABASE_CONFIG
        print(f"数据库配置: {DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}")
        print(f"数据库名: {DATABASE_CONFIG['database']}")
        print(f"用户名: {DATABASE_CONFIG['user']}")

        # 直接测试Tortoise ORM连接
        print("\n1. 测试Tortoise ORM连接...")
        from tortoise import Tortoise
        from core.database import init_db

        # 初始化数据库
        await init_db()
        print("✅ Tortoise ORM连接成功!")
        print("✅ 数据库迁移执行成功!")

        # 测试模型操作
        print("\n2. 测试模型操作...")
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

        # 显示表信息
        print("\n3. 显示数据库表信息...")
        conn = Tortoise.get_connection("default")

        async with conn.execute_query("SHOW TABLES") as result:
            tables = result[1]
            print(f"表数量: {len(tables)}")
            for table in tables:
                table_name = table[0]
                print(f"\n📋 表: {table_name}")

                # 获取记录数
                async with conn.execute_query(f"SELECT COUNT(*) FROM {table_name}") as count:
                    record_count = count[1][0][0]
                    print(f"   记录数: {record_count}")

        # 关闭连接
        await Tortoise.close_connections()

        print("\n" + "=" * 50)
        print("🎉 所有测试通过! MySQL配置正确!")
        print("现在可以启动应用程序: python main.py")

        return True

    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("\n请安装所需依赖:")
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
        print("5. 是否已安装PyMySQL: pip install PyMySQL==1.1.0")
        return False


async def main():
    """主函数"""
    success = await test_mysql_connection()

    if success:
        print("\n下一步:")
        print("1. 启动应用: python main.py")
        print("2. 访问: http://localhost:12345")
        print("3. 测试文件上传功能")
    else:
        print("\n测试失败! 请检查配置后重试")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())