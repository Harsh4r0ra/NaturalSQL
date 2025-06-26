import os
import json
import csv
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd

class QueryLogger:
    def __init__(self, log_directory: str = "query_logs"):
        """
        Initialize the Query Logger to save all questions and answers
        
        Args:
            log_directory: Directory to store log files
        """
        self.log_directory = log_directory
        self.ensure_log_directory()
        
        # Define log file paths
        self.text_log_file = os.path.join(log_directory, "query_log.txt")
        self.json_log_file = os.path.join(log_directory, "query_log.json")
        self.csv_log_file = os.path.join(log_directory, "query_log.csv")
        
        # Initialize CSV file with headers if it doesn't exist
        self.initialize_csv_log()
        
        print(f"Query Logger initialized - Logs will be saved to: {log_directory}")
    
    def ensure_log_directory(self):
        """Create log directory if it doesn't exist"""
        if not os.path.exists(self.log_directory):
            os.makedirs(self.log_directory)
            print(f"Created log directory: {self.log_directory}")
    
    def initialize_csv_log(self):
        """Initialize CSV log file with headers if it doesn't exist"""
        if not os.path.exists(self.csv_log_file):
            headers = [
                'timestamp',
                'session_id', 
                'original_question',
                'improved_question',
                'template_used',
                'sql_query',
                'results_count',
                'conversational_response',
                'processing_time_ms',
                'success',
                'error_message',
                'user_ip',
                'preprocessing_used'
            ]
            
            with open(self.csv_log_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
    
    def log_query(self, 
                  original_question: str,
                  conversational_response: str,
                  improved_question: str = None,
                  sql_query: str = None,
                  results_count: int = 0,
                  template_used: str = None,
                  processing_time_ms: float = None,
                  success: bool = True,
                  error_message: str = None,
                  user_ip: str = None,
                  preprocessing_used: bool = True,
                  session_id: str = None) -> str:
        """
        Log a complete query interaction
        
        Returns:
            log_entry_id: Unique identifier for this log entry
        """
        
        timestamp = datetime.now()
        log_entry_id = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{hash(original_question) % 10000:04d}"
        
        # Create log entry data
        log_entry = {
            'log_entry_id': log_entry_id,
            'timestamp': timestamp.isoformat(),
            'session_id': session_id or 'unknown',
            'original_question': original_question,
            'improved_question': improved_question or original_question,
            'template_used': template_used or 'none',
            'sql_query': sql_query or '',
            'results_count': results_count,
            'conversational_response': conversational_response,
            'processing_time_ms': processing_time_ms or 0,
            'success': success,
            'error_message': error_message or '',
            'user_ip': user_ip or 'unknown',
            'preprocessing_used': preprocessing_used
        }
        
        # Log to all formats
        self._log_to_text(log_entry)
        self._log_to_json(log_entry)
        self._log_to_csv(log_entry)
        
        print(f"Query logged with ID: {log_entry_id}")
        return log_entry_id
    
    def _log_to_text(self, log_entry: Dict[str, Any]):
        """Log to human-readable text file"""
        try:
            with open(self.text_log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"Log Entry ID: {log_entry['log_entry_id']}\n")
                f.write(f"Timestamp: {log_entry['timestamp']}\n")
                f.write(f"Session ID: {log_entry['session_id']}\n")
                f.write(f"Success: {log_entry['success']}\n")
                f.write(f"Processing Time: {log_entry['processing_time_ms']}ms\n")
                f.write(f"\nOriginal Question:\n{log_entry['original_question']}\n")
                
                if log_entry['improved_question'] != log_entry['original_question']:
                    f.write(f"\nImproved Question:\n{log_entry['improved_question']}\n")
                
                if log_entry['template_used'] != 'none':
                    f.write(f"\nTemplate Used: {log_entry['template_used']}\n")
                
                if log_entry['sql_query']:
                    f.write(f"\nSQL Query:\n{log_entry['sql_query']}\n")
                
                f.write(f"\nResults Count: {log_entry['results_count']}\n")
                f.write(f"\nConversational Response:\n{log_entry['conversational_response']}\n")
                
                if log_entry['error_message']:
                    f.write(f"\nError Message:\n{log_entry['error_message']}\n")
                
                f.write(f"\n{'='*80}\n")
        except Exception as e:
            print(f"Error logging to text file: {e}")
    
    def _log_to_json(self, log_entry: Dict[str, Any]):
        """Log to JSON file (append to array)"""
        try:
            # Read existing data
            if os.path.exists(self.json_log_file):
                with open(self.json_log_file, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        data = []
            else:
                data = []
            
            # Append new entry
            data.append(log_entry)
            
            # Write back to file
            with open(self.json_log_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error logging to JSON file: {e}")
    
    def _log_to_csv(self, log_entry: Dict[str, Any]):
        """Log to CSV file"""
        try:
            with open(self.csv_log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                row = [
                    log_entry['timestamp'],
                    log_entry['session_id'],
                    log_entry['original_question'],
                    log_entry['improved_question'],
                    log_entry['template_used'],
                    log_entry['sql_query'],
                    log_entry['results_count'],
                    log_entry['conversational_response'],
                    log_entry['processing_time_ms'],
                    log_entry['success'],
                    log_entry['error_message'],
                    log_entry['user_ip'],
                    log_entry['preprocessing_used']
                ]
                writer.writerow(row)
        except Exception as e:
            print(f"Error logging to CSV file: {e}")
    
    def get_logs_summary(self) -> Dict[str, Any]:
        """Get summary statistics from logs"""
        try:
            if not os.path.exists(self.csv_log_file):
                return {"message": "No logs found"}
            
            df = pd.read_csv(self.csv_log_file)
            
            if len(df) == 0:
                return {"message": "No logs found"}
            
            summary = {
                "total_queries": len(df),
                "successful_queries": len(df[df['success'] == True]),
                "failed_queries": len(df[df['success'] == False]),
                "success_rate": len(df[df['success'] == True]) / len(df) * 100 if len(df) > 0 else 0,
                "avg_processing_time_ms": df['processing_time_ms'].mean() if len(df) > 0 else 0,
                "avg_results_count": df['results_count'].mean() if len(df) > 0 else 0,
                "most_used_templates": df['template_used'].value_counts().head(5).to_dict(),
                "date_range": {
                    "earliest": df['timestamp'].min() if len(df) > 0 else None,
                    "latest": df['timestamp'].max() if len(df) > 0 else None
                }
            }
            
            return summary
            
        except Exception as e:
            return {"error": f"Error generating summary: {e}"}
    
    def get_recent_queries(self, limit: int = 10) -> list:
        """Get recent queries from logs"""
        try:
            if not os.path.exists(self.json_log_file):
                return []
            
            with open(self.json_log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            # Sort by timestamp and return most recent
            logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return logs[:limit]
            
        except Exception as e:
            print(f"Error getting recent queries: {e}")
            return []
    
    def get_query_stats(self) -> Dict[str, Any]:
        """Get detailed query statistics"""
        try:
            summary = self.get_logs_summary()
            recent_queries = self.get_recent_queries(5)
            
            return {
                "summary": summary,
                "recent_queries": recent_queries
            }
            
        except Exception as e:
            return {"error": f"Error getting query stats: {e}"}
    
    def search_logs(self, query: str, limit: int = 10) -> list:
        """Search through logged queries"""
        try:
            if not os.path.exists(self.json_log_file):
                return []
            
            with open(self.json_log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            # Simple text search in questions and responses
            matching_logs = []
            query_lower = query.lower()
            
            for log in logs:
                if (query_lower in log.get('original_question', '').lower() or 
                    query_lower in log.get('conversational_response', '').lower() or
                    query_lower in log.get('improved_question', '').lower()):
                    matching_logs.append(log)
                    
                if len(matching_logs) >= limit:
                    break
            
            return matching_logs
            
        except Exception as e:
            print(f"Error searching logs: {e}")
            return []
    
    def export_logs_to_excel(self) -> str:
        """Export logs to Excel file"""
        try:
            if not os.path.exists(self.csv_log_file):
                return None
            
            df = pd.read_csv(self.csv_log_file)
            
            # Generate export filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(self.log_directory, f"query_logs_export_{timestamp}.xlsx")
            
            df.to_excel(filename, index=False)
            return filename
            
        except Exception as e:
            print(f"Error exporting logs to Excel: {e}")
            return None
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up old log entries"""
        try:
            if not os.path.exists(self.csv_log_file):
                return
            
            df = pd.read_csv(self.csv_log_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Keep only recent logs
            cutoff_date = datetime.now() - pd.Timedelta(days=days_to_keep)
            df_recent = df[df['timestamp'] >= cutoff_date]
            
            # Save cleaned CSV
            df_recent.to_csv(self.csv_log_file, index=False)
            
            # Update JSON file
            recent_logs = df_recent.to_dict('records')
            with open(self.json_log_file, 'w', encoding='utf-8') as f:
                json.dump(recent_logs, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"Cleaned up logs - kept {len(df_recent)} records from last {days_to_keep} days")
            
        except Exception as e:
            print(f"Error cleaning up logs: {e}")


# Example usage and testing
if __name__ == "__main__":
    # Test the logger
    logger = QueryLogger()
    
    # Log a sample query
    logger.log_query(
        original_question="What are the top customers by revenue?",
        conversational_response="Based on your data, here are the top 5 customers by revenue: CustomerA ($50M), CustomerB ($45M), CustomerC ($42M), CustomerD ($38M), CustomerE ($35M)",
        improved_question="Show me customers ranked by total revenue in descending order",
        sql_query="SELECT customer_name, SUM(revenue) as total_revenue FROM customers GROUP BY customer_name ORDER BY total_revenue DESC LIMIT 5",
        results_count=5,
        template_used="top_customers_by_metric",
        processing_time_ms=234.5,
        success=True,
        session_id="session_123"
    )
    
    print("\nTest query logged successfully!")
    print("\nLog summary:")
    summary = logger.get_logs_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")