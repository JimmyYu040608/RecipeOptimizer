import os
from src.common import ObjMethods
from src.recipe import Product, load_recipes, get_item_sink_pt
from src.solver import ProductionProblem

OUTPUT_DIR = "./images/soo"

def main():
    # Load from data JSON file for all possible recipes, items, etc in Satisfactory
    recipes = load_recipes()

    # with open('output.txt', 'w', encoding='utf-8') as f:
    #     for recipe in recipes:
    #         f.write(recipe.description() + '\n\n')

    # What is provided to the solver for optimization
    inputs = { # Product: provided rate
        "Iron Ore": 1000,
        "Copper Ore": 800,
        "Coal": 900,
        "Crude Oil": 500
    }
    inputs = {Product(k, get_item_sink_pt(k)): v for k, v in inputs.items()}
    output_scores = { # {Product: score}
        "Modular Engine": 1000
    }
    output_scores = {Product(k, get_item_sink_pt(k)): v for k, v in output_scores.items()}

    # Create problem
    problem_produce = ProductionProblem(recipes, inputs, output_scores)
    problem_waste = ProductionProblem(recipes, inputs, output_scores, ObjMethods.S_WASTE)
    problem_PnW = ProductionProblem(recipes, inputs, output_scores, ObjMethods.S_VALUE_WASTE)
        
    if not problem_produce.validate():
        print("Problem (Produce) is invalid")
        return
    if not problem_waste.validate():
        print("Problem (Waste) is invalid")
        return
    if not problem_PnW.validate():
        print("Problem (Produce and Waste) is invalid")
        return
    
    # Create output_png folder if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # Heuristics of maximizing target production
    save_path = f'{OUTPUT_DIR}/extraordinary_graph_produce'
    problem_produce.optimize()
    problem_produce.create_graph()
    problem_produce.print_graph()
    problem_produce.visualize_graph(save_path, 'Extraordinary Graph (Maximize Production)')
    # Heuristics of minimizing waste
    save_path = f'{OUTPUT_DIR}/extraordinary_graph_waste'
    problem_waste.optimize()
    problem_waste.create_graph()
    problem_waste.print_graph()
    problem_waste.visualize_graph(save_path, 'Extraordinary Graph (Minimize Waste)')
    # Heuristics of maximizing target production with penalty of waste
    save_path = f'{OUTPUT_DIR}/extraordinary_graph_produce_and_waste'
    problem_PnW.optimize()
    problem_PnW.create_graph()
    problem_PnW.print_graph()
    problem_PnW.visualize_graph(save_path, 'Extraordinary Graph (Production Penalized with Waste)')

if __name__ == "__main__":
    main()