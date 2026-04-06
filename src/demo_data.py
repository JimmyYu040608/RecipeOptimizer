from typing import List
from src.common import ObjMethods
from src.recipe import Recipe, Product, load_recipes, get_item_sink_pt
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
    iron_screw = Recipe('Iron Screw', 'Constructor', True)
    iron_screw.add_input(DemoItems.iron_ingot, 1)
    iron_screw.add_output(DemoItems.screw, 4)
    
    copper_screw = Recipe('Copper Screw', 'Constructor', True)
    copper_screw.add_input(DemoItems.copper_ingot, 1)
    copper_screw.add_output(DemoItems.screw, 4)
    
    iron_plate = Recipe('Iron Plate', 'Constructor', False)
    iron_plate.add_input(DemoItems.iron_ingot, 3)
    iron_plate.add_output(DemoItems.iron_plate, 2)
    
    reinforced_iron_plate = Recipe('Reinforced Iron Plate', 'Constructor', False)
    reinforced_iron_plate.add_input(DemoItems.iron_plate, 3)
    reinforced_iron_plate.add_input(DemoItems.screw, 8)
    reinforced_iron_plate.add_output(DemoItems.reinforced_iron_plate, 1)
    
    copper_wire = Recipe('Copper Wire', 'Constructor', False)
    copper_wire.add_input(DemoItems.copper_ingot, 2)
    copper_wire.add_output(DemoItems.copper_wire, 10)
    
    @classmethod
    def get_demo_recipes(cls):
        return [cls.iron_screw, cls.copper_screw, cls.iron_plate, cls.reinforced_iron_plate, cls.copper_wire]

class DemoProblems:
    def demo_example(method: ObjMethods) -> ProductionProblem:
        """ Methods: Any options in ObjMethods """
        
        recipes = DemoRecipes.get_demo_recipes()
        inputs = {
            DemoItems.iron_ingot: 120,
            DemoItems.copper_ingot: 60
            
        }
        output_scores = {
            DemoItems.reinforced_iron_plate: 1000,
            DemoItems.copper_wire: 20
        }
        problem = ProductionProblem(recipes, inputs, output_scores, method)
        return problem
    
    def complex_example(method: ObjMethods) -> ProductionProblem:
        """ Methods: Any options in ObjMethods """
        
        recipes = DemoRecipes.get_demo_recipes()
        inputs = {
            DemoItems.iron_ingot: 120,
            DemoItems.copper_ingot: 60
            
        }
        output_scores = {
            DemoItems.reinforced_iron_plate: 1000,
            DemoItems.copper_wire: 20
        }
        problem = ProductionProblem(recipes, inputs, output_scores, method)
        return problem
    
    def example_5(method: ObjMethods) -> ProductionProblem:
        """ Medium example with around 5 major outputs and around 5 inputs """
        
        # Load real recipes from data.json
        recipes = load_recipes()
        
        # 5 Input materials: Raw materials and premature products
        inputs = {
            "Iron Ore": 300,
            "Copper Ore": 50,
            "Coal": 250,
            "Limestone": 50,
            "Water": 600,
            "Sulfur": 150,
            "Wood": 180,
            "Crude Oil": 100,
        }
        inputs = {Product(k, get_item_sink_pt(k)): v for k, v in inputs.items()}
        
        # 5 Output materials: Big/completed products (target production items)
        output_scores = {
            "Smart Plating": 500,
            "Versatile Framework": 1176,
            "Automated Wiring": 1440,
            "Modular Engine": 9960,
            "Adaptive Control Unit": 86120,
        }
        output_scores = {Product(k, get_item_sink_pt(k)): v for k, v in output_scores.items()}
        
        problem = ProductionProblem(recipes, inputs, output_scores, method)
        return problem