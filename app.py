import streamlit as st
import os
import sqlite3
import google.generativeai as genai
import dotenv
import pandas as pd
from schema_embedder import SchemaEmbedder
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# Load environment variables
dotenv.load_dotenv()

# Configure API
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# Initialize schema embedder
schema_embedder = SchemaEmbedder()

# Custom CSS for dark UI
def load_css():
    st.markdown("""
    <style>
    /* Global Styles */
    .stApp {
        background-color: #1a202c;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: #e2e8f0;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container */
    .main-container {
        background: #2d3748;
        border-radius: 12px;
        padding: 2rem;
        margin: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        border: 1px solid #4a5568;
    }
    
    /* Title styling */
    .main-title {
        text-align: center;
        color: #e2e8f0;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .sub-title {
        text-align: center;
        color: #a0aec0;
        font-size: 1.1rem;
        font-weight: 400;
        margin-bottom: 2rem;
    }
    
    /* Query interface */
    .query-container {
        background: #2d3748;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #4a5568;
    }
    
    .query-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #e2e8f0;
        margin-bottom: 1rem;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #1a202c;
    }
    
    .sidebar-title {
        color: #e2e8f0;
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 1rem;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #4c51bf;
        color: #e2e8f0;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        border: 1px solid #4c51bf;
    }
    
    .stButton > button:hover {
        background-color: #434190;
        border-color: #434190;
    }
    
    /* Schema info styling */
    .schema-badge {
        background-color: #2a4365;
        color: #a0aec0;
        padding: 0.25rem 0.75rem;
        border-radius: 16px;
        font-size: 0.875rem;
        font-weight: 500;
        display: inline-block;
        margin: 0.25rem;
    }
    
    /* Results styling */
    .results-container {
        background: #2d3748;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #4a5568;
    }
    
    /* Metrics styling */
    .metric-container {
        background: #2d3748;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        border: 1px solid #4a5568;
    }
    
    .metric-value {
        font-size: 1.875rem;
        font-weight: 700;
        color: #e2e8f0;
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: #a0aec0;
        margin-top: 0.25rem;
    }
    
    /* Success/Error messages */
    .success-message {
        background-color: #2f855a;
        color: #c6f6d5;
        padding: 1rem;
        border-radius: 6px;
        margin: 1rem 0;
        border: 1px solid #38a169;
    }
    
    .error-message {
        background-color: #742a2a;
        color: #feb2b2;
        padding: 1rem;
        border-radius: 6px;
        margin: 1rem 0;
        border: 1px solid #f56565;
    }
    
    /* Text styling */
    h1, h2, h3 {
        color: #e2e8f0;
    }
    
    p, div {
        color: #a0aec0;
    }
    </style>
    """, unsafe_allow_html=True)

def get_schema_aware_response(user_query):
    """Generate SQL query using schema-aware prompting"""
    try:
        relevant_schemas = schema_embedder.search_relevant_tables(user_query, k=3)
        
        schema_context = "Available database tables and their structures:\n\n"
        for doc, meta in relevant_schemas:
            table_name = meta.get('table', 'Unknown Table')
            description = doc if doc else f"No description for {table_name}"
            schema_context += f"- {table_name}: {description}\n"
        
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
- "Get average marks by department" → Use JOIN with COURSES and GROUP BY

Now convert this English question to SQL:
{user_query}

