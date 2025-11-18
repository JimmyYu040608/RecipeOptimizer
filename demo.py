from src.recipe import Product, Recipe
from src.graph import ProductionGraph
from src.solver import ProductionProblem

OUTPUT_DIR = './output_png'

def mini_example_opt(save_path, title):
    """ Example of a production problem with a single recipe """
    # Hardcode customized recipes
    recipe = Recipe('Combined Iron Plate', 'Assembler', False)
    recipe.add_input(Product('Iron Plate'), 2)
    recipe.add_input(Product('Screw'), 4)
    recipe.add_output(Product('Combined Iron Plate'), 1)
    recipes = [recipe]
    inputs = {
        Product('Iron Plate'): 6,
        Product('Screw'): 12
    }
    output_scores = {
        Product('Combined Iron Plate'): 10,
    }
    problem = ProductionProblem(recipes, inputs, output_scores)
    problem.optimize()
    problem.create_graph()
    problem.visualize_graph(save_path, title)

def mini_example_waste(save_path, title):
    """ Example of a production problem with a single recipe, with waste """
    # Hardcode customized recipes
    recipe = Recipe('Combined Iron Plate', 'Assembler', False)
    recipe.add_input(Product('Iron Plate'), 2)
    recipe.add_input(Product('Screw'), 4)
    recipe.add_output(Product('Combined Iron Plate'), 1)
    recipes = [recipe]
    inputs = {
        Product('Iron Plate'): 2,
        Product('Screw'): 12
    }
    output_scores = {
        Product('Combined Iron Plate'): 10,
    }
    problem = ProductionProblem(recipes, inputs, output_scores)
    problem.optimize()
    problem.create_graph()
    problem.visualize_graph(save_path, title)

def simple_example_waste(save_path, title):
    """ Example of a production problem with ratio adjustment, with waste """
    # Hardcode customized recipes
    recipe1 = Recipe('Iron Part A', 'Constructor', False)
    recipe1.add_input(Product('Iron Ore'), 4)
    recipe1.add_output(Product('Iron Part A'), 1)
    recipe2 = Recipe('Iron Part B', 'Constructor', False)
    recipe2.add_input(Product('Iron Ore'), 3)
    recipe2.add_output(Product('Iron Part B'), 2)
    recipe3 = Recipe('Special Component', 'Assembler', False)
    recipe3.add_input(Product('Iron Part A'), 2)
    recipe3.add_input(Product('Iron Part B'), 2)
    recipe3.add_output(Product('Special Component'), 1)
    recipes = [recipe1, recipe2, recipe3]
    inputs = {
        Product('Iron Ore'): 60,
    }
    output_scores = {
        Product('Special Component'): 10,
    }
    problem = ProductionProblem(recipes, inputs, output_scores)
    problem.optimize()
    # Intercept to hardcode create wasteful arrangements
    problem.opt_recipe_count = {
        recipe1.name: (recipe1, 8),
        recipe2.name: (recipe2, 8),
        recipe3.name: (recipe3, 4)
    }
    problem.create_graph()
    problem.visualize_graph(save_path, title)

def simple_example_opt(save_path, title):
    """ Example of a production problem with ratio adjustment, with least waste """
    # Hardcode customized recipes
    recipe1 = Recipe('Iron Part A', 'Constructor', False)
    recipe1.add_input(Product('Iron Ore'), 4)
    recipe1.add_output(Product('Iron Part A'), 1)
    recipe2 = Recipe('Iron Part B', 'Constructor', False)
    recipe2.add_input(Product('Iron Ore'), 3)
    recipe2.add_output(Product('Iron Part B'), 2)
    recipe3 = Recipe('Special Component', 'Assembler', False)
    recipe3.add_input(Product('Iron Part A'), 2)
    recipe3.add_input(Product('Iron Part B'), 2)
    recipe3.add_output(Product('Special Component'), 1)
    recipes = [recipe1, recipe2, recipe3]
    inputs = {
        Product('Iron Ore'): 60,
    }
    output_scores = {
        Product('Special Component'): 10,
    }
    problem = ProductionProblem(recipes, inputs, output_scores)
    problem.optimize()
    problem.create_graph()
    problem.visualize_graph(save_path, title)

def alternate_example_waste(save_path, title):
    """ Example of a production problem with alternate recipes, with waste """
    # Hardcode customized recipes
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
    inputs = {
        Product('Iron Ingot'): 120,
        Product('Copper Ingot'): 60
    }
    output_scores = {
        Product('Reinforced Iron Plate'): 1000,
        Product('Copper Wire'): 20
    }
    problem = ProductionProblem(recipes, inputs, output_scores)
    problem.optimize()
    # Intercept to hardcode create wasteful arrangements
    problem.opt_recipe_count = {
        recipe1.name: (recipe1, 36),
        recipe2.name: (recipe2, 0),
        recipe3.name: (recipe3, 27),
        recipe4.name: (recipe4, 18),
        recipe5.name: (recipe5, 30)
    }
    problem.create_graph()
    problem.visualize_graph(save_path, title)

def alternate_example_opt(save_path, title):
    # Hardcode customized recipes
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
    inputs = {
        Product('Iron Ingot'): 120,
        Product('Copper Ingot'): 60
    }
    output_scores = {
        Product('Reinforced Iron Plate'): 1000,
        Product('Copper Wire'): 20
    }
    problem = ProductionProblem(recipes, inputs, output_scores)
    problem.optimize()
    problem.create_graph()
    problem.visualize_graph(save_path, title)

def demo():
    """ Demonstrate different examples of how optimization helps """
    mini_example_opt(f'{OUTPUT_DIR}/mini_example_opt', 'Mini Example Opt')
    mini_example_waste(f'{OUTPUT_DIR}/mini_example_waste', 'Mini Example Waste')
    simple_example_waste(f'{OUTPUT_DIR}/simple_example_waste', 'Simple Example Waste')
    simple_example_opt(f'{OUTPUT_DIR}/simple_example_opt', 'Simple Example Opt')
    alternate_example_waste(f'{OUTPUT_DIR}/alternate_example_waste', 'Alternate Example Waste')
    alternate_example_opt(f'{OUTPUT_DIR}/alternate_example_opt', 'Alternate Example Opt')

if __name__ == '__main__':
    demo()