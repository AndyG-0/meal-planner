import { describe, it, expect, vi, beforeEach } from 'vitest';
import { 
  authService, 
  recipeService, 
  calendarService, 
  groceryListService,
  groupService,
  collectionService 
} from './index';
import api from './api';

vi.mock('./api');

describe('authService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should check if setup is required', async () => {
    const mockResponse = { data: { setup_required: true } };
    api.get.mockResolvedValue(mockResponse);

    const result = await authService.checkSetupRequired();

    expect(api.get).toHaveBeenCalledWith('/auth/setup-required');
    expect(result).toEqual(mockResponse.data);
  });

  it('should setup admin user', async () => {
    const mockResponse = { data: { id: 1, username: 'admin', is_admin: true } };
    api.post.mockResolvedValue(mockResponse);

    const result = await authService.setupAdmin('admin', 'admin@example.com', 'password');

    expect(api.post).toHaveBeenCalledWith('/auth/setup-admin', {
      username: 'admin',
      email: 'admin@example.com',
      password: 'password',
    });
    expect(result).toEqual(mockResponse.data);
  });

  it('should register a user', async () => {
    const mockResponse = { data: { id: 1, username: 'testuser' } };
    api.post.mockResolvedValue(mockResponse);

    const result = await authService.register('testuser', 'test@example.com', 'password');

    expect(api.post).toHaveBeenCalledWith('/auth/register', {
      username: 'testuser',
      email: 'test@example.com',
      password: 'password',
    });
    expect(result).toEqual(mockResponse.data);
  });

  it('should login a user', async () => {
    const mockResponse = { data: { token: 'test-token' } };
    api.post.mockResolvedValue(mockResponse);

    const result = await authService.login('testuser', 'password');

    expect(api.post).toHaveBeenCalled();
    expect(result).toEqual(mockResponse.data);
  });

  it('should get current user', async () => {
    const mockResponse = { data: { id: 1, username: 'testuser' } };
    api.get.mockResolvedValue(mockResponse);

    const result = await authService.getCurrentUser();

    expect(api.get).toHaveBeenCalledWith('/auth/me');
    expect(result).toEqual(mockResponse.data);
  });

  it('should search users', async () => {
    const mockResponse = { data: [{ id: 1, username: 'user1' }] };
    api.get.mockResolvedValue(mockResponse);

    const result = await authService.searchUsers('user1');

    expect(api.get).toHaveBeenCalledWith('/auth/users/search', { params: { q: 'user1' } });
    expect(result).toEqual(mockResponse.data);
  });
});

