# Permissions System Documentation

## Overview

The meal planner application now includes a comprehensive permissions system that allows for granular control over who can view, edit, and manage recipes, calendars, and grocery lists.

## Visibility Levels

All main objects (recipes, calendars, grocery lists) now support three visibility levels:

### 1. **Private**
- Only visible to the owner
- Cannot be viewed or edited by other users
- Default visibility for new objects

### 2. **Group**
- Visible to all members of a specific group
- Group members can view the object
- Group admins can edit the object
- Requires selecting a group when creating/editing

### 3. **Public**
- Visible to all authenticated users
- Anyone can view
- Only owner and admins can edit

## User Roles

### Regular User
- Can create and manage their own content
- Can view public content
- Can view and participate in group content (if group member)

### Group Admin
- All regular user permissions
- Can edit group content in their groups
- Can manage group members

### System Administrator
- Full access to all content
- Can view, edit, and delete any object
- Access to admin dashboard
- Can manage users (promote to admin, delete users)
- Can view system statistics

## Database Schema Changes

### New/Updated Tables

#### users
- Added `is_admin` (boolean) - Indicates if user has admin privileges

#### recipes
- Added `visibility` (string) - One of: 'private', 'group', 'public'
- Added `group_id` (integer, nullable) - References groups table
- Deprecated `is_shared` and `is_public` (kept for backward compatibility)

#### calendars
- Added `visibility` (string) - One of: 'private', 'group', 'public'
- Deprecated `is_shared` (kept for backward compatibility)

#### grocery_lists
- Added `visibility` (string) - One of: 'private', 'group', 'public'
- Added `group_id` (integer, nullable) - References groups table

## API Endpoints

### Admin Endpoints (Admin Only)

#### GET /api/v1/admin/stats
Returns system-wide statistics:
- Total users, recipes, calendars, groups
- Recipe visibility breakdown (public/group/private)

#### GET /api/v1/admin/users
List all users with their statistics:
- User details
- Recipe count, calendar count, group count

#### GET /api/v1/admin/users/{user_id}
Get detailed information about a specific user

#### PATCH /api/v1/admin/users/{user_id}
Update user details (email, admin status)

#### DELETE /api/v1/admin/users/{user_id}
Soft delete a user (cannot delete yourself)

#### GET /api/v1/admin/recipes
List all recipes with optional visibility filter

#### DELETE /api/v1/admin/recipes/{recipe_id}
Delete any recipe (admin privilege)

### Permission Checks

The application now includes a `PermissionService` that handles all permission checks:

- `can_view_recipe()` - Check if user can view a recipe
- `can_edit_recipe()` - Check if user can edit a recipe
- `can_delete_recipe()` - Check if user can delete a recipe
- Similar methods for calendars and grocery lists

## Frontend Changes

### Recipe Form
Now includes visibility selector with options:
- Private (Only me)
- Group (Shared with group) - Shows group dropdown
- Public (Everyone)

### Admin Dashboard
- Accessible at `/admin` route
- Only visible to admin users
- Shows system statistics
- User management interface
- Recipe visibility breakdown

### Navigation
- Admin menu item appears only for admin users
- Links to admin dashboard

## Usage Examples

### Creating a Group Recipe

1. Create or select a recipe
2. Set visibility to "Group"
3. Select the group to share with
4. Save the recipe

Group members will now be able to view the recipe. Group admins can edit it.

### Making a User an Admin

1. Navigate to Admin Dashboard (admin only)
2. Click edit icon next to user
3. Toggle "Administrator" switch
4. Save changes

### Viewing System Statistics

1. Navigate to Admin Dashboard
2. View cards showing:
   - Total users, recipes, calendars, groups
   - Recipe visibility breakdown

## Migration

The database migration automatically converts existing data:
- `is_public=true` → `visibility='public'`
- `is_shared=true` → `visibility='group'`
- Otherwise → `visibility='private'`

The old `is_public` and `is_shared` fields are retained for backward compatibility but deprecated.

## Security Considerations

1. **Authentication Required**: All endpoints require authentication
2. **Admin Verification**: Admin endpoints verify `is_admin` flag
3. **Group Membership**: Group visibility checks actual group membership
4. **Owner Verification**: Delete operations verify ownership
5. **Permission Service**: Centralized permission logic prevents bypass

## Future Enhancements

Potential future features:
- Fine-grained group permissions (view-only, edit, admin)
- User roles within groups
- Shared editing capabilities
- Activity logs for admin actions
- Bulk user operations
- Content moderation tools
