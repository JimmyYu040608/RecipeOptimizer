""" Helpers for estimating normalization parameters used by weighted-metric multi-objective optimization """

from typing import Dict, List, Tuple, TypedDict

from src.utils import ObjMethods
from src.recipe import Product, Recipe
from src.demo_data import DemoProblems
from src.solver import ProductionProblem


_BOUNDS_CACHE: Dict[tuple, Dict[str, Tuple[float, float]]] = {}


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


def _problem_signature(problem_obj: ProblemObj = None) -> tuple:
    """ Build a hashable signature for cache lookup of normalization bounds """
    if problem_obj is None:
        return ("demo",)

    recipes_sig = []
    for recipe in problem_obj['recipes']:
        product_sig = tuple(sorted((product.name, recipe.product_net_rate(product)) for product in recipe.products_used()))
        recipes_sig.append((recipe.name, recipe.power_consumption, bool(recipe.alternate), product_sig))

    inputs_sig = tuple(sorted((product.name, float(rate)) for product, rate in problem_obj['inputs'].items()))
    outputs_sig = tuple(sorted((product.name, float(score)) for product, score in problem_obj['outputs'].items()))
    return (tuple(sorted(recipes_sig)), inputs_sig, outputs_sig)


def _compute_total_value(problem: ProductionProblem) -> float:
    """ Compute target output value directly from solved recipe variables """
    return sum(
        recipe.product_net_rate(product) * score * problem.recipe_vars[recipe.name].solution_value()
        for recipe in problem.recipes
        for product, score in problem.outputs.items()
    )


def _compute_total_waste(problem: ProductionProblem) -> float:
    """ Compute waste amount directly from solved variables without creating graph objects """
    # Preferred source: explicit leftover variables already encode non-target surplus.
    if problem.leftover_vars:
        return sum(leftover_var.solution_value() for leftover_var in problem.leftover_vars.values())

    # Fallback: reconstruct non-target surplus from net rates if leftover vars are absent.
    products = sorted({product for recipe in problem.recipes for product in recipe.products_used()}, key=lambda p: p.name)
    total_waste = 0.0
    for product in products:
        if product in problem.outputs:
            continue
        input_amount = problem.inputs[product] if product in problem.inputs else 0.0
        produced_amount = sum(
            recipe.product_net_rate(product) * problem.recipe_vars[recipe.name].solution_value()
            for recipe in problem.recipes
        )
        total_waste += max(0.0, input_amount + produced_amount)
    return total_waste


def _estimate_value_bounds(problem_obj: ProblemObj = None) -> Tuple[float, float]:
    """ Return (best, worst) bounds for objective value """
    f_problem = _build_problem(problem_obj, ObjMethods.S_VALUE)
    f_problem.optimize()
    f_best = _compute_total_value(f_problem)
    f_worst = 0 # Background knowledge: Best case = Maximum value achieved by optimizing for value only

    return f_best, f_worst


def _estimate_waste_bounds(problem_obj: ProblemObj = None) -> Tuple[float, float]:
    """ Return (best, worst) bounds for waste amount """
    
    # Best case = Minimum waste achieved by optimizing for waste only
    f_problem_best = _build_problem(problem_obj, ObjMethods.S_WASTE)
    f_problem_best.optimize()
    f_best = _compute_total_waste(f_problem_best)
    

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

    f_worst = _compute_total_waste(f_problem_worst)
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


def wm_norm_params(problem_obj: ProblemObj = None, objectives: List[str] = None) -> Dict[str, Tuple[float, float]]:
    """ Generalized normalization parameter estimator for weighted-metric objectives
    Supported objective keys: value, waste, power
    Returns: {objective_name: (best, worst)}
    """
    # Default: maximizing value and minimizing waste
    if objectives is None:
        objectives = ['value', 'waste']

    # Cache normalization bounds per static problem definition.
    cache_key = _problem_signature(problem_obj)
    if cache_key not in _BOUNDS_CACHE:
        _BOUNDS_CACHE[cache_key] = {}
    cached_bounds = _BOUNDS_CACHE[cache_key]

    result: Dict[str, Tuple[float, float]] = {}
    for objective in objectives:
        if objective in cached_bounds:
            result[objective] = cached_bounds[objective]
            continue

        if objective == 'value':
            result['value'] = _estimate_value_bounds(problem_obj)
        elif objective == 'waste':
            result['waste'] = _estimate_waste_bounds(problem_obj)
        elif objective == 'power':
            result['power'] = _estimate_power_bounds(problem_obj)
        else:
            raise ValueError(f"Unsupported objective key: {objective}")
        cached_bounds[objective] = result[objective]
    return result