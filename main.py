from src.recipe import Recipe, load_recipes

recipes = load_recipes()

with open('output.txt', 'w', encoding='utf-8') as f:
    for recipe in recipes:
        f.write(recipe.description() + '\n\n')
