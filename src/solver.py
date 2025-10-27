from ortools.linear_solver import pywraplp
from typing import List, Dict

from recipe import Product, Recipe
from graph import ProductionGraph

def optimize_recipes(recipes: List[Recipe], inputs: Dict[Product, float], outputs: Dict[Product, float]) -> ProductionGraph:
    pass