describe('recipeService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should get recipes', async () => {
    const mockResponse = { data: { items: [], pagination: {} } };
    api.get.mockResolvedValue(mockResponse);

    const result = await recipeService.getRecipes();

    expect(api.get).toHaveBeenCalledWith('/recipes', { params: {} });
    expect(result).toEqual(mockResponse.data);
  });

  it('should get a single recipe', async () => {
    const mockResponse = { data: { id: 1, name: 'Test Recipe' } };
    api.get.mockResolvedValue(mockResponse);

    const result = await recipeService.getRecipe(1);

    expect(api.get).toHaveBeenCalledWith('/recipes/1');
    expect(result).toEqual(mockResponse.data);
  });

  it('should create a recipe', async () => {
    const mockRecipe = { name: 'New Recipe', ingredients: [] };
    const mockResponse = { data: { id: 1, ...mockRecipe } };
    api.post.mockResolvedValue(mockResponse);

    const result = await recipeService.createRecipe(mockRecipe);

    expect(api.post).toHaveBeenCalledWith('/recipes', mockRecipe);
    expect(result).toEqual(mockResponse.data);
  });

  it('should update a recipe', async () => {
    const mockData = { name: 'Updated Recipe' };
    const mockResponse = { data: { id: 1, ...mockData } };
    api.put.mockResolvedValue(mockResponse);

    const result = await recipeService.updateRecipe(1, mockData);

    expect(api.put).toHaveBeenCalledWith('/recipes/1', mockData);
    expect(result).toEqual(mockResponse.data);
  });

  it('should delete a recipe', async () => {
    api.delete.mockResolvedValue({});

    await recipeService.deleteRecipe(1);

    expect(api.delete).toHaveBeenCalledWith('/recipes/1');
  });

  it('should favorite a recipe', async () => {
    const mockResponse = { data: { favorite: true } };
    api.post.mockResolvedValue(mockResponse);

    const result = await recipeService.favoriteRecipe(1);

    expect(api.post).toHaveBeenCalledWith('/recipes/1/favorite');
    expect(result).toEqual(mockResponse.data);
  });

  it('should unfavorite a recipe', async () => {
    api.delete.mockResolvedValue({});

    await recipeService.unfavoriteRecipe(1);

    expect(api.delete).toHaveBeenCalledWith('/recipes/1/favorite');
  });

  it('should rate a recipe', async () => {
    const mockResponse = { data: { rating: 5 } };
    api.post.mockResolvedValue(mockResponse);

    const result = await recipeService.rateRecipe(1, 5, 'Great!');

    expect(api.post).toHaveBeenCalledWith('/recipes/1/ratings', { rating: 5, review: 'Great!' });
    expect(result).toEqual(mockResponse.data);
  });

  it('should add tag to recipe', async () => {
    const mockResponse = { data: { id: 1, tag_name: 'vegan' } };
    api.post.mockResolvedValue(mockResponse);

    const result = await recipeService.addTag(1, 'vegan', 'dietary');

    expect(api.post).toHaveBeenCalledWith('/recipes/1/tags', { tag_name: 'vegan', tag_category: 'dietary' });
    expect(result).toEqual(mockResponse.data);
  });

  it('should remove tag from recipe', async () => {
    api.delete.mockResolvedValue({});

    await recipeService.removeTag(1, 2);

    expect(api.delete).toHaveBeenCalledWith('/recipes/1/tags/2');
  });

  it('should get all tags', async () => {
    const mockResponse = { data: [{ id: 1, name: 'vegan' }] };
    api.get.mockResolvedValue(mockResponse);

    const result = await recipeService.getAllTags();

    expect(api.get).toHaveBeenCalledWith('/recipes/tags/all');
    expect(result).toEqual(mockResponse.data);
  });
});

describe('calendarService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should get calendars', async () => {
    const mockResponse = { data: [{ id: 1, name: 'Calendar 1' }] };
    api.get.mockResolvedValue(mockResponse);

    const result = await calendarService.getCalendars();

    expect(api.get).toHaveBeenCalledWith('/calendars', { params: {} });
    expect(result).toEqual(mockResponse.data);
  });

  it('should get a single calendar', async () => {
    const mockResponse = { data: { id: 1, name: 'Calendar 1' } };
    api.get.mockResolvedValue(mockResponse);

    const result = await calendarService.getCalendar(1);

    expect(api.get).toHaveBeenCalledWith('/calendars/1');
    expect(result).toEqual(mockResponse.data);
  });

  it('should create a calendar', async () => {
    const mockData = { name: 'New Calendar' };
    const mockResponse = { data: { id: 1, ...mockData } };
    api.post.mockResolvedValue(mockResponse);

    const result = await calendarService.createCalendar(mockData);

    expect(api.post).toHaveBeenCalledWith('/calendars', mockData);
    expect(result).toEqual(mockResponse.data);
  });

  it('should get calendar meals', async () => {
    const mockResponse = { data: [{ id: 1, recipe_id: 1 }] };
    api.get.mockResolvedValue(mockResponse);

    const result = await calendarService.getCalendarMeals(1);

    expect(api.get).toHaveBeenCalledWith('/calendars/1/meals', { params: {} });
    expect(result).toEqual(mockResponse.data);
  });

  it('should add meal to calendar', async () => {
    const mockData = { recipe_id: 1, date: '2024-01-01' };
    const mockResponse = { data: { id: 1, ...mockData } };
    api.post.mockResolvedValue(mockResponse);

    const result = await calendarService.addMealToCalendar(1, mockData);

    expect(api.post).toHaveBeenCalledWith('/calendars/1/meals', mockData);
    expect(result).toEqual(mockResponse.data);
  });

  it('should remove meal from calendar', async () => {
    api.delete.mockResolvedValue({});

    await calendarService.removeMealFromCalendar(1, 2);

    expect(api.delete).toHaveBeenCalledWith('/calendars/1/meals/2');
  });

  it('should prepopulate calendar', async () => {
    const mockData = { start_date: '2024-01-01', end_date: '2024-01-07' };
    const mockResponse = { data: { meals_created: 7 } };
    api.post.mockResolvedValue(mockResponse);

    const result = await calendarService.prepopulateCalendar(1, mockData);

    expect(api.post).toHaveBeenCalledWith('/calendars/1/prepopulate', mockData);
    expect(result).toEqual(mockResponse.data);
  });

  it('should copy calendar period', async () => {
    const mockData = { source_start: '2024-01-01', source_end: '2024-01-07' };
    const mockResponse = { data: { meals_copied: 7 } };
    api.post.mockResolvedValue(mockResponse);

    const result = await calendarService.copyCalendarPeriod(1, mockData);

    expect(api.post).toHaveBeenCalledWith('/calendars/1/copy', mockData);
    expect(result).toEqual(mockResponse.data);
  });
});

