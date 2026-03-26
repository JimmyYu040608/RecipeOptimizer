""" A specialized Python script for estimating most suitable weights for different multi-objective optimization methods, not for doing the optimization itself """

from src.common import ObjMethods
from src.recipe import Recipe, Product
from src.shared_setup import create_demo_problem
from src.solver import ProductionProblem
from src.graph import ProductionGraph, WasteVertex
from typing import List, Dict, TypedDict


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


def ws_value_waste_norm_param(problem_obj: ProblemObj = None):
    """ By conducting single-objective optimization on value and waste independently, return the normalized objectives for weighted sum method in multi-objective optimization """
    # Two objectives: Maximize value and minimize waste
    
    
    # f1: Minimize -value
    f1_worst = 0 # Background knowledge: Worst case = No desired output product is produced
    f1_problem = None
    if problem_obj is None:
        print("Value-Waste weight estimate: Used demo problem")
        f1_problem = create_demo_problem()
    else:
        f1_problem = ProductionProblem(problem_obj['recipes'], problem_obj['inputs'], problem_obj['outputs'])
    # Solve for best f1 value independently
    f1_problem.optimize()
    f1_best = sum(f1_problem.recipe_vars[recipe.name].solution_value() * sum([recipe.product_net_rate(c) * s for c, s in f1_problem.outputs.items()]) for recipe in f1_problem.recipes)
    
    
    # f2: Minimize waste
    f2_problem_worst = None
    if problem_obj is None:
        print("Value-Waste weight estimate: Used demo problem")
        f2_problem_worst = create_demo_problem(ObjMethods.S_WASTE)
    else:
        f2_problem_worst = ProductionProblem(problem_obj['recipes'], problem_obj['inputs'], problem_obj['outputs'], ObjMethods.S_WASTE)
        
    f2_best = 0 # Background knowledge: Best case = No waste is left
    
    # Customize "deoptimize" procedure to get as much waste as possible
    if not f2_problem_worst.validate():
        raise ValueError("The problem is invalid")
    f2_problem_worst.reduce()
    products = list(set([c for recipe in f2_problem_worst.recipes for c in recipe.products_used()]))
    products.sort()
    f2_problem_worst.recipe_vars = dict([(r.name, f2_problem_worst.solver.IntVar(0, f2_problem_worst.get_recipe_max(), r.name)) for r in f2_problem_worst.recipes])
    for product in products:
        min_value = -f2_problem_worst.inputs[product] if product in f2_problem_worst.inputs else 0
        ct = f2_problem_worst.solver.RowConstraint(min_value, f2_problem_worst.get_product_max(), product.name)
        for recipe in f2_problem_worst.recipes:
            ct.SetCoefficient(f2_problem_worst.recipe_vars[recipe.name], recipe.product_net_rate(product))
    f2_problem_worst.objective = f2_problem_worst.solver.Objective()
    for recipe in f2_problem_worst.recipes:
        waste_contribution = sum([recipe.product_net_rate(product) for product in recipe.products_used() if product not in f2_problem_worst.outputs])
        f2_problem_worst.objective.SetCoefficient(f2_problem_worst.recipe_vars[recipe.name], waste_contribution)
    f2_problem_worst.objective.SetMaximization()
    f2_problem_worst.solver.Solve()
    for var in f2_problem_worst.recipe_vars.values():
        if not var.solution_value().is_integer():
            raise ValueError("Non-integer solution value for recipe count")
    for recipe in f2_problem_worst.recipes:
        f2_problem_worst.opt_recipe_count[recipe.name] = (recipe, int(f2_problem_worst.recipe_vars[recipe.name].solution_value()))
    # End of "deoptimize" procedure
    
    # Create temporary graph to calculate actual waste
    temp_graph = ProductionGraph()
    temp_graph.create([(recipe, int(f2_problem_worst.recipe_vars[recipe.name].solution_value())) for recipe in f2_problem_worst.recipes], f2_problem_worst.inputs, f2_problem_worst.outputs)
    f2_worst = sum(vertex.wasted_rate for vertex in temp_graph.vertices if isinstance(vertex, WasteVertex))
    temp_graph.visualize('./images/draw/deoptimize_waste', f'Deoptimized Waste Routine (Waste: {f2_worst})')
    
    print(f"DEBUG: {f1_best}, {f1_worst}, {f2_best}, {f2_worst}")
    return f1_best, f1_worst, f2_best, f2_worst


def main():
    pass


if __name__ == "__main__":
    pass