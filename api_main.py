import os
import json
import pyodbc
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import openai
from dotenv import load_dotenv
import re

load_dotenv()

class InteractiveSQLGenerator:
    def __init__(self, json_file_path: str = "field_mappings.json"):
        """
        Interactive SQL Generator with template support
        Combines AI natural language processing with pre-built SQL templates
        """
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.connection_string = self._build_connection_string()
        self.field_mappings = self._load_field_mappings(json_file_path)
        self.schema_context = self._build_comprehensive_schema()
        
        # Load SQL templates and query patterns
        self.sql_templates = self._load_sql_templates()
        self.query_patterns = self._load_query_patterns()
        
        print(f"Interactive SQL Generator Ready!")
        print(f"Loaded {len(self.schema_context['tables'])} tables from database schema")
        print(f"Loaded {len(self.sql_templates)} pre-built SQL templates")
        
    def _build_connection_string(self) -> str:
        """Build database connection string from environment variables"""
        return (
            f"DRIVER={{SQL Server}};"
            f"SERVER={os.getenv('DB_SERVER', 'localhost')};"
            f"DATABASE={os.getenv('DB_NAME', 'YourDatabase')};"
            f"UID={os.getenv('DB_USER', 'username')};"
            f"PWD={os.getenv('DB_PASSWORD', 'password')};"
            f"Trusted_Connection=no;"
        )
    
    def _load_field_mappings(self, json_file_path: str) -> Dict:
        """Load field mappings from JSON file"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                mappings = json.load(file)
                print(f"Successfully loaded field mappings from {json_file_path}")
                
                # Validate the structure
                if "field_mappings" not in mappings:
                    raise ValueError("Invalid JSON structure: missing 'field_mappings' key")
                
                # Count loaded categories and fields
                total_fields = 0
                for category, fields in mappings["field_mappings"].items():
                    total_fields += len(fields)
                
                print(f"Loaded {len(mappings['field_mappings'])} categories with {total_fields} total fields")
                return mappings
                
        except FileNotFoundError:
            print(f"ERROR: {json_file_path} not found!")
            print("Please ensure the field_mappings.json file exists in the current directory")
            raise
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in {json_file_path}: {e}")
            raise
        except Exception as e:
            print(f"ERROR: Failed to load {json_file_path}: {e}")
            raise
            
    def _load_sql_templates(self) -> Dict:
        """Load SQL templates - customize this method with your templates"""
        # This is where you would load your SQL templates
        # Structure should be:
        # {
        #     "template_name": {
        #         "description": "Description of what this template does",
        #         "keywords": ["list", "of", "keywords", "that", "trigger", "this", "template"],
        #         "sql": "Your SQL query template with {placeholders}"
        #     }
        # }
        return {}
    
    def _load_query_patterns(self) -> Dict:
        """Load query patterns for template matching"""
        # This is where you would define patterns that help identify which template to use
        return {}
    
    def _build_comprehensive_schema(self) -> Dict:
        """Build database schema context from field mappings"""
        schema = {
            "database": os.getenv('DB_NAME', 'YourDatabase'),
            "tables": {},
            "relationships": [],
            "business_rules": {}
        }
        
        # Extract information from field mappings
        field_mappings = self.field_mappings.get("field_mappings", {})
        
        print("Building schema from JSON mappings...")
        for category, fields in field_mappings.items():
            print(f"  Processing category: {category}")
            
            for field_name, field_info in fields.items():
                table = field_info["table"]
                column = field_info["column"]
                
                if table not in schema["tables"]:
                    schema["tables"][table] = {
                        "columns": [],
                        "description": self._describe_table(table),
                        "category": []
                    }
                
                # Check if column already exists to avoid duplicates
                existing_columns = [col["name"] for col in schema["tables"][table]["columns"]]
                if column not in existing_columns:
                    column_info = {
                        "name": column,
                        "description": field_info.get("description", ""),
                        "keywords": field_info.get("keywords", []),
                        "data_type": self._guess_data_type(column, field_name),
                        "business_meaning": field_info.get("description", ""),
                        "field_name": field_name,
                        "category": category
                    }
                    schema["tables"][table]["columns"].append(column_info)
                
                # Track categories per table
                if category not in schema["tables"][table]["category"]:
                    schema["tables"][table]["category"].append(category)
        
        # Add relationships from JSON if they exist
        if "table_relationships" in self.field_mappings:
            relationships_data = self.field_mappings["table_relationships"]
            if "primary_joins" in relationships_data:
                schema["relationships"] = list(relationships_data["primary_joins"].values())
        
        # Add business rules
        schema["business_rules"] = {
            "date_handling": "Use appropriate date fields for filtering",
            "text_search": "Use LIKE '%value%' for text searches",
            "case_insensitive_search": "Use COLLATE for case-insensitive searches"
        }
        
        print(f"Schema built successfully:")
        print(f"  - {len(schema['tables'])} tables")
        print(f"  - {sum(len(table['columns']) for table in schema['tables'].values())} total columns")
        
        return schema
    
    def _describe_table(self, table: str) -> str:
        """Provide description for database tables"""
        descriptions = {
            # Add your table descriptions here
            # "TABLE_NAME": "Description of what this table contains"
        }
        return descriptions.get(table, f"Database table: {table}")
    
    def _guess_data_type(self, column: str, field_name: str) -> str:
        """Guess data type based on column name patterns"""
        column_lower = column.lower()
        field_lower = field_name.lower()
        
        if "date" in column_lower or "time" in column_lower:
            return "datetime"
        elif any(word in column_lower for word in ["depth", "pressure", "temperature", "weight"]):
            return "decimal(10,2)"
        elif "id" in column_lower:
            return "int"
        elif "name" in column_lower or "description" in column_lower:
            return "varchar(255)"
        else:
            return "varchar(100)"
    
    def extract_filters_from_question(self, user_question: str) -> Dict[str, str]:
        """
        Extract filters from user question - customize based on your data patterns
        """
        filters = {
            "well_filter": "",
            "date_filter": "",
            "has_well_constraint": False,
            "has_date_constraint": False,
            "query_type": "general"
        }
        
        question_lower = user_question.lower()
        
        # Add your specific extraction logic here
        # For example, looking for specific patterns in your data
        
        return filters
    
    def identify_query_template(self, user_question: str) -> Optional[str]:
        """
        Identify which template best matches the user question
        """
        question_lower = user_question.lower()
        
        # Template matching logic
        template_scores = {}
        
        for template_name, template_info in self.sql_templates.items():
            score = 0
            keywords = template_info.get("keywords", [])
            
            # Score based on keyword matches
            for keyword in keywords:
                if keyword.lower() in question_lower:
                    score += 1
            
            template_scores[template_name] = score
        
        # Return the template with the highest score
        if template_scores:
            best_template = max(template_scores, key=template_scores.get)
            if template_scores[best_template] > 0:
                return best_template
        
        return None
    
    def build_sql_from_template(self, template_name: str, user_question: str) -> str:
        """
        Build SQL query from template with dynamic filters
        """
        template = self.sql_templates[template_name]
        filters = self.extract_filters_from_question(user_question)
        
        print(f"Using template: {template_name}")
        
        # Get the base SQL template
        sql_query = template["sql"]
        
        # Build replacements based on filters
        replacements = {}
        
        # Add your replacement logic here
        # For example:
        # replacements["{well_filter}"] = filters.get("well_filter", "1=1")
        # replacements["{date_filter}"] = filters.get("date_filter", "")
        
        # Apply all replacements
        for placeholder, replacement in replacements.items():
            if placeholder in sql_query:
                sql_query = sql_query.replace(placeholder, replacement)
        
        return self._clean_sql_query(sql_query)
    
    def _clean_sql_query(self, sql_query: str) -> str:
        """Clean up SQL query to handle edge cases"""
        # Remove extra spaces
        sql_query = re.sub(r'\s+', ' ', sql_query).strip()
        
        # Fix WHERE clauses that might start with AND
        sql_query = re.sub(r'\bWHERE\s+AND\b', 'WHERE', sql_query, flags=re.IGNORECASE)
        
        # Fix multiple consecutive AND clauses
        sql_query = re.sub(r'\bAND\s+AND\b', 'AND', sql_query, flags=re.IGNORECASE)
        
        # Ensure semicolon at end
        if not sql_query.endswith(';'):
            sql_query += ';'
        
        return sql_query
    
    def generate_sql_from_natural_language(self, user_question: str) -> str:
        """
        Main method: Try template matching first, fall back to AI generation
        """
        # First, try to identify if this matches a pre-built template
        template_name = self.identify_query_template(user_question)
        
        if template_name:
            print(f"Using pre-built template: {template_name}")
            return self.build_sql_from_template(template_name, user_question)
        
        # Fall back to AI generation for unmatched queries
        print("No template match found, using AI generation...")
        return self._ai_generate_sql(user_question)
    
    def _ai_generate_sql(self, user_question: str) -> str:
        """
        AI-powered SQL generation as fallback
        """
        schema_info = self._format_schema_for_ai()

        prompt = f"""
