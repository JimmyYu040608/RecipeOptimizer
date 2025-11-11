from typing import List, Dict, Tuple
from src.recipe import Product, Recipe


class FlowEdge:
    """ Represents a flow (edge) on the graph that is moving from one machine to another """
    def __init__(self, product: Product, provide: float, consume: float):
        self.product = product
        self.provide = provide # Numerator
        self.consume = consume # Denominator


# Abstract class
class Vertex():
    """ Represents a vertex on the graph """
    def __init__(self):
        self.src: Dict[Vertex, FlowEdge] = {}
        self.dst: Dict[Vertex, FlowEdge] = {}
    
    def add_src(self, vertex: 'Vertex', flow: FlowEdge):
        self.src[vertex] = flow
    
    def add_dst(self, vertex: 'Vertex', flow: FlowEdge):
        self.dst[vertex] = flow


class SourceVertex(Vertex):
    """ Represents a source of products where input products are provided """
    def __init__(self, product: Product, rate: float):
        super().__init__()
        self.provide_product = product
        self.provide_rate = rate
        self.wasted = 0 # How much input products are unused
    
    def add_src(self, vertex: 'Vertex', flow: FlowEdge):
        raise ValueError("Source vertex cannot have incoming edges")
    
    def add_dst(self, vertex: 'Vertex', flow: FlowEdge):
        return super().add_dst(vertex, flow)


class SinkVertex(Vertex):
    """ Represents a sink of products where output products are required """
    def __init__(self, product: Product, rate: float):
        super().__init__()
        self.receive_product = product
        self.receive_rate = rate
    
    def add_src(self, vertex: 'Vertex', flow: FlowEdge):
        return super().add_src(vertex, flow)
    
    def add_dst(self, vertex: 'Vertex', flow: FlowEdge):
        raise ValueError("Sink vertex cannot have outgoing edges")


class MachineVertex(Vertex):
    """ Represents a machine (vertex) on the graph where production with a recipe is taken place """
    def __init__(self, recipe: Recipe, scale: int):
        super().__init__()
        self.recipe = recipe
        # Enforce only int for scale
        if not scale.is_integer():
            raise ValueError("Scale must be an integer")
        self.scale = scale
        self.wasted_dict = {} # How much is wasted for each output product
    
    def add_src(self, vertex: 'Vertex', flow: FlowEdge):
        return super().add_src(vertex, flow)
    
    def add_dst(self, vertex: 'Vertex', flow: FlowEdge):
        return super().add_dst(vertex, flow)
    
    def in_demands(self) -> Dict[Product, float]:
        """ Calcute expected in-flows of this machine according to recipe and scale """
        # Scale up each product rate according to scale
        return {product: rate * self.scale for product, rate in self.recipe.inputs.items()}
    
    def out_available(self) -> Dict[Product, float]:
        """ Calcute expected out-flows of this machine according to recipe and scale """
        # Scale up each product rate according to scale
        return {product: rate * self.scale for product, rate in self.recipe.outputs.items()}
    
    def satisfied(self) -> bool:
        """ Check if the machine's in-flows and out-flows satisfy the recipe demands """
        # Check all demands
        for product, demand in self.in_demands().items():
            # Sum all flows of that product
            total_in_flow = sum(flow.provide for vertex, flow in self.src.items() if flow.product == product)
            if total_in_flow < demand:
                return False
        return True


