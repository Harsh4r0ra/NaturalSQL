import os
import json
import openai
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional
import traceback

load_dotenv()

class ConversationalFormatter:
    def __init__(self):
        """
        Conversational Formatter that takes raw SQL results and user queries
        and formats them into natural, conversational responses using OpenAI
        """
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        print("Conversational Formatter initialized!")
    
    def format_response(self, 
                       user_query: str, 
                       sql_query: str, 
                       results_df: pd.DataFrame, 
                       show_sql: bool = False) -> str:
        """
        Main method to format SQL results into conversational response
        
        Args:
            user_query: Original user question
            sql_query: Generated SQL query
            results_df: Pandas DataFrame with results
            show_sql: Whether to include SQL in response
        
        Returns:
            Conversational formatted response
        """
        try:
            # Handle empty results
            if results_df.empty:
                return self._format_no_results(user_query)
            
            # Prepare data summary for OpenAI
            data_summary = self._prepare_data_summary(results_df)
            
            # Generate conversational response
            conversational_response = self._generate_conversational_response(
                user_query, sql_query, data_summary, show_sql
            )
            
            return conversational_response
            
        except Exception as e:
            print(f"Error in conversational formatting: {e}")
            traceback.print_exc()
            return self._format_error_response(user_query, str(e))
    
    def _prepare_data_summary(self, df: pd.DataFrame) -> Dict:
        """Prepare a summary of the data for OpenAI processing"""
        
        # Convert DataFrame to a manageable format
        summary = {
            "total_rows": len(df),
            "column_count": len(df.columns),
            "columns": df.columns.tolist(),
            "sample_data": [],
            "key_insights": {}
        }
        
        # Include sample data (limit to avoid token limits)
        max_rows = min(10, len(df))
        
        for i in range(max_rows):
            row_data = {}
            for col in df.columns:
                try:
                    # Handle duplicate column names from SQL joins
                    col_series = df[col]
                    
                    # If we get a DataFrame instead of Series (duplicate columns), take first
                    if isinstance(col_series, pd.DataFrame):
                        value = col_series.iloc[i, 0]
                    else:
                        value = col_series.iloc[i]
                    
                    # Handle different data types
                    if value is None:
                        row_data[col] = "N/A"
                    elif isinstance(value, (pd.Series, np.ndarray)):
                        row_data[col] = str(value)
                    elif pd.isna(value) if not isinstance(value, (pd.Series, np.ndarray)) else False:
                        row_data[col] = "N/A"
                    elif isinstance(value, (int, float)):
                        if pd.isna(value):
                            row_data[col] = "N/A"
                        else:
                            row_data[col] = value
                    elif isinstance(value, pd.Timestamp):
                        row_data[col] = value.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(value) else "N/A"
                    else:
                        row_data[col] = str(value) if value is not None else "N/A"
                        
                except Exception as e:
                    try:
                        fallback_value = df.iloc[i][col]
                        if isinstance(fallback_value, pd.DataFrame):
                            fallback_value = fallback_value.iloc[0, 0]
                        row_data[col] = str(fallback_value) if fallback_value is not None else "N/A"
                    except:
                        row_data[col] = "N/A"
            
            summary["sample_data"].append(row_data)
        
        # Add key insights
        summary["key_insights"] = self._extract_key_insights(df)
        
        return summary
    
    def _extract_key_insights(self, df: pd.DataFrame) -> Dict:
        """Extract key insights from the data"""
        insights = {}
        
        try:
            # Basic statistics
            insights["row_count"] = len(df)
            insights["column_count"] = len(df.columns)
            
            # Identify unique values for key columns
            for col in df.columns:
                try:
                    # Skip if column name is duplicated
                    if df.columns.tolist().count(col) > 1:
                        continue
                        
                    col_series = df[col]
                    
                    # Handle duplicate column names
                    if isinstance(col_series, pd.DataFrame):
                        col_series = col_series.iloc[:, 0]
                    
                    col_data = col_series.dropna()
                    
                    if len(col_data) == 0:
                        continue
                        
                    # Check if column is numeric
                    if col_series.dtype in ['int64', 'float64', 'int32', 'float32']:
                        if not col_data.empty:
                            insights[f"{col}_stats"] = {
                                "min": float(col_data.min()) if pd.notna(col_data.min()) else None,
                                "max": float(col_data.max()) if pd.notna(col_data.max()) else None,
                                "mean": float(col_data.mean()) if pd.notna(col_data.mean()) else None
                            }
                    elif col_series.dtype == 'object' or str(col_series.dtype).startswith('string'):
                        try:
                            unique_values = col_data.unique()
                            if len(unique_values) <= 10:
                                insights[f"{col}_unique_values"] = [str(v) for v in unique_values if v is not None]
                            else:
                                insights[f"{col}_unique_count"] = len(unique_values)
                        except Exception:
                            continue
                            
                except Exception as e:
                    print(f"Warning: Could not process column {col}: {e}")
                    continue
            
            # Look for important data patterns
            # Add your domain-specific pattern detection here
            
        except Exception as e:
            print(f"Error extracting insights: {e}")
            insights["error"] = f"Could not extract insights: {str(e)}"
        
        return insights
    
    def _generate_conversational_response(self, 
                                        user_query: str, 
                                        sql_query: str, 
                                        data_summary: Dict, 
                                        show_sql: bool) -> str:
        """Generate conversational response using OpenAI"""
        
        # Limit the data shown to OpenAI to avoid token limits
        limited_sample_data = data_summary.get('sample_data', [])[:3]
        
        # Create a focused summary for important fields
        important_fields = {}
        for row in limited_sample_data:
            for key, value in row.items():
                # Focus on key fields - customize this for your domain
                if any(keyword in key.lower() for keyword in [
                    'name', 'id', 'status', 'date', 'count', 'total', 'amount'
                ]):
                    if key not in important_fields:
                        important_fields[key] = []
                    important_fields[key].append(str(value))
        
        # Prepare context for OpenAI
        context = f"""
You are a helpful assistant working for a company. You're helping team members by answering their questions about data.

USER QUESTION:
"{user_query}"

DATA SUMMARY:
- Total Rows Returned: {data_summary.get('total_rows', 0)}
- Total Columns: {data_summary.get('column_count', 0)}

IMPORTANT DATA FOUND:
{json.dumps(important_fields, indent=2, default=str)[:1500]}...

KEY INSIGHTS:
{json.dumps(data_summary.get('key_insights', {}), indent=2, default=str)[:1000]}...

YOUR TASK:
Generate a clear, chat-style response to the user. You are acting as a smart, friendly assistant.

RESPONSE GUIDELINES:
- Start with a friendly greeting (e.g., "Hi! Here's what I found...")
- Answer the question directly first, then explain further if needed
- Use real values from the data
- Be concise and structured — use bullet points, short paragraphs, and clear formatting
- Focus on the most important information
- Always maintain a professional tone with a helpful and approachable vibe
- End with a helpful note offering to provide more specific details if needed

EXAMPLE RESPONSE FORMAT:
Hi! Here's what I found:

**Summary:**
- Total records: X
- Key information: [relevant details]

**Details:**
- Item 1: [details]
- Item 2: [details]

Let me know if you'd like more specific details!

Remember: Focus on the most important information and present it clearly.
"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{
                    "role": "user", 
                    "content": context
                }],
                max_tokens=800,
                temperature=0.3
            )
            
            conversational_response = response.choices[0].message.content.strip()
            
            # Optionally add SQL query if requested
            if show_sql:
                conversational_response += f"\n\n**Technical Details:** The query used was:\n```sql\n{sql_query}\n```"
            
            return conversational_response
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            # Fallback to basic formatting
            return self._generate_fallback_response(user_query, data_summary)
    
    def _generate_fallback_response(self, user_query: str, data_summary: Dict) -> str:
        """Fallback response generation if OpenAI fails"""
        
        total_rows = data_summary['total_rows']
        
        if total_rows == 0:
            return f"I couldn't find any results for your query: '{user_query}'. The search returned no matching records."
        
        response = f"Here's what I found for your query '{user_query}':\n\n"
        
        # Extract key information from insights
        insights = data_summary.get('key_insights', {})
        
        response += f"**Summary:** Found {total_rows} record(s) with {data_summary.get('column_count', 0)} data fields.\n\n"
        
        # Show sample data if available
        sample_data = data_summary.get('sample_data', [])
        if sample_data:
            response += "**Sample Results:**\n"
            for i, row in enumerate(sample_data[:3], 1):
                response += f"Record {i}:\n"
                for key, value in list(row.items())[:5]:  # Show first 5 fields
                    response += f"  - {key}: {value}\n"
                response += "\n"
        
        response += "Let me know if you'd like more specific details about any aspect of the data!"
        
        return response
    
    def _format_no_results(self, user_query: str) -> str:
        """Format response when no results are found"""
        return f"I couldn't find any data matching your query: '{user_query}'. This could mean:\n\n" \
               f"• The specific criteria you mentioned doesn't exist in the current data\n" \
               f"• The time period specified might not have recorded data\n" \
               f"• There might be a spelling variation in names or identifiers\n\n" \
               f"Try rephrasing your question or checking the spelling of key terms."
    
    def _format_error_response(self, user_query: str, error_message: str) -> str:
        """Format response when there's an error"""
        return f"I encountered an issue while processing your query: '{user_query}'.\n\n" \
               f"The system was able to retrieve data, but had trouble formatting the response. " \
               f"This usually happens with very large datasets or complex query results.\n\n" \
               f"Please try asking for more specific information, or contact support if the issue persists."
    
    def format_multiple_queries(self, queries_and_results: List[Dict]) -> str:
        """
        Format multiple related queries into a single conversational response
        
        Args:
            queries_and_results: List of dicts with 'query', 'sql', 'results' keys
        """
        if not queries_and_results:
            return "No queries were processed."
        
        if len(queries_and_results) == 1:
            item = queries_and_results[0]
            return self.format_response(
                item['query'], 
                item['sql'], 
                item['results']
            )
        
        # Multiple queries - create comprehensive response
        combined_response = "Here's what I found from your related queries:\n\n"
        
        for i, item in enumerate(queries_and_results, 1):
            response = self.format_response(
                item['query'], 
                item['sql'], 
                item['results']
            )
            combined_response += f"**Query {i}:** {item['query']}\n{response}\n\n"
        
        return combined_response


def main():
    """Test the conversational formatter"""
    print("Conversational Formatter Test")
    
    # Create test data
    test_data = pd.DataFrame({
        'Name': ['Item 1', 'Item 2', 'Item 3'],
        'Count': [10, 20, 15],
        'Status': ['Active', 'Inactive', 'Active']
    })
    
    formatter = ConversationalFormatter()
    
    test_query = "What are the current items?"
    test_sql = "SELECT name, count, status FROM items"
    
    result = formatter.format_response(test_query, test_sql, test_data)
    print("\n" + "="*60)
    print("TEST RESULT:")
    print("="*60)
    print(result)

if __name__ == "__main__":
    main()