Return only the SQL query without any explanation or formatting.
"""

        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        response = model.generate_content(enhanced_prompt)
        
        # Extract text from response, handling different possible structures
        generated_text = response.text if hasattr(response, 'text') else str(response) if response else ""
        
        return generated_text, relevant_schemas
        
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

def get_database_stats():
    """Get database statistics for dashboard"""
    try:
        conn = sqlite3.connect("college.db")
        cursor = conn.cursor()
        
        # Get table names, excluding system tables and COMPANIES
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name != 'COMPANIES';")
        all_tables = [row[0] for row in cursor.fetchall()]
        
        # Filter out tables with 0 records for main stats
        active_tables = []
        total_records = 0
        
        for table in all_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            total_records += count
            if count > 0:  # Only include tables with data
                active_tables.append({'table': table, 'records': count})
        
        stats = {
            'total_tables': len(active_tables),
            'total_records': total_records,
            'table_info': active_tables,
            'all_tables': all_tables  # Keep all tables for schema display
        }
        
        conn.close()
        return stats
        
    except Exception as e:
        st.error(f"Error getting database stats: {e}")
        return None

def render_home_page():
    """Render the home page with minimal UI"""
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Hero section
    st.markdown('<h1 class="main-title">IntellioLLM</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Natural Language Database Querying</p>', unsafe_allow_html=True)
    
    # Stats dashboard
    stats = get_database_stats()
    if stats:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-value">{stats['total_tables']}</div>
                <div class="metric-label">Active Tables</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-value">{stats['total_records']:,}</div>
                <div class="metric-label">Total Records</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-value">AI</div>
                <div class="metric-label">Powered</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Database schema overview
    st.markdown('<h3 style="color: #e2e8f0; margin-bottom: 1rem;">Database Tables</h3>', unsafe_allow_html=True)
    
    # Schema details
    try:
        all_schemas = schema_embedder.get_all_schemas()
        
        # Filter to show only tables with data, excluding COMPANIES
        stats = get_database_stats()
        active_table_names = [t['table'].lower() for t in stats['table_info']] if stats else []
        
        for schema_info in all_schemas:
            table_name = schema_info.get('table', 'Unknown Table')
            description = schema_info.get('description', f"No description for {table_name}")
            
            # Only show tables that have data and exclude COMPANIES
            if table_name.lower() in active_table_names and table_name != 'COMPANIES':
                with st.expander(f"{table_name.upper()} Table"):
                    st.markdown(f"**Description:** {description}")
                    
                    # Show sample data
                    conn = sqlite3.connect("college.db")
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                    sample_data = cursor.fetchall()
                    
                    if sample_data:
                        cursor.execute(f"PRAGMA table_info('{table_name}')")
                        columns = [row[1] for row in cursor.fetchall()]
                        
                        df = pd.DataFrame(sample_data, columns=columns)
                        st.dataframe(df, use_container_width=True)
                    
                    conn.close()
                
    except Exception as e:
        st.error(f"Error displaying schema info: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_query_page():
    """Render the query page with minimal UI"""
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    st.markdown('<h1 class="query-title">Query Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #a0aec0; margin-bottom: 2rem;">Ask questions about your data in natural language.</p>', unsafe_allow_html=True)
    
    # Query input section
    st.markdown('<div class="query-container">', unsafe_allow_html=True)
    
    # Query examples as buttons
    st.markdown("### Example queries:")
    example_queries = [
        "Show students with their course enrollments",
        "List all professors and their departments", 
        "Average marks by department",
        "Students enrolled in Computer Science courses",
        "Count of students per course"
    ]
    
    cols = st.columns(len(example_queries))
    for i, query in enumerate(example_queries):
        with cols[i]:
            if st.button(query, key=f"example_{i}", use_container_width=True):
                st.session_state.user_query = query
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Main query input
    user_query = st.text_area(
        "Enter your question:",
        value=st.session_state.get('user_query', ''),
        height=100,
        placeholder="e.g., Show me all students enrolled in Computer Science courses..."
    )
    
    submit_button = st.button("Generate Query", use_container_width=True, type="primary")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Process query
    if submit_button and user_query:
        with st.spinner("Analyzing your query..."):
            response, relevant_schemas = get_schema_aware_response(user_query)
        
        if response:
            # Show relevant schemas
            if relevant_schemas:
                st.markdown('<div class="results-container">', unsafe_allow_html=True)
                st.markdown("### Relevant tables:")
                for doc, meta in relevant_schemas:
                    table_name = meta.get('table', 'Unknown Table')
                    if table_name != 'COMPANIES':
                        st.markdown(f'<span class="schema-badge">{table_name}</span>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Show generated SQL
            cleaned_sql = clean_sql_response(response)
            st.markdown('<div class="results-container">', unsafe_allow_html=True)
            st.markdown("### Generated SQL:")
            st.code(cleaned_sql, language="sql")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Execute query
            with st.spinner("Executing query..."):
                rows, columns = read_query(cleaned_sql, "college.db")
            
            if rows is not None and columns is not None:
                st.markdown('<div class="results-container">', unsafe_allow_html=True)
                st.markdown("### Results:")
                
                if len(rows) > 0:
                    df = pd.DataFrame(rows, columns=columns)
                    
                    # Show results count
                    st.markdown(f'<div class="success-message">Found {len(rows)} record(s)</div>', unsafe_allow_html=True)
                    
                    # Display results
                    st.dataframe(df, use_container_width=True)
                    
                    # Option to download results
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                    
                else:
                    st.markdown('<div class="error-message">No results found.</div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="error-message">Failed to execute query.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="error-message">Failed to generate SQL query.</div>', unsafe_allow_html=True)
    
    elif submit_button and not user_query:
        st.markdown('<div class="error-message">Please enter a query.</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_about_page():
    """Render the about page"""
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    st.markdown('<h1 style="color: #e2e8f0; margin-bottom: 2rem;">ℹ️ About IntellioLLM</h1>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### 🚀 What is IntellioLLM?
        
        IntellioLLM is a next-generation database querying system that combines the power of Large Language Models 
        with semantic schema awareness. Built with cutting-edge AI technology, it transforms natural language 
        questions into sophisticated SQL queries.
        
        ### 🔧 Technical Architecture
        
        - **AI Engine**: Google's Gemini 2.0 Flash for natural language processing
        - **Schema Understanding**: ChromaDB with sentence transformers for semantic matching
        - **Database**: SQLite with comprehensive college management schema
        - **Frontend**: Modern Streamlit interface with custom CSS styling
        
        ### 🎯 Key Capabilities
        
        - **Natural Language Processing**: Ask questions in plain English
        - **Schema-Aware Queries**: Automatically understands table relationships
        - **Complex SQL Generation**: Creates JOINs, subqueries, and aggregations
        - **Real-time Execution**: Instant query results with beautiful visualizations
        - **Export Functionality**: Download results in multiple formats
        
        ### 🛡️ Why Choose IntellioLLM?
        
        Traditional database querying requires extensive SQL knowledge. IntellioLLM democratizes data access 
        by allowing anyone to query complex databases using natural language, making data insights accessible 
        to everyone in your organization.
        """)
    
    with col2:
        st.markdown("""
        <div class="feature-card" style="text-align: center;">
            <div class="feature-icon">🎓</div>
            <div class="feature-title">Perfect for Education</div>
            <div class="feature-desc">Ideal for students, researchers, and educators working with academic data</div>
        </div>
        
        <div class="feature-card" style="text-align: center;">
            <div class="feature-icon">🏢</div>
            <div class="feature-title">Enterprise Ready</div>
            <div class="feature-desc">Scalable architecture suitable for business intelligence applications</div>
        </div>
        
        <div class="feature-card" style="text-align: center;">
            <div class="feature-icon">🔒</div>
            <div class="feature-title">Secure & Reliable</div>
            <div class="feature-desc">Built with security best practices and error handling</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Technology stack
    st.markdown("### 🛠️ Technology Stack")
    
    tech_cols = st.columns(4)
    technologies = [
        ("🤖", "Google Gemini", "AI Language Model"),
        ("🔍", "ChromaDB", "Vector Database"),
        ("🐍", "Streamlit", "Web Framework"), 
        ("💾", "SQLite", "Database Engine")
    ]
    
    for i, (icon, name, desc) in enumerate(technologies):
        with tech_cols[i]:
            st.markdown(f"""
            <div class="metric-container">
                <div style="font-size: 2rem;">{icon}</div>
                <div class="metric-label" style="font-weight: 600; color: #e2e8f0;">{name}</div>
                <div class="metric-label">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Main application function"""
    # Initialize session state
    if 'user_query' not in st.session_state:
        st.session_state.user_query = ''
    
    # Refresh schema index
    schema_embedder.refresh_schema_index()
    
    # Page configuration
    st.set_page_config(
        page_title="IntellioLLM - AI Database Assistant",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Load custom CSS
    load_css()
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown('<h2 class="sidebar-title">🧭 Navigation</h2>', unsafe_allow_html=True)
        
        pages = {
            "🏠 Home": "home",
            "🧠 Query Assistant": "query", 
            "ℹ️ About": "about"
        }
        
        selected_page = st.radio(
            "Choose a page:",
            list(pages.keys()),
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Database info in sidebar
        st.markdown('<h3 class="sidebar-title">📊 Database Info</h3>', unsafe_allow_html=True)
        
        stats = get_database_stats()
        if stats:
            st.markdown(f"""
            <div style="color: #e2e8f0; font-size: 0.9rem;">
                <div style="margin-bottom: 0.5rem;">📋 Active Tables: <strong>{stats['total_tables']}</strong></div>
                <div style="margin-bottom: 0.5rem;">📈 Records: <strong>{stats['total_records']:,}</strong></div>
                <div style="margin-bottom: 1rem;">🤖 AI Model: <strong>Gemini 2.0</strong></div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("**Tables with Data:**")
            for table_info in stats['table_info']:
                st.markdown(f"• {table_info['table']} ({table_info['records']} records)", 
                          help=f"Table: {table_info['table']}")
            
            # Show empty tables if any
            empty_tables = [t for t in stats.get('all_tables', []) if t not in [ti['table'] for ti in stats['table_info']]]
            if empty_tables:
                st.markdown("**Empty Tables:**")
                for table in empty_tables:
                    if not table.startswith('sqlite_'):  # Skip system tables
                        st.markdown(f"• {table} (0 records)", help=f"Empty table: {table}")
        
        st.markdown("---")
        st.markdown('<p style="color: rgba(226,232,240,0.7); font-size: 0.8rem; text-align: center;">Built with ❤️ using Streamlit & AI</p>', unsafe_allow_html=True)
    
    # Render pages
    current_page = pages[selected_page]
    
    if current_page == "home":
        render_home_page()
    elif current_page == "query":
        render_query_page()
    elif current_page == "about":
        render_about_page()

if __name__ == "__main__":
    main()