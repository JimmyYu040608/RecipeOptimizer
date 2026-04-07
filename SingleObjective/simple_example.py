from src.common import ObjMethods
from src.recipe import Product, Recipe, get_item_sink_pt
from src.solver import ProductionProblem
from src.demo_data import DemoItems, DemoRecipes

OUTPUT_DIR = './images/demo'

def mini_example_opt(save_path, title):
    """ Example of a production problem with a single recipe """
    # Hardcode customized recipes
    iron_plate = Product('Iron Plate', 40)
    screw = Product('Screw', 5)
    combined_iron_plate = Product('Combined Iron Plate', 100)
    recipe = Recipe('Combined Iron Plate', 'Assembler', False)
    recipe.add_input(iron_plate, 2)
    recipe.add_input(screw, 4)
    recipe.add_output(combined_iron_plate, 1)
    recipes = [recipe]
    inputs = {
        iron_plate: 6,
        screw: 12
    }
    output_scores = {
        combined_iron_plate: 10,
    }
    problem = ProductionProblem(recipes, inputs, output_scores)
    problem.optimize()
    problem.create_graph()
    problem.visualize_graph(save_path, title)

def mini_example_waste(save_path, title):
    """ Example of a production problem with a single recipe, with waste """
    # Hardcode customized recipes
    iron_plate = Product('Iron Plate', 40)
    screw = Product('Screw', 5)
    combined_iron_plate = Product('Combined Iron Plate', 100)
    recipe = Recipe('Combined Iron Plate', 'Assembler', False)
    recipe.add_input(iron_plate, 2)
    recipe.add_input(screw, 4)
    recipe.add_output(combined_iron_plate, 1)
    recipes = [recipe]
    inputs = {
        iron_plate: 2,
        screw: 12
    }
    output_scores = {
        combined_iron_plate: 10,
    }
    problem = ProductionProblem(recipes, inputs, output_scores)
    problem.optimize()
    problem.create_graph()
    problem.visualize_graph(save_path, title)

def simple_example_waste(save_path, title):
    """ Example of a production problem with ratio adjustment, with waste """
    # Hardcode customized recipes
    recipes = [DemoRecipes.iron_screw, DemoRecipes.iron_plate, DemoRecipes.reinforced_iron_plate]
    inputs = {
        DemoItems.iron_ingot: 120,
    }
    output_scores = {
        DemoItems.reinforced_iron_plate: 1000,
    }
    problem = ProductionProblem(recipes, inputs, output_scores)
    problem.optimize()
    # Intercept to hardcode create wasteful arrangements
    problem.opt_recipe_count = {
        recipes[0].name: (recipes[0], 30),
        recipes[1].name: (recipes[1], 30),
        recipes[2].name: (recipes[2], 15)
    }
    problem.create_graph()
    problem.visualize_graph(save_path, title)

def simple_example_opt(save_path, title):
    """ Example of a production problem with ratio adjustment, with least waste """
    # Hardcode customized recipes
    recipes = [DemoRecipes.iron_screw, DemoRecipes.iron_plate, DemoRecipes.reinforced_iron_plate]
    inputs = {
        DemoItems.iron_ingot: 120,
    }
    output_scores = {
        DemoItems.reinforced_iron_plate: 1000,
    }
    problem = ProductionProblem(recipes, inputs, output_scores)
    problem.optimize()
    problem.create_graph()
    problem.visualize_graph(save_path, title)

def alternate_example_waste(save_path, title):
    """ Example of a production problem with alternate recipes, with waste """
    # Hardcode customized recipes
    recipes = DemoRecipes.get_demo_recipes()
    inputs = {
        DemoItems.iron_ingot: 120,
        DemoItems.copper_ingot: 60
    }
    output_scores = {
        DemoItems.reinforced_iron_plate: 1000,
        DemoItems.copper_wire: 20
    }
    problem = ProductionProblem(recipes, inputs, output_scores)
    problem.optimize()
    # Intercept to hardcode create wasteful arrangements
    problem.opt_recipe_count = {
        recipes[0].name: (recipes[0], 36),
        recipes[1].name: (recipes[1], 0),
        recipes[2].name: (recipes[2], 27),
        recipes[3].name: (recipes[3], 18),
        recipes[4].name: (recipes[4], 30)
    }
    problem.create_graph()
    problem.visualize_graph(save_path, title)

def alternate_example_opt(save_path, title):
    # Hardcode customized recipes
    recipes = DemoRecipes.get_demo_recipes()
    inputs = {
        DemoItems.iron_ingot: 120,
        DemoItems.copper_ingot: 60
    }
    output_scores = {
        DemoItems.reinforced_iron_plate: 1000,
        DemoItems.copper_wire: 20
    }
    problem = ProductionProblem(recipes, inputs, output_scores)
    problem.optimize()
    problem.create_graph()
    problem.visualize_graph(save_path, title)

def demo():
    """ Demonstrate different examples of how optimization helps """
    mini_example_opt(f'{OUTPUT_DIR}/mini_example_opt', 'Mini Example [Opt]')
    mini_example_waste(f'{OUTPUT_DIR}/mini_example_waste', 'Mini Example [Waste]')
    simple_example_waste(f'{OUTPUT_DIR}/simple_example_waste', 'Simple Example [Waste]')
    simple_example_opt(f'{OUTPUT_DIR}/simple_example_opt', 'Simple Example [Opt]')
    alternate_example_waste(f'{OUTPUT_DIR}/alternate_example_waste', 'Example [Waste]')
    alternate_example_opt(f'{OUTPUT_DIR}/alternate_example_opt', 'Example [Opt]')

if __name__ == '__main__':
    demo()