# AI-Powered SQL Query Generator

A Flask-based web application that converts natural language questions into SQL queries using OpenAI's GPT models, with built-in query preprocessing, template matching, and conversational response formatting.

## Features

- **Natural Language to SQL**: Convert questions like "Who is the manager for Project ABC?" into SQL queries
- **Query Preprocessing**: Automatically fix grammar, spelling, and improve query clarity
- **Template Matching**: Fast responses using pre-built SQL templates for common queries
- **Conversational Responses**: AI-powered formatting of SQL results into natural language
- **Query Logging**: Comprehensive logging of all queries, responses, and performance metrics
- **Multiple Query Scenarios**: Handles entity-specific, date-specific, both, or general queries

## Architecture

```
User Question → Query Preprocessor → Template Matcher → SQL Generator → Database → Response Formatter → User
                                         ↓
                                   Query Logger (logs everything)
```

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sql-query-generator
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

4. **Configure field mappings**
   ```bash
   cp field_mappings.json.example field_mappings.json
   # Edit field_mappings.json with your database schema
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

## Configuration

### Environment Variables (.env)

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
DB_SERVER=your_database_server
DB_NAME=your_database_name
DB_USER=your_database_username
DB_PASSWORD=your_database_password

# Application Configuration
FLASK_ENV=development
FLASK_DEBUG=True
```

### Field Mappings (field_mappings.json)

This file defines your database schema and how natural language maps to your tables and columns:

```json
{
  "field_mappings": {
    "category_name": {
      "field_name": {
        "table": "TABLE_NAME",
        "column": "column_name",
        "description": "What this field represents",
        "keywords": ["list", "of", "keywords", "that", "trigger", "this", "field"]
      }
    }
  },
  "table_relationships": {
    "primary_joins": {
      "join_name": "TABLE1.id = TABLE2.foreign_key"
    }
  }
}
```

## API Endpoints

### Main Query Endpoint
- **POST** `/api/conversational_query`
  - Body: `{"query": "your natural language question"}`
  - Returns: Conversational response with query results

### Logging Endpoints
- **GET** `/api/logs/recent` - Get recent queries
- **GET** `/api/logs/stats` - Get query statistics
- **GET** `/api/logs/search?q=term` - Search through logs
- **GET** `/api/logs/export` - Export logs to Excel

### Development Endpoints
- **POST** `/api/preprocess` - Test query preprocessing only
- **POST** `/api/generate_sql` - Test SQL generation only
- **POST** `/api/execute_query` - Full pipeline execution

## Usage Examples

### Basic Query
```bash
curl -X POST http://localhost:5000/api/conversational_query \
  -H "Content-Type: application/json" \
  -d '{"query": "Who is the manager for Project Alpha?"}'
```

### With SQL Display
```bash
curl -X POST http://localhost:5000/api/conversational_query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me all active projects", "show_sql": true}'
```

## Customization

### Adding SQL Templates

In `api_main.py`, add templates to the `_load_sql_templates()` method:

```python
def _load_sql_templates(self) -> Dict:
    return {
        "your_template_name": {
            "description": "What this template does",
            "keywords": ["trigger", "words", "for", "this", "template"],
            "sql": "SELECT * FROM your_table WHERE {placeholder}"
        }
    }
```

### Customizing Query Preprocessing

In `query_preprocessor.py`, modify the domain-specific replacements:

```python
def _basic_cleanup(self, query: str) -> str:
    replacements = {
        r'\byour_abbreviation\b': 'full_term',
        # Add your domain-specific replacements
    }
    # ... rest of method
```

### Customizing Response Formatting

In `conversational_formatter.py`, modify the response generation:

```python
def _generate_conversational_response(self, user_query, sql_query, data_summary, show_sql):
    # Customize the prompt and response format for your domain
    context = f"""
    You are a helpful assistant for [YOUR COMPANY/DOMAIN].
    # ... customize the prompt
    """
```

## Query Flow

1. **Preprocessing**: Cleans up grammar, spelling, and domain-specific abbreviations
2. **Template Matching**: Attempts to match query to pre-built SQL templates
3. **AI Generation**: Falls back to OpenAI for complex or unmatched queries
4. **Execution**: Runs SQL against your database
5. **Formatting**: Converts results into conversational responses
6. **Logging**: Records everything for analytics and debugging

## Logging

All queries are logged in multiple formats:
- **Text**: Human-readable log file
- **JSON**: Structured data for programmatic access
- **CSV**: For analysis in Excel/pandas

Log data includes:
- Original and improved questions
- SQL queries generated
- Results count and processing time
- Success/failure status
- User session information

## Development

### Running Tests
```bash
python query_logger.py  # Test logging system
python conversational_formatter.py  # Test response formatting
python query_preprocessor.py  # Test query preprocessing
python api_main.py  # Test SQL generation
```

### Adding New Features

1. **New Query Types**: Add templates in `api_main.py`
2. **Better Preprocessing**: Enhance domain rules in `query_preprocessor.py`
3. **Response Formats**: Customize formatting in `conversational_formatter.py`
4. **Additional Logging**: Extend `query_logger.py` with new metrics

## Security Notes

- Store all sensitive information in environment variables
- Use parameterized queries to prevent SQL injection
- Implement proper authentication for production use
- Review and sanitize all user inputs
- Limit database user permissions to necessary operations only

## Performance Optimization

- Pre-built templates provide instant responses for common queries
- Query caching can be added for frequently asked questions
- Database connection pooling for high-load scenarios
- Rate limiting for API endpoints

## Troubleshooting

### Common Issues

1. **OpenAI API Errors**: Check API key and rate limits
2. **Database Connection**: Verify connection string and credentials
3. **Template Matching**: Add more keywords to improve recognition
4. **Empty Results**: Check field mappings and table relationships

### Debug Mode

Set `FLASK_DEBUG=True` in your `.env` file for detailed error messages and automatic reloading.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request