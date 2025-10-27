from typing import List, Dict, Set
import json
import os


# ================================
# Classes Section
# ================================

class Building:
    """ Represents a specific placeholder of string for building type, no special function """
    def __init__(self, name: str):
        self.name = name
    
    def __str__(self):
        return self.name


class Product:
    """ Represents a specific placeholder of string for a product that involves in a recipe """
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return self.name


class Recipe:
    """ Represents a recipe and its specified input, output, building etc """
    def __init__(self, name: str, building: Building, alternate=False):
        self.name = name
        self.building: Building = building
        self.inputs: Dict[Product, float] = {}
        self.outputs: Dict[Product, float] = {}
        self.alternate = alternate
    
    def __str__(self):
        return self.name
    
    def add_input(self, product: Product, rate: float):
        self.inputs[product] = rate
    
    def add_output(self, product: Product, rate: float):
        self.outputs[product] = rate
    
    def products_used(self) -> Set[Product]:
        """ Get all products used in this recipe """
        return set(self.inputs.keys()).union(set(self.outputs.keys()))
    
    def product_net_rate(self, product: Product) -> float:
        """ Calculate the net intake/usage of a specific product in this recipe """
        net = 0
        if product in self.inputs:
            net -= self.inputs[product]
        if product in self.outputs:
            net += self.outputs[product]
        return net
    
    def description(self):
        input_str = '\n\t'.join([f"{rate} {product}" for product, rate in self.inputs.items()])
        output_str = '\n\t'.join([f"{rate} {product}" for product, rate in self.outputs.items()])
        return f"{self.name}\nProduced in: {self.building}\nInputs:\n\t{input_str}\nOutputs:\n\t{output_str}"


# ================================
# Functions Section
# ================================

def load_recipes() -> List[Recipe]:
    """ Loads recipes from a JSON file """
    
    path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'data.json')
    recipes = []
    # Open and parse the JSON file
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Iterate through each recipe in the "recipes" object
    for recipe_id, recipe_data in data["recipes"].items():
        # Extract basic recipe information
        name = recipe_data["name"]
        alternate = recipe_data["alternate"]
        
        # Get the building where this recipe is produced (use first one if multiple)
        building = recipe_data["producedIn"][0] if recipe_data["producedIn"] else "Unknown"
        
        # Create the recipe object
        recipe = Recipe(name, building, alternate)
        
        # Add input ingredients to the recipe
        for ingredient in recipe_data["ingredients"]:
            item_name = ingredient["item"]
            amount = ingredient["amount"]
            recipe.add_input(item_name, float(amount))
        
        # Add output products to the recipe
        for product in recipe_data["products"]:
            item_name = product["item"]
            amount = product["amount"]
            recipe.add_output(item_name, float(amount))
        
        recipes.append(recipe)
    
    return recipes