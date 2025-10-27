-- MySQL数据库初始化脚本
-- 使用方法: mysql -h 192.168.9.56 -u filebox -p < mysql_init.sql

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS filecodebox
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE filecodebox;

-- 创建migrations表
CREATE TABLE IF NOT EXISTS migrates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    migration_file VARCHAR(255) NOT NULL UNIQUE,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 显示创建的数据库
SHOW DATABASES LIKE 'filecodebox';

-- 显示表结构
SHOW TABLES;