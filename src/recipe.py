from typing import List
import json
import os

class Recipe:
    """ Represents the inputs, outputs, etc for a single recipe """

    def __init__(self, name: str, building: str, alternate=False):
        self.name = name
        self.building = building
        self.inputs = {}
        self.outputs = {}
        self.alternate = alternate

    def add_input(self, name: str, quantity: float):
        self.inputs[name] = quantity

    def add_output(self, name: str, quantity: float):
        self.outputs[name] = quantity

    def products_used(self):
        return set(self.inputs.keys()).union(set(self.outputs.keys()))

    def product_net_quantity(self, product: str):
        net = 0

        if product in self.inputs:
            net -= self.inputs[product]
        if product in self.outputs:
            net += self.outputs[product]

        return net

    def description(self):
        input_str = '\n\t'.join([f"{q} {i}" for i, q, in self.inputs.items()])
        output_str = '\n\t'.join([f"{q} {i}" for i, q, in self.outputs.items()])
        return f"{self.name}\nProduced in: {self.building}\nInputs:\n\t{input_str}\nOutputs:\n\t{output_str}"

    def __str__(self):
        return self.name

def load_recipes() -> List[Recipe]:
    """ Loads recipes from a JSON file """
    
    path = os.path.join(os.path.dirname(__file__), '..', 'resources', 'data.json')
    recipes = []
    # Open and parse the JSON file
    with open(path, 'r') as f:
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
