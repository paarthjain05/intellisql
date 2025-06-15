import streamlit as st
import os
import sqlite3
import google.generativeai as genai
import dotenv
from schema_embedder import SchemaEmbedder

dotenv.load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

schema_embedder = SchemaEmbedder()
    
def get_schema_aware_response(user_query):
    """Generate SQL query using schema-aware prompting"""
    try:
        relevant_schemas = schema_embedder.search_relevant_tables(user_query, k=3)
        
        schema_context = "Available database tables and their structures:\n\n"
        for description, metadata in relevant_schemas:
            schema_context += f"- {description}\n"
        
        enhanced_prompt = f"""
You are an expert in converting English questions to SQL queries!

{schema_context}

Important Guidelines:
1. Use proper JOIN operations when querying multiple tables
2. Always use table aliases for better readability
3. Use appropriate WHERE clauses for filtering
4. Consider using aggregate functions (COUNT, SUM, AVG, etc.) when appropriate
5. Pay attention to foreign key relationships between tables
6. Use DISTINCT when necessary to avoid duplicates

Examples of complex queries:
- "Show students and their course enrollments" → Use JOIN between STUDENTS and ENROLLMENTS
- "Find companies with their student counts" → Use JOIN and GROUP BY
- "Get average marks by department" → Use JOIN with COURSES and GROUP BY

Now convert this English question to SQL:
{user_query}

Return only the SQL query without any explanation or formatting.
"""

        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        response = model.generate_content(enhanced_prompt)
        return response.text, relevant_schemas
        
    except Exception as e:
        st.error(f"Error generating response: {e}")
        return None, []

def read_query(sql, db):
    """Execute SQL query and return results"""
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        column_names = [description[0] for description in cursor.description]
        
        conn.close()
        return rows, column_names
    except Exception as e:
        st.error(f"Database error: {e}")
        return None, None

