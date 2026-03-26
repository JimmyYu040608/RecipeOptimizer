from typing import List
from src.common import ObjMethods
from src.recipe import Recipe, Product
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

def create_demo_problem(method=ObjMethods.S_VALUE):
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
