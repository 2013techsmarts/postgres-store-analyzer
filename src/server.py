import os
import sys
from fastmcp import FastMCP

# Add the current directory to sys.path to resolve imports cleanly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import (
    list_tables as db_list_tables,
    describe_table as db_describe_table,
    execute_query as db_execute_query,
    DB_SCHEMA
)

# Initialize FastMCP Server
mcp = FastMCP(
    name="PostgresStoreAnalyzer",
    version="1.0.0",
    instructions="MCP server to interact with the PostgreSQL store database for analysis"
)

@mcp.tool()
def list_tables() -> str:
    """
    List all tables available in the current PostgreSQL database schema.
    Returns table names and comments/descriptions. Use this first to explore what tables exist.
    """
    try:
        tables = db_list_tables()
        if not tables:
            return f"No tables found in schema '{DB_SCHEMA}'."
            
        result = [
            f"Tables in schema '{DB_SCHEMA}':",
            "",
            f"| {'Table Name':<25} | {'Description':<50} |",
            f"| {'-'*25} | {'-'*50} |"
        ]
        
        for t in tables:
            name = t.get("table_name", "")
            desc = t.get("description", "") or "No description available."
            result.append(f"| {name:<25} | {desc:<50} |")
            
        return "\n".join(result)
    except Exception as e:
        return f"Error listing tables: {str(e)}"

@mcp.tool()
def describe_table(table_name: str) -> str:
    """
    Retrieve columns, data types, constraints, and descriptions for a specific table.
    Use this to understand table columns and join relationships before writing queries.
    
    Args:
        table_name (str): The name of the table to describe (e.g. 'items', 'orders')
    """
    try:
        details = db_describe_table(table_name)
        if not details or not details["columns"]:
            return f"Table '{table_name}' not found or contains no columns in schema '{DB_SCHEMA}'."
            
        result = [
            f"### Table Structure: {DB_SCHEMA}.{table_name}",
            "",
            "#### Columns",
            f"| {'Column Name':<25} | {'Data Type':<20} | {'Nullable':<10} | {'Default':<20} | {'Description':<40} |",
            f"| {'-'*25} | {'-'*20} | {'-'*10} | {'-'*20} | {'-'*40} |"
        ]
        
        for col in details["columns"]:
            name = col.get("column_name", "")
            dtype = col.get("data_type", "")
            null = col.get("is_nullable", "")
            default = col.get("column_default", "") or "NULL"
            desc = col.get("description", "") or "No description."
            
            # Format display strings
            default_str = str(default)
            if len(default_str) > 20:
                default_str = default_str[:17] + "..."
                
            result.append(f"| {name:<25} | {dtype:<20} | {null:<10} | {default_str:<20} | {desc:<40} |")
            
        constraints = details["constraints"]
        if constraints:
            result.extend([
                "",
                "#### Constraints & Keys",
                f"| {'Type':<15} | {'Column Name':<20} | {'References Table':<20} | {'References Column':<20} |",
                f"| {'-'*15} | {'-'*20} | {'-'*20} | {'-'*20} |"
            ])
            for c in constraints:
                ctype = c.get("constraint_type", "")
                col = c.get("column_name", "")
                ftable = c.get("foreign_table", "") or "N/A"
                fcol = c.get("foreign_column", "") or "N/A"
                result.append(f"| {ctype:<15} | {col:<20} | {ftable:<20} | {fcol:<20} |")
                
        return "\n".join(result)
    except Exception as e:
        return f"Error describing table '{table_name}': {str(e)}"

@mcp.tool()
def execute_query(sql_query: str) -> str:
    """
    Execute a read-only SQL query (SELECT or WITH statements) against the store database.
    Note: The schema search path is automatically set to 'products', so you can query tables 
    directly (e.g. 'SELECT * FROM items' or 'SELECT * FROM customers').
    Only read-only operations are allowed.
    
    Args:
        sql_query (str): The SQL query string to execute.
    """
    try:
        res = db_execute_query(sql_query)
        columns = res["columns"]
        rows = res["rows"]
        row_count = res["row_count"]
        
        if row_count == 0:
            return "Query completed successfully. 0 rows returned."
            
        result = [
            f"#### Query Results ({row_count} rows returned):",
            ""
        ]
        
        # Calculate dynamic column widths for markdown formatting (max width 50)
        col_widths = {c: max(len(c), 4) for c in columns}
        sample_rows = rows[:20]
        for row in sample_rows:
            for c in columns:
                val_str = str(row.get(c, ""))
                if len(val_str) > col_widths[c]:
                    col_widths[c] = min(len(val_str), 50)
                    
        # Generate markdown headers
        headers_str = "| " + " | ".join([f"{c:<{col_widths[c]}}" for c in columns]) + " |"
        divider_str = "| " + " | ".join(["-" * col_widths[c] for c in columns]) + " |"
        result.append(headers_str)
        result.append(divider_str)
        
        # Limit rows displayed in text output to avoid token limits
        display_limit = 100
        display_rows = rows[:display_limit]
        for row in display_rows:
            row_vals = []
            for c in columns:
                val = row.get(c)
                if val is None:
                    val_str = "NULL"
                else:
                    val_str = str(val)
                # Clean line breaks to keep table layout intact
                val_str = val_str.replace("\n", " ").replace("\r", "")
                if len(val_str) > col_widths[c]:
                    val_str = val_str[:col_widths[c]-3] + "..."
                row_vals.append(f"{val_str:<{col_widths[c]}}")
            result.append("| " + " | ".join(row_vals) + " |")
            
        if row_count > display_limit:
            result.extend([
                "",
                f"*Note: Output has been truncated to first {display_limit} rows. The query returned {row_count} rows total.*"
            ])
            
        return "\n".join(result)
    except Exception as e:
        return f"Error executing query: {str(e)}"

if __name__ == "__main__":
    # Start the FastMCP server (default runs on stdio transport)
    mcp.run()
