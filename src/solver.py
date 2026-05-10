import numpy as np
from ortools.linear_solver import pywraplp
from typing import List, Dict, Set, Callable, Tuple
import math

from src.utils import custom_round_float, MethodTypes, ObjMethods, integer_simplex
from src.recipe import Product, Recipe
from src.graph import ProductionGraph, SinkVertex, WasteVertex, MachineVertex

RECIPE_MAX = 100 # Maximum allowable amount of any single recipe
PRODUCT_MAX = 10000 # Maximum allowable amount of any single product

RECIPE_COST = 0.01 # Small cost to discourage extraneous recipes
ALT_PENALTY = 1e-6 # Penalty weight for using alternate recipes, to be tuned based on the specific problem context
WASTE_PENALTY = 1 # Penalty weight for waste in value+waste optimization, to be tuned based on the specific problem context
POWER_PENALTY = 1 # Penalty weight for power consumption in value+power optimization, to be tuned based on the specific problem context

PARETO_RESOLUTION = 10 # Resolution for sampling weights in weighted-metric multi-objective optimization, to be tuned based on the specific problem context and computational budget

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
        self._alt_penalty = ALT_PENALTY
        self._waste_penalty = WASTE_PENALTY
        self._power_penalty = POWER_PENALTY
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
        self.best_weights = None # {"objective_name": weight} for multi-objective methods, None for single-objective
        
        # Initialize the solver
        # GLOP: General linear programming solver
        # SAT: Mixed integer programming solver (decision variables have to be integers)
        self.solver = pywraplp.Solver.CreateSolver("SCIP")
        if not self.solver:
            raise ValueError("Solver not found")

    
    def get_recipe_max(self):
        return self._recipe_max
    
    
    def get_product_max(self):
        return self._product_max
    
    
    def get_recipe_cost(self):
        return self._recipe_cost


    def get_alt_penalty(self):
        return self._alt_penalty


    def get_waste_penalty(self):
        return self._waste_penalty


    def get_power_penalty(self):
        return self._power_penalty


    def get_best_weights(self):
        return self.best_weights


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


    def _is_reversible_pair(self, recipe_a: Recipe, recipe_b: Recipe, tol: float = 1e-9) -> bool:
        """ Detect whether recipe_b is the reverse transform of recipe_a up to a positive scale. """
        products = recipe_a.products_used().union(recipe_b.products_used())
        ratio = None

        for product in products:
            net_a = recipe_a.product_net_rate(product)
            net_b = recipe_b.product_net_rate(product)

            # Ignore products unused by both recipes.
            if abs(net_a) <= tol and abs(net_b) <= tol:
                continue
            # A reversible pair must involve both recipes on every used product.
            if abs(net_a) <= tol or abs(net_b) <= tol:
                return False

            local_ratio = -net_a / net_b
            if local_ratio <= tol:
                return False
            if ratio is None:
                ratio = local_ratio
            elif abs(local_ratio - ratio) > 1e-6 * max(1.0, abs(ratio)):
                return False

        return ratio is not None


    def _add_reversible_pair_exclusion_constraints(self):
        """ Add hard mutual-exclusion constraints for detected reversible recipe pairs. """
        reversible_pairs: List[Tuple[Recipe, Recipe]] = []
        for i in range(len(self.recipes)):
            recipe_a = self.recipes[i]
            for j in range(i + 1, len(self.recipes)):
                recipe_b = self.recipes[j]
                if self._is_reversible_pair(recipe_a, recipe_b):
                    reversible_pairs.append((recipe_a, recipe_b))

        if not reversible_pairs:
            return

        # Introduce binary "active" vars and link usage with x <= M * active.
        active_vars: Dict[str, pywraplp.Variable] = {}
        for recipe_a, recipe_b in reversible_pairs:
            for recipe in (recipe_a, recipe_b):
                if recipe.name in active_vars:
                    continue
                active_var = self.solver.IntVar(0, 1, f"active_{recipe.name}")
                active_vars[recipe.name] = active_var
                link_ct = self.solver.RowConstraint(-self.solver.infinity(), 0, f"link_active_{recipe.name}")
                link_ct.SetCoefficient(self.recipe_vars[recipe.name], 1)
                link_ct.SetCoefficient(active_var, -self.get_recipe_max())

        # For each reversible pair, enforce that at most one recipe can be active.
        for recipe_a, recipe_b in reversible_pairs:
            pair_ct = self.solver.RowConstraint(-self.solver.infinity(), 1, f"mutex_reversible_{recipe_a.name}__{recipe_b.name}")
            pair_ct.SetCoefficient(active_vars[recipe_a.name], 1)
            pair_ct.SetCoefficient(active_vars[recipe_b.name], 1)
    
    
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
                recipe_contribution -= self.get_alt_penalty()
            recipe_contribution = -recipe_contribution # To be turned into minimization problem
            self._add_obj_coeff(self.recipe_vars[recipe.name], recipe_contribution)
    
    
    def _set_obj_waste(self):
        """ (To be used in _single_obj_process) Create waste penalities to the objective """
        for product_name, leftover_var in self.leftover_vars.items():
            self._add_obj_coeff(leftover_var, self.get_waste_penalty())
        # Ensure the optimizer picks the routine which uses fewest recipes among those with same waste
        for recipe in self.recipes:
            self._add_obj_coeff(self.recipe_vars[recipe.name], self.get_recipe_cost())
    
    
    def _set_obj_power(self):
        """ (To be used in _single_obj_process) Create power consumption penalities to the objective """
        for recipe in self.recipes:
            self._add_obj_coeff(self.recipe_vars[recipe.name], recipe.power_consumption * self.get_power_penalty())
    
    
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
        
        from src.multi_objective.weight_estimate import normalize, wm_norm_params
        
        resolution = PARETO_RESOLUTION # Sampled step = 1/resolution
        weights = np.array(integer_simplex(2, resolution), dtype=float) / resolution

        # Precompute variable handles and objective coefficients to avoid repeated dictionary/list traversals.
        recipe_var_items = [(recipe, self.recipe_vars[recipe.name]) for recipe in self.recipes]
        recipe_value_coeff = {
            recipe.name: sum(recipe.product_net_rate(c) * s for c, s in self.outputs.items())
            for recipe in self.recipes
        }
        leftover_var_list = list(self.leftover_vars.values())
        
        # Obtain normalization parameters for this problem
        problem_obj = {'recipes': self.recipes, 'inputs': self.inputs, 'outputs': self.outputs}
        params = wm_norm_params(problem_obj, ['value', 'waste'])
        f1_best, f1_worst = params['value']
        f2_best, f2_worst = params['waste']
        waste_norm_scale = 1 / (abs(f2_worst - f2_best) + 1e-10)

        utopia_point = [f1_best, f2_best]

        normalized_value_coeff = {}
        for recipe in self.recipes:
            recipe_contribution = recipe_value_coeff[recipe.name] - self.get_recipe_cost()
            recipe_contribution = -recipe_contribution # To be turned into minimization problem
            normalized_value_coeff[recipe.name] = normalize(recipe_contribution, f1_best, f1_worst)

        # Track best solution online to avoid storing all sampled Pareto points with full assignments.
        best_dist = None
        best_point = None
        best_weights = None
        best_solution = None
        
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
            for recipe, recipe_var in recipe_var_items:
                # Weighted combination (maximize value part)
                weighted_contribution = w1 * normalized_value_coeff[recipe.name]
                # Penalize alternate recipes slightly to prioritize original recipes for simplicity
                if recipe.alternate:
                    weighted_contribution -= self.get_alt_penalty()
                self.objective.SetCoefficient(recipe_var, weighted_contribution)

            # Add weighted waste part from explicit leftover variables
            for leftover_var in leftover_var_list:
                self.objective.SetCoefficient(leftover_var, w2 * waste_norm_scale)

            self.objective.SetMinimization()

            # Different from single objective, solve for now to locate different weight combinations
            self.solver.Solve()
            
            # Calculate objective values
            total_value = sum(
                recipe_var.solution_value() * recipe_value_coeff[recipe.name]
                for recipe, recipe_var in recipe_var_items
            )
            # Read waste directly from leftover decision variables
            total_waste = sum(leftover_var.solution_value() for leftover_var in leftover_var_list)

            point = (total_value, total_waste)
            dist = math.dist(utopia_point, point)
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best_point = point
                best_weights = (w1, w2)
                best_solution = {recipe.name: recipe_var.solution_value() for recipe, recipe_var in recipe_var_items}

        if best_dist is None or best_solution is None or best_weights is None or best_point is None:
            raise ValueError("Fail to locate best Pareto optimum")

        print(f"Best Pareto optimum found: {best_point} with distance {best_dist} to utopia point {utopia_point}")
        best_w1, best_w2 = best_weights
        print(f"The best weight between value and waste is {best_w1}:{best_w2}")
        self.best_weights = {"value": best_w1, "waste": best_w2}
        for recipe_name, sol_val in best_solution.items():
            self.opt_recipe_count[recipe_name] = (self.get_recipe_by_name(recipe_name), int(sol_val))


    def _multi_obj_value_waste_power(self):
        """ Multi-objective: maximize production score, minimize waste, and minimize power simultaneously """

        from src.multi_objective.weight_estimate import normalize, wm_norm_params

        resolution = PARETO_RESOLUTION # Sampled step = 1/resolution
        weights = np.array(integer_simplex(3, resolution), dtype=float) / resolution

        # Precompute variable handles and objective coefficients to avoid repeated dictionary/list traversals.
        recipe_var_items = [(recipe, self.recipe_vars[recipe.name]) for recipe in self.recipes]
        recipe_value_coeff = {
            recipe.name: sum(recipe.product_net_rate(c) * s for c, s in self.outputs.items())
            for recipe in self.recipes
        }
        leftover_var_list = list(self.leftover_vars.values())

        # Obtain normalization parameters for this problem
        problem_obj = {'recipes': self.recipes, 'inputs': self.inputs, 'outputs': self.outputs}
        params = wm_norm_params(problem_obj, ['value', 'waste', 'power'])
        f1_best, f1_worst = params['value']
        f2_best, f2_worst = params['waste']
        f3_best, f3_worst = params['power']
        waste_norm_scale = 1 / (abs(f2_worst - f2_best) + 1e-10)
        power_norm_scale = 1 / (abs(f3_worst - f3_best) + 1e-10)

        utopia_point = [f1_best, f2_best, 0]

        normalized_value_coeff = {}
        for recipe in self.recipes:
            recipe_contribution = recipe_value_coeff[recipe.name] - self.get_recipe_cost()
            recipe_contribution = -recipe_contribution # To be turned into minimization problem
            normalized_value_coeff[recipe.name] = normalize(recipe_contribution, f1_best, f1_worst)

        # Track best solution online to avoid storing all sampled Pareto points with full assignments.
        best_dist = None
        best_point = None
        best_weights = None
        best_solution = None

        # Iterate through different combinations of weights
        for w in weights:
            w1, w2, w3 = w

            # Create weighted objective
            self.objective = self.solver.Objective()
            for recipe, recipe_var in recipe_var_items:
                weighted_contribution = (w1 * normalized_value_coeff[recipe.name]) + (w3 * recipe.power_consumption * power_norm_scale)
                # Penalize alternate recipes slightly to prioritize original recipes for simplicity
                if recipe.alternate:
                    weighted_contribution -= self.get_alt_penalty()
                self.objective.SetCoefficient(recipe_var, weighted_contribution)

            # Add weighted waste part from explicit leftover variables
            for leftover_var in leftover_var_list:
                self.objective.SetCoefficient(leftover_var, w2 * waste_norm_scale)

            self.objective.SetMinimization()

            # Different from single objective, solve for now to locate different weight combinations
            self.solver.Solve()

            # Calculate objective values
            total_value = sum(
                recipe_var.solution_value() * recipe_value_coeff[recipe.name]
                for recipe, recipe_var in recipe_var_items
            )
            # Read waste directly from leftover decision variables
            total_waste = sum(leftover_var.solution_value() for leftover_var in leftover_var_list)
            # Calculate total power consumption directly from solved recipe counts
            total_power = sum(
                recipe.power_consumption * recipe_var.solution_value()
                for recipe, recipe_var in recipe_var_items
            )

            point = (total_value, total_waste, total_power)
            dist = math.dist(utopia_point, point)
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best_point = point
                best_weights = (w1, w2, w3)
                best_solution = {recipe.name: recipe_var.solution_value() for recipe, recipe_var in recipe_var_items}

        if best_dist is None or best_solution is None or best_weights is None or best_point is None:
            raise ValueError("Fail to locate best Pareto optimum")

        print(f"Best Pareto optimum found: {best_point} with distance {best_dist} to utopia point {utopia_point}")
        best_w1, best_w2, best_w3 = best_weights
        print(f"The best weight between value:waste:power is {best_w1}:{best_w2}:{best_w3}")
        self.best_weights = {"value": best_w1, "waste": best_w2, "power": best_w3}
        for recipe_name, sol_val in best_solution.items():
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

        # Add hard mutual-exclusion constraints for known reversible recipe pairs.
        self._add_reversible_pair_exclusion_constraints()
        
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
        # Multi-Objective Method 1: Maximize total scores given by target products and minimize waste (weighted-metric method)
        elif self.obj_method == ObjMethods.M_VALUE_WASTE:
            self._multi_obj_value_waste()
        # Multi-Objective Method 2: Maximize value and minimize waste and power (weighted-metric method)
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
        total_vertices = len(self.graph.vertices)
        total_edges = len(self.graph.edges)
        title = f"{title} (Product Value: {total_score}, Wasted: {total_waste} unit/min, Power: {total_power} MW)"
        
        # Prepare stats to be displayed on dedicated legend panel
        stats = {
            "Vertices": total_vertices,
            "Edges": total_edges,
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