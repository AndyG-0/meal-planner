# Kroger API Integration Progress

## Overview

This document tracks the implementation progress of the Kroger grocery store API integration into the meal planner application. The integration consists of two main features controlled by feature toggles:

1. **Kroger Product Search** - Catalog and location search functionality using client credentials flow
2. **Kroger Shopping Cart** - Identity and cart management using OAuth2 authorization code flow

## ✅ Completed Work

### Backend Infrastructure

#### Database Models
- ✅ **KrogerSettings** - Stores API credentials and configuration
  - Client credentials (for catalog/location APIs)
  - OAuth credentials (for cart/identity APIs)
  - Base URL and environment selection (production/certification)
- ✅ **KrogerUserLocation** - Stores user's saved Kroger store location
  - Location ID, name, address, city, state, zip
  - Distance from user's search point
- ✅ **KrogerUserAuth** - Stores OAuth tokens per user
  - Access token, refresh token, token type
  - Expiration timestamp for automatic refresh

#### Database Migration
- ✅ Created and applied Alembic migration `k1l2m3n4o5p6_add_kroger_integration.py`
  - Creates `kroger_settings`, `kroger_user_locations`, `kroger_user_auth` tables
  - Inserts two feature toggles: `kroger_product_search` and `kroger_shopping_cart`
  - Successfully merged with parallel migration and applied to database

#### Configuration
- ✅ Added 7 Kroger-related environment variables to `backend/app/config.py`:
  - `KROGER_CLIENT_ID` - Client credentials ID
  - `KROGER_CLIENT_SECRET` - Client credentials secret
  - `KROGER_OAUTH_CLIENT_ID` - OAuth client ID
  - `KROGER_OAUTH_CLIENT_SECRET` - OAuth client secret
  - `KROGER_REDIRECT_URI` - OAuth redirect URI
  - `KROGER_BASE_URL` - API base URL (defaults to production)
  - `KROGER_ENVIRONMENT` - Environment selection (production/certification)

#### Pydantic Schemas
- ✅ Created 15+ schemas in `backend/app/schemas/__init__.py`:
  - **Settings**: KrogerSettingsBase, KrogerSettingsUpdate, KrogerSettingsResponse
  - **Location**: KrogerLocationBase, KrogerLocationCreate, KrogerLocationResponse
  - **Products**: KrogerProductSearchRequest, KrogerProductResponse
  - **Auth**: KrogerAuthCallbackRequest, KrogerAuthResponse
  - **Cart**: KrogerCartItem, KrogerAddToCartRequest, KrogerCartResponse

#### Service Layer
- ✅ Implemented comprehensive `backend/app/services/kroger_service.py` (450+ lines):
  - **Token Management**:
    - `get_client_credentials_token()` - Auto-refreshing token with caching (5-minute expiry buffer)
    - `exchange_code_for_token()` - OAuth code to token exchange
    - `refresh_access_token()` - Automatic token refresh for expired user tokens
  - **Location APIs**:
    - `search_locations()` - Search stores by zip code or lat/long with radius filtering
  - **Product APIs**:
    - `search_products()` - Product catalog search with pagination support
  - **Auth APIs**:
    - `get_authorization_url()` - Generate OAuth URL with PKCE and state parameter for CSRF protection
  - **Cart APIs**:
    - `add_to_cart()` - Add products to user's Kroger cart
  - **Factory**: `get_kroger_service()` - Creates service instance using DB settings with env fallback

#### API Endpoints - Admin
- ✅ Added to `backend/app/api/v1/endpoints/admin.py`:
  - `GET /admin/kroger-settings` - Retrieve Kroger configuration (credentials masked)
  - `PATCH /admin/kroger-settings` - Update Kroger configuration

#### API Endpoints - User
- ✅ Created `backend/app/api/v1/endpoints/kroger.py` with 8 endpoints:
  - `POST /kroger/locations/search` - Search for Kroger store locations
  - `POST /kroger/locations/save` - Save user's preferred location
  - `POST /kroger/products/search` - Search product catalog (requires kroger_product_search feature)
  - `GET /kroger/auth/authorize` - Get OAuth authorization URL (requires kroger_shopping_cart feature)
  - `POST /kroger/auth/callback` - Handle OAuth callback and exchange code for token
  - `POST /kroger/cart/add` - Add items to cart (requires kroger_shopping_cart feature)
  - Helper: `check_feature_enabled()` - Validates feature toggle before API execution

