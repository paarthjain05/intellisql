import streamlit as st
import os
import sqlite3
import google.generativeai as genai
import dotenv

api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

prompt = [
"""
You are an expert in converting English questions to SQL query!
The SQL database has the name STUDENTS and has the following columns - NAME, CLASS, 
Marks, Company \n\nFor example,\nExample 1 - How many entries of records are present?, 
the SQL command will be something like this: SELECT COUNT(*) FROM STUDENTS;
\nExample 2 - Tell me all the students studying in MCom class?, 
the SQL command will be something like this: SELECT * FROM STUDENTS 
WHERE CLASS="MCom";

"""
]

def setup_database():
    """Create and populate the STUDENTS database"""
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS STUDENTS (
            NAME TEXT,
            CLASS TEXT,
            Marks INTEGER,
            Company TEXT
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM STUDENTS")
    count = cursor.fetchone()[0]
    
    if count == 0:
        cursor.execute('''INSERT INTO STUDENTS VALUES('Sijo', 'BTech', 75, 'JSW')''')
        cursor.execute('''INSERT INTO STUDENTS VALUES('Lijo', 'MTech', 69, 'TCS')''')
        cursor.execute('''INSERT INTO STUDENTS VALUES('Rijo', 'BSc', 79, 'WIPRO')''')
        cursor.execute('''INSERT INTO STUDENTS VALUES('Sibin', 'MSc', 89, 'INFOSYS')''')
        cursor.execute('''INSERT INTO STUDENTS VALUES('Isha', 'MCom', 99, 'Cyient')''')
        
        conn.commit()
        print("Database setup completed with sample data!")
    else:
        print("Database already contains data.")
    
    conn.close()

def get_response(que, prompt):
    """Generate SQL query using Google's Gemini model"""
    try:
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        response = model.generate_content([prompt[0], que])
        return response.text
    except Exception as e:
        st.error(f"Error generating response: {e}")
        return None

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

def page_home():
    st.markdown("""
    <style>
    body {
        background-color: #2E2E2E;
    }
    .main-title {
        text-align: center;
        color: #4CAF50; /* Green color for headings */
        font-size: 2.5em;
    }
    .sub-title {
        text-align: center;
        color: #4CAF50; /* Green color for headings */
        font-size: 1.5em;
    }
    .offerings {
        padding: 20px;
        color: white; /* White color for body text */
    }
    .offerings h2 {
        color: #4CAF50; /* Green color for headings */
    }
    .offerings ul {
        list-style-type: none;
        padding: 0;
    }
    .offerings li {
        margin: 10px 0;
        font-size: 18px;
    }
    .custom-sidebar {
        background-color: #2E2E2E;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1 class='main-title'>Welcome to IntellioLLM</h1>", unsafe_allow_html=True)
    st.markdown("<h2 class='sub-title'>Revolutionizing Database Querying with Advanced LLM Capabilities</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.image("https://cdn1.iconfinder.com/data/icons/business-deal-color-glyph-set-3/128/Data_warehouse-1024.png", use_container_width=True)
    
    with col2:
        st.markdown(
            """
            <div class="offerings">
                <h2>🔍 Range of Offerings</h2>
                <ul>
                    <li>🤖 Intelligent Query Assistance</li>
                    <li>📊 Data Exploration and Insights</li>
                    <li>🛠️ Efficient Data Retrieval</li>
                    <li>🚀 Performance Optimization</li>
                    <li>💡 Syntax Suggestions</li>
                    <li>📈 Trend Analysis</li>
                </ul>
            </div>
            """, unsafe_allow_html=True
        )

def page_about():
    st.markdown("""
    <style>
    .content {
        color: white; /* White color for body text */
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1 style='color: #4CAF50;'>About IntellioLLM</h1>", unsafe_allow_html=True)
    st.markdown("<div class='content'>", unsafe_allow_html=True)
    st.markdown(
        "IntellioLLM is an innovative project aimed at revolutionizing database querying using advanced Language Model capabilities. "
        "Our system converts natural language questions into SQL queries, making database interaction accessible to everyone."
    )
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.image("https://download.logo.wine/logo/Oracle_SQL_Developer/Oracle_SQL_Developer_Logo.wine.png", use_container_width=True)

def page_intelligent_query_assistance():
    st.markdown("""
    <style>
    .tool-input {
        margin-bottom: 20px;
        color: white; /* White color for body text */
    }
    .response {
        margin-top: 20px;
        color: white; /* White color for body text */
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<h1 style='color: #4CAF50;'>Intelligent Query Assistance</h1>", unsafe_allow_html=True)
    st.write(
        "IntellioLLM enhances the querying process by providing intelligent assistance to users, whether they are novice or experienced SQL practitioners."
    )
    
    st.subheader("📋 Current Database Schema")
    st.info("**STUDENTS Table**: NAME, CLASS, Marks, Company")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("<div class='tool-input'>", unsafe_allow_html=True)
        que = st.text_input("Enter Your Query:", key="sql_query", placeholder="e.g., Show me all students with marks above 80")
        submit = st.button("Get Answer", key="submit_button", help="Click to retrieve the SQL data")
        st.markdown("</div>", unsafe_allow_html=True)
        
        if submit and que:
            try:
                with st.spinner("Generating SQL query..."):
                    response = get_response(que, prompt)
                
                if response:
                    cleaned_sql = clean_sql_response(response)
                    
                    st.markdown("### 🔍 Generated SQL Query:")
                    st.code(cleaned_sql, language="sql")
                    
                    with st.spinner("Executing query..."):
                        rows, columns = read_query(cleaned_sql, "data.db")
                    
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
        
        st.subheader("💡 Sample Queries")
        sample_queries = [
            "Show all students",
            "How many students are there?",
            "Students with marks above 80",
            "Students from TCS company",
            "Average marks of all students"
        ]
        
        for query in sample_queries:
            if st.button(query, key=f"sample_{query}"):
                st.session_state.sql_query = query

def main():
    setup_database()
    
    st.set_page_config(
        page_title="IntellioLLM",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.sidebar.title("🧭 Navigation")
    st.sidebar.markdown("<style>.sidebar .sidebar-content {background-color: #2E2E2E; color: white;}</style>", unsafe_allow_html=True)
    
    pages = {
        "🏠 Home": page_home,
        "ℹ️ About": page_about,
        "🤖 Intelligent Query Assistance": page_intelligent_query_assistance,
    }
    
    selection = st.sidebar.radio("Go to", list(pages.keys()))
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Database Info")
    st.sidebar.info("Database: STUDENTS\nRecords: 5\nColumns: NAME, CLASS, Marks, Company")
    
    page = pages[selection]
    page()

if __name__ == "__main__":
    main()