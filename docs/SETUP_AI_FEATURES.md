# Setup Guide for AI Enhanced Features

## Prerequisites

1. **SEARXNG Running**: Ensure SEARXNG is running at `http://localhost:8085/` (or configure a different URL)
2. **OpenAI API Key**: Have your OpenAI API key ready

## Installation Steps

### 1. Install Backend Dependencies

```bash
cd backend
uv sync
```

This will install the new dependencies:
- `httpx>=0.27.0` - For HTTP requests
- `beautifulsoup4>=4.12.3` - For HTML parsing

### 2. Run Database Migration

Apply the new database migration to add the `searxng_url` field:

```bash
cd backend
uv run alembic upgrade head
```

### 3. Configure OpenAI Settings (Admin Only)

1. Start the application:
   ```bash
   cd /Users/andy/workspaces/meal-planner
   ./start.sh
   ```

2. Log in as an admin user

3. Navigate to Admin Dashboard

4. Scroll to "OpenAI Configuration" section

5. Configure the following:
   - **API Key**: Your OpenAI API key (if not already set)
   - **Model**: Choose your preferred model (e.g., `gpt-4`, `gpt-4-turbo`)
   - **SEARXNG URL**: Set to your SEARXNG instance URL (default: `http://localhost:8085`)

6. Click "Save OpenAI Settings"

## Testing the New Features

### Test 1: Dietary Preferences Toggle

1. Set your dietary preferences:
   - Go to Profile/Settings
   - Set dietary preferences (e.g., "vegan", "gluten-free")

2. Open AI Recipe Chat

3. Toggle the "Use Dietary Preferences" switch:
   - **ON**: AI will respect your dietary preferences
   - **OFF**: AI will ignore dietary preferences

4. Test creating a recipe:
   ```
   Create a dinner recipe
   ```
   - With toggle ON: Should create a recipe matching your dietary preferences
   - With toggle OFF: Should create any recipe without restrictions

### Test 2: Web Search

1. Open AI Recipe Chat

2. Ask the AI to search for information:
   ```
   Search for healthy Mediterranean recipes
   ```
   or
   ```
   Find recipes for chocolate cake
   ```

3. The AI should:
   - Use the `search_web` tool
   - Return relevant search results
   - Optionally suggest creating a recipe based on findings

### Test 3: URL Import

1. Find a recipe URL online (e.g., from AllRecipes, Food Network, etc.)

2. Open AI Recipe Chat

3. Share the URL with AI:
   ```
   Can you create a recipe based on this: https://example.com/recipe-url
   ```
   or
   ```
   Import this recipe: https://example.com/pasta-recipe
   ```

4. The AI should:
   - Fetch the URL content
   - Extract recipe information
   - Present a recipe for your confirmation
   - Create the recipe in your account upon confirmation

## Troubleshooting

### SEARXNG Connection Issues

**Error**: "Search error: Connection refused"

**Solution**:
1. Verify SEARXNG is running:
   ```bash
   curl http://localhost:8085/search?q=test&format=json
   ```

2. Check the SEARXNG URL in Admin Dashboard

3. Update if needed (e.g., if using Docker: `http://searxng:8080`)

### Import "bs4" Could Not Be Resolved

**Error**: IDE shows import error for `bs4`

**Solution**:
This is a Pylance/Pyright type checking warning. The package is installed as `beautifulsoup4` but imported as `bs4`. This is normal and will work at runtime.

### URL Fetching Timeout

**Error**: "Failed to fetch URL: timeout"

**Solution**:
1. Some websites block automated requests
2. Try a different URL
3. The timeout is set to 30 seconds (hardcoded in `openai_service.py`)

### Type Checking Warnings

The backend code may show type checking warnings with SQLAlchemy models. These are normal and don't affect functionality. The warnings are from Pylance/Pyright being strict about SQLAlchemy Column types.

## Example Usage Scenarios

### Scenario 1: Vegan User with Toggle OFF
```
User: "Create a pasta recipe"
AI: (ignores vegan preference, may include cheese/meat)
```

### Scenario 2: Vegan User with Toggle ON
```
User: "Create a pasta recipe"
AI: (respects vegan preference, no dairy/meat)
```

### Scenario 3: Search-Based Recipe Creation
```
User: "Search for popular Asian stir-fry recipes and create one for me"
AI: 
  1. Uses search_web tool
  2. Finds relevant recipes
  3. Creates a recipe based on findings
  4. Asks for confirmation
```

### Scenario 4: Import from URL
```
User: "Make this recipe: https://foodblog.com/amazing-cake"
AI:
  1. Uses fetch_url tool
  2. Extracts recipe details (ingredients, instructions)
  3. Formats as a proper recipe
  4. Asks for confirmation
  5. Saves to your account
```

## API Endpoints Reference

### POST /api/v1/ai/chat
**New Parameter**: `use_dietary_preferences` (boolean, default: true)

**Example Request**:
```json
{
  "messages": [
    {"role": "user", "content": "Create a vegan recipe"}
  ],
  "use_dietary_preferences": true
}
```

### POST /api/v1/ai/execute-tool
**New Tool Names**:
- `search_web` - Search the internet
- `fetch_url` - Fetch content from a URL

**Example Request (Search)**:
```json
{
  "name": "search_web",
  "arguments": {
    "query": "healthy breakfast recipes",
    "max_results": 5
  }
}
```

**Example Request (Fetch URL)**:
```json
{
  "name": "fetch_url",
  "arguments": {
    "url": "https://example.com/recipe"
  }
}
```

## Security Notes

1. **URL Fetching**: 
   - 30-second timeout to prevent hanging
   - Content limited to 8000 characters
   - Scripts and styles are removed
   - Uses identifiable User-Agent

2. **SEARXNG URL**: Only admins can configure

3. **Rate Limiting**: Consider implementing rate limits for production use

## Next Steps

After setup, consider:
1. Testing with various recipe websites
2. Monitoring SEARXNG usage and performance
3. Adding rate limiting for search/fetch operations
4. Implementing caching for frequently accessed URLs
5. Adding user feedback for imported recipes
