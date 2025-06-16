import sqlite3
import google.generativeai as genai
from typing import Dict, List, Tuple, Optional, Any
import json
import re
import logging
from datetime import datetime
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryType(Enum):
    """Enumeration for different types of queries"""
    SIMPLE_LOOKUP = "simple_lookup"
    COMPLEX_ANALYSIS = "complex_analysis"
    RELATIONSHIP = "relationship"
    TREND_ANALYSIS = "trend_analysis"
    COMPARISON = "comparison"

class QueryProcessor:
    """
    Main class for processing natural language queries into SQL
    and determining if business summaries are needed
    """
    
    def __init__(self, database_path: str, gemini_api_key: str = None):
        """
        Initialize the Query Processor
        
        Args:
            database_path: Path to SQLite database
            gemini_api_key: Gemini API key (optional if configured globally)
        """
        self.db_path = database_path
        
        # Configure Gemini API if key provided
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
        
        # Initialize Gemini model
        try:
            self.model = genai.GenerativeModel('gemini-pro')
            logger.info("Gemini model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            raise
        
        # Cache for database schema
        self._schema_cache = None
        self._last_schema_update = None
        
    def get_database_schema(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get comprehensive database schema information
        
        Args:
            force_refresh: Force refresh of schema cache
            
        Returns:
            Dictionary containing complete schema information
        """
        if self._schema_cache and not force_refresh:
            return self._schema_cache
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            schema_info = {
                'tables': {},
                'relationships': {},
                'indexes': {},
                'views': {}
            }
            
            # Get all tables
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            
            table_names = [row[0] for row in cursor.fetchall()]
            
            for table in table_names:
                # Get column information
                cursor.execute(f"PRAGMA table_info('{table}')")
                columns = cursor.fetchall()
                
                # Get foreign key information
                cursor.execute(f"PRAGMA foreign_key_list('{table}')")
                foreign_keys = cursor.fetchall()
                
                # Get sample data
                cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                sample_data = cursor.fetchall()
                
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                
                schema_info['tables'][table] = {
                    'columns': [
                        {
                            'name': col[1],
                            'type': col[2],
                            'not_null': bool(col[3]),
                            'default_value': col[4],
                            'primary_key': bool(col[5])
                        } for col in columns
                    ],
                    'foreign_keys': [
                        {
                            'column': fk[3],
                            'references_table': fk[2],
                            'references_column': fk[4]
                        } for fk in foreign_keys
                    ],
                    'sample_data': sample_data,
                    'row_count': row_count
                }
            
            conn.close()
            
            # Cache the schema
            self._schema_cache = schema_info
            self._last_schema_update = datetime.now()
            
            logger.info(f"Schema loaded for {len(table_names)} tables")
            return schema_info
            
        except Exception as e:
            logger.error(f"Error loading database schema: {e}")
            return {'tables': {}, 'relationships': {}, 'indexes': {}, 'views': {}}
    
    def analyze_query_intent(self, user_query: str) -> Dict[str, Any]:
        """
        Analyze user query to determine intent and complexity
        
        Args:
            user_query: Natural language query from user
            
        Returns:
            Dictionary containing query analysis results
        """
        query_lower = user_query.lower()
        
        # Keywords that indicate different query types
        analysis_keywords = [
            'analyze', 'analysis', 'relationship', 'relation', 'correlation',
            'trend', 'pattern', 'insight', 'impact', 'effect', 'influence',
            'compare', 'comparison', 'versus', 'vs', 'difference', 'performance',
            'over time', 'yearly', 'monthly', 'growth', 'decline'
        ]
        
        simple_keywords = [
            'show', 'list', 'display', 'get', 'find', 'top', 'bottom',
            'count', 'sum', 'total', 'average', 'max', 'min'
        ]
        
        aggregation_keywords = [
            'group by', 'order by', 'sum', 'count', 'average', 'max', 'min',
            'total', 'aggregate'
        ]
        
        # Determine query type
        analysis_score = sum(1 for keyword in analysis_keywords if keyword in query_lower)
        simple_score = sum(1 for keyword in simple_keywords if keyword in query_lower)
        aggregation_score = sum(1 for keyword in aggregation_keywords if keyword in query_lower)
        
        # Classify query type
        if analysis_score > 0:
            query_type = QueryType.COMPLEX_ANALYSIS
            needs_summary = True
        elif 'relation' in query_lower or 'relationship' in query_lower:
            query_type = QueryType.RELATIONSHIP
            needs_summary = True
        elif aggregation_score > simple_score and aggregation_score > 1:
            query_type = QueryType.TREND_ANALYSIS
            needs_summary = True
        elif 'compare' in query_lower or 'versus' in query_lower:
            query_type = QueryType.COMPARISON
            needs_summary = True
        else:
            query_type = QueryType.SIMPLE_LOOKUP
            needs_summary = False
        
        return {
            'query_type': query_type,
            'needs_summary': needs_summary,
            'analysis_score': analysis_score,
            'simple_score': simple_score,
            'aggregation_score': aggregation_score,
            'confidence': max(analysis_score, simple_score, aggregation_score) / 10
        }
    
    def generate_sql_query(self, user_query: str, schema_context: str = None) -> Tuple[bool, str]:
        """
        Generate SQL query from natural language using Gemini API
        
        Args:
            user_query: Natural language query
            schema_context: Database schema context (optional)
            
        Returns:
            Tuple of (needs_summary: bool, sql_query: str)
        """
        # Get schema if not provided
        if not schema_context:
            schema_info = self.get_database_schema()
            schema_context = self._format_schema_for_prompt(schema_info)
        
        # Analyze query intent
        intent_analysis = self.analyze_query_intent(user_query)
        
        prompt = f"""
You are an expert SQL generator. Your task is to:
1. Determine if a business summary is needed for the query
2. Generate accurate SQL based on the provided schema

DATABASE SCHEMA:
{schema_context}

QUERY CLASSIFICATION RULES:
- Return "yes" for business summary if query involves:
  * Analysis, insights, or complex relationships
  * Trends, patterns, or performance evaluation
  * Comparisons or correlations
  * Questions asking "why", "how", or requesting interpretation

- Return "no" for business summary if query is:
  * Simple data retrieval (show, list, display)
  * Basic filtering or sorting
  * Simple counts or totals without analysis
  * Straightforward lookups

USER QUERY: "{user_query}"

RESPONSE FORMAT:
Line 1: "yes" or "no" (needs business summary)
Line 2+: Valid SQL query only (no explanations, no markdown)

Generate response:"""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            lines = response_text.split('\n')
            needs_summary_line = lines[0].strip().lower()
            needs_summary = needs_summary_line == 'yes'
            
            # Extract SQL (everything after first line)
            sql_lines = lines[1:]
            sql_query = '\n'.join(sql_lines).strip()
            
            # Clean SQL query
            sql_query = self._clean_sql_query(sql_query)
            
            # Override with intent analysis if confidence is high
            if intent_analysis['confidence'] > 0.7:
                needs_summary = intent_analysis['needs_summary']
            
            logger.info(f"Generated SQL query, needs_summary: {needs_summary}")
            return needs_summary, sql_query
            
        except Exception as e:
            logger.error(f"Error generating SQL query: {e}")
            return False, f"-- Error: Unable to generate SQL query"
    
    def _clean_sql_query(self, sql_query: str) -> str:
        """Clean and format SQL query"""
        # Remove markdown formatting
        sql_query = re.sub(r'^```sql\s*', '', sql_query, flags=re.MULTILINE)
        sql_query = re.sub(r'^```\s*$', '', sql_query, flags=re.MULTILINE)
        sql_query = re.sub(r'```', '', sql_query)
        
        # Remove extra whitespace
        sql_query = '\n'.join(line.strip() for line in sql_query.split('\n') if line.strip())
        
        return sql_query.strip()
    
    def _format_schema_for_prompt(self, schema_info: Dict[str, Any]) -> str:
        """Format schema information for LLM prompt"""
        formatted_schema = []
        
        for table_name, table_info in schema_info['tables'].items():
            formatted_schema.append(f"\nTABLE: {table_name}")
            formatted_schema.append(f"Rows: {table_info['row_count']}")
            
            # Columns
            columns = []
            for col in table_info['columns']:
                col_str = f"{col['name']} ({col['type']})"
                if col['primary_key']:
                    col_str += " [PRIMARY KEY]"
                if col['not_null']:
                    col_str += " [NOT NULL]"
                columns.append(col_str)
            
            formatted_schema.append(f"Columns: {', '.join(columns)}")
            
            # Foreign keys
            if table_info['foreign_keys']:
                fks = []
                for fk in table_info['foreign_keys']:
                    fks.append(f"{fk['column']} -> {fk['references_table']}.{fk['references_column']}")
                formatted_schema.append(f"Foreign Keys: {', '.join(fks)}")
            
            # Sample data
            if table_info['sample_data']:
                formatted_schema.append(f"Sample data: {table_info['sample_data'][:2]}")
        
        return '\n'.join(formatted_schema)
    
    def execute_sql(self, sql_query: str) -> List[Dict[str, Any]]:
        """
        Execute SQL query against database
        
        Args:
            sql_query: SQL query to execute
            
        Returns:
            List of dictionaries containing results
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            results = [dict(row) for row in rows]
            
            conn.close()
            logger.info(f"SQL executed successfully, returned {len(results)} rows")
            return results
            
        except Exception as e:
            logger.error(f"SQL execution error: {e}")
            raise Exception(f"SQL Error: {str(e)}")
    
    def generate_business_summary(self, user_query: str, sql_query: str, 
                                query_results: List[Dict[str, Any]]) -> str:
        """
        Generate business summary from query results
        
        Args:
            user_query: Original user query
            sql_query: Executed SQL query
            query_results: Results from SQL execution
            
        Returns:
            Business summary string
        """
        # Limit results for summary to avoid token limits
        sample_size = min(20, len(query_results))
        sample_results = query_results[:sample_size]
        
        # Calculate basic statistics
        stats = self._calculate_result_statistics(query_results)
        
        prompt = f"""
Create a business summary for non-technical stakeholders.

ORIGINAL QUESTION: {user_query}

SQL QUERY: {sql_query}

RESULTS SAMPLE ({sample_size} of {len(query_results)} total):
{json.dumps(sample_results, indent=2, default=str)}

STATISTICS:
{json.dumps(stats, indent=2, default=str)}

REQUIREMENTS:
- Write in plain business language
- Focus on insights and actionable findings
- Highlight key trends, patterns, or anomalies
- Provide context and implications
- Keep it concise but comprehensive
- Avoid technical jargon

BUSINESS SUMMARY:"""

        try:
            response = self.model.generate_content(prompt)
            summary = response.text.strip()
            logger.info("Business summary generated successfully")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating business summary: {e}")
            return f"Unable to generate summary: {str(e)}"
    
    def _calculate_result_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate basic statistics from query results"""
        if not results:
            return {'total_rows': 0}
        
        stats = {
            'total_rows': len(results),
            'columns': list(results[0].keys()) if results else [],
            'numeric_summaries': {}
        }
        
        # Calculate numeric summaries
        for col in stats['columns']:
            values = [row.get(col) for row in results if row.get(col) is not None]
            numeric_values = []
            
            for val in values:
                try:
                    numeric_values.append(float(val))
                except (ValueError, TypeError):
                    pass
            
            if numeric_values:
                stats['numeric_summaries'][col] = {
                    'count': len(numeric_values),
                    'min': min(numeric_values),
                    'max': max(numeric_values),
                    'avg': sum(numeric_values) / len(numeric_values)
                }
        
        return stats

class SQLQueryManager:
    """
    High-level manager class for handling complete query workflows
    """
    
    def __init__(self, database_path: str, gemini_api_key: str = None):
        """
        Initialize SQL Query Manager
        
        Args:
            database_path: Path to SQLite database
            gemini_api_key: Gemini API key
        """
        self.processor = QueryProcessor(database_path, gemini_api_key)
        self.query_history = []
    
    def process_natural_language_query(self, user_query: str) -> Dict[str, Any]:
        """
        Complete workflow for processing natural language query
        
        Args:
            user_query: Natural language query from user
            
        Returns:
            Dictionary containing complete results
        """
        start_time = datetime.now()
        
        try:
            # Step 1: Generate SQL and determine if summary needed
            needs_summary, sql_query = self.processor.generate_sql_query(user_query)
            
            # Step 2: Execute SQL query
            query_results = self.processor.execute_sql(sql_query)
            
            # Step 3: Generate business summary if needed
            business_summary = None
            if needs_summary and query_results:
                business_summary = self.processor.generate_business_summary(
                    user_query, sql_query, query_results
                )
            
            # Prepare response
            response = {
                'success': True,
                'user_query': user_query,
                'needs_summary': needs_summary,
                'sql_query': sql_query,
                'results': query_results,
                'result_count': len(query_results),
                'business_summary': business_summary,
                'processing_time': (datetime.now() - start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            }
            
            # Add to history
            self.query_history.append(response)
            
            return response
            
        except Exception as e:
            error_response = {
                'success': False,
                'user_query': user_query,
                'error': str(e),
                'processing_time': (datetime.now() - start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            }
            
            self.query_history.append(error_response)
            return error_response
    
    def get_query_history(self) -> List[Dict[str, Any]]:
        """Get query processing history"""
        return self.query_history
    
    def clear_history(self):
        """Clear query history"""
        self.query_history = []

# Utility functions for easy usage
def create_query_manager(database_path: str, api_key: str = None) -> SQLQueryManager:
    """Create a new SQL Query Manager instance"""
    return SQLQueryManager(database_path, api_key)

def query_database(user_query: str, database_path: str, api_key: str = None) -> Dict[str, Any]:
    """
    One-shot function to query database with natural language
    
    Args:
        user_query: Natural language query
        database_path: Path to SQLite database
        api_key: Gemini API key
        
    Returns:
        Complete query results
    """
    manager = create_query_manager(database_path, api_key)
    return manager.process_natural_language_query(user_query)

# Example usage and testing
if __name__ == "__main__":
    # Example usage
    DATABASE_PATH = "college.db"
    API_KEY = "your-gemini-api-key-here"  # Replace with actual key
    
    # Create manager
    query_manager = create_query_manager(DATABASE_PATH, API_KEY)
    
    # Test queries
    test_queries = [
        "Show me the top 5 students with highest GPA",
        "What is the relationship between student GPA and company salary offers?",
        "List all computer science courses",
        "Analyze the performance trends of students across different departments",
        "How many students are enrolled in each department?",
        "Compare the average salaries offered by different companies"
    ]
    
    print("🚀 Testing Natural Language to SQL System\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"{'='*60}")
        print(f"TEST {i}: {query}")
        print(f"{'='*60}")
        
        result = query_manager.process_natural_language_query(query)
        
        if result['success']:
            print(f"✅ SQL Generated: {result['sql_query']}")
            print(f"📊 Results: {result['result_count']} rows")
            print(f"📝 Needs Summary: {result['needs_summary']}")
            
            if result['business_summary']:
                print(f"💼 Business Summary:")
                print(result['business_summary'])
        else:
            print(f"❌ Error: {result['error']}")
        
        print(f"⏱️  Processing Time: {result['processing_time']:.2f}s\n")