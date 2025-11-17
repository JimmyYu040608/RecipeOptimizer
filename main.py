import os
from src.recipe import Product, load_recipes
from src.solver import ProductionProblem

def main():
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

    # Create problem
    problem = ProductionProblem(recipes, inputs, outputs)
        
    if not problem.validate():
        print("Problem is invalid")
        return
    
    # Create output_png folder if it doesn't exist
    if not os.path.exists('./output_png'):
        os.makedirs('./output_png')
    
    problem.optimize()
    problem.create_graph()
    problem.print_graph()
    problem.visualize_graph('./output_png/production_graph')

if __name__ == "__main__":
    main()