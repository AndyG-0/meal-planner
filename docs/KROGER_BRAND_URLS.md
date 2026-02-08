# Kroger Brand URLs Feature

## Overview

The Kroger Brand URLs feature allows the system to dynamically select the correct cart and checkout URLs based on the user's selected store location. This is necessary because the Kroger Co. operates multiple store brands (Kroger, Ralphs, Fred Meyer, etc.), each with their own website domain.

## Database Schema

### `kroger_brand_urls` Table

Stores brand-specific cart and checkout URLs for all Kroger family brands.

| Column | Type | Description |
|--------|------|-------------|
| `id` | Integer | Primary key |
| `brand` | String(100) | Brand/chain name (uppercase, unique) |
| `display_name` | String(100) | User-friendly brand name |
| `cart_url` | String(500) | Production cart URL |
| `checkout_url` | String(500) | Production checkout URL |
| `certification_cart_url` | String(500) | Certification cart URL |
| `certification_checkout_url` | String(500) | Certification checkout URL |
| `is_active` | Boolean | Whether brand is active |
| `created_at` | DateTime | Creation timestamp |
| `updated_at` | DateTime | Last update timestamp |

## Supported Brands

The system supports all 19 Kroger family of companies brands:

1. **Kroger** - https://www.kroger.com
2. **Ralphs** - https://www.ralphs.com
3. **Fred Meyer** - https://www.fredmeyer.com
4. **King Soopers** - https://www.kingsoopers.com
5. **Smith's Food and Drug** - https://www.smithsfoodanddrug.com
6. **Fry's** - https://www.frysfood.com
7. **Dillons** - https://www.dillons.com
8. **City Market** - https://www.citymarket.com
9. **QFC** - https://www.qfc.com
10. **Baker's** - https://www.shopbakers.com
11. **Food 4 Less** - https://www.food4less.com
12. **Foods Co** - https://www.foodsco.net
13. **Gerbes** - https://www.gerbes.com
14. **Jay C Food Store** - https://www.jaycfoods.com
15. **Mariano's** - https://www.marianos.com
16. **Metro Market** - https://www.metromarket.net
17. **Pay-Less Super Markets** - https://www.pay-less.com
18. **Pick'n Save** - https://www.picknsave.com
19. **Ruler** - https://www.rulerfoods.com

## How It Works

### 1. Location Selection

When a user selects a Kroger store location, the `location_chain` field is stored in the `kroger_user_locations` table. This field comes from the Kroger Locations API and indicates which brand the store belongs to.

### 2. URL Resolution

When the user requests cart or checkout URLs:

1. **System retrieves the user's selected location** from `kroger_user_locations`
2. **Normalizes the chain name** to uppercase for matching
3. **Queries for brand-specific URLs** from `kroger_brand_urls` based on the chain
4. **Selects environment-specific URL** (production vs certification)
5. **Falls back to default URLs** from `kroger_settings` if no brand-specific URL found

### 3. API Endpoints

#### Get Cart URL
```
GET /api/v1/kroger/cart-url
```

Returns:
```json
{
  "cart_url": "https://www.ralphs.com/cart",
  "environment": "production",
  "brand": "RALPHS"
}
```

#### Get Checkout URL
```
GET /api/v1/kroger/checkout-url
```

Returns:
```json
{
  "checkout_url": "https://www.ralphs.com/checkout",
  "environment": "production",
  "brand": "RALPHS"
}
```

### 4. Admin Management

Admins can manage brand URLs through the following endpoints:

#### List All Brands
```
GET /api/v1/kroger/admin/brands
```

#### Create Brand
```
POST /api/v1/kroger/admin/brands
```

Request body:
```json
{
  "brand": "KROGER",
  "display_name": "Kroger",
  "cart_url": "https://www.kroger.com/cart",
  "checkout_url": "https://www.kroger.com/checkout",
  "certification_cart_url": "https://api-ce.kroger.com/cart",
  "certification_checkout_url": "https://api-ce.kroger.com/checkout",
  "is_active": true
}
```

#### Update Brand
```
PUT /api/v1/kroger/admin/brands/{brand_id}
```

Request body:
```json
{
  "display_name": "Updated Name",
  "cart_url": "https://new-url.com/cart",
  "is_active": false
}
```

#### Delete Brand
```
DELETE /api/v1/kroger/admin/brands/{brand_id}
```

## Database Migration

The migration script creates the `kroger_brand_urls` table:

```bash
cd backend
uv run alembic upgrade head
```

## Seeding Data

To populate the brand URLs with default values:

```bash
cd backend
uv run python seed_kroger_brands.py
```

This script will:
- Add all 19 Kroger family brands
- Set production cart and checkout URLs
- Mark all brands as active
- Update existing brands if they already exist

## Configuration

### Environment Variables

No new environment variables are required. The system uses existing Kroger API configuration from `kroger_settings`.

### Feature Flags

The brand URL selection is automatically enabled for all Kroger integrations. No feature flag is required.

## User Experience

### For Users

1. **Select a store location** (e.g., Ralphs in Los Angeles)
2. **Add items to cart** using product search
3. **Click "View Cart"** - opens the correct Ralphs cart URL
4. **Click "Checkout"** - opens the correct Ralphs checkout URL

The system automatically routes to the correct brand website based on the selected location.

### For Administrators

Administrators can:
- View all configured brands
- Add new brands if Kroger acquires/creates new chains
- Update URLs if brand websites change
- Deactivate brands that are no longer supported
- Configure separate URLs for certification environment

## Testing

### Manual Testing

1. Select a Ralphs location
2. Add items to cart
3. Click "View Cart" - verify it opens https://www.ralphs.com/cart
4. Click "Checkout" - verify it opens https://www.ralphs.com/checkout

### Backend Tests

```bash
cd backend
uv run pytest tests/ -k kroger -v
```

## Error Handling

### No Brand Found

If a user's location chain doesn't match any brand in the database:
- System falls back to default URLs from `kroger_settings`
- User experience is not impacted

### No URL Configured

If a brand exists but has no URL configured:
- System returns 404 error with descriptive message
- User is notified to contact support

### Invalid Location

If user has no location selected:
- Cart/checkout endpoints attempt to use default URLs
- User is prompted to select a location

## Future Enhancements

Potential improvements:
1. Auto-detect brand from location API response
2. Cache brand URLs for performance
3. Support for mobile app deep links
4. A/B testing different URL patterns
5. Analytics on brand usage

## References

- [Kroger Family of Companies](https://www.kroger.com/i/kroger-family-of-companies)
- Kroger Locations API Documentation
- Kroger Cart API Documentation
