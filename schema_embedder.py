import sqlite3
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import os
import json
from typing import List, Dict, Tuple, Optional

DB_PATH = "college.db"
CHROMA_PATH = "./chroma/"
CHROMA_COLLECTION = "schema_index"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

class SchemaEmbedder:
    def __init__(self, db_path: str = DB_PATH, chroma_path: str = CHROMA_PATH, 
                 collection_name: str = CHROMA_COLLECTION):
        """
        Initialize the SchemaEmbedder with database and ChromaDB connections.
        
        Args:
            db_path: Path to SQLite database
            chroma_path: Path to ChromaDB persistent directory
            collection_name: Name of ChromaDB collection
        """
        self.db_path = db_path
        self.chroma_path = chroma_path
        self.collection_name = collection_name
        
        print("Loading embedding model...")
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        
        os.makedirs(self.chroma_path, exist_ok=True)
        
        self.chroma_client = chromadb.PersistentClient(path=self.chroma_path)
        
        try:
            self.collection = self.chroma_client.get_collection(self.collection_name)
            print(f"Connected to existing ChromaDB collection: {self.collection_name}")
        except:
            self.collection = self.chroma_client.create_collection(self.collection_name)
            print(f"Created new ChromaDB collection: {self.collection_name}")
        
        self.refresh_schema_index()

    def extract_table_schemas(self) -> List[Dict]:
        """
        Extract comprehensive schema information from the SQLite database.
        
        Returns:
            List of dictionaries containing table schema information
        """
        if not os.path.exists(self.db_path):
            print(f"Database {self.db_path} not found!")
            return []
            
        schemas = []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                cursor.execute(f"PRAGMA table_info('{table}')")
                columns_info = cursor.fetchall()
                
                if not columns_info:
                    continue
                
                columns = []
                column_types = []
                primary_keys = []
                
                for col_info in columns_info:
                    col_name = col_info[1]
                    col_type = col_info[2]
                    is_pk = col_info[5]
                    
                    columns.append(col_name)
                    column_types.append(f"{col_name} ({col_type})")
                    
                    if is_pk:
                        primary_keys.append(col_name)
                
                cursor.execute(f"PRAGMA foreign_key_list('{table}')")
                foreign_keys = cursor.fetchall()
                
                fk_info = []
                for fk in foreign_keys:
                    fk_info.append(f"{fk[3]} -> {fk[2]}.{fk[4]}")
                
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                
                description = self._build_table_description(
                    table, columns, column_types, primary_keys, fk_info, row_count
                )
                
                schemas.append({
                    "table": table,
                    "description": description,
                    "columns": columns,
                    "column_types": column_types,
                    "primary_keys": primary_keys,
                    "foreign_keys": fk_info,
                    "row_count": row_count
                })
            
            conn.close()
            print(f"Extracted schemas for {len(schemas)} tables")
            return schemas
            
        except Exception as e:
            print(f"Error extracting schemas: {e}")
            return []

    def _build_table_description(self, table: str, columns: List[str], 
                                column_types: List[str], primary_keys: List[str],
                                foreign_keys: List[str], row_count: int) -> str:
        """
        Build a comprehensive natural language description of a table.
        
        Args:
            table: Table name
            columns: List of column names
            column_types: List of column names with types
            primary_keys: List of primary key columns
            foreign_keys: List of foreign key relationships
            row_count: Number of rows in the table
            
        Returns:
            Natural language description of the table
        """
        description = f"Table {table.upper()} contains {row_count} records"
        
        description += f" with columns: {', '.join(column_types)}"
        
        if primary_keys:
            description += f". Primary key: {', '.join(primary_keys)}"
        
        if foreign_keys:
            description += f". Foreign key relationships: {', '.join(foreign_keys)}"
        
        context_info = self._add_contextual_info(table, columns)
        if context_info:
            description += f". {context_info}"
        
        return description

    def _add_contextual_info(self, table: str, columns: List[str]) -> str:
        """
        Add contextual information about what the table likely contains.
        
        Args:
            table: Table name
            columns: List of column names
            
        Returns:
            Contextual description
        """
        table_lower = table.lower()
        columns_lower = [col.lower() for col in columns]
        
        contexts = []
        
        if 'student' in table_lower or any('student' in col for col in columns_lower):
            contexts.append("Contains student information")
        
        if 'course' in table_lower or any('course' in col for col in columns_lower):
            contexts.append("Contains course/academic information")
        
        if 'company' in table_lower or any('company' in col or 'employer' in col for col in columns_lower):
            contexts.append("Contains company/employer information")
        
        if 'enrollment' in table_lower or 'registration' in table_lower:
            contexts.append("Tracks student-course relationships and academic records")
        
        if any(word in col for col in columns_lower for word in ['grade', 'mark', 'score']):
            contexts.append("Includes academic performance data")
        
        if any(word in col for col in columns_lower for word in ['location', 'address', 'city', 'state']):
            contexts.append("Includes location/geographical information")
        
        return ". ".join(contexts) if contexts else ""

    def refresh_schema_index(self) -> None:
        """
        Refresh the ChromaDB index with current database schema.
        This method handles schema updates, additions, and deletions.
        """
        print("Refreshing schema index...")
    
        current_schemas = self.extract_table_schemas()
        
        if not current_schemas:
            print("No schemas found in database")
            return
        
        try:
            existing_data = self.collection.get(include=["metadatas", "documents"])
            existing_tables = set()
            
            if existing_data and existing_data.get("metadatas"):
                for meta in existing_data["metadatas"]:
                    if meta and "table" in meta:
                        existing_tables.add(meta["table"])
        except Exception as e:
            print(f"Error getting existing data: {e}")
            existing_tables = set()
        
        current_tables = {schema["table"] for schema in current_schemas}
        
        tables_to_remove = existing_tables - current_tables
        if tables_to_remove:
            try:
                self.collection.delete(ids=list(tables_to_remove))
                print(f"Removed {len(tables_to_remove)} obsolete tables from index")
            except Exception as e:
                print(f"Error removing obsolete tables: {e}")
        
        descriptions = []
        embeddings = []
        ids = []
        metadatas = []
        
        for schema in current_schemas:
            table_name = schema["table"]
            description = schema["description"]
            columns_str = ', '.join(schema["columns"]) if schema["columns"] else ""
            column_types_str = ', '.join(schema["column_types"]) if schema["column_types"] else ""
            primary_keys_str = ', '.join(schema["primary_keys"]) if schema["primary_keys"] else ""
            foreign_keys_str = ', '.join(schema["foreign_keys"]) if schema["foreign_keys"] else ""
            
            descriptions.append(description)
            ids.append(table_name)
            metadatas.append({
                "table": table_name,
                "columns": columns_str,
                "column_types": column_types_str,
                "primary_keys": primary_keys_str,
                "foreign_keys": foreign_keys_str,
                "row_count": schema["row_count"]
            })
        
        if descriptions:
            try:
                print(f"Generating embeddings for {len(descriptions)} schemas...")
                embeddings = self.model.encode(descriptions).tolist()
                
                self.collection.upsert(
                    embeddings=embeddings,
                    documents=descriptions,
                    metadatas=metadatas,
                    ids=ids
                )
                
                print(f"Successfully indexed {len(descriptions)} table schemas")
                
            except Exception as e:
                print(f"Error updating ChromaDB index: {e}")

    def search_relevant_tables(self, user_query: str, k: int = 3) -> List[Tuple[str, Dict]]:
        """
        Search for the most relevant table schemas based on user query.
        
        Args:
            user_query: User's natural language query
            k: Number of top results to return
            
        Returns:
            List of tuples containing (description, metadata) for relevant tables
        """
        try:
            query_embedding = self.model.encode([user_query]).tolist()[0]
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(k, self._get_collection_count())
            )
            
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            
            relevant_tables = []
            for i, (doc, meta) in enumerate(zip(documents, metadatas)):
                if doc and meta:
                    meta_with_score = meta.copy()
                    meta_with_score["similarity_score"] = 1 - distances[i] if distances else 1.0
                    relevant_tables.append((doc, meta_with_score))
            
            print(f"Found {len(relevant_tables)} relevant tables for query: '{user_query}'")
            return relevant_tables
            
        except Exception as e:
            print(f"Error searching relevant tables: {e}")
            return []

    def get_all_schemas(self) -> List[Dict]:
        """
        Get all schema information from ChromaDB.
        
        Returns:
            List of all schema dictionaries
        """
        try:
            results = self.collection.get(include=["metadatas"])
            metadatas = results.get("metadatas", [])
            
            return [meta for meta in metadatas if meta is not None]
            
        except Exception as e:
            print(f"Error getting all schemas: {e}")
            return []

    def _get_collection_count(self) -> int:
        """
        Get the number of items in the ChromaDB collection.
        
        Returns:
            Number of items in collection
        """
        try:
            return self.collection.count()
        except:
            return 0

    def get_table_relationships(self) -> Dict[str, List[str]]:
        """
        Extract and return table relationships based on foreign keys.
        
        Returns:
            Dictionary mapping table names to their related tables
        """
        relationships = {}
        schemas = self.get_all_schemas()
        
        for schema in schemas:
            table_name = schema.get("table", "")
            foreign_keys = schema.get("foreign_keys", [])
            
            related_tables = []
            for fk in foreign_keys:
                if " -> " in fk:
                    referenced_table = fk.split(" -> ")[1].split(".")[0]
                    related_tables.append(referenced_table)
            
            if related_tables:
                relationships[table_name] = related_tables
        
        return relationships

    def suggest_joins(self, tables: List[str]) -> List[str]:
        """
        Suggest JOIN conditions based on foreign key relationships.
        
        Args:
            tables: List of table names
            
        Returns:
            List of suggested JOIN conditions
        """
        joins = []
        relationships = self.get_table_relationships()
        
        for i, table1 in enumerate(tables):
            for j, table2 in enumerate(tables[i+1:], i+1):
                if table1 in relationships and table2 in relationships[table1]:
                    joins.append(f"JOIN {table2} ON {table1}.{table2.lower()}_id = {table2}.id")
                elif table2 in relationships and table1 in relationships[table2]:
                    joins.append(f"JOIN {table1} ON {table2}.{table1.lower()}_id = {table1}.id")
        
        return joins

    def get_schema_summary(self) -> Dict:
        """
        Get a summary of the entire database schema.
        
        Returns:
            Dictionary containing schema summary statistics
        """
        schemas = self.get_all_schemas()
        
        if not schemas:
            return {"error": "No schemas found"}
        
        total_tables = len(schemas)
        total_columns = sum(len(schema.get("columns", [])) for schema in schemas)
        total_records = sum(schema.get("row_count", 0) for schema in schemas)
        
        tables_with_fks = sum(1 for schema in schemas if schema.get("foreign_keys"))
        
        return {
            "total_tables": total_tables,
            "total_columns": total_columns,
            "total_records": total_records,
            "tables_with_relationships": tables_with_fks,
            "tables": [schema.get("table") for schema in schemas]
        }

    def debug_collection(self) -> None:
        """
        Debug method to print collection contents.
        """
        try:
            results = self.collection.get(include=["metadatas", "documents"])
            print(f"Collection '{self.collection_name}' contains {len(results.get('ids', []))} items:")
            
            for i, (doc, meta) in enumerate(zip(
                results.get("documents", []), 
                results.get("metadatas", [])
            )):
                if doc and meta:
                    print(f"{i+1}. Table: {meta.get('table', 'Unknown')}")
                    print(f"   Description: {doc[:100]}...")
                    print(f"   Columns: {len(meta.get('columns', []))}")
                    print(f"   Records: {meta.get('row_count', 0)}")
                    print()
                    
        except Exception as e:
            print(f"Error debugging collection: {e}")


