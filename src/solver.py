import numpy as np
from ortools.linear_solver import pywraplp
from typing import List, Dict, Set, Callable

from src.utils import custom_round_float, MethodTypes, ObjMethods, integer_simplex
from src.recipe import Product, Recipe
from src.graph import ProductionGraph, SinkVertex, WasteVertex, MachineVertex
from src.multi_objective.pick_best_pareto import pick_utopia

RECIPE_MAX = 100 # Maximum allowable amount of any single recipe
PRODUCT_MAX = 10000 # Maximum allowable amount of any single product
RECIPE_COST = 0.01 # Small cost to discourage extraneous recipes

ALT_PENALTY = 0.001 # Penalty weight for using alternate recipes, to be tuned based on the specific problem context
WASTE_PENALTY = 10 # Penalty weight for waste in value+waste optimization, to be tuned based on the specific problem context
POWER_PENALTY = 1 # Penalty weight for power consumption in value+power optimization, to be tuned based on the specific problem context


class ProductionProblem:
    def __init__(self, recipes: List[Recipe], inputs: Dict[Product, float], outputs: Dict[Product, float], obj_method=ObjMethods.S_VALUE):
        # Initialize input variables
        self.recipes = recipes
        self.inputs = inputs # {product: given_rate}
        self.outputs = outputs # {product: score}
        self.obj_method = obj_method
        self._recipe_max = RECIPE_MAX
        self._product_max = PRODUCT_MAX
        self._recipe_cost = RECIPE_COST
        # Initialize other optimization variables
        self.recipe_vars = {} # {"recipe_name": RecipeVariable}
        self.objective = None
        self.leftover_vars = {} # {"product_name": leftover_amount_var}
        # Initialize output variables
        self.opt_recipe_count = {} # {"recipe_name": (Recipe, int)}
        self.graph = ProductionGraph()
        self.result_output_count = {} # {"output_product_name": int}
        self.result_waste_count = {} # {"wasted_product_name": int}
        self.result_output_value = None
        self.result_waste_value = None
        self.result_power_consumption = None
        
        # Initialize the solver
        # GLOP: General linear programming solver
        # SAT: Mixed integer programming solver (decision variables have to be integers)
        self.solver = pywraplp.Solver.CreateSolver("SCIP")
        if not self.solver:
            raise ValueError("Solver not found")

    
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
        unnecessary_recipes = [r for r in self.recipes if all(r.product_net_rate(p) <= 0 for p in needed_products)]
        self.recipes = [r for r in self.recipes if r not in unnecessary_recipes]
        
        # Remove inputs that aren't needed
        unnecessary_inputs = [p for p in self.inputs.keys() if p not in needed_products]
        self.inputs = {p: rate for p, rate in self.inputs.items() if p in needed_products}
        
        # DEBUG: Announce reduction results
        # print(f"Reducing problem: removed {len(unnecessary_inputs)} unnecessary inputs and {len(unnecessary_recipes)} recipes.")
    
    
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
    
    """ Helper functions in creating objective functions for all variants of single-objective optimization """
    def _add_obj_coeff(self, var, delta: float):
        """Accumulate objective coefficient for a variable instead of overwriting it."""
        self.objective.SetCoefficient(var, self.objective.GetCoefficient(var) + delta)


    def _set_obj_value(self):
        """ (To be used in _single_obj_process) Create target product value contribution to the objective """
        for recipe in self.recipes:
            # Calculate score contribution (sum of the all target production rate * its score)
            recipe_contribution = sum([recipe.product_net_rate(c) * s for c, s in self.outputs.items()])
            recipe_contribution -= self.get_recipe_cost()
            # Penalize alternate recipes slightly to prioritize original recipes for simplicity
            if recipe.alternate:
                recipe_contribution -= ALT_PENALTY
            recipe_contribution = -recipe_contribution # To be turned into minimization problem
            self._add_obj_coeff(self.recipe_vars[recipe.name], recipe_contribution)
    
    
    def _set_obj_waste(self):
        """ (To be used in _single_obj_process) Create waste penalities to the objective """
        for product_name, leftover_var in self.leftover_vars.items():
            self._add_obj_coeff(leftover_var, WASTE_PENALTY)
    
    
    def _set_obj_power(self):
        """ (To be used in _single_obj_process) Create power consumption penalities to the objective """
        for recipe in self.recipes:
            self._add_obj_coeff(self.recipe_vars[recipe.name], recipe.power_consumption * POWER_PENALTY)
    
    
    def _report_solution(self):
        """ A helper function to print out the solution in a readable format, can be called after optimization is done """
        print("\nSolution:")
        print(f"Objective value: {self.objective.Value():.2f}")
        print("\nRecipes Used:")
        for recipe in self.recipes:
            var = self.recipe_vars[recipe.name]
            if var.solution_value():
                print(f"{recipe.name}: {var.solution_value()}")
        print("\nInputs Remaining:")
        for p, q in self.inputs.items():
            for recipe in self.recipes:
                q += recipe.product_net_rate(p) * self.recipe_vars[recipe.name].solution_value()
            print(f"{p}: {q:.2f}")
        print("\nProduced:")
        for p in self.outputs:
            q = 0
            for recipe in self.recipes:
                q += recipe.product_net_rate(p) * self.recipe_vars[recipe.name].solution_value()
            if q > 0.01:
                print(f"{p}: {q:.2f}")
    
    
    def _single_obj_process(self, methods: List[Callable[[], None]]):
        """ A dynamic handler function which receives different objective setup functions for different single-objective optimization variants """
        
        # Initialize objective function
        self.objective = self.solver.Objective()
        
        # Apply objective setups, e.g., value, waste, power, stacking contributions or penalties to final score
        for method in methods:
            method()
        
        # Set minimization for the combined objective, minimization as the ground rule for all variants in above methods
        self.objective.SetMinimization()
        
        # Solve
        self.solver.Solve()
        
        # Validate that all recipes are of integer scale
        for var in self.recipe_vars.values():
            if not var.solution_value().is_integer():
                raise ValueError("Non-integer solution value for recipe count")
        
        # Store optimized recipe counts in int type
        for recipe in self.recipes:
            self.opt_recipe_count[recipe.name] = (recipe, int(self.recipe_vars[recipe.name].solution_value()))
        
        # DEBUG
        # self._report_solution()

    
    def _multi_obj_value_waste(self):
        """ Multi-objective: maximize production score and minimize waste simultaneously """
        
        from src.multi_objective.weight_estimate import normalize, ws_norm_params
        
        pareto_solutions = []
        resolution = 20 # Sampled step = 1/resolution
        weights = np.array(integer_simplex(2, resolution), dtype=float) / resolution
        
        # Obtain normalization parameters for this problem
        problem_obj = {'recipes': self.recipes, 'inputs': self.inputs, 'outputs': self.outputs}
        params = ws_norm_params(problem_obj, ['value', 'waste'])
        f1_best, f1_worst = params['value']
        f2_best, f2_worst = params['waste']
        waste_norm_scale = 1 / (abs(f2_worst - f2_best) + 1e-10)

        utopia_point = [f1_best, f2_best]
        
        # DEBUG
        # print("DEBUG: Normalize test:")
        # f1_values = [27000, 0.1, 6000, 19999]
        # f2_values = [0, 100, 500, f2_worst]
        # for i in range(4):
        #     print(f"f1: {f1_values[i]}, normalized: {normalize(f1_values[i], f1_best, f1_worst)}")
        #     print(f"f2: {f2_values[i]}, normalized: {normalize(f2_values[i], f2_best, f2_worst)}")
        
        # Iterate through different combinations of weights
        for w in weights:
            w1, w2 = w
            
            # Create weighted objective
            self.objective = self.solver.Objective()
            for recipe in self.recipes:
                # Calculate score contribution (sum of the all target production rate * its score)
                recipe_contribution = sum([recipe.product_net_rate(c) * s for c, s in self.outputs.items()])
                recipe_contribution -= self.get_recipe_cost()
                recipe_contribution = -recipe_contribution # To be turned into minimization problem
                recipe_contribution = normalize(recipe_contribution, f1_best, f1_worst)
                # Weighted combination (maximize value part)
                weighted_contribution = w1 * recipe_contribution
                # Penalize alternate recipes slightly to prioritize original recipes for simplicity
                if recipe.alternate:
                    weighted_contribution -= ALT_PENALTY
                self.objective.SetCoefficient(self.recipe_vars[recipe.name], weighted_contribution)

            # Add weighted waste part from explicit leftover variables
            for product_name, leftover_var in self.leftover_vars.items():
                self.objective.SetCoefficient(leftover_var, w2 * waste_norm_scale)

            self.objective.SetMinimization()

            # Different from single objective, solve for now to locate different weight combinations
            self.solver.Solve()
            
            # Calculate objective values
            total_value = sum(
                self.recipe_vars[recipe.name].solution_value() *
                sum([recipe.product_net_rate(c) * s for c, s in self.outputs.items()])
                for recipe in self.recipes
            )
            
            # Store current solution for graph creation
            current_solution = {recipe.name: self.recipe_vars[recipe.name].solution_value() for recipe in self.recipes}
            
            # Create temporary graph to calculate actual waste
            temp_graph = ProductionGraph()
            temp_graph.create([(recipe, int(current_solution[recipe.name])) for recipe in self.recipes], self.inputs, self.outputs)
            
            # Calculate total waste from WasteVertex objects
            total_waste = sum(vertex.wasted_rate for vertex in temp_graph.vertices if isinstance(vertex, WasteVertex))
            
            pareto_solutions.append((total_value, total_waste, w1, w2, current_solution))
        
        # DEBUG
        # print("Pareto Front Solutions (Value, Waste, w_production, w_waste):")
        # for solution in pareto_solutions:
        #     print(f"Value: {solution[0]:.2f}, Waste: {solution[1]:.2f}, w1: {solution[2]:.2f}, w2: {solution[3]:.2f}")
        
        # Pick the best solution among pareto solutions based on utopia point
        best_index = pick_utopia(utopia_point, [(solution[0], solution[1]) for solution in pareto_solutions])
        
        # Locate back the best weight set and store best solution
        best_w1 = pareto_solutions[best_index][2]
        best_w2 = pareto_solutions[best_index][3]
        print(f"The best weight between value and waste is {best_w1}:{best_w2}")
        for recipe_name, sol_val in pareto_solutions[best_index][4].items():
            # Recall: [4] stores current_solution {recipe.name: ...solution_value()}
            self.opt_recipe_count[recipe_name] = (self.get_recipe_by_name(recipe_name), int(sol_val))


    def _multi_obj_value_waste_power(self):
        """ Multi-objective: maximize production score, minimize waste, and minimize power simultaneously """

        from src.multi_objective.weight_estimate import normalize, ws_norm_params

        pareto_solutions = []
        resolution = 20 # Sampled step = 1/resolution
        weights = np.array(integer_simplex(3, resolution), dtype=float) / resolution

        # Obtain normalization parameters for this problem
        problem_obj = {'recipes': self.recipes, 'inputs': self.inputs, 'outputs': self.outputs}
        params = ws_norm_params(problem_obj, ['value', 'waste', 'power'])
        f1_best, f1_worst = params['value']
        f2_best, f2_worst = params['waste']
        f3_best, f3_worst = params['power']
        waste_norm_scale = 1 / (abs(f2_worst - f2_best) + 1e-10)
        power_norm_scale = 1 / (abs(f3_worst - f3_best) + 1e-10)

        utopia_point = [f1_best, f2_best, 0]

        # Iterate through different combinations of weights
        for w in weights:
            w1, w2, w3 = w

            # Create weighted objective
            self.objective = self.solver.Objective()
            for recipe in self.recipes:
                # Calculate score contribution (sum of the all target production rate * its score)
                recipe_contribution = sum([recipe.product_net_rate(c) * s for c, s in self.outputs.items()])
                recipe_contribution -= self.get_recipe_cost()
                recipe_contribution = -recipe_contribution # To be turned into minimization problem
                recipe_contribution = normalize(recipe_contribution, f1_best, f1_worst)
                weighted_contribution = (w1 * recipe_contribution) + (w3 * recipe.power_consumption * power_norm_scale)
                # Penalize alternate recipes slightly to prioritize original recipes for simplicity
                if recipe.alternate:
                    weighted_contribution -= ALT_PENALTY
                self.objective.SetCoefficient(self.recipe_vars[recipe.name], weighted_contribution)

            # Add weighted waste part from explicit leftover variables
            for product_name, leftover_var in self.leftover_vars.items():
                self.objective.SetCoefficient(leftover_var, w2 * waste_norm_scale)

            self.objective.SetMinimization()

            # Different from single objective, solve for now to locate different weight combinations
            self.solver.Solve()

            # Calculate objective values
            total_value = sum(
                self.recipe_vars[recipe.name].solution_value() *
                sum([recipe.product_net_rate(c) * s for c, s in self.outputs.items()])
                for recipe in self.recipes
            )
            
            # Store current solution for graph creation
            current_solution = {recipe.name: self.recipe_vars[recipe.name].solution_value() for recipe in self.recipes}

            # Create temporary graph to calculate actual waste and power consumption
            temp_graph = ProductionGraph()
            temp_graph.create([(recipe, int(current_solution[recipe.name])) for recipe in self.recipes], self.inputs, self.outputs)
            
            # Calculate total waste from WasteVertex objects
            total_waste = sum(vertex.wasted_rate for vertex in temp_graph.vertices if isinstance(vertex, WasteVertex))
            # Calculate total power consumption from MachineVertex objects
            total_power = sum(
                self.get_recipe_by_name(recipe_name).power_consumption * int(sol_val)
                for recipe_name, sol_val in current_solution.items()
            )

            pareto_solutions.append((total_value, total_waste, total_power, w1, w2, w3, current_solution))

        # Pick the best solution among pareto solutions based on utopia point
        best_index = pick_utopia(utopia_point, [(solution[0], solution[1], solution[2]) for solution in pareto_solutions])

        # Locate back the best weight set and store best solution
        best_w1 = pareto_solutions[best_index][3]
        best_w2 = pareto_solutions[best_index][4]
        best_w3 = pareto_solutions[best_index][5]
        print(f"The best weight between value:waste:power is {best_w1}:{best_w2}:{best_w3}")
        for recipe_name, sol_val in pareto_solutions[best_index][6].items():
            # Recall: [6] stores current_solution {recipe.name: ...solution_value()}
            self.opt_recipe_count[recipe_name] = (self.get_recipe_by_name(recipe_name), int(sol_val))
    
    
    def optimize(self):
        """ Optimize the production problem to find the best recipe counts """
        
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
        # List of recipe counts, if there are 100 different recipes, here creates 100 variables to be optimized
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

        # Build leftover variables for all non-target products to keep track on waste (optional, not to be used in all methods)
        # leftover(product) = input(product) + sum(recipe_count * net_rate(product))
        self.leftover_vars = {}
        for product in products:
            if product in self.outputs:
                continue
            input_amount = self.inputs[product] if product in self.inputs else 0
            leftover_var = self.solver.NumVar(0, self.get_product_max(), f"leftover_{product.name}")
            self.leftover_vars[product.name] = leftover_var
            # Equality form: sum(net_rate * x) - leftover = -input_amount
            ct_leftover = self.solver.RowConstraint(-input_amount, -input_amount, f"leftover_balance_{product.name}")
            for recipe in self.recipes:
                ct_leftover.SetCoefficient(self.recipe_vars[recipe.name], recipe.product_net_rate(product))
            ct_leftover.SetCoefficient(leftover_var, -1)

        # Create objective functions

        # Single Objective Method 1: Maximize value
        if self.obj_method == ObjMethods.S_VALUE:
            self._single_obj_process([self._set_obj_value])
        # Single Objective Method 2: Minimize waste
        elif self.obj_method == ObjMethods.S_WASTE:
            self._single_obj_process([self._set_obj_waste])
        # Single Objective Method 3: Maximize value with waste penalty
        elif self.obj_method == ObjMethods.S_VALUE_WASTE:
            self._single_obj_process([self._set_obj_value, self._set_obj_waste])
        # Single Objective Method 4: Maximize value with power consumption penalty
        elif self.obj_method == ObjMethods.S_VALUE_POWER:
            self._single_obj_process([self._set_obj_value, self._set_obj_power])
        # Single Objective Method 5: Maximize value with both waste and power consumption penalty
        elif self.obj_method == ObjMethods.S_VALUE_WASTE_POWER:
            self._single_obj_process([self._set_obj_value, self._set_obj_waste, self._set_obj_power])
        # Multi-Objective Method 1: Maximize total scores given by target products and minimize waste (weighted-sum method)
        elif self.obj_method == ObjMethods.M_VALUE_WASTE:
            self._multi_obj_value_waste()
        # Multi-Objective Method 2: Maximize value and minimize waste and power (weighted-sum method)
        elif self.obj_method == ObjMethods.M_VALUE_WASTE_POWER:
            self._multi_obj_value_waste_power()
        else:
            raise ValueError(f"Invalid objective method: {self.obj_method}")

    
    def read_graph(self):
        """ Retrieve output, waste, and power results by reading the graph directly. """
        # Reset records to avoid residual values on repeated calls
        self.result_output_count = {}
        self.result_waste_count = {}
        self.result_power_consumption = 0
        # Count each output/waste
        for vertex in self.graph.vertices:
            if isinstance(vertex, SinkVertex):
                self.result_output_count[vertex.receive_product.name] = vertex.receive_rate
            elif isinstance(vertex, WasteVertex):
                self.result_waste_count[vertex.wasted_product.name] = self.result_waste_count.get(vertex.wasted_product.name, 0) + vertex.wasted_rate
            elif isinstance(vertex, MachineVertex):
                self.result_power_consumption += vertex.recipe.power_consumption * vertex.scale
        # Calculate total output value according to each product's score
        self.result_output_value = sum(self.result_output_count.get(product.name, 0) * score for product, score in self.outputs.items())
        # Calculate total waste value according to total amount of wasted items
        self.result_waste_value = sum(self.result_waste_count.values())
    
    
    def create_graph(self):
        # Ensure that the problem is optimized
        if not self.opt_recipe_count:
            print("No optimization has been performed yet. Please call optimize() first.")
            return
        
        # Build the production graph topology
        self.graph.create(self.opt_recipe_count.values(), self.inputs, self.outputs)

        # Validate machine inflow-demand consistency for debugging and safety
        valid, issues = self.graph.validate_machine_satisfaction()
        if not valid:
            print(f"Warning: graph has {len(issues)} unsatisfied machine-demand entries.")
            for detail in issues[:10]:
                print(f"  - {detail}")
            if len(issues) > 10:
                print(f"  ... and {len(issues) - 10} more")
        
        # Read important data back to problem instance for convenience
        self.read_graph()
    
    
    def print_graph(self):
        self.graph.terminal_display()
    
    
    def visualize_graph(self, save_path, title):
        # Create and read graph if not already done
        if not self.graph.vertices:
            self.create_graph()

        total_score = custom_round_float(self.result_output_value)
        total_waste = custom_round_float(self.result_waste_value)
        total_power = custom_round_float(self.result_power_consumption)
        title = f"{title} (Product Value: {total_score}, Wasted: {total_waste} unit/min, Power: {total_power} MW)"
        
        # Prepare stats to be displayed on dedicated legend panel
        stats = {
            "Product Value": total_score,
            "Wasted": f"{total_waste} unit/min",
            "Power": f"{total_power} MW",
        }
        self.graph.visualize(save_path, title, stats=stats)
    
    
    def get_value(self):
        if self.result_output_value is None:
            raise ValueError("Graph has not been created yet. Please call create_graph() first.")
        return self.result_output_value
    
    
    def get_waste(self):
        if self.result_waste_value is None:
            raise ValueError("Graph has not been created yet. Please call create_graph() first.")
        return self.result_waste_value


    def get_power_consumption(self):
        if self.result_power_consumption is None:
            raise ValueError("Graph has not been created yet. Please call create_graph() first.")
        return self.result_power_consumption


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