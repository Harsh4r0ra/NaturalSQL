import os
import json
import openai
from dotenv import load_dotenv
from typing import Dict, List, Tuple, Optional
import re

load_dotenv()

class QueryPreprocessor:
    def __init__(self, field_mappings_file: str = "field_mappings.json"):
        """
        Query Preprocessing Agent to clean and improve user queries
        before sending them to the SQL generation system
        """
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.field_mappings = self._load_field_mappings(field_mappings_file)
        self.domain_context = self._build_domain_context()
        
        print("Query Preprocessing Agent initialized!")
        print(f"Loaded domain context from {len(self.field_mappings.get('field_mappings', {}))} categories")
    
    def _load_field_mappings(self, json_file_path: str) -> Dict:
        """Load field mappings to understand domain context"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            print(f"Warning: Could not load field mappings: {e}")
            return {"field_mappings": {}}
    
    def _build_domain_context(self) -> Dict:
        """Build domain-specific context for query improvement"""
        context = {
            "common_terms": [],
            "technical_terms": [],
            "date_patterns": [],
            "entity_patterns": []
        }
        
        # Extract common terms from field mappings
        field_mappings = self.field_mappings.get("field_mappings", {})
        
        for category, fields in field_mappings.items():
            for field_name, field_info in fields.items():
                # Add keywords to appropriate categories
                keywords = field_info.get("keywords", [])
                context["common_terms"].extend(keywords)
        
        # Common date patterns and relative terms
        context["date_patterns"] = [
            "yesterday", "today", "last week", "last month", 
            "current", "latest", "recent", "now", "this week",
            "this month", "last 24 hours", "next 24 hours"
        ]
        
        return context
    
    def preprocess_query(self, user_query: str) -> Dict[str, str]:
        """
        Main preprocessing function that cleans and improves the user query
        Returns both the original and improved query with explanations
        """
        print(f"\n{'='*60}")
        print(f"PREPROCESSING QUERY: {user_query}")
        print('='*60)
        
        # Step 1: Basic cleaning
        cleaned_query = self._basic_cleanup(user_query)
        
        # Step 2: AI-powered grammar and clarity improvement
        improved_query = self._ai_improve_query(cleaned_query)
        
        # Step 3: Domain-specific enhancement
        enhanced_query = self._domain_enhance_query(improved_query)
        
        # Step 4: Final validation and formatting
        final_query = self._final_validation(enhanced_query)
        
        result = {
            "original_query": user_query,
            "cleaned_query": cleaned_query,
            "improved_query": improved_query,
            "enhanced_query": enhanced_query,
            "final_query": final_query,
            "improvements_made": self._explain_improvements(user_query, final_query)
        }
        
        print(f"FINAL IMPROVED QUERY: {final_query}")
        print(f"IMPROVEMENTS: {result['improvements_made']}")
        
        return result
    
    def _basic_cleanup(self, query: str) -> str:
        """Basic text cleanup - remove extra spaces, fix common issues"""
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query.strip())
        
        # Basic replacements - customize these for your domain
        replacements = {
            r'\bppl\b': 'people',
            r'\bwhrs\b': 'hours',
            r'\bhr\b': 'hour',
            r'\bhrs\b': 'hours',
            r'\bmgr\b': 'manager',
            r'\bsup\b': 'supervisor',
            r'\beng\b': 'engineer',
            r'\bwho r\b': 'who are',
            r'\bwat\b': 'what',
        }
        
        for pattern, replacement in replacements.items():
            query = re.sub(pattern, replacement, query, flags=re.IGNORECASE)
        
        return query
    
    def _ai_improve_query(self, query: str) -> str:
        """Use AI to fix grammar and improve clarity"""
        
        prompt = f"""
You are a query improvement specialist. Your job is to take user queries that may have grammatical errors, unclear phrasing, or awkward wording and improve them while preserving the original intent.

RULES FOR IMPROVEMENT:
1. Fix grammatical errors (spelling, punctuation, verb tense)
2. Improve clarity and readability
3. Preserve the original question intent completely
4. Use natural, professional language
5. Keep the same level of specificity
6. Make questions more direct and clear
7. Fix awkward phrasing while maintaining meaning

EXAMPLES:
- "wat is current status" → "What is the current status?"
- "show me ppl working today" → "Show me the people working today"
- "who r the managers" → "Who are the managers?"

IMPORTANT: Only improve grammar and clarity. Do NOT:
- Change the fundamental question being asked
- Add new information or constraints not in the original
- Remove specific details or names
- Change technical terms to different technical terms

Original query: "{query}"