describe('groceryListService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should get grocery lists', async () => {
    const mockResponse = { data: [{ id: 1, name: 'List 1' }] };
    api.get.mockResolvedValue(mockResponse);

    const result = await groceryListService.getGroceryLists();

    expect(api.get).toHaveBeenCalledWith('/grocery-lists');
    expect(result).toEqual(mockResponse.data);
  });

  it('should create grocery list', async () => {
    const mockData = { name: 'New List' };
    const mockResponse = { data: { id: 1, ...mockData } };
    api.post.mockResolvedValue(mockResponse);

    const result = await groceryListService.createGroceryList(1, mockData);

    expect(api.post).toHaveBeenCalledWith('/grocery-lists', mockData, {
      params: { calendar_id: 1 },
    });
    expect(result).toEqual(mockResponse.data);
  });

  it('should get a single grocery list', async () => {
    const mockResponse = { data: { id: 1, name: 'List 1' } };
    api.get.mockResolvedValue(mockResponse);

    const result = await groceryListService.getGroceryList(1);

    expect(api.get).toHaveBeenCalledWith('/grocery-lists/1');
    expect(result).toEqual(mockResponse.data);
  });

  it('should delete grocery list', async () => {
    api.delete.mockResolvedValue({});

    await groceryListService.deleteGroceryList(1);

    expect(api.delete).toHaveBeenCalledWith('/grocery-lists/1');
  });

  it('should update grocery list', async () => {
    const mockItems = [{ id: 1, checked: true }];
    const mockResponse = { data: { id: 1, items: mockItems } };
    api.patch.mockResolvedValue(mockResponse);

    const result = await groceryListService.updateGroceryList(1, mockItems);

    expect(api.patch).toHaveBeenCalledWith('/grocery-lists/1', mockItems);
    expect(result).toEqual(mockResponse.data);
  });
});

