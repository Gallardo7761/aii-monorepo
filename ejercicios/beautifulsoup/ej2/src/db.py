import sqlite3
from pathlib import Path


class DBAttr:
    def __init__(self, name, type_, modifier=""):
        self.name = name
        self.type_ = type_
        self.modifier = modifier

    def sql(self):
        parts = [self.name, self.type_]
        if self.modifier:
            parts.append(self.modifier)
        return " ".join(parts)


class DBManager:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, path):
        self.path = Path(path)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row

    def create_table(self, table_name, attributes: list[DBAttr]):
        columns_sql = ",\n    ".join(attr.sql() for attr in attributes)

        query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {columns_sql}
        );
        """

        try:
            with self.conn:
                self.conn.execute(query)
        except Exception as e:
            print("Error creating table:", e)

    def get_all(self, table_name):
        try:
            cursor = self.conn.execute(f"SELECT * FROM {table_name};")
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print("Error selecting:", e)
            return []
        
    def get_singleton(self, singleton_table):
        try:
            cursor = self.conn.execute(f"SELECT * FROM {singleton_table}")
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print("Error selecting:", e)
            return []

    def get_by(self, table_name, column, value):
        try:
            query = f"SELECT * FROM {table_name} WHERE {column} = ?;"
            cursor = self.conn.execute(query, (value,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print("Error selecting:", e)
            return []

    def insert(self, table_name, data: dict):
        keys = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        values = tuple(data.values())

        query = f"""
        INSERT INTO {table_name} ({keys})
        VALUES ({placeholders});
        """

        try:
            with self.conn:
                self.conn.execute(query, values)
        except Exception as e:
            print("Error inserting:", e)

    def update(self, table_name, data: dict, where_column, where_value):
        set_clause = ", ".join(f"{key} = ?" for key in data.keys())
        values = list(data.values())
        values.append(where_value)

        query = f"""
        UPDATE {table_name}
        SET {set_clause}
        WHERE {where_column} = ?;
        """

        try:
            with self.conn:
                self.conn.execute(query, tuple(values))
        except Exception as e:
            print("Error updating:", e)

    def delete(self, table_name, where_column, where_value):
        query = f"DELETE FROM {table_name} WHERE {where_column} = ?;"

        try:
            with self.conn:
                self.conn.execute(query, (where_value,))
        except Exception as e:
            print("Error deleting:", e)
            
    def clear(self, table_name):
        query = f"DELETE FROM {table_name};"
        
        try:
            with self.conn:
                self.conn.execute(query)
        except Exception as e:
            print("Error clearing table: ", e)

    def exists(self, table_name, where_column, where_value):
        query = f"SELECT 1 FROM {table_name} WHERE {where_column} = ? LIMIT 1;"

        try:
            cursor = self.conn.execute(query, (where_value,))
            return cursor.fetchone() is not None
        except Exception as e:
            print("Error checking existence:", e)
            return False

    def count(self, table_name):
        try:
            cursor = self.conn.execute(f"SELECT COUNT(*) as total FROM {table_name};")
            return cursor.fetchone()["total"]
        except Exception as e:
            print("Error counting:", e)
            return 0

    def close(self):
        self.conn.close()