def clean_sql_response(response):
    """Clean the SQL response from the LLM"""
    if response:
        cleaned = response.strip()
        if cleaned.startswith("```sql"):
            cleaned = cleaned[6:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()
    return response

def display_schema_info():
    """Display current database schema information"""
    try:
        all_schemas = schema_embedder.get_all_schemas()
        
        st.subheader("📋 Current Database Schema")
        
        for schema_info in all_schemas:
            table_name = schema_info['table']
            description = schema_info['description']
            
            with st.expander(f"📊 {table_name.upper()} Table"):
                st.write(description)

                conn = sqlite3.connect("college.db")
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                sample_data = cursor.fetchall()
                
                if sample_data:
                    cursor.execute(f"PRAGMA table_info('{table_name}')")
                    columns = [row[1] for row in cursor.fetchall()]
                    
                    import pandas as pd
                    df = pd.DataFrame(sample_data, columns=columns)
                    st.write("**Sample Data:**")
                    st.dataframe(df, use_container_width=True)
                
                conn.close()
                
    except Exception as e:
        st.error(f"Error displaying schema info: {e}")

def page_home():
    st.markdown("""
    <style>
    body {
        background-color: #2E2E2E;
    }
    .main-title {
        text-align: center;
        color: #4CAF50;
        font-size: 2.5em;
    }
    .sub-title {
        text-align: center;
        color: #4CAF50;
        font-size: 1.5em;
    }
    .offerings {
        padding: 20px;
        color: white;
    }
    .offerings h2 {
        color: #4CAF50;
    }
    .offerings ul {
        list-style-type: none;
        padding: 0;
    }
    .offerings li {
        margin: 10px 0;
        font-size: 18px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1 class='main-title'>Welcome to IntellioLLM</h1>", unsafe_allow_html=True)
    st.markdown("<h2 class='sub-title'>Schema-Aware Database Querying with Advanced LLM</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.image("https://cdn1.iconfinder.com/data/icons/business-deal-color-glyph-set-3/128/Data_warehouse-1024.png", use_container_width=True)
    
    with col2:
        st.markdown(
            """
            <div class="offerings">
                <h2>🔍 Enhanced Features</h2>
                <ul>python
                    <li>🧠 Schema-Aware Query Generation</li>
                    <li>🔗 Automatic JOIN Operations</li>
                    <li>📊 Multi-Table Complex Queries</li>
                    <li>🎯 Semantic Schema Matching</li>
                    <li>💡 Intelligent Context Awareness</li>
                    <li>📈 Advanced Analytics Support</li>
                    <li>🚀 ChromaDB Integration</li>
                </ul>
            </div>
            """, unsafe_allow_html=True
        )
    
    display_schema_info()

def page_about():
    st.markdown("""
    <style>
    .content {
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1 style='color: #4CAF50;'>About IntellioLLM</h1>", unsafe_allow_html=True)
    st.markdown("<div class='content'>", unsafe_allow_html=True)
    st.markdown(
        """
        IntellioLLM is an advanced database querying system that combines the power of Large Language Models 
        with semantic schema awareness. Using ChromaDB and sentence transformers, the system automatically 
        understands your database structure and generates complex SQL queries including JOINs and aggregations.
        
        **Key Features:**
        - **Schema-Aware**: Automatically discovers and understands all database tables and relationships
        - **Semantic Matching**: Uses embeddings to find relevant tables based on your query context
        - **Complex Queries**: Generates sophisticated SQL with JOINs, subqueries, and aggregations
        - **Real-time Adaptation**: Dynamically updates schema understanding as database evolves
        """
    )
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.image("https://download.logo.wine/logo/Oracle_SQL_Developer/Oracle_SQL_Developer_Logo.wine.png", use_container_width=True)

def page_intelligent_query_assistance():
    st.markdown("""
    <style>
    .tool-input {
        margin-bottom: 20px;
        color: white;
    }
    .response {
        margin-top: 20px;
        color: white;
    }
    .schema-context {
        background-color: #f0f0f0;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1 style='color: #4CAF50;'>Schema-Aware Query Assistant</h1>", unsafe_allow_html=True)
    st.write(
        "Ask complex questions about your data! The system automatically understands table relationships and generates appropriate JOINs."
    )
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("<div class='tool-input'>", unsafe_allow_html=True)
        que = st.text_input("Enter Your Query:", key="sql_query", placeholder="e.g., Show students with their course enrollments and grades")
        submit = st.button("Get Answer", key="submit_button", help="Click to generate and execute SQL query")
        st.markdown("</div>", unsafe_allow_html=True)
        
        if submit and que:
            try:
                with st.spinner("Analyzing query and finding relevant schemas..."):
                    response, relevant_schemas = get_schema_aware_response(que)
                
                if response:
                    if relevant_schemas:
                        st.markdown("### 🎯 Relevant Schemas Identified:")
                        for description, metadata in relevant_schemas:
                            st.info(f"📊 {description}")
                    
                    cleaned_sql = clean_sql_response(response)
                    
                    st.markdown("### 🔍 Generated SQL Query:")
                    st.code(cleaned_sql, language="sql")
                    
                    with st.spinner("Executing query..."):
                        rows, columns = read_query(cleaned_sql, "college.db")
                    
                    if rows is not None and columns is not None:
                        st.markdown("<div class='response'>", unsafe_allow_html=True)
                        st.subheader("📊 Query Results:")
                        
                        if len(rows) > 0:
                            import pandas as pd
                            df = pd.DataFrame(rows, columns=columns)
                            st.dataframe(df, use_container_width=True)
                            st.success(f"Found {len(rows)} record(s)")
                        else:
                            st.warning("No results found for your query.")
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.error("Failed to execute the query. Please check the generated SQL.")
                else:
                    st.error("Failed to generate SQL query. Please try again.")
                    
            except Exception as e:
                st.subheader("❌ Error:")
                st.error(f"An error occurred: {e}")
        
        elif submit and not que:
            st.warning("Please enter a query before clicking 'Get Answer'.")
    
    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/9850/9850477.png", use_container_width=True)
        
        st.subheader("💡 Complex Query Examples")
        complex_queries = [
            "Show students with their course enrollments",
            "Find companies and count of their students",
            "Average marks by department",
            "Students in Computer Science courses",
            "Top performing students with company info",
            "Courses with most enrollments",
            "Students who haven't enrolled in any course",
            "Company-wise average student marks"
        ]
        
        for query in complex_queries:
            if st.button(query, key=f"complex_{query}"):
                st.session_state.sql_query = query

def main():
    
    schema_embedder.refresh_schema_index()
    
    st.set_page_config(
        page_title="IntellioLLM - Schema Aware",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.sidebar.title("🧭 Navigation")
    st.sidebar.markdown("<style>.sidebar .sidebar-content {background-color: #2E2E2E; color: white;}</style>", unsafe_allow_html=True)
    
    pages = {
        "🏠 Home": page_home,
        "ℹ️ About": page_about,
        "🧠 Schema-Aware Queries": page_intelligent_query_assistance,
    }
    
    selection = st.sidebar.radio("Go to", list(pages.keys()))
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Database Info")
    
    try:
        conn = sqlite3.connect("college.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        total_records = 0
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            total_records += count
        
        conn.close()
        
        st.sidebar.info(f"Tables: {len(tables)}\nTotal Records: {total_records}")
        
        st.sidebar.markdown("**Tables:**")
        for table in tables:
            st.sidebar.markdown(f"• {table}")
            
    except Exception as e:
        st.sidebar.error(f"Error loading DB info: {e}")
    
    page = pages[selection]
    page()

if __name__ == "__main__":
    main()