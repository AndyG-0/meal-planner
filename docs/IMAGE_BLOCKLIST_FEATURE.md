# Image Download Validation and Blocklist Feature

## Overview

This feature implements comprehensive image download validation and domain blocking for recipe images. It proactively checks if images can be downloaded before attempting the download, auto-blocks domains that return 403 errors, and provides admin tools to manage a blocklist.

## Features

### 1. Pre-Download Validation
- **Frontend validation** before attempting to download images
- Validates that image URLs are accessible without actually downloading
- User-friendly error messages when validation fails
- Prevents wasted time and bandwidth on failed downloads

### 2. Domain Blocklist System
- **Database table** to store blocked image domains
- **Auto-blocking** of domains that return 403 Forbidden errors
- **Manual blocking** via admin interface
- Blocks checked before any image download attempt
- **Filtered from search results** - Blocked domains are automatically excluded from both AI and user image search results

### 3. Admin Management UI
- **Block list management** in Admin Dashboard → Settings tab
- Add new domains to blocklist with optional reason
- View all blocked domains with timestamps
- Remove domains from blocklist
- See auto-blocked vs manually blocked domains

## Technical Implementation

### Backend Changes

#### Database Schema
```python
# New table: blocked_image_domains
- id: Integer (Primary Key)
- domain: String (Unique, indexed)
- reason: String (optional)
- created_at: DateTime (auto-populated)
- created_by_id: Integer (Foreign Key to users)
```

#### New Files
1. **backend/app/models/blocked_domain.py**
   - BlockedImageDomain model
   - Relationship to User model

2. **backend/app/schemas/blocked_domain.py**
   - BlockedDomainCreate schema
   - BlockedDomainResponse schema
   - BlockedDomainBase schema

3. **backend/alembic/versions/add_blocked_image_domains.py**
   - Migration to create blocked_image_domains table

#### Enhanced Endpoints

**`/image-proxy` (GET)** - Enhanced with:
- `validate_only` parameter for HEAD requests
- Domain extraction and normalization (removes www, lowercases)
- Blocklist check before download
- Auto-blocking on 403 errors
- Clear error messages for blocked domains

**Admin Endpoints:**
- `GET /admin/blocked-domains` - List all blocked domains
- `POST /admin/blocked-domains` - Add domain to blocklist
- `DELETE /admin/blocked-domains/{domain_id}` - Remove from blocklist

**Image Search Filtering:**
- `/ai/search-images` endpoint now filters blocked domains from results
- OpenAIService.search_images() method queries blocked domains before returning results
- Blocked images are excluded, ensuring users only see downloadable options
- Logging tracks how many images were filtered from each search

### Frontend Changes

#### Recipe Management (Recipes.jsx)
**Pre-download validation in both create and update flows:**
```javascript
// Validation check before downloading
const validateUrl = `/image-proxy?image_url=${encodeURIComponent(url)}&validate_only=true`
const validateResponse = await fetch(validateUrl)
if (!validateResponse.ok) {
  // Show error, don't attempt download
}
```

**Enhanced error handling:**
- Different messages for blocked domains vs general failures
- Snackbar notifications for user feedback
- Graceful fallback (save recipe without image)

#### Admin Dashboard
**New "Image Download Block List" section in Settings tab:**
- Add domain form with domain and reason fields
- Table showing all blocked domains
- Delete button to unblock domains
- Timestamps for when domains were blocked

## Usage

### For Users
1. When selecting an image from search results, the system validates it first
2. If validation fails, a clear error message appears
3. Users can try a different image or upload a file instead
4. No more broken recipe images or confusing errors

### For Admins
1. Navigate to Admin Dashboard → Settings tab
2. Scroll to "Image Download Block List" section
3. To block a domain:
   - Enter domain (e.g., "example.com")
   - Optionally enter reason
   - Click "Block Domain"
4. To unblock: Click delete icon next to domain
5. View all auto-blocked domains from 403 errors

## Auto-Blocking Behavior

When an image download attempt receives a 403 Forbidden response:
1. The backend logs the blocked domain
2. Adds domain to `blocked_image_domains` table
3. Reason: "Auto-blocked: Returned 403 Forbidden"
4. Future attempts to download from this domain are prevented
5. Admin can review and remove if desired

## Image Search Filtering

Blocked domains are automatically filtered from image search results:
1. When a user or AI searches for images via `/ai/search-images`
2. Backend queries the blocklist from the database
3. Each image result's domain is extracted and normalized
4. Results from blocked domains are excluded before returning to the user
5. Logs show how many images were filtered from each search
6. Users only see images from domains that allow downloads

This prevents frustration by ensuring search results only contain usable images.

## Migration

To apply the database schema:
```bash
cd backend
uv run alembic upgrade head
```

## Testing

### Test Pre-Download Validation
1. Create/edit a recipe
2. Select image from search results  
3. Try an image from a blocked domain
4. Should see error message without recipe creation failure

### Test Admin Blocklist
1. Login as admin
2. Navigate to Admin Dashboard → Settings
3. Scroll to "Image Download Block List"
4. Add a test domain (e.g., "test.com")
5. Verify it appears in the list
6. Delete it
7. Verify it's removed

### Test Auto-Blocking
1. Find an image URL that returns 403 (e.g., greengiantvegetables.com)
2. Try to use it in a recipe
3. Check Admin Dashboard → Settings → Block List
4. Domain should appear with "Auto-blocked: Returned 403 Forbidden"

## Benefits

1. **Better UX**: Users get immediate feedback instead of silently failing
2. **Prevents clutter**: No more HTML files saved as images
3. **Saves time**: Don't waste time on images that won't work
4. **Self-healing**: Auto-blocking prevents repeated failures
5. **Admin control**: Full visibility and management of blocklist
6. **Proactive**: Validation before download, not after
7. **Clean search results**: Blocked domains filtered from image search, users only see working options

## Future Enhancements

Potential improvements:
- Import/export blocklist
- Whitelist for specific users/recipes
- Analytics on blocked attempts
- Bulk add domains from CSV
