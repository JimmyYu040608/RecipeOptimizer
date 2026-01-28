from src.recipe import Product, Recipe
from src.graph import ProductionGraph
from src.solver import ProductionProblem

OUTPUT_DIR = './demo_png'

def alternate_example_opt(save_path, title, obj_method='produce'):
    # Specify recipes
    recipe1 = Recipe('Iron Screw', 'Constructor', True)
    recipe1.add_input(Product('Iron Ingot'), 1)
    recipe1.add_output(Product('Screw'), 4)
    recipe2 = Recipe('Copper Screw', 'Constructor', True)
    recipe2.add_input(Product('Copper Ingot'), 1)
    recipe2.add_output(Product('Screw'), 4)
    recipe3 = Recipe('Iron Plate', 'Constructor', False)
    recipe3.add_input(Product('Iron Ingot'), 3)
    recipe3.add_output(Product('Iron Plate'), 2)
    recipe4 = Recipe('Reinforced Iron Plate', 'Constructor', False)
    recipe4.add_input(Product('Iron Plate'), 3)
    recipe4.add_input(Product('Screw'), 8)
    recipe4.add_output(Product('Reinforced Iron Plate'), 1)
    recipe5 = Recipe('Copper Wire', 'Constructor', False)
    recipe5.add_input(Product('Copper Ingot'), 2)
    recipe5.add_output(Product('Copper Wire'), 10)
    recipes = [recipe1, recipe2, recipe3, recipe4, recipe5]
    
    # Specify input products
    inputs = {
        Product('Iron Ingot'): 120,
        Product('Copper Ingot'): 60
    }
    
    # Specify output products and scores
    output_scores = {
        Product('Reinforced Iron Plate'): 1000,
        Product('Copper Wire'): 20
    }
    
    # Execute the program
    problem = ProductionProblem(recipes, inputs, output_scores)
    problem.optimize()
    problem.create_graph()
    problem.print_graph()
    problem.visualize_graph(save_path, title)

def demo():
    alternate_example_opt(f'{OUTPUT_DIR}/alternate_example_opt', 'Example [Opt]')

if __name__ == '__main__':
    demo()