from typing import List
from src.utils import ObjMethods
from src.recipe import Building, Recipe, Product, load_recipes, get_item_sink_pt
from src.solver import ProductionProblem

class DemoItems:
    iron_ingot = Product('Iron Ingot', 10)
    copper_ingot = Product('Copper Ingot', 10)
    screw = Product('Screw', 5)
    iron_plate = Product('Iron Plate', 40)
    reinforced_iron_plate = Product('Reinforced Iron Plate', 100)
    copper_wire = Product('Copper Wire', 4)
    
    @classmethod
    def get_demo_items(self) -> List[Product]:
        return [self.iron_ingot, self.copper_ingot, self.screw, self.iron_plate, self.reinforced_iron_plate, self.copper_wire]

class DemoRecipes:
    constructor = Building('Constructor', 4)

    iron_screw = Recipe('Iron Screw', constructor, True)
    iron_screw.add_input(DemoItems.iron_ingot, 1)
    iron_screw.add_output(DemoItems.screw, 4)
    
    copper_screw = Recipe('Copper Screw', constructor, True)
    copper_screw.add_input(DemoItems.copper_ingot, 1)
    copper_screw.add_output(DemoItems.screw, 4)
    
    iron_plate = Recipe('Iron Plate', constructor, False)
    iron_plate.add_input(DemoItems.iron_ingot, 3)
    iron_plate.add_output(DemoItems.iron_plate, 2)
    
    reinforced_iron_plate = Recipe('Reinforced Iron Plate', constructor, False)
    reinforced_iron_plate.add_input(DemoItems.iron_plate, 3)
    reinforced_iron_plate.add_input(DemoItems.screw, 8)
    reinforced_iron_plate.add_output(DemoItems.reinforced_iron_plate, 1)
    
    copper_wire = Recipe('Copper Wire', constructor, False)
    copper_wire.add_input(DemoItems.copper_ingot, 2)
    copper_wire.add_output(DemoItems.copper_wire, 10)
    
    @classmethod
    def get_demo_recipes(cls):
        return [cls.iron_screw, cls.copper_screw, cls.iron_plate, cls.reinforced_iron_plate, cls.copper_wire]

