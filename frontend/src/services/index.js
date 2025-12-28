import api from './api'

export const authService = {
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
}

export const recipeService = {
  async getRecipes(params = {}) {
    const response = await api.get('/recipes', { params })
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
}
