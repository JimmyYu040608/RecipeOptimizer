from src.recipe import Product, Recipe, load_recipes
from src.graph import ProductionGraph
from src.solver import optimize_recipes

# Load from data.json for all possible recipes, items, etc in Satisfactory
recipes = load_recipes()

with open('output.txt', 'w', encoding='utf-8') as f:
    for recipe in recipes:
        f.write(recipe.description() + '\n\n')

# What is provided to the solver for optimization
inputs = {
    "Crude Oil": 300,
    "Water": 800,
    "Coal": 533.33,
    "Sulfur": 533.33
}
inputs = {Product(k): v for k, v in inputs.items()}
outputs = {
    "Fuel": 600,
    "Turbofuel": 2000
}
outputs = {Product(k): v for k, v in outputs.items()}

# Use the solver for optimization
graph = optimize_recipes(recipes, inputs, outputs)