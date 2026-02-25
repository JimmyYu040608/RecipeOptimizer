from src.recipe import Recipe, Product
from src.solver import ProductionProblem

def create_demo_recipes():
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
    return recipes

def create_demo_problem(method='value'):
    """ Methods: value | waste | value_waste | multi_obj_value_waste """
    recipes = create_demo_recipes()
    inputs = {
        'Iron Ingot': 120,
        'Copper Ingot': 60
    }
    inputs = {Product(k): v for k, v in inputs.items()}
    output_scores = {
        'Reinforced Iron Plate': 1000,
        'Copper Wire': 20
    }
    output_scores = {Product(k): v for k, v in output_scores.items()}
    problem = ProductionProblem(recipes, inputs, output_scores, method)
    return problem
