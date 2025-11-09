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
    
    def __repr__(self):
        return self.name
    
    def __eq__(self, other):
        if isinstance(other, Product):
            return self.name == other.name
        return False

    def __hash__(self):
        return hash(self.name)

    def __lt__(self, other):
        if isinstance(other, Product):
            return self.name < other.name
        return NotImplemented


class Product:
    """ Represents a specific placeholder of string for a product that involves in a recipe """
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.name
    
    def __eq__(self, other):
        if isinstance(other, Product):
            return self.name == other.name
        return False

    def __hash__(self):
        return hash(self.name)

    def __lt__(self, other):
        if isinstance(other, Product):
            return self.name < other.name
        return NotImplemented


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
    
    def __repr__(self):
        return self.name
    
    def add_input(self, product: Product, rate: float):
        self.inputs[product] = rate
    
    def add_output(self, product: Product, rate: float):
        self.outputs[product] = rate
    
    def in_products(self) -> Set[Product]:
        """ Get all input products for this recipe """
        return set(self.inputs.keys())
    
    def out_products(self) -> Set[Product]:
        """ Get all output products for this recipe """
        return set(self.outputs.keys())
    
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
        input_str = "\n\t".join([f"{rate} {product}" for product, rate in self.inputs.items()])
        output_str = "\n\t".join([f"{rate} {product}" for product, rate in self.outputs.items()])
        return f"{self.name}\nProduced in: {self.building}\nInputs:\n\t{input_str}\nOutputs:\n\t{output_str}"


# ================================
# Functions Section
# ================================

def load_recipes() -> List[Recipe]:
    """ Loads recipes from a JSON file """
    
    path = os.path.join(os.path.dirname(__file__), "..", "resources", "data.json")
    recipes = []
    # Open and parse the JSON file
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Load data related to recipes as well
    item_data = data["items"] # For getting readable item names from their json name
    building_data = data["buildings"] # For getting readable building names from their json name
    recipe_data = data["recipes"]
    
    # Iterate through each recipe in the "recipes" object
    for recipe_id, recipe_content in recipe_data.items():
        # Ignore recipes which are not related to automated manufacturing (E.g. Those for construction and hand-crafted items)
        if recipe_content["forBuilding"] or not recipe_content["inMachine"]:
            continue
        
        # Extract basic recipe information
        name = recipe_content["name"]
        alternate = recipe_content["alternate"] # Bool value specified whether this recipe has alternate recipes that give the same product
        
        # Get the building where this recipe is produced (use first one if multiple)
        building_id = recipe_content["producedIn"][0]
        building_name = building_data[building_id]["name"]
        
        # Create the recipe object
        recipe = Recipe(name, building_name, alternate)
        
        # Add input ingredients to the recipe
        multiplier = 60 / recipe_content["time"] # To convert all amounts to rate per minute
        for ingredient in recipe_content["ingredients"]:
            item_id = ingredient["item"]
            item_name = item_data[item_id]["name"]
            amount = ingredient["amount"]
            recipe.add_input(Product(item_name), float(amount) * multiplier)
        
        # Add output products to the recipe
        for product in recipe_content["products"]:
            item_id = product["item"]
            item_name = item_data[item_id]["name"]
            amount = product["amount"]
            recipe.add_output(Product(item_name), float(amount) * multiplier)
        
        recipes.append(recipe)
    
    return recipes