class DemoProblems:
    def demo_example(method: ObjMethods) -> ProductionProblem:
        """ Methods: Any options in ObjMethods """
        # Load recipes from demo data
        recipes = DemoRecipes.get_demo_recipes()
        # Input materials: Raw materials and premature products
        inputs = {
            DemoItems.iron_ingot: 120,
            DemoItems.copper_ingot: 60
            
        }
        # Output materials with scores
        output_scores = {
            DemoItems.reinforced_iron_plate: 1000,
            DemoItems.copper_wire: 20
        }
        # Problem formation
        problem = ProductionProblem(recipes, inputs, output_scores, method)
        return problem
    
    def complex_example(method: ObjMethods) -> ProductionProblem:
        """ Methods: Any options in ObjMethods """
        # Load real recipes from data JSON file
        recipes = load_recipes()
        # Input materials: Raw materials and premature products
        inputs = {
            "Iron Ore": 500,
            "Copper Ore": 100,
            "Coal": 80,
        }
        # Output materials: Medium-sized products
        inputs = {Product(k, get_item_sink_pt(k)): v for k, v in inputs.items()}
        output_scores = {
            "Reinforced Iron Plate": 120,
            "Motor": 1520,
        }
        output_scores = {Product(k, get_item_sink_pt(k)): v for k, v in output_scores.items()}
        # Problem formation
        problem = ProductionProblem(recipes, inputs, output_scores, method)
        return problem

    def complex_example_2(method: ObjMethods) -> ProductionProblem:
        """ Methods: Any options in ObjMethods """
        # Load real recipes from data JSON file
        recipes = load_recipes()
        # Input materials: Raw materials and premature products
        inputs = {
            "Iron Ore": 1000,
            "Copper Ore": 800,
            "Coal": 700,
            "Limestone": 700,
        }
        inputs = {Product(k, get_item_sink_pt(k)): v for k, v in inputs.items()}
        # Output materials
        output_scores = {
            "Heavy Modular Frame": 10800,
            "Stator": 240
        }
        output_scores = {Product(k, get_item_sink_pt(k)): v for k, v in output_scores.items()}
        # Problem formation
        problem = ProductionProblem(recipes, inputs, output_scores, method)
        return problem

    def single_large_example(method: ObjMethods) -> ProductionProblem:
        """ Methods: Any options in ObjMethods """
        # Load real recipes from data JSON file
        recipes = load_recipes()
        # Input materials: Raw materials and premature products
        inputs = {
            "Iron Ore": 1000,
            "Copper Ore": 800,
            "Coal": 900,
            "Crude Oil": 500
        }
        inputs = {Product(k, get_item_sink_pt(k)): v for k, v in inputs.items()}
        # Output materials: Single big product (ultimate game mission items)
        output_scores = {
            "Modular Engine": 1000
        }
        output_scores = {Product(k, get_item_sink_pt(k)): v for k, v in output_scores.items()}
        # Problem formation
        problem = ProductionProblem(recipes, inputs, output_scores, method)
        return problem
    
    def example_5(method: ObjMethods) -> ProductionProblem:
        """ Medium example with around 5 major outputs and around 5 inputs """
        # Load real recipes from data JSON file
        recipes = load_recipes()
        # Input materials: Raw materials and premature products
        inputs = {
            "Iron Ore": 2000,
            "Copper Ore": 1000,
            "Coal": 1000,
            "Limestone": 500,
            "Wood": 180,
            "Water": 600,
            "Crude Oil": 100,
        }
        inputs = {Product(k, get_item_sink_pt(k)): v for k, v in inputs.items()}
        # Output materials: 5 Big products (target production items)
        output_scores = {
            "Smart Plating": 520,
            "Versatile Framework": 1176,
            "Automated Wiring": 1440,
            "Modular Engine": 9960,
            "Adaptive Control Unit": 76368,
        }
        output_scores = {Product(k, get_item_sink_pt(k)): v for k, v in output_scores.items()}
        # Problem formation
        problem = ProductionProblem(recipes, inputs, output_scores, method)
        return problem
    
    def example_12(method: ObjMethods) -> ProductionProblem:
        """ Large example with around 12 major outputs and around 12 inputs """
        # Load real recipes from data JSON file
        recipes = load_recipes()
        # Input materials: Raw materials and premature products (should be merely sufficient)
        inputs = {
            "Iron Ore": 9200,
            "Copper Ore": 3600,
            "Coal": 4200,
            "Limestone": 6900,
            "Wood": 1000,
            "Water": 1300,
            "Crude Oil": 1200,
            "Caterium Ore": 1500,
            "Sulfur": 1000,
            "Bauxite": 1200,
            "Nitrogen Gas": 1200,
            "Raw Quartz": 1300,
            "SAM": 1000,
            "Uranium": 200,
        }
        inputs = {Product(k, get_item_sink_pt(k)): v for k, v in inputs.items()}
        # Output materials: 12 Big products (ultimate game mission items)
        output_scores = {
            "Smart Plating": 520,
            "Versatile Framework": 1176,
            "Automated Wiring": 1440,
            "Modular Engine": 9960,
            "Adaptive Control Unit": 76368,
            "Magnetic Field Generator": 11000,
            "Assembly Director System": 500176,
            "Thermal Propulsion Rocket": 728508,
            "Nuclear Pasta": 538976,
            "Biochemical Sculptor": 301778,
            "Ballistic Warp Drive": 2895334,
            "AI Expansion Server": 597652,
        }
        output_scores = {Product(k, get_item_sink_pt(k)): v for k, v in output_scores.items()}
        
        problem = ProductionProblem(recipes, inputs, output_scores, method)
        return problem