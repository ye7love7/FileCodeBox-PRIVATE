from tortoise import connections


async def create_file_codes_table():
    conn = connections.get("default")
    await conn.execute_script(
        """
        CREATE TABLE IF NOT EXISTS filecodes
        (
            id             INT AUTO_INCREMENT PRIMARY KEY,
            code           VARCHAR(255) NOT NULL UNIQUE,
            prefix         VARCHAR(255) DEFAULT '' NOT NULL,
            suffix         VARCHAR(255) DEFAULT '' NOT NULL,
            uuid_file_name VARCHAR(255),
            file_path      VARCHAR(255),
            size           INT DEFAULT 0 NOT NULL,
            text           TEXT,
            expired_at     TIMESTAMP NULL,
            expired_count  INT DEFAULT 0 NOT NULL,
            used_count     INT DEFAULT 0 NOT NULL,
            created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            INDEX idx_filecodes_code (code)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    )


async def create_key_value_table():
    conn = connections.get("default")
    await conn.execute_script(
        """
        CREATE TABLE IF NOT EXISTS keyvalue
        (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            `key`      VARCHAR(255) NOT NULL UNIQUE,
            value      JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            INDEX idx_keyvalue_key (`key`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    )


async def migrate():
    await create_file_codes_table()
    await create_key_value_table()
