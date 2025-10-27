#!/usr/bin/env python3
"""
测试用户ID功能的脚本
运行前请确保服务已启动: python main.py
"""

import asyncio
import httpx
import json
from pathlib import Path


BASE_URL = "http://localhost:8000"


async def test_text_upload_with_user():
    """测试带用户ID的文本上传"""
    print("测试带用户ID的文本上传...")

    async with httpx.AsyncClient() as client:
        # 准备测试数据
        data = {
            "text": "这是一个测试文本内容，用于验证用户ID功能",
            "expire_value": 1,
            "expire_style": "day",
            "user_id": "test_user_123"
        }

        try:
            response = await client.post(f"{BASE_URL}/share/text/", data=data)
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.json()}")

            if response.status_code == 200:
                result = response.json()
                if "detail" in result and "code" in result["detail"]:
                    code = result["detail"]["code"]
                    print(f"✅ 文本上传成功，取件码: {code}")
                    return code
            print("❌ 文本上传失败")
        except Exception as e:
            print(f"❌ 请求失败: {e}")
    return None


async def test_file_upload_with_user():
    """测试带用户ID的文件上传"""
    print("\n测试带用户ID的文件上传...")

    # 创建临时测试文件
    test_file_path = "test_upload.txt"
    test_content = "这是一个测试文件内容，用于验证用户ID功能\n用户ID将与此文件关联"

    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(test_content)

    async with httpx.AsyncClient() as client:
        try:
            with open(test_file_path, "rb") as f:
                files = {"file": ("test_upload.txt", f, "text/plain")}
                data = {
                    "expire_value": 1,
                    "expire_style": "day",
                    "user_id": "test_user_123"
                }

                response = await client.post(f"{BASE_URL}/share/file/", files=files, data=data)
                print(f"响应状态码: {response.status_code}")
                print(f"响应内容: {response.json()}")

                if response.status_code == 200:
                    result = response.json()
                    if "detail" in result and "code" in result["detail"]:
                        code = result["detail"]["code"]
                        print(f"✅ 文件上传成功，取件码: {code}")
                        return code
                print("❌ 文件上传失败")
        except Exception as e:
            print(f"❌ 请求失败: {e}")

    # 清理临时文件
    if Path(test_file_path).exists():
        Path(test_file_path).unlink()

    return None


async def test_user_file_list():
    """测试用户文件列表查询"""
    print("\n测试用户文件列表查询...")

    async with httpx.AsyncClient() as client:
        data = {
            "user_id": "test_user_123",
            "page": 1,
            "page_size": 10
        }

        try:
            response = await client.post(
                f"{BASE_URL}/share/user/files/",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

            if response.status_code == 200:
                result = response.json()
                if "detail" in result:
                    files = result["detail"].get("files", [])
                    pagination = result["detail"].get("pagination", {})
                    print(f"✅ 查询成功，共找到 {pagination.get('total', 0)} 个文件")
                    for file_info in files:
                        print(f"  - 文件名: {file_info.get('name')}, 取件码: {file_info.get('code')}")
                    return True
            print("❌ 查询失败")
        except Exception as e:
            print(f"❌ 请求失败: {e}")

    return False


async def main():
    """主测试函数"""
    print("开始测试用户ID功能...")
    print("=" * 50)

    # 测试文本上传
    text_code = await test_text_upload_with_user()

    # 测试文件上传
    file_code = await test_file_upload_with_user()

    # 等待一下确保数据已保存
    await asyncio.sleep(1)

    # 测试用户文件列表查询
    await test_user_file_list()

    print("\n" + "=" * 50)
    print("测试完成！")


if __name__ == "__main__":
    print("请确保服务已启动: python main.py")
    print("然后运行此测试脚本")
    asyncio.run(main())