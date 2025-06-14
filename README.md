
---

# 🧠 IntelliSQL: Intelligent SQL Querying with LLMs Using Gemini

IntelliSQL leverages the power of **Gemini Pro**, a large language model, to enhance how users interact with databases. It allows users to write natural language queries and receive optimized SQL statements in return — making data access and exploration faster, easier, and more intuitive.

---

## 🚀 Features

### 🔍 Scenario 1: Intelligent Query Assistance

* Understands **natural language questions** and converts them into **accurate SQL queries**
* Provides **syntax suggestions** and **auto-completion**
* Helps users craft **complex SQL joins, subqueries**, and **filters** with ease
* Offers **query optimization tips** to improve performance

### 📊 Scenario 2: Data Exploration and Insights

* Enables users to explore databases with **conversational queries**
* Detects and extracts **hidden trends**, **patterns**, and **insights**
* Supports **ad-hoc analysis** for analysts and researchers without deep SQL expertise


---

## 🛠️ Tech Stack

* **LLM**: Gemini Pro
* **App Framework**: Streamlit (Python-based interactive UI)
* **Database**: SQLite3 (lightweight and file-based)
* **NLP Layer**: Gemini Pro API integration for natural language-to-SQL translation

---


## 📦 Installation

### 1. Clone the repo

```bash
git clone https://github.com/your-username/IntelliSQL.git
cd IntelliSQL
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set environment variables

Create a `.env` file with your Gemini API key:

```
GEMINI_API_KEY=your_api_key_here
```

### 4. Run the app

```bash
streamlit run app.py
```

---

## ✨ Usage

* Run the app and go to `http://localhost:8000` (or equivalent).
* Type a natural language query like:

  > *"Show me the top 10 customers by revenue in 2024."*
* IntelliSQL will:

  * Translate it into SQL
  * Display the results
  * Offer refinement options if needed

---

## 🧪 Example Queries

| 🗣 Natural Language               | 🧾 SQL Generated                                                 |
| --------------------------------- | ---------------------------------------------------------------- |
| "List all products sold in March" | `SELECT * FROM sales WHERE MONTH(date) = 3;`                     |
| "Average order value by country"  | `SELECT country, AVG(order_value) FROM orders GROUP BY country;` |

---