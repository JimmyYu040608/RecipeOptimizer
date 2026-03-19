import numpy as np
from ortools.linear_solver import pywraplp
from typing import List, Dict, Set

from src.common import custom_round_float, MethodTypes, ObjMethods
from src.recipe import Product, Recipe
from src.graph import ProductionGraph, SinkVertex, WasteVertex
from MultiObjective.src.pick_best_pareto import pick_utopia

RECIPE_MAX = 100 # Maximum allowable amount of any single recipe
PRODUCT_MAX = 10000 # Maximum allowable amount of any single product
RECIPE_COST = 0.01 # Small cost to discourage extraneous recipes

class ProductionProblem:
    def __init__(self, recipes: List[Recipe], inputs: Dict[Product, float], outputs: Dict[Product, float], obj_method=ObjMethods.VALUE):
        # Initialize input variables
        self.recipes = recipes
        self.inputs = inputs # {product: given_rate}
        self.outputs = outputs # {product: score}
        self.obj_method = obj_method
        self._recipe_max = RECIPE_MAX
        self._product_max = PRODUCT_MAX
        self._recipe_cost = RECIPE_COST
        
        # Initialize the solver
        # GLOP: General linear programming solver
        # SAT: Mixed integer programming solver (decision variables have to be integers)
        self.solver = pywraplp.Solver.CreateSolver("SCIP")
        if not self.solver:
            raise ValueError("Solver not found")
        
        # Initialize other optimization variables
        self.recipe_vars = {} # {"recipe_name": RecipeVariable}
        self.objective = None
        
        # Initialize output variables
        self.opt_recipe_count = {} # {"recipe_name": (Recipe, int)}
        self.graph = ProductionGraph()
        self.result_output_count = {} # {"output_product_name": int}
        self.result_waste_count = {} # {"wasted_product_name": int}
        self.result_output_value = 0
        self.result_waste_value = 0
    
    
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
    
    
    def get_recipe_by_name(self, name):
        for recipe in self.recipes:
            if recipe.name == name:
                return recipe
        raise ValueError(f"Recipe with name {name} not found")
    
    
    def validate(self):
        """ Validate that output products can be produced from input products using the given recipes. """
        visiting_set = set() # (For DP) A set of products that are currently being visited
        valid_dict = {} # (For DP) A dictionary of whether a product is valid
        # Validate that each output can be produced from the inputs
        for target_product in self.outputs.keys():
            if not validate_product(self.recipes, self.inputs.keys(), target_product, visiting_set, valid_dict):
                print(f"No recipe can produce {target_product}. The problem is invalid.")
                return False
        # print("All output products can be produced from possible recipes. The problem is valid.")
        return True
    
    
    def reduce(self):
        """ Reduce the problem by removing recipes and inputs that are irrevelant to the production of outputs """
        # Find all products needed to produce outputs
        needed_products = set()
        visiting_set = set()
        
        def find_needed_products(product):
            if product in visiting_set or product in needed_products:
                return
            visiting_set.add(product)
            needed_products.add(product)
            
            # Find recipes that produce this product
            for recipe in self.recipes:
                if recipe.product_net_rate(product) > 0:
                    # Add all inputs needed by this recipe
                    for input_product in recipe.products_used():
                        if recipe.product_net_rate(input_product) < 0:
                            find_needed_products(input_product)
            visiting_set.remove(product)
        
        # Start from output products
        for output_product in self.outputs.keys():
            find_needed_products(output_product)
        
        # Remove recipes that don't produce needed products
        self.recipes = [r for r in self.recipes if any(r.product_net_rate(p) > 0 for p in needed_products)]
        
        # Remove inputs that aren't needed
        self.inputs = {p: rate for p, rate in self.inputs.items() if p in needed_products}
    
    
    def _single_obj_solve(self):
        """
        Handler function for all single objective functions to solve the problem and store parameters after prior objective and constraints setup
        To be used following _set_obj_XXX functions
        """
        self.solver.Solve()
        # Validate that all recipes are of integer scale
        for var in self.recipe_vars.values():
            if not var.solution_value().is_integer():
                raise ValueError("Non-integer solution value for recipe count")
        # Store optimized recipe counts in int type
        for recipe in self.recipes:
            self.opt_recipe_count[recipe.name] = (recipe, int(self.recipe_vars[recipe.name].solution_value()))
        
        # DEBUG
        # print("\nSolution:")
        # print(f"Objective value: {self.objective.Value():.2f}")
        # print("\nRecipes Used:")
        # for recipe in self.recipes:
        #     var = self.recipe_vars[recipe.name]
        #     if var.solution_value():
        #         print(f"{recipe.name}: {var.solution_value()}")
        # print("\nInputs Remaining:")
        # for p, q in self.inputs.items():
        #     for recipe in self.recipes:
        #         q += recipe.product_net_rate(p) * self.recipe_vars[recipe.name].solution_value()
        #     print(f"{p}: {q:.2f}")
        # print("\nProduced:")
        # for p in products:
        #     q = 0
        #     for recipe in self.recipes:
        #         q += recipe.product_net_rate(p) * self.recipe_vars[recipe.name].solution_value()
        #     if q > 0.01:
        #         print(f"{p}: {q:.2f}")
    
    
    # def _multi_obj_solve(self, contribution_list, resolution):
    #     # Apply integer simplex technique to generate samples where w1+w2+...+wn = 1
    #     dimension = len(contribution_list)
    #     integer_points = integer_simplex(dimension, resolution)
    #     weights = np.array(integer_points) / resolution
    #     # Try out all pareto_solutions
    #     pareto_solutions = []
    #     for w in weights:
    #         # contribution_list is assumed to be processed independently for each objective (e.g. whether to negate it for minimization)
    #         weighted_contribution = sum(w[i] * contribution_list[i] for i in range(dimension))
    
    
    """ Three single objective functions for test """
    def _set_obj_produce(self):
        """ Objective 1: Maximize total scores given by target products """
        self.objective = self.solver.Objective()
        for recipe in self.recipes:
            # Calculate score contribution (sum of the all target production rate * its score)
            recipe_contribution = sum([recipe.product_net_rate(c) * s for c, s in self.outputs.items()])
            recipe_contribution -= self.get_recipe_cost()
            # Penalize alternate recipes slightly to prioritize original recipes for simplicity
            if recipe.alternate:
                recipe_contribution -= 0.001
            recipe_contribution = -recipe_contribution # To be turned into minimization problem
            self.objective.SetCoefficient(self.recipe_vars[recipe.name], recipe_contribution)
        self.objective.SetMinimization()
        
    
    def _set_obj_waste(self):
        """ Objective 2: Minimize total waste """
        self.objective = self.solver.Objective()
        for recipe in self.recipes:
            # Calculate waste contribution (positive net production of non-target products)
            waste_contribution = sum([recipe.product_net_rate(product) for product in recipe.products_used() if product not in self.outputs])
            # Penalize alternate recipes slightly to prioritize original recipes for simplicity
            if recipe.alternate:
                waste_contribution += 0.001
            self.objective.SetCoefficient(self.recipe_vars[recipe.name], waste_contribution)
        self.objective.SetMinimization()  # Minimize waste directly
    
    
    def _set_obj_produce_and_waste(self):
        """ Objective 3 (flawed): Maximize total scores given by target products with a penalty of waste """
        self.objective = self.solver.Objective()
        waste_penalty = 10  # Penalty weight for waste <-- quite arbitrary
        for recipe in self.recipes:
            # Production contribution (same as _set_obj_produce)
            recipe_contribution = sum([recipe.product_net_rate(c) * s for c, s in self.outputs.items()])
            recipe_contribution -= self.get_recipe_cost()
            # Waste penalty
            waste_contribution = sum([recipe.product_net_rate(product) for product in recipe.products_used() if product not in self.outputs and product not in self.inputs])
            recipe_contribution -= waste_penalty * waste_contribution
            # Penalize alternate recipes slightly to prioritize original recipes for simplicity
            if recipe.alternate:
                recipe_contribution -= 0.001
            recipe_contribution = -recipe_contribution # To be turned into minimization problem
            self.objective.SetCoefficient(self.recipe_vars[recipe.name], recipe_contribution)
        self.objective.SetMinimization()
    
    
    def _multi_obj_value_waste(self):
        """ Multi-objective: maximize production score and minimize waste simultaneously """
        
        from MultiObjective.src.weight_estimate import normalize, ws_value_waste_norm_param
        
        pareto_solutions = []
        weights = np.linspace(0, 1, 21)  # 21 weight combinations
        
        # Obtain normalization parameters for this problem
        problem_obj = {'recipes': self.recipes, 'inputs': self.inputs, 'outputs': self.outputs}
        f1_best, f1_worst, f2_best, f2_worst = ws_value_waste_norm_param(problem_obj)
        utopia_point = [f1_best, f2_best]
        
        # DEBUG
        # print("DEBUG: Normalize test:")
        # f1_values = [27000, 0.1, 6000, 19999]
        # f2_values = [0, 100, 500, f2_worst]
        # for i in range(4):
        #     print(f"f1: {f1_values[i]}, normalized: {normalize(f1_values[i], f1_best, f1_worst)}")
        #     print(f"f2: {f2_values[i]}, normalized: {normalize(f2_values[i], f2_best, f2_worst)}")
        
        # Iterate through different combinations of weights
        for w1 in weights:
            w2 = 1 - w1
            
            # Create weighted objective
            self.objective = self.solver.Objective()
            for recipe in self.recipes:
                # Calculate score contribution (sum of the all target production rate * its score)
                recipe_contribution = sum([recipe.product_net_rate(c) * s for c, s in self.outputs.items()])
                recipe_contribution -= self.get_recipe_cost()
                recipe_contribution = -recipe_contribution # To be turned into minimization problem
                recipe_contribution = normalize(recipe_contribution, f1_best, f1_worst)
                # Calculate waste contribution (positive production for non-target products)
                waste_contribution = sum([recipe.product_net_rate(product) for product in recipe.products_used() if product not in self.outputs])
                waste_contribution = normalize(waste_contribution, f2_best, f2_worst)
                # Weighted combination (maximize value, minimize waste)
                weighted_contribution = w1 * recipe_contribution + w2 * waste_contribution
                # Penalize alternate recipes slightly to prioritize original recipes for simplicity
                if recipe.alternate:
                    weighted_contribution -= 0.001
                self.objective.SetCoefficient(self.recipe_vars[recipe.name], weighted_contribution)
            self.objective.SetMinimization()
            # Different from single objective, solve for now to locate different weight combinations
            self.solver.Solve()
            
            # Calculate objective values
            total_value = sum(self.recipe_vars[recipe.name].solution_value() * sum([recipe.product_net_rate(c) * s for c, s in self.outputs.items()]) for recipe in self.recipes)
            
            # Store current solution for graph creation
            current_solution = {recipe.name: self.recipe_vars[recipe.name].solution_value() for recipe in self.recipes}
            
            # Create temporary graph to calculate actual waste
            temp_graph = ProductionGraph()
            temp_graph.create([(recipe, int(current_solution[recipe.name])) for recipe in self.recipes], self.inputs, self.outputs)
            
            # Calculate total waste from WasteVertex objects
            total_waste = sum(vertex.wasted_rate for vertex in temp_graph.vertices if isinstance(vertex, WasteVertex))
            
            pareto_solutions.append((total_value, total_waste, w1, w2, current_solution))
        
        print("Pareto Front Solutions (Value, Waste, w_production, w_waste):")
        for solution in pareto_solutions:
            print(f"Value: {solution[0]:.2f}, Waste: {solution[1]:.2f}, w1: {solution[2]:.2f}, w2: {solution[3]:.2f}")
        
        # Pick the best solution among pareto solutions based on utopia point
        best_index = pick_utopia(utopia_point, [(solution[0], solution[1]) for solution in pareto_solutions])
        
        # Locate back the best weight set and store best solution
        best_w1 = pareto_solutions[best_index][2]
        best_w2 = pareto_solutions[best_index][3]
        print(f"The best weight between value and waste is {best_w1}:{best_w2}")
        for recipe_name, sol_val in pareto_solutions[best_index][4].items():
            # Recall: [4] stores current_solution {recipe.name: ...solution_valuee()}
            self.opt_recipe_count[recipe_name] = (self.get_recipe_by_name(recipe_name), int(sol_val))
    
    
    def optimize(self):
        """ Create a production graph optimizing the given recipes for the specified inputs and outputs """
        
        # Validate the problem
        if not self.validate():
            raise ValueError("The problem is invalid")
        
        # Reduce the problem first by removing irrelevant recipes and inputs
        self.reduce()
        
        # Flatten recipes to obtain all products involved
        products = list(set([c for recipe in self.recipes for c in recipe.products_used()]))
        products.sort()
        
        # Define decision variable: How can time should each recipe be executed
        # m1, m2, m3... for multiplication of r1, r2, r3...
        # Integer variable bounded from 0 to RECIPE_MAX, with name of the recipes
        # List of recipe counts, if there are 100 available recipes, here creates 100 variables to be optimized
        self.recipe_vars = dict([(r.name, self.solver.IntVar(0, self.get_recipe_max(), r.name)) for r in self.recipes]) # {str: IntVar}
        
        # DEBUG
        # print("\nNumber of variables: ", self.solver.NumVariables())
        
        # For each product, add a constraint that the total amount is at least 0
        for product in products:
            min_value = -self.inputs[product] if product in self.inputs else 0
            ct = self.solver.RowConstraint(min_value, self.get_product_max(), product.name)

            # Add the contribution of each recipe
            for recipe in self.recipes:
                ct.SetCoefficient(self.recipe_vars[recipe.name], recipe.product_net_rate(product))
                
        # Create objective function
        if self.obj_method == ObjMethods.VALUE:
            self._set_obj_produce()
        elif self.obj_method == ObjMethods.WASTE:
            self._set_obj_waste()
        elif self.obj_method == ObjMethods.S_VALUE_WASTE:
            self._set_obj_produce_and_waste()
        elif self.obj_method == ObjMethods.M_VALIE_WASTE:
            self._multi_obj_value_waste()
        else:
            raise ValueError(f"Invalid objective method: {self.obj_method}")
        # Do nothing if is MULTIPLE (the follow-up has already been handled in their own functions)
        # Do _single_obj_solve() for obj_mode type being SINGLE
        if ObjMethods.mode_type(self.obj_method) == MethodTypes.SINGLE:
            self._single_obj_solve()
        
        # Next step: Create production graph
        self.graph.create(self.opt_recipe_count.values(), self.inputs, self.outputs)
        
        # Read important data back to problem instance for convenience
        for vertex in self.graph.vertices:
            if isinstance(vertex, SinkVertex):
                self.result_output_count[vertex.receive_product.name] = vertex.receive_rate
            elif isinstance(vertex, WasteVertex):
                self.result_waste_count[vertex.wasted_product.name] = vertex.wasted_rate
    
    
    def print_graph(self):
        self.graph.terminal_display()
    
    
    def visualize_graph(self, save_path, title):
        # Sum all the scores contributed by different products
        total_score = sum(score * self.result_output_count.get(product.name, 0) for product, score in self.outputs.items())
        total_score = custom_round_float(total_score)
        # Sum all the waste counts
        total_waste = sum(self.result_waste_count.values())
        total_waste = custom_round_float(total_waste)
        # Edit title to display important metrics as well
        title = f"{title} (Product Value: {total_score}, Wasted: {total_waste} unit/min)"
        self.graph.visualize(save_path, title)


