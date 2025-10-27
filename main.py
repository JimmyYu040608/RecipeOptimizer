from src.recipe import Recipe, load_recipes

recipes = load_recipes()

for recipe in recipes:
    print(recipe.description())

