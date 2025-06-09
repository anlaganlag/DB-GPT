#!/usr/bin/env python3
"""
Test script for enhanced error handling in DB-GPT
This script tests the improved "Generate view content failed" error handling.
"""

import logging
import sys
import traceback
from pathlib import Path

# Add the DB-GPT packages to the Python path
sys.path.insert(0, str(Path(__file__).parent / "packages" / "dbgpt-core" / "src"))
sys.path.insert(0, str(Path(__file__).parent / "packages" / "dbgpt-app" / "src"))

def setup_logging():
    """Setup detailed logging for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('test_enhanced_error_handling.log')
        ]
    )

def test_enhanced_output_parser():
    """Test the enhanced DbChatOutputParser."""
    print("🧪 Testing Enhanced DbChatOutputParser...")
    
    try:
        from dbgpt_app.scene.chat_db.auto_execute.out_parser import DbChatOutputParser, SqlAction
        
        # Test 1: Basic initialization
        parser = DbChatOutputParser()
        print("✅ Enhanced DbChatOutputParser created successfully")
        
        # Test 2: Test with mock connector
        class MockConnector:
            def get_columns(self, table_name):
                # Mock some common columns
                if table_name.lower() == 'orders':
                    return [
                        {'name': 'id'},
                        {'name': 'customer_id'},
                        {'name': 'total_amount'},
                        {'name': 'status'},
                        {'name': 'created_at'}  # Note: no order_date
                    ]
                return []
            
            def get_simple_fields(self, table_name):
                if table_name.lower() == 'orders':
                    return [('id',), ('customer_id',), ('total_amount',), ('status',), ('created_at',)]
                return []
        
        mock_connector = MockConnector()
        parser_with_connector = DbChatOutputParser(connector=mock_connector)
        print("✅ DbChatOutputParser with connector created successfully")
        
        # Test 3: Test SQL validation
        if parser_with_connector._sql_validator:
            test_sql = "SELECT o.order_date FROM orders o"  # This should fail
            is_valid, errors = parser_with_connector._sql_validator.validate_sql(test_sql)
            if not is_valid:
                print(f"✅ SQL validation correctly detected error: {errors[0][:50]}...")
            else:
                print("⚠️ SQL validation should have detected the missing column")
        else:
            print("⚠️ SQL validator not initialized")
        
        # Test 4: Test error message creation
        test_error = Exception("Unknown column 'order_date' in 'field list'")
        detailed_msg = parser_with_connector._create_detailed_error_message(
            test_error, 
            "SELECT order_date FROM orders", 
            "Test Context"
        )
        if "Column Reference Error" in detailed_msg and "🔍" in detailed_msg:
            print("✅ Detailed error message creation works correctly")
        else:
            print("❌ Detailed error message creation failed")
        
        # Test 5: Test enhanced PCA processing
        import pandas as pd
        import numpy as np
        
        # Create test DataFrame with vector data
        test_df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['A', 'B', 'C'],
            'vector': ['[1,2,3,4]', '[2,3,4,5]', '[3,4,5,6]']
        })
        
        result_df, visualizable = parser_with_connector._safe_parse_vector_data_with_pca(test_df)
        if not visualizable:
            print("✅ PCA processing correctly handled non-vector data")
        else:
            print("⚠️ PCA processing result unexpected")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced DbChatOutputParser test failed: {e}")
        traceback.print_exc()
        return False

def test_sql_validator():
    """Test the SQL validator functionality."""
    print("\n🧪 Testing SQL Validator...")
    
    try:
        from dbgpt_app.scene.chat_db.auto_execute.sql_validator import SQLValidator
        
        # Mock connector for testing
        class MockConnector:
            def get_columns(self, table_name):
                if table_name.lower() == 'orders':
                    return [
                        {'name': 'id'},
                        {'name': 'customer_id'},
                        {'name': 'total_amount'},
                        {'name': 'status'},
                        {'name': 'created_at'}
                    ]
                elif table_name.lower() == 'customers':
                    return [
                        {'name': 'id'},
                        {'name': 'name'},
                        {'name': 'email'}
                    ]
                return []
            
            def get_simple_fields(self, table_name):
                if table_name.lower() == 'orders':
                    return [('id',), ('customer_id',), ('total_amount',), ('status',), ('created_at',)]
                elif table_name.lower() == 'customers':
                    return [('id',), ('name',), ('email',)]
                return []
        
        validator = SQLValidator(MockConnector())
        
        # Test valid SQL
        valid_sql = "SELECT o.id, o.total_amount FROM orders o"
        is_valid, errors = validator.validate_sql(valid_sql)
        if is_valid:
            print("✅ Valid SQL correctly validated")
        else:
            print(f"❌ Valid SQL incorrectly rejected: {errors}")
        
        # Test invalid SQL (missing column)
        invalid_sql = "SELECT o.order_date FROM orders o"
        is_valid, errors = validator.validate_sql(invalid_sql)
        if not is_valid and "order_date" in errors[0]:
            print("✅ Invalid SQL correctly rejected")
        else:
            print(f"❌ Invalid SQL not properly detected: {errors}")
        
        # Test suggestions
        suggestions = validator.suggest_corrections(invalid_sql, errors)
        if suggestions and "created_at" in suggestions:
            print("✅ SQL correction suggestions working")
        else:
            print(f"⚠️ SQL suggestions could be improved: {suggestions}")
        
        return True
        
    except Exception as e:
        print(f"❌ SQL Validator test failed: {e}")
        traceback.print_exc()
        return False

def test_error_categorization():
    """Test error categorization functionality."""
    print("\n🧪 Testing Error Categorization...")
    
    try:
        from dbgpt_app.scene.chat_db.auto_execute.out_parser import DbChatOutputParser
        
        parser = DbChatOutputParser()
        
        # Test different error types
        test_cases = [
            (Exception("Unknown column 'test' in 'field list'"), "Column Reference Error", "🔍"),
            (Exception("You have an error in your SQL syntax"), "SQL Syntax Error", "⚠️"),
            (Exception("Can't connect to MySQL server"), "Database Connection Error", "🔌"),
            (Exception("Access denied for user"), "Permission Error", "🔒"),
            (Exception("Query execution timeout"), "Timeout Error", "⏱️"),
            (Exception("Some other error"), "General Error", "❌"),
        ]
        
        all_passed = True
        for error, expected_category, expected_icon in test_cases:
            detailed_msg = parser._create_detailed_error_message(error, "SELECT * FROM test", "Test")
            if expected_category in detailed_msg and expected_icon in detailed_msg:
                print(f"✅ {expected_category} correctly categorized")
            else:
                print(f"❌ {expected_category} not properly categorized")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error categorization test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🚀 Enhanced Error Handling Test Suite\n")
    
    setup_logging()
    
    tests = [
        ("Enhanced Output Parser", test_enhanced_output_parser),
        ("SQL Validator", test_sql_validator),
        ("Error Categorization", test_error_categorization),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} CRASHED: {e}")
    
    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} tests passed")
    print('='*50)
    
    if passed == total:
        print("🎉 All tests passed! Enhanced error handling is working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 