You are an expert SQL query generator.

SCHEMA INFORMATION:
{schema_info}

RULES:
1. Generate valid SQL Server syntax
2. Use proper table joins
3. Handle case-insensitive text searches appropriately
4. Return ONLY SQL - no explanations

Generate SQL for: "{user_question}"
"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.1
            )

            sql_query = response.choices[0].message.content.strip()
            
            # Clean response
            sql_query = re.sub(r'```sql\n?', '', sql_query)
            sql_query = re.sub(r'```\n?', '', sql_query)
            
            if ';' in sql_query:
                sql_query = sql_query.split(';')[0] + ';'
            
            sql_query = sql_query.strip()
            
            if not sql_query.endswith(';'):
                sql_query += ';'
            
            return self._clean_sql_query(sql_query)

        except Exception as e:
            print(f"AI SQL generation failed: {e}")
            return f"-- Error generating SQL: {str(e)}"

    def _format_schema_for_ai(self) -> str:
        """Format schema information for AI prompt"""
        schema_text = f"DATABASE: {self.schema_context['database']}\n\n"
        
        # Format each table with its columns
        for table_name, table_info in self.schema_context["tables"].items():
            schema_text += f"TABLE: {table_name}\n"
            schema_text += f"Purpose: {table_info['description']}\n"
            schema_text += "Columns:\n"
            
            for col in table_info["columns"][:10]:  # Limit to avoid token limits
                schema_text += f"  - {col['name']} ({col['data_type']}): {col['description']}\n"
                    
            schema_text += "\n"
        
        # Add relationships
        schema_text += "TABLE RELATIONSHIPS:\n"
        for rel in self.schema_context["relationships"]:
            schema_text += f"  - {rel}\n"
        
        return schema_text
    
    def execute_sql(self, sql_query: str) -> pd.DataFrame:
        """Execute SQL and return results"""
        try:
            print(f"Executing SQL query...")
            with pyodbc.connect(self.connection_string) as conn:
                df = pd.read_sql(sql_query, conn)
                print(f"Query executed successfully. Retrieved {len(df)} rows.")
                return df
        except pyodbc.Error as e:
            print(f"Database error: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Query execution error: {e}")
            return pd.DataFrame()
    
    def format_results(self, df: pd.DataFrame, max_rows: int = 20) -> str:
        """Format results for display"""
        if df.empty:
            return "No results found"
        
        result_text = f"Found {len(df)} result(s):\n\n"
        
        if len(df) <= max_rows:
            result_text += df.to_string(index=False, max_colwidth=50)
        else:
            result_text += f"Showing first {max_rows} results:\n"
            result_text += df.head(max_rows).to_string(index=False, max_colwidth=50)
            result_text += f"\n\n... and {len(df) - max_rows} more results"
        
        return result_text
    
    def process_user_question(self, question: str) -> Tuple[str, pd.DataFrame, str]:
        """Main processing method"""
        print(f"\n{'='*80}")
        print(f"QUESTION: {question}")
        print('='*80)
        
        try:
            # Generate SQL
            sql_query = self.generate_sql_from_natural_language(question)
            print(f"\nGENERATED SQL:\n{sql_query}")
            
            # Execute if valid
            if sql_query and not sql_query.startswith("--"):
                print(f"\nEXECUTING QUERY...")
                results = self.execute_sql(sql_query)
                formatted_results = self.format_results(results)
                print(f"\n{formatted_results}")
            else:
                results = pd.DataFrame()
                formatted_results = sql_query
                print(f"\n{formatted_results}")
            
            return sql_query, results, formatted_results
            
        except Exception as e:
            error_msg = f"Error processing question: {str(e)}"
            print(f"\n{error_msg}")
            return f"-- {error_msg}", pd.DataFrame(), error_msg


def main():
    """Main function for testing"""
    print("Starting Interactive SQL Generator...")
    
    # Check if the JSON file exists
    json_file = "field_mappings.json"
    if not os.path.exists(json_file):
        print(f"ERROR: {json_file} not found in current directory!")
        print("Please ensure your field_mappings.json file is present")
        return
    
    try:
        generator = InteractiveSQLGenerator(json_file)
        print("\n✅ Successfully initialized")
        
        # Test database connection
        try:
            test_query = "SELECT TOP 1 * FROM INFORMATION_SCHEMA.TABLES;"
            test_df = generator.execute_sql(test_query)
            if not test_df.empty:
                print(f"  • Database connection: ✅ Connected")
            else:
                print(f"  • Database connection: ⚠️  Connected but no data")
        except:
            print(f"  • Database connection: ❌ Failed (queries will show SQL only)")
        
        # Example usage
        test_question = "Show me all data"
        sql, results, formatted = generator.process_user_question(test_question)
        
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
    except Exception as e:
        print(f"\nFatal error: {e}")
        print("Please check that:")
        print("1. field_mappings.json has valid structure")
        print("2. OpenAI API key is configured in .env file")
        print("3. Database connection settings are correct")


if __name__ == "__main__":
    main()