schema_embedder = SchemaEmbedder()

def search_relevant_tables(self, user_query: str, k: int = 3) -> List[Tuple[str, Dict]]:
    """
    Search for the most relevant table schemas based on user query.
    
    Args:
        user_query: User's natural language query
        k: Number of top results to return
        
    Returns:
        List of tuples containing (description, metadata) for relevant tables
    """
    try:
        query_embedding = self.model.encode([user_query]).tolist()[0]
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(k, self._get_collection_count())
        )
        
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        
        relevant_tables = []
        for i, (doc, meta) in enumerate(zip(documents, metadatas)):
            if doc and meta:
                meta_with_score = meta.copy()
                meta_with_score["columns"] = [col.strip() for col in meta["columns"].split(',') if col.strip()]
                meta_with_score["column_types"] = [col.strip() for col in meta["column_types"].split(',') if col.strip()]
                meta_with_score["primary_keys"] = [col.strip() for col in meta["primary_keys"].split(',') if col.strip()]
                meta_with_score["foreign_keys"] = [col.strip() for col in meta["foreign_keys"].split(',') if col.strip()]
                meta_with_score["similarity_score"] = 1 - distances[i] if distances else 1.0
                relevant_tables.append((doc, meta_with_score))
        
        print(f"Found {len(relevant_tables)} relevant tables for query: '{user_query}'")
        return relevant_tables
        
    except Exception as e:
        print(f"Error searching relevant tables: {e}")
        return []
    
def extract_all_schema() -> List[Dict]:
    """
    Convenience function to extract all schemas.
    
    Returns:
        List of all schema dictionaries
    """
    return schema_embedder.get_all_schemas()

def index_schema_in_chroma(schemas: List[Dict]) -> None:
    """
    Convenience function to refresh the schema index.
    Note: The schemas parameter is ignored as the function
    automatically extracts schemas from the database.
    
    Args:
        schemas: Ignored - kept for backward compatibility
    """
    schema_embedder.refresh_schema_index()

def get_schema_summary() -> Dict:
    """
    Convenience function to get schema summary.
    
    Returns:
        Dictionary containing schema summary
    """
    return schema_embedder.get_schema_summary()

if __name__ == "__main__":
    print("Schema Embedder initialized")
    schema_embedder.debug_collection()
    summary = get_schema_summary()
    print(f"Schema Summary: {summary}")