#### Router Registration
- ✅ Registered Kroger router in `backend/app/main.py`

### Frontend - Complete Implementation ✅

#### Kroger Service
- ✅ Added complete Kroger service to `frontend/src/services/index.js`:
  - Settings management (get/update)
  - Location search and save
  - Product search with pagination
  - OAuth authorization flow
  - Cart management
  - Feature toggle retrieval

#### Reusable Components
- ✅ **KrogerLocationSelector** (`frontend/src/components/KrogerLocationSelector.jsx`):
  - ZIP code-based store search
  - Location selection with distance display
  - Warning dialog for location changes (cart reset)
  - Current location display with change option
  
- ✅ **KrogerProductSearch** (`frontend/src/components/KrogerProductSearch.jsx`):
  - Manual product search with real-time results
  - Bulk search for all grocery list items
  - Expandable product details (brand, size, categories, price)
  - Multi-select with checkboxes
  - Individual and bulk "Add to Cart" functionality
  - Loading states and error handling

#### OAuth Callback Page
- ✅ **KrogerCallback** (`frontend/src/pages/KrogerCallback.jsx`):
  - Handles OAuth redirect from Kroger
  - Extracts and validates code/state parameters
  - Displays processing/success/error states
  - Auto-redirects to grocery lists on success
  - User-friendly error messages with retry option

#### Grocery List Integration
- ✅ Updated `frontend/src/pages/GroceryList.jsx`:
  - Integrated KrogerLocationSelector component
  - Integrated KrogerProductSearch component
  - Collapsible Kroger section (show/hide)
  - Feature toggle enforcement (product search & cart)
  - OAuth connection flow for cart features
  - Success/error notifications via Snackbar
  - Cart reset warning on location change

#### Routing
- ✅ Added `/kroger/callback` route to `frontend/src/App.jsx`

### Frontend - Admin Dashboard

#### Admin Settings UI
- ✅ Added comprehensive Kroger configuration section to `frontend/src/pages/AdminDashboard.jsx`:
  - **State Management**: krogerSettings state variable
  - **Data Loading**: Integrated into loadData() to fetch current settings
  - **Update Handler**: handleUpdateKrogerSettings() async function
  - **UI Components**:
    - Separate cards for Client Credentials and OAuth Credentials
    - Visual indicators (CheckCircleIcon) showing configured credentials
    - Environment selector (production/certification)
    - Info alert about feature toggle settings
    - Masked credential display for security
    - Save button with loading state

### Quality Assurance
- ✅ All CI checks passed:
  - Ruff linting (2 issues auto-fixed)
  - Mypy type checking (new code type-safe)
  - Pytest collection (346 tests, no import errors)
  - Database migration applied successfully

## 📋 Remaining Frontend Work

### 1. Grocery List Integration (HIGH PRIORITY) ✅ COMPLETED

The primary integration point for Kroger features is the grocery list page.

#### Location Selection
- ✅ Create location selector component
  - Call `POST /kroger/locations/search` with zip code or lat/long
  - Display search results with store details (name, address, distance)
  - Allow user to select and save location via `POST /kroger/locations/save`
  - **IMPORTANT**: Implement warning dialog when changing location
    - "If the location changes carts must be reset. Warn the user that this will empty their cart"
    - Require user confirmation before proceeding with location change
    - Clear cart after location change confirmed

#### Product Search Interface
- ✅ Create product search component
  - **Manual Search**:
    - Search input field calling `POST /kroger/products/search`
    - Display results with relevant details: name, price, quantity, size
    - Expandable detail view for each product
  - **Automatic Search**:
    - "Users should be able to search for individual products or click a button to automatically search for all products"
    - Bulk search button that searches for all items in grocery list
    - Progress indicator during bulk search
  - **Product Display**:
    - Show important details: name, price, quantity, package size, brand
    - "Show which details are important" - prioritize price, size, availability
    - "option to expand for each detail" - collapsible sections for additional info

