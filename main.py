import os
from src.recipe import Product, load_recipes
from src.solver import ProductionProblem

OUTPUT_DIR = "./output_png"

def main():
    # Load from data.json for all possible recipes, items, etc in Satisfactory
    recipes = load_recipes()

    with open('output.txt', 'w', encoding='utf-8') as f:
        for recipe in recipes:
            f.write(recipe.description() + '\n\n')

    # What is provided to the solver for optimization
    inputs = { # Product: provided rate
        "Crude Oil": 300,
        "Water": 800,
        "Coal": 533.33,
        "Sulfur": 533.33
    }
    inputs = {Product(k): v for k, v in inputs.items()}
    output_scores = { # {Product: score}
        "Fuel": 600,
        "Turbofuel": 2000
    }
    output_scores = {Product(k): v for k, v in output_scores.items()}

    # Create problem
    problem = ProductionProblem(recipes, inputs, output_scores)
        
    if not problem.validate():
        print("Problem is invalid")
        return
    
    # Create output_png folder if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    save_path = f'{OUTPUT_DIR}/production_graph'
    problem.optimize()
    problem.create_graph()
    problem.print_graph()
    problem.visualize_graph(save_path, 'Production Graph')

if __name__ == "__main__":
    main()