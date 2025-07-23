
---

# 🧠 IntelliSQL: Schema-Aware Intelligent SQL Querying with LLMs

IntelliSQL is an advanced database querying system that integrates **Gemini Pro** with semantic schema awareness to enable natural language interactions with databases. It automatically understands database structures and generates optimized SQL queries, including complex JOINs, aggregations, and multi-table operations.

---

## 🚀 Key Features

🧠 **Schema-Aware**: Automatically discovers database tables, columns, and relationships  
🔗 **Automatic JOINs**: Generates precise queries with proper JOIN operations  
📊 **Multi-Table Queries**: Seamlessly handles queries across multiple related tables  
🎯 **Semantic Matching**: Uses embeddings to identify relevant tables based on query context  
💡 **Intelligent Context**: Provides enriched schema context to Gemini Pro for accurate query generation  
📈 **Real-time Adaptation**: Dynamically updates schema understanding as the database evolves  
🚀 **ChromaDB Integration**: Persistent vector storage for schema embeddings  
🔍 **Query Optimization**: Offers suggestions to improve query performance  
📊 **Data Insights**: Detects trends, patterns, and insights through conversational queries  

---

## 🛠️ Tech Stack

* **LLM**: Gemini Pro (via Google API)  
* **App Framework**: Streamlit (Python-based interactive UI)  
* **Database**: SQLite3 (lightweight, file-based)  
* **NLP Layer**: Gemini Pro API for natural language-to-SQL translation  
* **Embedding Layer**: `sentence-transformers` for semantic schema embeddings  
* **Vector Storage**: ChromaDB for fast similarity search  

---

## 📦 Installation

### Prerequisites

* Python 3.8 or higher  
* Google API Key for Gemini Pro  

### Setup Steps

1. **Clone the repository**:

   ```bash
   git clone https://github.com/your-username/IntelliSQL.git
   cd IntelliSQL
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables**:

   Create a `.env` file in the project directory:

   ```
   GOOGLE_API_KEY=your_google_api_key_here
   ```

4. **Initialize the database**:

   ```bash
   python sql.py
   ```

   This creates a sample database with tables such as:
   * **CUSTOMERS**: Customer information and demographics  
   * **ORDERS**: Order details with timestamps and values  
   * **PRODUCTS**: Product catalog with categories and prices  
   * **SALES**: Sales records linking customers, orders, and products  
   * **INVENTORY**: Stock levels and warehouse details  

5. **Run the application**:

   ```bash
   streamlit run app.py
   ```

---

## ✨ How It Works

### Schema Awareness Process

1. **Schema Extraction**: Scans the SQLite database to extract:
   * Table names, columns, and data types  
   * Primary and foreign key relationships  
   * Sample data for context  

2. **Natural Language Descriptions**: Converts schema into human-readable format, e.g.:

   ```
   "Table CUSTOMERS contains 100 records with columns: id (INTEGER), name (TEXT), 
   country (TEXT), revenue (FLOAT). Stores customer details and purchase history."
   ```

3. **Embedding Generation**: Uses `sentence-transformers` to create semantic embeddings of schema descriptions  

4. **Vector Storage**: Stores embeddings in ChromaDB for efficient similarity search  

5. **Query Processing**:
   * Generates an embedding for the user’s natural language query  
   * Retrieves relevant table schemas via semantic similarity  
   * Passes schema context to Gemini Pro  
   * Generates and executes optimized SQL queries  

### Architecture

```
User Query → Embedding → ChromaDB Search → Relevant Schemas → 
Enhanced Prompt → Gemini Pro → SQL Generation → Execution → Results
```

---

## 📝 Usage

1. Run the app and access it at `http://localhost:8501` (or the provided port).  
2. Enter a natural language query, such as:

   > *"Show the top 10 customers by revenue in 2024."*  
   > *"Find products with low inventory in the electronics category."*  
   > *"Average order value by country for the last quarter."*  

3. IntelliSQL will:
   * Translate the query into SQL  
   * Display the results  
   * Provide query optimization tips and refinement options  

---

## 🧪 Example Queries

| 🗣 Natural Language Query                     | 🧾 SQL Generated                                                                 |
|----------------------------------------------|---------------------------------------------------------------------------------|
| "List all products sold in March"            | `SELECT * FROM sales WHERE MONTH(sale_date) = 3;`                               |
| "Average order value by country"             | `SELECT country, AVG(order_value) FROM orders GROUP BY country;`                |
| "Top 5 customers by revenue with their orders" | `SELECT c.name, SUM(o.order_value) FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.name ORDER BY SUM(o.order_value) DESC LIMIT 5;` |

### Complex Queries

* "Customers who ordered electronics products in 2024 with total spend over $10,000":

  ```sql
  SELECT c.name, SUM(o.order_value)
  FROM customers c
  JOIN orders o ON c.id = o.customer_id
  JOIN sales s ON o.order_id = s.order_id
  JOIN products p ON s.product_id = p.id
  WHERE p.category = 'electronics' AND YEAR(o.order_date) = 2024
  GROUP BY c.name
  HAVING SUM(o.order_value) > 10000;
  ```

* "Inventory trends by product category":

  ```sql
  SELECT p.category, AVG(i.stock_level), MONTH(i.check_date)
  FROM products p
  JOIN inventory i ON p.id = i.product_id
  GROUP BY p.category, MONTH(i.check_date)
  ORDER BY MONTH(i.check_date);
  ```

---

## 🌟 Advanced Analytics

* **Trend Analysis**: "Compare sales performance across quarters by product category"  
* **Customer Insights**: "Find valuable customers whose order frequency is decreasing"  
* **Inventory Optimization**: "Products with stock levels below reorder threshold by warehouse"  
* **Ad-Hoc Exploration**: "Correlation between order value and customer location"  

IntelliSQL empowers users to explore data conversationally, making it ideal for analysts, researchers, and business users without deep SQL expertise.

---