describe('groupService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should get groups', async () => {
    const mockResponse = { data: [{ id: 1, name: 'Group 1' }] };
    api.get.mockResolvedValue(mockResponse);

    const result = await groupService.getGroups();

    expect(api.get).toHaveBeenCalledWith('/groups');
    expect(result).toEqual(mockResponse.data);
  });

  it('should get a single group', async () => {
    const mockResponse = { data: { id: 1, name: 'Group 1' } };
    api.get.mockResolvedValue(mockResponse);

    const result = await groupService.getGroup(1);

    expect(api.get).toHaveBeenCalledWith('/groups/1');
    expect(result).toEqual(mockResponse.data);
  });

  it('should create a group', async () => {
    const mockData = { name: 'New Group' };
    const mockResponse = { data: { id: 1, ...mockData } };
    api.post.mockResolvedValue(mockResponse);

    const result = await groupService.createGroup(mockData);

    expect(api.post).toHaveBeenCalledWith('/groups', mockData);
    expect(result).toEqual(mockResponse.data);
  });

  it('should update a group', async () => {
    const mockData = { name: 'Updated Group' };
    const mockResponse = { data: { id: 1, ...mockData } };
    api.patch.mockResolvedValue(mockResponse);

    const result = await groupService.updateGroup(1, mockData);

    expect(api.patch).toHaveBeenCalledWith('/groups/1', mockData);
    expect(result).toEqual(mockResponse.data);
  });

  it('should delete a group', async () => {
    api.delete.mockResolvedValue({});

    await groupService.deleteGroup(1);

    expect(api.delete).toHaveBeenCalledWith('/groups/1');
  });

  it('should get group members', async () => {
    const mockResponse = { data: [{ id: 1, user_id: 1 }] };
    api.get.mockResolvedValue(mockResponse);

    const result = await groupService.getGroupMembers(1);

    expect(api.get).toHaveBeenCalledWith('/groups/1/members');
    expect(result).toEqual(mockResponse.data);
  });

  it('should add group member', async () => {
    const mockData = { user_id: 1 };
    const mockResponse = { data: { id: 1, ...mockData } };
    api.post.mockResolvedValue(mockResponse);

    const result = await groupService.addGroupMember(1, mockData);

    expect(api.post).toHaveBeenCalledWith('/groups/1/members', mockData);
    expect(result).toEqual(mockResponse.data);
  });

  it('should remove group member', async () => {
    api.delete.mockResolvedValue({});

    await groupService.removeGroupMember(1, 2);

    expect(api.delete).toHaveBeenCalledWith('/groups/1/members/2');
  });
});

describe('collectionService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should get collections', async () => {
    const mockResponse = { data: [{ id: 1, name: 'Collection 1' }] };
    api.get.mockResolvedValue(mockResponse);

    const result = await collectionService.getCollections();

    expect(api.get).toHaveBeenCalledWith('/collections');
    expect(result).toEqual(mockResponse.data);
  });

  it('should get a single collection', async () => {
    const mockResponse = { data: { id: 1, name: 'Collection 1' } };
    api.get.mockResolvedValue(mockResponse);

    const result = await collectionService.getCollection(1);

    expect(api.get).toHaveBeenCalledWith('/collections/1');
    expect(result).toEqual(mockResponse.data);
  });

  it('should create a collection', async () => {
    const mockData = { name: 'New Collection' };
    const mockResponse = { data: { id: 1, ...mockData } };
    api.post.mockResolvedValue(mockResponse);

    const result = await collectionService.createCollection(mockData);

    expect(api.post).toHaveBeenCalledWith('/collections', mockData);
    expect(result).toEqual(mockResponse.data);
  });

  it('should update a collection', async () => {
    const mockData = { name: 'Updated Collection' };
    const mockResponse = { data: { id: 1, ...mockData } };
    api.patch.mockResolvedValue(mockResponse);

    const result = await collectionService.updateCollection(1, mockData);

    expect(api.patch).toHaveBeenCalledWith('/collections/1', mockData);
    expect(result).toEqual(mockResponse.data);
  });

  it('should delete a collection', async () => {
    api.delete.mockResolvedValue({});

    await collectionService.deleteCollection(1);

    expect(api.delete).toHaveBeenCalledWith('/collections/1');
  });

  it('should get collection recipes', async () => {
    const mockResponse = { data: [{ id: 1, name: 'Recipe 1' }] };
    api.get.mockResolvedValue(mockResponse);

    const result = await collectionService.getCollectionRecipes(1);

    expect(api.get).toHaveBeenCalledWith('/collections/1/recipes');
    expect(result).toEqual(mockResponse.data);
  });

  it('should add recipe to collection', async () => {
    const mockResponse = { data: { collection_id: 1, recipe_id: 2 } };
    api.post.mockResolvedValue(mockResponse);

    const result = await collectionService.addRecipeToCollection(1, 2);

    expect(api.post).toHaveBeenCalledWith('/collections/1/recipes/2');
    expect(result).toEqual(mockResponse.data);
  });

  it('should remove recipe from collection', async () => {
    api.delete.mockResolvedValue({});

    await collectionService.removeRecipeFromCollection(1, 2);

    expect(api.delete).toHaveBeenCalledWith('/collections/1/recipes/2');
  });
});
