# Quick Reference - Sample Data

## Populating Sample Data

The Meal Planner includes scripts to populate the database with sample data for testing and demonstration purposes.

### What Gets Created

When you run the populate script, it creates:

**3 Sample Users:**
- `demo` / `demo@example.com` - Password: `password123`
- `chef_alice` / `alice@example.com` - Password: `password123`
- `foodie_bob` / `bob@example.com` - Password: `password123`

**8 Sample Recipes:**
1. Classic Spaghetti Carbonara (Medium difficulty, Italian)
2. Overnight Oats (Easy, Breakfast)
3. Grilled Chicken Caesar Salad (Easy, Lunch)
4. Homemade Margherita Pizza (Medium, Dinner)
5. Thai Green Curry (Medium, Dinner)
6. Chocolate Chip Cookies (Easy, Dessert)
7. Avocado Toast with Poached Egg (Easy, Breakfast)
8. Beef Tacos (Easy, Dinner)

Each recipe includes:
- Full ingredient list with quantities and units
- Step-by-step instructions
- Nutritional information (calories, protein, carbs, fat)
- Prep and cook times
- Serving sizes
- Difficulty level
- High-quality stock images

**Sample Calendars:**
- One personal calendar for each user

**Sample Meal Plans:**
- Pre-planned meals for the next 7 days
- 2-3 meals per day (breakfast, lunch, dinner)
- Distributed across all sample recipes

### How to Use

#### For Docker Setup:

```bash
# Make sure services are running
docker-compose up -d

# Populate the database
./populate-data-docker.sh
```

#### For Local Development:

```bash
# Make sure backend is set up
cd backend
source .venv/bin/activate

# Run the populate script
cd ..
./populate-data.sh
```

#### Manual Method:

If the scripts don't work, you can run directly:

```bash
cd backend
source .venv/bin/activate  # Skip for Docker
python populate_sample_data.py
```

Or with Docker:

```bash
docker-compose exec backend python populate_sample_data.py
```

### After Populating

1. Visit http://localhost:3080
2. Click "Sign In"
3. Enter username: `demo` and password: `password123`
4. Explore the pre-populated recipes and meal plans!

### Tips

- You can run the script multiple times - it will add more data each time
- To start fresh, reset the database (see TROUBLESHOOTING.md)
- Each user has their own calendar and can see all public recipes
- Try logging in as different users to see their perspectives

### Sample Recipe Features Demonstrated

All features are demonstrated in the sample recipes:

✅ Recipe images (from Unsplash)  
✅ Nutritional information  
✅ Prep and cook times  
✅ Multiple serving sizes  
✅ Difficulty levels  
✅ Detailed ingredients with units  
✅ Step-by-step instructions  
✅ Various cuisine types  
✅ Different meal types (breakfast, lunch, dinner)  

Enjoy exploring the Meal Planner! 🍽️