Return ONLY the improved query with no explanations or additional text:
"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.1
            )
            
            improved = response.choices[0].message.content.strip()
            
            # Remove quotes if AI added them
            improved = improved.strip('"\'')
            
            return improved
            
        except Exception as e:
            print(f"AI improvement failed: {e}")
            return query
    
    def _domain_enhance_query(self, query: str) -> str:
        """Enhance query with domain-specific improvements"""
        
        # Domain-specific fixes - customize these for your specific domain
        domain_fixes = {
            r'\bcurrent status\b': 'current status',
            r'\bpeople\b': 'people',
            r'\bmanager\b': 'manager',
            r'\bsupervisor\b': 'supervisor',
            r'\bengineer\b': 'engineer',
        }
        
        for pattern, replacement in domain_fixes.items():
            query = re.sub(pattern, replacement, query, flags=re.IGNORECASE)
        
        return query
    
    def _final_validation(self, query: str) -> str:
        """Final validation and formatting"""
        
        # Ensure question ends with appropriate punctuation
        if not query.endswith(('?', '.', '!')):
            if any(word in query.lower() for word in ['who', 'what', 'where', 'when', 'which', 'how']):
                query += '?'
            else:
                query += '.'
        
        # Capitalize first letter
        if query:
            query = query[0].upper() + query[1:]
        
        # Final cleanup
        query = re.sub(r'\s+', ' ', query.strip())
        
        return query
    
    def _explain_improvements(self, original: str, final: str) -> str:
        """Explain what improvements were made"""
        improvements = []
        
        if original.lower() != final.lower():
            improvements.append("Grammar and clarity improved")
        
        if len(final.split()) != len(original.split()):
            improvements.append("Wording optimized")
        
        if not original.endswith(('?', '.', '!')) and final.endswith(('?', '.', '!')):
            improvements.append("Added proper punctuation")
        
        if original[0].islower() and final[0].isupper():
            improvements.append("Capitalized first letter")
        
        if not improvements:
            improvements.append("No changes needed")
        
        return "; ".join(improvements)
    
    def process_and_explain(self, user_query: str, show_steps: bool = True) -> Dict:
        """
        Process query and optionally show all improvement steps
        """
        result = self.preprocess_query(user_query)
        
        if show_steps:
            print(f"\n{'='*60}")
            print("QUERY IMPROVEMENT STEPS:")
            print('='*60)
            print(f"1. ORIGINAL:  {result['original_query']}")
            print(f"2. CLEANED:   {result['cleaned_query']}")
            print(f"3. AI IMPROVED: {result['improved_query']}")
            print(f"4. ENHANCED:  {result['enhanced_query']}")
            print(f"5. FINAL:     {result['final_query']}")
            print(f"\nIMPROVEMENTS MADE: {result['improvements_made']}")
        
        return result


class IntegratedSQLGenerator:
    """
    Integrated version that combines query preprocessing with SQL generator
    """
    def __init__(self, json_file_path: str = "field_mappings.json"):
        """Initialize both the preprocessor and SQL generator"""
        
        # Import your existing SQL generator
        from api_main import InteractiveSQLGenerator
        
        self.preprocessor = QueryPreprocessor(json_file_path)
        self.sql_generator = InteractiveSQLGenerator(json_file_path)
        
        print("Integrated SQL Generator with Query Preprocessing initialized!")
    
    def process_user_question_enhanced(self, question: str, show_preprocessing: bool = True):
        """
        Enhanced version that includes preprocessing
        """
        print(f"\n{'='*80}")
        print(f"ENHANCED PROCESSING: {question}")
        print('='*80)
        
        # Step 1: Preprocess the query
        preprocessing_result = self.preprocessor.process_and_explain(question, show_preprocessing)
        improved_question = preprocessing_result['final_query']
        
        print(f"\nUSING IMPROVED QUERY: {improved_question}")
        
        # Step 2: Generate SQL using existing system
        sql_query, results, formatted_results = self.sql_generator.process_user_question(improved_question)
        
        # Return enhanced results
        return {
            "original_question": question,
            "improved_question": improved_question,
            "preprocessing_details": preprocessing_result,
            "sql_query": sql_query,
            "results": results,
            "formatted_results": formatted_results
        }
    
    def get_preprocessing_examples(self) -> List[Tuple[str, str]]:
        """Get preprocessing examples for frontend display"""
        return [
            ("wat is current status", "What is the current status?"),
            ("show me ppl working today", "Show me the people working today"),
            ("who r the managers", "Who are the managers?"),
            ("whats the latest data", "What is the latest data?"),
            ("how many ppl today", "How many people today?"),
            ("give me status report", "Give me the status report")
        ]


def main():
    """Main function for web service - no interactive mode"""
    print("Query Preprocessor initialized for web service use")
    print("Use the Flask web application to interact with this system")
    print("Access the web interface at: http://localhost:5000")

if __name__ == "__main__":
    # For testing purposes only - in production, this is used via Flask app
    print("This module is designed to be used via the Flask web application")
    print("Run 'python app.py' to start the web server")