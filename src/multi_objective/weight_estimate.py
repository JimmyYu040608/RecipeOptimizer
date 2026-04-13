""" Helpers for estimating normalization parameters used by weighted-sum multi-objective optimization """

from typing import Dict, List, Tuple, TypedDict

from src.utils import ObjMethods
from src.recipe import Product, Recipe
from src.demo_data import DemoProblems
from src.solver import ProductionProblem


class ProblemObj(TypedDict):
    recipes: List[Recipe]
    inputs: Dict[Product, float]
    outputs: Dict[Product, float]


def normalize_min(f, f_best, f_worst):
    """ f is the value of the objective to be minimized, thus f_best <= f_worst """
    return (f - f_best) / (f_worst - f_best + 1e-10)


def normalize_max(f, f_best, f_worst):
    """ f is the value of the objective to be maximized, thus f_best >= f_worst """
    return (f - f_worst) / (f_best - f_worst + 1e-10)
    # return (f_worst - f) / (f_worst - f_best + 1e-10)


def normalize(f, f_best, f_worst):
    """ Detect f to be minimized if f_best < f_worst, or maximized if f_best > f_worst """
    if (f_best > f_worst):
        return normalize_max(f, f_best, f_worst)
    return normalize_min(f, f_best, f_worst)


def _build_problem(problem_obj: ProblemObj = None, obj_method: str = ObjMethods.S_VALUE) -> ProductionProblem:
    """ Create a ProductionProblem from either an explicit problem object or the demo fallback """
    if problem_obj is None:
        return DemoProblems.demo_example(obj_method)
    return ProductionProblem(problem_obj['recipes'], problem_obj['inputs'], problem_obj['outputs'], obj_method)


def _estimate_value_bounds(problem_obj: ProblemObj = None) -> Tuple[float, float]:
    """ Return (best, worst) bounds for objective value """
    f_problem = _build_problem(problem_obj, ObjMethods.S_VALUE)
    f_problem.optimize()
    f_problem.create_graph()
    f_best = f_problem.get_value()
    f_worst = 0 # Background knowledge: Best case = Maximum value achieved by optimizing for value only

    return f_best, f_worst


def _estimate_waste_bounds(problem_obj: ProblemObj = None) -> Tuple[float, float]:
    """ Return (best, worst) bounds for waste amount """
    
    # Best case = Minimum waste achieved by optimizing for waste only
    f_problem_best = _build_problem(problem_obj, ObjMethods.S_WASTE)
    f_problem_best.optimize()
    f_problem_best.create_graph()
    f_best = f_problem_best.get_waste()
    

    # Customize "deoptimize" procedure to get as much waste as possible
    f_problem_worst = _build_problem(problem_obj, ObjMethods.S_WASTE)

    if not f_problem_worst.validate():
        raise ValueError("The problem is invalid")
    f_problem_worst.reduce()
    products = list(set([c for recipe in f_problem_worst.recipes for c in recipe.products_used()]))
    products.sort()
    f_problem_worst.recipe_vars = dict([
        (r.name, f_problem_worst.solver.IntVar(0, f_problem_worst.get_recipe_max(), r.name))
        for r in f_problem_worst.recipes
    ])
    for product in products:
        min_value = -f_problem_worst.inputs[product] if product in f_problem_worst.inputs else 0
        ct = f_problem_worst.solver.RowConstraint(min_value, f_problem_worst.get_product_max(), product.name)
        for recipe in f_problem_worst.recipes:
            ct.SetCoefficient(f_problem_worst.recipe_vars[recipe.name], recipe.product_net_rate(product))

    f_problem_worst.objective = f_problem_worst.solver.Objective()
    for recipe in f_problem_worst.recipes:
        waste_contribution = sum([
            recipe.product_net_rate(product)
            for product in recipe.products_used()
            if product not in f_problem_worst.outputs
        ])
        f_problem_worst.objective.SetCoefficient(f_problem_worst.recipe_vars[recipe.name], waste_contribution)
    f_problem_worst.objective.SetMaximization()
    f_problem_worst.solver.Solve()

    for var in f_problem_worst.recipe_vars.values():
        if not var.solution_value().is_integer():
            raise ValueError("Non-integer solution value for recipe count")
    for recipe in f_problem_worst.recipes:
        f_problem_worst.opt_recipe_count[recipe.name] = (recipe, int(f_problem_worst.recipe_vars[recipe.name].solution_value()))

    f_problem_worst.create_graph()
    f_worst = f_problem_worst.get_waste()
    return f_best, f_worst


def _estimate_power_bounds(problem_obj: ProblemObj = None) -> Tuple[float, float]:
    """ Return (best, worst) bounds for power consumption """
    f_best = 0 # Background knowledge: Best case = No recipe is used, thus no power is consumed
    # Worst case = All recipes are used at their maximum capacity, thus power consumption is the sum of all recipe power consumptions multiplied by their max usage
    if problem_obj is None:
        p = _build_problem(problem_obj, ObjMethods.S_VALUE)
        recipes = p.recipes
        recipe_max = p.get_recipe_max()
    else:
        recipes = problem_obj['recipes']
        recipe_max = ProductionProblem(problem_obj['recipes'], problem_obj['inputs'], problem_obj['outputs']).get_recipe_max()
    f_worst = sum(recipe.power_consumption * recipe_max for recipe in recipes)
    return f_best, f_worst


def ws_norm_params(problem_obj: ProblemObj = None, objectives: List[str] = None) -> Dict[str, Tuple[float, float]]:
    """ Generalized normalization parameter estimator for weighted-sum objectives
    Supported objective keys: value, waste, power
    Returns: {objective_name: (best, worst)}
    """
    # Default: maximizing value and minimizing waste
    if objectives is None:
        objectives = ['value', 'waste']

    result: Dict[str, Tuple[float, float]] = {}
    for objective in objectives:
        if objective == 'value':
            result['value'] = _estimate_value_bounds(problem_obj)
        elif objective == 'waste':
            result['waste'] = _estimate_waste_bounds(problem_obj)
        elif objective == 'power':
            result['power'] = _estimate_power_bounds(problem_obj)
        else:
            raise ValueError(f"Unsupported objective key: {objective}")
    return result