import api from './api'

export const authService = {
  async checkSetupRequired() {
    const response = await api.get('/auth/setup-required')
    return response.data
  },

  async setupAdmin(username, email, password) {
    const response = await api.post('/auth/setup-admin', { username, email, password })
    return response.data
  },

  async register(username, email, password) {
    const response = await api.post('/auth/register', { username, email, password })
    return response.data
  },

  async login(username, password) {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    
    const response = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
    return response.data
  },

  async getCurrentUser() {
    const response = await api.get('/auth/me')
    return response.data
  },

  async searchUsers(query) {
    const response = await api.get('/auth/users/search', { params: { q: query } })
    return response.data
  },
}

export const recipeService = {
  async getRecipes(params = {}) {
    const response = await api.get('/recipes', { params })
    // Backend now returns paginated response: { items: [], pagination: {} }
    return response.data
  },

  async getRecipe(id) {
    const response = await api.get(`/recipes/${id}`)
    return response.data
  },

  async createRecipe(data) {
    const response = await api.post('/recipes', data)
    return response.data
  },

  async updateRecipe(id, data) {
    const response = await api.put(`/recipes/${id}`, data)
    return response.data
  },

  async deleteRecipe(id) {
    await api.delete(`/recipes/${id}`)
  },

  async favoriteRecipe(id) {
    const response = await api.post(`/recipes/${id}/favorite`)
    return response.data
  },

  async unfavoriteRecipe(id) {
    await api.delete(`/recipes/${id}/favorite`)
  },

  async rateRecipe(id, rating, review) {
    const response = await api.post(`/recipes/${id}/ratings`, { rating, review })
    return response.data
  },

  async addTag(id, tag_name, tag_category) {
    const response = await api.post(`/recipes/${id}/tags`, { tag_name, tag_category })
    return response.data
  },

  async removeTag(recipeId, tagId) {
    await api.delete(`/recipes/${recipeId}/tags/${tagId}`)
  },

  async uploadImage(id, formData) {
    const response = await api.post(`/recipes/${id}/image`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  async checkFeature(featureKey) {
    const response = await api.get(`/features/${featureKey}`)
    return response.data
  },

  async exportRecipes() {
    const response = await api.get('/recipes/export/all', {
      responseType: 'blob',
    })
    return response
  },

  async importRecipes(formData) {
    const response = await api.post('/recipes/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  async getNutrition(id) {
    const response = await api.get(`/recipes/${id}/nutrition`)
    return response.data
  },

  async getAllTags() {
    const response = await api.get('/recipes/tags/all')
    return response.data
  },
}

export const calendarService = {
  async getCalendars() {
    const response = await api.get('/calendars')
    return response.data
  },

  async getCalendar(id) {
    const response = await api.get(`/calendars/${id}`)
    return response.data
  },

  async createCalendar(data) {
    const response = await api.post('/calendars', data)
    return response.data
  },

  async getCalendarMeals(calendarId, params = {}) {
    const response = await api.get(`/calendars/${calendarId}/meals`, { params })
    return response.data
  },

  async addMealToCalendar(calendarId, data) {
    const response = await api.post(`/calendars/${calendarId}/meals`, data)
    return response.data
  },

  async removeMealFromCalendar(calendarId, mealId) {
    await api.delete(`/calendars/${calendarId}/meals/${mealId}`)
  },

  async prepopulateCalendar(calendarId, data) {
    const response = await api.post(`/calendars/${calendarId}/prepopulate`, data)
    return response.data
  },

  async copyCalendarPeriod(calendarId, data) {
    const response = await api.post(`/calendars/${calendarId}/copy`, data)
    return response.data
  },
}

export const groceryListService = {
  async getGroceryLists() {
    const response = await api.get('/grocery-lists')
    return response.data
  },

  async createGroceryList(calendarId, data) {
    const response = await api.post('/grocery-lists', data, {
      params: { calendar_id: calendarId },
    })
    return response.data
  },

  async getGroceryList(id) {
    const response = await api.get(`/grocery-lists/${id}`)
    return response.data
  },

  async deleteGroceryList(id) {
    await api.delete(`/grocery-lists/${id}`)
  },

  async updateGroceryList(listId, items) {
    const response = await api.patch(`/grocery-lists/${listId}`, items)
    return response.data
  },

  async exportCSV(listId) {
    const response = await api.get(`/grocery-lists/${listId}/export/csv`, {
      responseType: 'blob',
    })
    return response.data
  },

  async exportTXT(listId) {
    const response = await api.get(`/grocery-lists/${listId}/export/txt`, {
      responseType: 'blob',
    })
    return response.data
  },

  async getPrintHTML(listId) {
    const response = await api.get(`/grocery-lists/${listId}/print`)
    return response.data
  },
}

export const groupService = {
  async getGroups() {
    const response = await api.get('/groups')
    return response.data
  },

  async getGroup(id) {
    const response = await api.get(`/groups/${id}`)
    return response.data
  },

  async createGroup(data) {
    const response = await api.post('/groups', data)
    return response.data
  },

  async updateGroup(id, data) {
    const response = await api.patch(`/groups/${id}`, data)
    return response.data
  },

  async deleteGroup(id) {
    await api.delete(`/groups/${id}`)
  },

  async getGroupMembers(groupId) {
    const response = await api.get(`/groups/${groupId}/members`)
    return response.data
  },

  async addGroupMember(groupId, data) {
    const response = await api.post(`/groups/${groupId}/members`, data)
    return response.data
  },

  async removeGroupMember(groupId, memberId) {
    await api.delete(`/groups/${groupId}/members/${memberId}`)
  },
}
export const collectionService = {
  async getCollections() {
    const response = await api.get('/collections')
    return response.data
  },

  async getCollection(id) {
    const response = await api.get(`/collections/${id}`)
    return response.data
  },

  async createCollection(data) {
    const response = await api.post('/collections', data)
    return response.data
  },

  async updateCollection(id, data) {
    const response = await api.patch(`/collections/${id}`, data)
    return response.data
  },

  async deleteCollection(id) {
    await api.delete(`/collections/${id}`)
  },

  async getCollectionRecipes(id) {
    const response = await api.get(`/collections/${id}/recipes`)
    return response.data
  },

  async addRecipeToCollection(collectionId, recipeId) {
    const response = await api.post(`/collections/${collectionId}/recipes/${recipeId}`)
    return response.data
  },

  async removeRecipeFromCollection(collectionId, recipeId) {
    await api.delete(`/collections/${collectionId}/recipes/${recipeId}`)
  },
}