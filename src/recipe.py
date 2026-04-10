from dataclasses import dataclass, field
from typing import List, Dict, Set
import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "resources", "data_1.1.json")

# ================================
# Classes Section
# ================================

@dataclass(frozen=True, eq=False)
class Building:
    """ Represents a specific placeholder of string for building type, no special function """
    name: str
    power_consumption: float = 0.0
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.name
    
    def __eq__(self, other):
        if isinstance(other, Building):
            return self.name == other.name
        return False

    def __hash__(self):
        return hash(self.name)

    def __lt__(self, other):
        if isinstance(other, Building):
            return self.name < other.name
        return NotImplemented


@dataclass(frozen=True, eq=False)
class Product:
    """ Represents a specific placeholder of string for a product that involves in a recipe """
    name: str
    sink_pt: int

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


@dataclass(eq=False)
class Recipe:
    """Represents a recipe together with its building, inputs, and outputs."""
    name: str
    building: Building | str
    alternate: bool = False
    inputs: Dict[Product, float] = field(default_factory=dict)
    outputs: Dict[Product, float] = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.building, str):
            self.building = Building(self.building)
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.name

    @property
    def building_name(self) -> str:
        return self.building.name

    @property
    def power_consumption(self) -> float:
        return self.building.power_consumption
    
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
    
    path = DATA_PATH
    recipes = []
    # Open and parse the JSON file
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Load data related to recipes as well
    item_data = data["items"] # For getting readable item names and sink points from their json name
    building_data = data["buildings"] # For getting readable building names from their json name
    recipe_data = data["recipes"]
    # Power data is stored under building metadata in this dataset schema.
    building_cache = {
        building_id: Building(
            building_content["name"],
            float(building_content.get("metadata", {}).get("powerConsumption", 0.0)),
        )
        for building_id, building_content in building_data.items()
    } # To store different buildings which will be used in multiple recipes, not to repeatedly create identical Building instances
    
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
        building = building_cache[building_id]
        
        # Create the recipe object
        recipe = Recipe(name, building, alternate)
        
        # Add input ingredients to the recipe
        multiplier = 60 / recipe_content["time"] # To convert all amounts to rate per minute
        for ingredient in recipe_content["ingredients"]:
            item_id = ingredient["item"]
            item_name = item_data[item_id]["name"]
            item_sink_pt = item_data[item_id]["sinkPoints"]
            amount = ingredient["amount"]
            recipe.add_input(Product(item_name, item_sink_pt), float(amount) * multiplier)
        
        # Add output products to the recipe
        for product in recipe_content["products"]:
            item_id = product["item"]
            item_name = item_data[item_id]["name"]
            item_sink_pt = item_data[item_id]["sinkPoints"]
            amount = product["amount"]
            recipe.add_output(Product(item_name, item_sink_pt), float(amount) * multiplier)
        
        recipes.append(recipe)
    
    return recipes

def get_item_sink_pt(item_name: str) -> int:
    """ Get the sink point of a specific item by its name """
    path = DATA_PATH
    # Open and parse the JSON file
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Load all items
    item_data = data["items"]
    # Loop through items to locate the target
    for item_id, item_content in item_data.items():
        if item_content["name"] == item_name:
            return item_content["sinkPoints"]
    raise ValueError(f"Item '{item_name}' not found in data file")