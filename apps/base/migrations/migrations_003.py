from tortoise import connections


async def add_user_id_to_filecodes():
    conn = connections.get("default")
    await conn.execute_script(
        """
        ALTER TABLE filecodes ADD COLUMN user_id VARCHAR(255);
        ALTER TABLE uploadchunk ADD COLUMN user_id VARCHAR(255);
        CREATE INDEX idx_filecodes_user_id ON filecodes (user_id);
        CREATE INDEX idx_uploadchunk_user_id ON uploadchunk (user_id);
        """
    )


async def migrate():
    await add_user_id_to_filecodes()