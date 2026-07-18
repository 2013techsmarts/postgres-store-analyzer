import os
import re
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "store")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_SSLMODE = os.getenv("DB_SSLMODE", "disable")
DB_SCHEMA = os.getenv("DB_SCHEMA", "products")

def get_connection():
    """Establish a connection to the PostgreSQL database returning dictionary rows."""
    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        sslmode=DB_SSLMODE,
        row_factory=dict_row
    )

def is_safe_query(query: str) -> bool:
    """
    Check if a SQL query is read-only.
    Strips single-line and block comments, then verifies that the query starts
    with 'select' or 'with' and does not contain mutating DML/DDL keywords.
    """
    # Remove single-line comments starting with --
    query_clean = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
    # Remove multi-line block comments /* ... */
    query_clean = re.sub(r'/\*.*?\*/', '', query_clean, flags=re.DOTALL)
    
    query_clean = query_clean.strip().lower()
    
    # Enforce read-only prefix
    if not (query_clean.startswith("select") or query_clean.startswith("with")):
        return False
        
    # Forbidden mutating/administrative SQL words
    forbidden_keywords = {
        "insert", "update", "delete", "drop", "alter", "truncate", 
        "grant", "revoke", "create", "replace", "upsert", "merge",
        "copy", "vacuum", "analyze", "explain"
    }
    
    # Tokenize to find exact word matches (avoids blocking "created_at" or "updated_by")
    words = set(re.findall(r'\b[a-z]+\b', query_clean))
    
    if forbidden_keywords.intersection(words):
        return False
        
    return True

def list_tables(schema: str = DB_SCHEMA):
    """
    List all tables in the specified schema, including table comments.
    """
    query = """
        SELECT 
            t.table_name,
            obj_description(pgc.oid, 'pg_class') AS description
        FROM 
            information_schema.tables t
        JOIN 
            pg_class pgc ON pgc.relname = t.table_name
        JOIN 
            pg_namespace pgn ON pgn.oid = pgc.relnamespace AND pgn.nspname = t.table_schema
        WHERE 
            t.table_schema = %s
            AND t.table_type = 'BASE TABLE'
        ORDER BY 
            t.table_name;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (schema,))
            return cur.fetchall()

def describe_table(table_name: str, schema: str = DB_SCHEMA):
    """
    Retrieve columns, data types, nullability, defaults, keys, and descriptions for a table.
    """
    # 1. Fetch column definitions and comments
    col_query = """
        SELECT 
            c.column_name,
            c.data_type,
            c.is_nullable,
            c.column_default,
            col_description(pgc.oid, c.ordinal_position) AS description
        FROM 
            information_schema.columns c
        JOIN 
            pg_class pgc ON pgc.relname = c.table_name
        JOIN 
            pg_namespace pgn ON pgn.oid = pgc.relnamespace AND pgn.nspname = c.table_schema
        WHERE 
            c.table_schema = %s
            AND c.table_name = %s
        ORDER BY 
            c.ordinal_position;
    """
    
    # 2. Fetch primary and foreign key constraints
    key_query = """
        SELECT
            tc.constraint_type,
            kcu.column_name,
            ccu.table_name AS foreign_table,
            ccu.column_name AS foreign_column
        FROM 
            information_schema.table_constraints tc
        JOIN 
            information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        LEFT JOIN 
            information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE 
            tc.table_schema = %s
            AND tc.table_name = %s;
    """
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(col_query, (schema, table_name))
            columns = cur.fetchall()
            
            cur.execute(key_query, (schema, table_name))
            constraints = cur.fetchall()
            
    return {
        "table_name": table_name,
        "schema": schema,
        "columns": columns,
        "constraints": constraints
    }

def execute_query(sql_query: str):
    """
    Safely execute a SQL SELECT/WITH query.
    Returns list of rows, or error message.
    """
    if not is_safe_query(sql_query):
        raise ValueError(
            "Query rejected: Only read-only queries starting with 'SELECT' or 'WITH' are permitted. "
            "Mutating operations (INSERT, UPDATE, DELETE, etc.) are blocked."
        )
        
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Set the schema search path so queries don't require the schema prefix
            cur.execute(f"SET search_path TO {DB_SCHEMA}, public;")
            cur.execute(sql_query)
            # Fetch column headers
            columns = [desc[0] for desc in cur.description] if cur.description else []
            rows = cur.fetchall()
            return {
                "columns": columns,
                "row_count": len(rows),
                "rows": rows
            }
