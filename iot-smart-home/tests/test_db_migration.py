"""Existing aether.db files (without is_open) must keep working (Batch 0)."""
import sqlite3


def test_migrate_adds_is_open_to_old_schema():
    import database as db
    conn = sqlite3.connect(":memory:")
    conn.execute("""CREATE TABLE sensor_readings (
        id INTEGER PRIMARY KEY, device_id TEXT, device_name TEXT,
        device_type TEXT, room TEXT, state INTEGER)""")
    db._migrate(conn)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(sensor_readings)")}
    assert "is_open" in cols
    db._migrate(conn)  # idempotent
    conn.close()


def test_fresh_schema_has_is_open():
    import database as db
    conn = sqlite3.connect(":memory:")
    conn.executescript(db.SCHEMA)
    db._migrate(conn)
    cols = {r[1] for r in conn.execute("PRAGMA table_info(sensor_readings)")}
    assert "is_open" in cols
    conn.close()