class ProductionGraph:
    """ A graph for the whole production line """
    def __init__(self):
        self.vertices: List[MachineVertex] = []
        self.edges: List[FlowEdge] = []

    def add_vertex(self, vertex: MachineVertex):
        self.vertices.append(vertex)

    def add_edge(self, edge: FlowEdge):
        self.edges.append(edge)

    def create(self, recipe_count_pairs: List[Tuple[Recipe, int]], inputs: Dict[Product, float], outputs: Dict[Product, float]):
        """ Create the production graph from recipes and their scale """
        # Add source vertices
        for product, rate in inputs.items():
            vertex = SourceVertex(product, rate)
            self.add_vertex(vertex)
        # Add sink vertices
        for product, score in outputs.items():
            vertex = SinkVertex(product, 0)
            self.add_vertex(vertex)
        # Add machine vertices
        for recipe, scale in recipe_count_pairs:
            if scale == 0:
                continue
            vertex = MachineVertex(recipe, scale)
            self.add_vertex(vertex)

        # Add ingredient edges
        for src_vertex in self.vertices:
            # Only start connection if this vertex is SourceVertex
            if not isinstance(vertex, SourceVertex):
                continue
            # Record the unused rate of product
            src_product = src_vertex.provide_product
            unused_rate = src_vertex.provide_rate
            # Find the MachineVertex that receives the product
            for vertex in self.vertices:
                if not isinstance(vertex, MachineVertex):
                    continue
                # Check if this machine needs the product
                demands = vertex.in_demands()
                if src_product not in demands:
                    continue
                # Create a new edge
                edge = FlowEdge(src_product, src_vertex.provide_rate, demands[src_product]) # TODO: how to represent "total providing rate"? for now: putting total in numerator
                # Add the edge to the graph
                self.add_edge(edge)
                # Add the edge to the source vertex
                src_vertex.add_dst(vertex, edge)
                # Add the edge to the destination vertex
                vertex.add_src(src_vertex, edge)
                # Update the unused rate
                unused_rate -= demands[src_product]
                if unused_rate < 0:
                    raise ValueError("Unused rate cannot be negative. The optimization program is wrong.")
            # Record wasted product
            if unused_rate > 0:
                src_vertex.wasted += unused_rate
        
        # Add product output edges
        for machine_vertex in self.vertices:
            # Only start connection if this vertex is MachineVertex
            if not isinstance(machine_vertex, MachineVertex):
                continue
            # Record the unused rate of product
            available = machine_vertex.out_available()
            unused_products = available.copy()
            # Find the MachineVertex that receives the product
            for vertex in self.vertices:
                if not isinstance(vertex, MachineVertex):
                    continue
                # Locate each product which this machine needs
                demands = vertex.in_demands()
                for product, demand in demands.items():
                    if product not in available:
                        continue
                    # If the machines needs the product, create a new edge
                    edge = FlowEdge(product, available[product], demand) # TODO: how to represent "total providing rate"? for now: putting total in numerator
                    # Add the edge to the graph
                    self.add_edge(edge)
                    # Add the edge to the source vertex
                    machine_vertex.add_dst(vertex, edge)
                    # Add the edge to the destination vertex
                    vertex.add_src(machine_vertex, edge)
                    # Update the unused rate
                    unused_products[product] -= demand
                    if unused_products[product] < 0:
                        raise ValueError("Unused rate cannot be negative. The optimization program is wrong.")
            # If the product is output product, deliver to target output vertex
            for product, remain in unused_products.items():
                if product not in outputs:
                    continue
                # Locate the target output vertex
                for out_vertex in self.vertices:
                    if not isinstance(out_vertex, SinkVertex):
                        continue
                    if out_vertex.receive_product != product:
                        continue
                    # Create a new edge
                    edge = FlowEdge(product, remain, remain)
                    # Add the edge to the graph
                    self.add_edge(edge)
                    # Add the edge to the source vertex
                    machine_vertex.add_dst(out_vertex, edge)
                    # Add the edge to the destination vertex
                    out_vertex.add_src(machine_vertex, edge)
                    # Set unused to 0
                    unused_products[product] = 0
                    break
            # Record wasted product
            for product, unused_rate in unused_products.items():
                if unused_rate > 0:
                    machine_vertex.wasted_dict[product] = unused_rate
    
    
    def terminal_display(self):
        """ Display the graph """
        print("\n=== Production Graph ===")
        
        # Display vertices with details
        for i, vertex in enumerate(self.vertices):
            if isinstance(vertex, SourceVertex):
                print(f"[{i}] SOURCE: {vertex.provide_product} (rate: {vertex.provide_rate}, wasted: {vertex.wasted})")
            elif isinstance(vertex, SinkVertex):
                print(f"[{i}] SINK: {vertex.receive_product} (rate: {vertex.receive_rate})")
            elif isinstance(vertex, MachineVertex):
                print(f"[{i}] MACHINE: {vertex.recipe} (scale: {vertex.scale})")
        
        print("\n=== Connections ===")
        # Display connections
        for i, vertex in enumerate(self.vertices):
            if vertex.dst:
                for dst_vertex, edge in vertex.dst.items():
                    dst_idx = self.vertices.index(dst_vertex)
                    print(f"[{i}] -> [{dst_idx}]: {edge.product} ({edge.provide}/{edge.consume})")