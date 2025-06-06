#!/usr/bin/env python3
"""
Database Schema Inspector for DB-GPT
This script helps you inspect your database schema to identify missing columns
and understand the structure that DB-GPT is working with.
"""

import sys
import json
from typing import Dict, List, Any

def inspect_database_schema(db_name: str = None):
    """Inspect database schema and show detailed information."""
    try:
        # Import DB-GPT components
        from dbgpt import SystemApp
        from dbgpt_serve.datasource.manages import ConnectorManager
        
        # Initialize system app
        system_app = SystemApp()
        
        # Get database manager
        db_manager = ConnectorManager.get_instance(system_app)
        
        if db_name:
            databases = [db_name]
        else:
            # Get all available databases
            db_list = db_manager.get_db_list()
            databases = [db["db_name"] for db in db_list]
            print(f"Available databases: {databases}")
        
        for db_name in databases:
            print(f"\n{'='*60}")
            print(f"INSPECTING DATABASE: {db_name}")
            print(f"{'='*60}")
            
            try:
                # Get database connector
                connector = db_manager.get_connector(db_name)
                
                # Get basic database info
                print(f"Database Type: {connector.db_type}")
                print(f"Database Dialect: {connector.dialect}")
                
                # Get table names
                table_names = connector.get_table_names()
                print(f"Number of tables: {len(table_names)}")
                print(f"Tables: {', '.join(table_names)}")
                
                # Inspect each table
                for table_name in table_names:
                    print(f"\n{'-'*40}")
                    print(f"TABLE: {table_name}")
                    print(f"{'-'*40}")
                    
                    try:
                        # Get columns using different methods
                        print("Columns (via get_columns):")
                        columns = connector.get_columns(table_name)
                        for col in columns:
                            print(f"  - {col.get('name', 'N/A')} ({col.get('type', 'N/A')})")
                            if col.get('comment'):
                                print(f"    Comment: {col['comment']}")
                    except Exception as e:
                        print(f"  Error getting columns via get_columns: {e}")
                        
                        # Fallback to simple fields
                        try:
                            print("Columns (via get_simple_fields):")
                            fields = connector.get_simple_fields(table_name)
                            for field in fields:
                                print(f"  - {field}")
                        except Exception as e2:
                            print(f"  Error getting simple fields: {e2}")
                    
                    # Get table comment
                    try:
                        comment = connector.get_table_comment(table_name)
                        if comment and comment.get('text'):
                            print(f"Table Comment: {comment['text']}")
                    except Exception as e:
                        print(f"  Could not get table comment: {e}")
                    
                    # Get indexes
                    try:
                        indexes = connector.get_indexes(table_name)
                        if indexes:
                            print("Indexes:")
                            for idx in indexes:
                                print(f"  - {idx}")
                    except Exception as e:
                        print(f"  Could not get indexes: {e}")
                
                # Test table_simple_info method
                print(f"\n{'-'*40}")
                print("TABLE SIMPLE INFO (used by DB-GPT):")
                print(f"{'-'*40}")
                try:
                    simple_info = connector.table_simple_info()
                    for info in simple_info:
                        print(f"  {info}")
                except Exception as e:
                    print(f"Error getting table simple info: {e}")
                    
            except Exception as e:
                print(f"Error connecting to database {db_name}: {e}")
                
    except Exception as e:
        print(f"Error initializing DB-GPT components: {e}")
        print("Make sure you're running this from the DB-GPT directory with proper configuration.")


def check_specific_table(db_name: str, table_name: str):
    """Check a specific table for common issues."""
    try:
        from dbgpt import SystemApp
        from dbgpt_serve.datasource.manages import ConnectorManager
        
        system_app = SystemApp()
        db_manager = ConnectorManager.get_instance(system_app)
        connector = db_manager.get_connector(db_name)
        
        print(f"Checking table '{table_name}' in database '{db_name}':")
        
        # Check for common date/time columns
        date_columns = []
        columns = connector.get_columns(table_name)
        
        for col in columns:
            col_name = col.get('name', '').lower()
            col_type = str(col.get('type', '')).lower()
            
            if any(keyword in col_name for keyword in ['date', 'time', 'created', 'updated', 'modified']):
                date_columns.append(col)
            elif any(keyword in col_type for keyword in ['date', 'time', 'timestamp']):
                date_columns.append(col)
        
        if date_columns:
            print("Found potential date/time columns:")
            for col in date_columns:
                print(f"  - {col['name']} ({col['type']})")
        else:
            print("No obvious date/time columns found.")
            print("You may need to add an 'order_date' column to your orders table.")
            
        # Show all columns
        print(f"\nAll columns in {table_name}:")
        for col in columns:
            print(f"  - {col['name']} ({col['type']})")
            
    except Exception as e:
        print(f"Error checking table: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if len(sys.argv) == 3:
            # Check specific table
            db_name, table_name = sys.argv[1], sys.argv[2]
            check_specific_table(db_name, table_name)
        else:
            # Inspect specific database
            db_name = sys.argv[1]
            inspect_database_schema(db_name)
    else:
        # Inspect all databases
        inspect_database_schema() 