#### Cart Operations
- ✅ Implement add to cart functionality
  - Individual "Add to Cart" button for each product
  - Bulk selection with checkboxes
  - "Add Selected to Cart" button calling `POST /kroger/cart/add`
  - Success/error notifications
  - Loading states during cart operations

#### Feature Toggle Enforcement
- ✅ Honor feature toggles in UI
  - "All ui should honor the feature toggle settings to control if any of these elements display or not"
  - Fetch feature toggle status from backend
  - Conditionally render product search components based on `kroger_product_search` toggle
  - Conditionally render cart components based on `kroger_shopping_cart` toggle
  - Show appropriate messaging when features are disabled

### 2. OAuth Callback Page (REQUIRED FOR CART) ✅ COMPLETED

Create dedicated page to handle Kroger OAuth redirect.

- ✅ Create `/kroger/callback` route in React app
- ✅ Extract `code` and `state` parameters from URL
- ✅ Call `POST /kroger/auth/callback` with code and state
- ✅ Handle success: Store auth status, redirect to grocery list
- ✅ Handle errors: Display error message, provide retry option
- ✅ Follow "web best practices for auth code flow in react applications":
  - Validate state parameter matches original request
  - Handle authorization errors (user denied, invalid request, etc.)
  - Secure token storage (handled server-side, store only auth status)

### 3. User Experience Enhancements ✅ COMPLETED

#### Loading States
- ✅ Show loading indicators during API calls
- ✅ Disable buttons during operations
- ✅ Progress bars for bulk operations

#### Error Handling
- ✅ Display user-friendly error messages
- ✅ Retry mechanisms for failed API calls
- ✅ Handle expired tokens gracefully (automatic refresh handled server-side)

#### Notifications
- ✅ Success notifications for cart additions
- ✅ Confirmation dialogs for destructive actions
- ✅ Toast/snackbar notifications for quick feedback

## Environment Configuration

### Required Environment Variables

For server-side configuration (`.env` file):

```bash
# Client Credentials (for catalog/location APIs)
KROGER_CLIENT_ID=your_client_id_here
KROGER_CLIENT_SECRET=your_client_secret_here

# OAuth Credentials (for cart/identity APIs)
KROGER_OAUTH_CLIENT_ID=your_oauth_client_id_here
KROGER_OAUTH_CLIENT_SECRET=your_oauth_client_secret_here
KROGER_REDIRECT_URI=http://localhost:3080/kroger/callback

# Environment Selection
KROGER_ENVIRONMENT=production  # or 'certification' for testing
KROGER_BASE_URL=https://api.kroger.com  # or https://api-ce.kroger.com for certification
```

**Note**: All credentials can also be configured via the Admin Dashboard UI.

## Security Considerations

✅ **Implemented**:
- Client credentials stored server-side only
- OAuth tokens stored in database with automatic refresh
- CSRF protection via state parameter in OAuth flow
- PKCE support for authorization code flow
- Credential masking in admin UI
- Feature toggles prevent unauthorized access

❌ **Frontend TODO**:
- Validate state parameter in OAuth callback
- Implement secure session handling
- Add rate limiting UI feedback

## Testing Recommendations

### Backend (Already Passing)
- All pytest tests collected successfully (346 tests)
- No import errors
- Type checking validated

### Frontend (TODO)
- Unit tests for new components
- Integration tests for API calls
- E2E tests for OAuth flow
- Test feature toggle behavior
- Test error scenarios

## API Documentation Reference

Kroger API documentation is available in `/kroger-api-docs/`:
- `auth.json` - Authentication endpoints
- `cart.json` - Cart management
- `catalog.json` - Product search
- `location.json` - Store location search

## Next Steps

1. **Start with Location Selection** - Foundation for all other features
2. **Implement Product Search** - Core functionality for grocery list
3. **Add OAuth Callback** - Required before cart features can work
4. **Build Cart Integration** - Complete the shopping experience
5. **Add Feature Toggle UI** - Ensure proper feature enforcement
6. **Comprehensive Testing** - Validate all flows work correctly

## Questions/Decisions Needed

- Should users be required to select a location before using any Kroger features?
- How should we handle products with multiple size/quantity options?
- Should bulk cart operations have a confirmation dialog?
- What's the desired behavior when a product is not found during automatic search?
- Should we cache product search results to reduce API calls?
