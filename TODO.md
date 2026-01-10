* ~~Retrieve the models list from the openai api directly and allow the admin to select which model to use.~~
* ~~If no users exist in the database, allow the user to create a new admin user to get started.~~ NOT TESTED
* ~~Create a forgot password flow.~~ - Ensure the email gets sent using an email service.
* Integration with vendors for grocery lists
* ~~Add the ability to have multiple meals for lunch/breakfast/dinner/snack~~
* ~~Add another category for something that is ingredients to other recipes. Dough, sauce, etc~~ (Changed to "staple" category)
* ~~Add desserts as a category different from snack~~
* ~~Allow users to set dietary preferences (vegan, keto, etc) and have the AI generate recipes accordingly.~~
* ~~Allow users to set calorie targets for recipes and have the AI generate recipes accordingly.~~
* ~~AI should include tags when creating recipes with examples and access to existing tags.~~
* ~~User can opt to have dietary preferences automatically applied in AI recipe creation (with toggle).~~
* ~~Add user roles and permissions for collaborative meal planning.~~ (Group-based permissions implemented)
* Add localization support for multiple languages.
* Add seasonal recipe suggestions based on current month or user location.
* Add recipe image generation or retrieval to the AI-generated recipes.
    Options:
    - ~~Use placeholder images (current solution - using Unsplash)~~
    - Integrate with an image generation API (DALL-E, Stable Diffusion)
    - ~~Use an image search API (Pexels, Bing, Google)~~
    - Prompt users to upload images after recipe creation
* ~~The admin should be able to modify all aspects of recipes not just a few details or deletion.~~
* ~~Add nutrition information calculation for recipes based on ingredients.~~ (Implemented with basic nutrition database)
* ~~Add a shopping list feature that aggregates ingredients from selected recipes.~~ (Grocery list implemented)
* ~~Add calendar exports to external calendars~~ (iCal export implemented)
* ~~Improve the PWA experience with better offline support and install prompts.~~ (Basic PWA implemented with service workers)
* Add drag-and-drop reordering of meals in the meal planner.
* ~~Add support for recipe ratings and reviews by users.~~
* ~~Add a favorites recipe view for the user and add to the dashboard.~~
* ~~Add more robust error handling and user feedback throughout the app.~~ (ErrorBoundary component implemented)
* Improve the UI/UX design for better usability and aesthetics.
* ~~Add unit tests and integration tests for critical components.~~
* Add proper versioning control to Docker builds and github releases
* Add playwright tests
* ~~Improve CI/CD pipelines for automated testing and deployment.~~ (Basic CI/CD pipeline implemented)
* Add analytics tracking for user behavior and app usage.
* Add email notifications for important events (new recipe created, password reset, etc).
* Add social sharing features for recipes and meal plans.
* Add a blog or news section for sharing meal planning tips and recipes.
* ~~Add API rate limiting and security enhancements.~~ (Rate limiting middleware implemented - 100 req/min, 2000 req/hour)
* Add database backups and recovery procedures.
* Add support for multiple database backends (PostgreSQL, MySQL, SQLite).
* ~~Add a dark mode theme for the frontend.~~
* ~~Add accessibility improvements for better support of screen readers and keyboard navigation.~~ (ARIA labels, ErrorBoundary, keyboard navigation)
* ~~Add a tutorial or onboarding flow for new users.~~ (Interactive onboarding tutorial implemented)
* Add a feedback mechanism for users to report bugs or suggest features.
* Add integration with third-party services (fitness apps, nutrition trackers, etc).
* Add support for meal prep planning and batch cooking recipes.
* Add a grocery delivery integration to order ingredients directly from the app.
* Add support for dietary restrictions and allergen warnings in recipes.
* ~~Add a recipe import/export feature for sharing recipes between users.~~ (JSON import/export implemented)
* Add a meal rating system to help users track their favorite meals.
* ~~Add a user profile page for managing personal information and preferences.~~
* ~~Allow the user to pick which day of the week the calendar starts on. For instance Monday instead of Sunday.~~
* ~~Create a new category for foods such as frozen foods or simple pre made foods. Hot Dogs, Hamburgers etc.~~
* ~~Improve the recipe search functionality with filters for dietary preferences, cooking time, difficulty, etc.~~
* ~~Add recipe collections or categories for better organization.~~ (Collections feature implemented with CRUD operations)
* ~~Add the ability to pre-populate calendars based on filters or use ai to populate the the calendar.~~
* ~~Allow the user to modify the grocery list.~~
* ~~Add comprehensive tagging system for recipes with dietary/cuisine/other tags~~
* ~~Support filtering recipes by multiple tags~~
* ~~Enable staple recipes (like dough, sauce) to be used as ingredients in other recipes~~ (Frontend UI completed - RecipeForm supports staple ingredient selection. Backend integration needs migration from JSON ingredients column to RecipeIngredient table)
* ~~Copy a day, month or a week in the meal planner to another day/week/month~~
* ~~Add the ability for the grocery list to be printed or exported to a txt file or csv.~~
* ~~Have a way for the user to manage calendars and be able to switch calendars.~~
* Create a new entity for simple menu items which do not require full recipes. Ex. Frozen chicken nuggets, frozen fries, etc. These need to be searchable along with the full recipes. 
* Prepopulate the database with many of the menu items so there is something to choose from to begin with.