def validate_product(recipes: List[Recipe], input_products: List[Product], target_product: Product, visiting_set: Set[Product] = None, valid_dict: Dict[Product, bool] = None) -> bool:
    """
    Validate that a single product can be produced from input products using the given recipes.
    :param recipes: List of available recipes
    :param input_products: Set of available input products
    :param target_product: Product to validate
    :param visiting_set: Set of products currently being validated
    :param valid_dict: Records for the validation results of each product
    """
    if visiting_set is None:
        visiting_set = set()
    if valid_dict is None:
        valid_dict = {}
    
    # If the target product is already validated, return the result
    if target_product in valid_dict:
        return valid_dict[target_product]
    
    # If the target product is directly in the inputs, it is valid
    if target_product in input_products:
        valid_dict[target_product] = True
        return True
    
    # If we are already visiting this product, there is a cycle -> invalid
    # Although according to current understanding to the problem, there should not be any cycle in recipes
    if target_product in visiting_set:
        valid_dict[target_product] = False
        return False
    
    visiting_set.add(target_product)
    
    # Search in all recipes that can produce this product
    for recipe in recipes:
        if target_product in recipe.out_products():
            # Check if all input products for this recipe can be produced from the inputs or directly as the inputs
            recipe_valid = True
            for ingredient in recipe.in_products():
                # If one of the ingredient itself is validated cannot be produced, this recipe cannot be used to produce target product
                if not validate_product(recipes, input_products, ingredient, visiting_set, valid_dict):
                    recipe_valid = False
                    break
            # If all the ingredients are valid, the target product is valid
            if recipe_valid:
                valid_dict[target_product] = True
                visiting_set.remove(target_product)
                return True
    
    # If the target product cannot be produced from any recipe, return invalid
    visiting_set.remove(target_product)
    valid_dict[target_product] = False
    return False