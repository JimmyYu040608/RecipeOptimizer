from ortools.linear_solver import pywraplp
from typing import List, Dict

from src.recipe import Product, Recipe
from src.graph import ProductionGraph

RECIPE_MAX = 100 # Maximum allowable amount of any single recipe
PRODUCT_MAX = 10000 # Maximum allowable amount of any single product
RECIPE_COST = 0.01 # Small cost to discourage extraneous recipes

class ProductionProblem:
    def __init__(self, recipes: List[Recipe], inputs: Dict[Product, float], outputs: Dict[Product, float]):
        self.recipes = recipes
        self.inputs = inputs
        self.outputs = outputs
        self._recipe_max = RECIPE_MAX
        self._product_max = PRODUCT_MAX
        self._recipe_cost = RECIPE_COST
        self.graph = ProductionGraph()
    
    
    def set_recipe_max(self, value: int):
        self._recipe_max = value
    
    
    def set_product_max(self, value: int):
        self._product_max = value
    
    
    def set_recipe_cost(self, value: float):
        self._recipe_cost = value

    
    def get_recipe_max(self):
        return self._recipe_max
    
    
    def get_product_max(self):
        return self._product_max
    
    
    def get_recipe_cost(self):
        return self._recipe_cost
    
    
    def validate(self):
        """ Validate that output products can be produced from input products using the given recipes. """
        # Validate that each output can be produced from the inputs
        problem_valid = True
        for target_product in self.outputs.keys():
            # Check for validity of each output product
            product_valid = validate_product(self.recipes, self.inputs.keys(), target_product)
            # If any product is invalid, the whole problem is invalid
            if not product_valid:
                problem_valid = False
                break
        return problem_valid
    
    
    def reduce(self):
        """ Reduce the problem by removing recipes and inputs that are irrevelant to the production of outputs """
        pass
    
    
    def optimize(self):
        """ Create a production graph optimizing the given recipes for the specified inputs and outputs """
        
        # Reduce the problem first by removing irrelevant recipes and inputs
        self.reduce()
        
        # Flatten recipes to obtain all produces involved
        products = list(set([c for recipe in self.recipes for c in recipe.products_used()]))
        products.sort()
        
        # Create the solver
        # GLOP: General linear programming solver
        # SAT: Mixed integer programming solver (decision variables have to be integers)
        solver = pywraplp.Solver.CreateSolver('SAT')
        infinity = solver.infinity()
        
        # Define decision variable: How can time should each recipe be executed
        # m1, m2, m3... for multiplication of r1, r2, r3...
        # Integer variable bounded from 0 to RECIPE_MAX, with name of the recipes
        recipe_vars = dict([(r.name, solver.IntVar(0, self.get_recipe_max(), r.name)) for r in self.recipes]) # List of recipe counts, for 100 available recipes, here creates 100 variables to be optimized
        
        print("Number of variables =", solver.NumVariables())
        
        # For each product, add a constraint that the total amount is at least 0
        for product in products:
            min_value = -self.inputs[product] if product in self.inputs else 0
            ct = solver.Constraint(min_value, self.product_max, product)

            # Add the contribution of each recipe
            for recipe in self.recipes:
                ct.SetCoefficient(recipe_vars[recipe.name], recipe.product_net_rate(product))
                
        # Create objective function: Total score of all outputs created by each recipe
        objective = solver.Objective()
        for recipe in self.recipes:
            recipe_contribution = sum([recipe.product_net_rate(c) * s for c, s in self.outputs.items()])
            recipe_contribution -= self.get_recipe_cost()
            objective.SetCoefficient(recipe_vars[recipe.name], recipe_contribution)

        objective.SetMaximization()

        solver.Solve()
        
        # DEBUG
        print('Solution:')
        print(f"Objective value: {objective.Value():.2f}")

        print("\nRecipes Used:")
        for recipe in self.recipes:
            var = recipe_vars[recipe.name]
            if var.solution_value():
                print(f"{recipe.name}: {var.solution_value():.2f}")

        print("\nInputs Remaining:")
        for p, q in self.inputs.items():
            for recipe in self.recipes:
                q += recipe.product_net_rate(p) * recipe_vars[recipe.name].solution_value()

            print(f"{p}: {q:.2f}")

        print("\nProduced:")
        for p in products:
            q = 0
            for recipe in self.recipes:
                q += recipe.product_net_rate(p) * recipe_vars[recipe.name].solution_value()

            if q > 0.01:
                print(f"{p}: {q:.2f}")


def validate_product(recipes: List[Recipe], input_products: List[Product], target_product: Product):
    """
    Validate that a single product can be produced from input products using the given recipes.
    :param recipes: List of available recipes
    :param product: Product to validate
    """
    exist_valid_recipe = False
    # Search in all recipes that can produce this product
    for recipe in recipes:
        if target_product in recipe.out_products():
            # Check if all input products for this recipe can be produced from the inputs or directly as the inputs
            recipe_valid = True
            for ingredient in recipe.in_products():
                # The ingredient is directly in the inputs -> this part is valid
                # The ingredient is not directly in the inputs -> need to check if it can be produced from inputs
                if ingredient not in input_products:
                    ingredient_valid = validate_product(recipes, input_products, ingredient)
                    # If the ingredient cannot be produced, this recipe path is invalid
                    if not ingredient_valid:
                        recipe_valid = False
                        break
            if recipe_valid:
                exist_valid_recipe = True
                break
    return exist_valid_recipe