from typing import List, Dict, Tuple
from graphviz import Digraph

from src.common import round_float_to_2
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
    
    def add_src(self, vertex: 'Vertex', flow: FlowEdge):
        raise ValueError("Source vertex cannot have incoming edges")


class SinkVertex(Vertex):
    """ Represents a sink of products where output products are required """
    def __init__(self, product: Product, rate: float):
        super().__init__()
        self.receive_product = product
        self.receive_rate = rate
    
    def add_dst(self, vertex: 'Vertex', flow: FlowEdge):
        raise ValueError("Sink vertex cannot have outgoing edges")


class MachineVertex(Vertex):
    """ Represents a machine (vertex) on the graph where production with a recipe is taken place """
    def __init__(self, recipe: Recipe, scale: int):
        super().__init__()
        self.recipe = recipe
        self.scale = scale
    
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


class WasteVertex(Vertex):
    """ Represents a sink of products which is wasted """
    def __init__(self, product: Product, rate: float):
        super().__init__()
        self.wasted_product = product
        self.wasted_rate = rate
    
    def add_dst(self, vertex: 'Vertex', flow: FlowEdge):
        raise ValueError("Waste vertex cannot have outgoing edges")


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
            vertex = SourceVertex(product, round_float_to_2(rate))
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
            if not isinstance(src_vertex, SourceVertex):
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
                # Create a new edge and record it in involved instances
                edge = FlowEdge(src_product, round_float_to_2(demands[src_product]), round_float_to_2(demands[src_product])) # TODO: In current implementation, all waste go to WasteVertex, so num/den is no use for showing waste
                self.add_edge(edge)
                src_vertex.add_dst(vertex, edge)
                vertex.add_src(src_vertex, edge)
                # Update the unused rate
                unused_rate = round_float_to_2(unused_rate - demands[src_product])
                if unused_rate < 0:
                    raise ValueError(f"Unused rate cannot be negative: {src_product}, {unused_rate}. The program is wrong.")
            # Record wasted product with WasteVertex
            if unused_rate > 0:
                waste_vertex = WasteVertex(src_product, round_float_to_2(unused_rate))
                self.add_vertex(waste_vertex)
                # Create a new edge and record it in involved instances
                waste_edge = FlowEdge(src_product, round_float_to_2(unused_rate), round_float_to_2(unused_rate))
                self.add_edge(waste_edge)
                src_vertex.add_dst(waste_vertex, waste_edge)
                waste_vertex.add_src(src_vertex, waste_edge)
        
        # Precompute remaining demands for machine-to-machine flows to assign just-enough rate to edge, waste should go to waste node
        remaining_demands = {}
        for vertex in self.vertices:
            if isinstance(vertex, MachineVertex):
                remaining_demands[vertex] = vertex.in_demands().copy()
        
        # Add product output edges
        for machine_vertex in self.vertices:
            # Only start connection if this vertex is MachineVertex
            if not isinstance(machine_vertex, MachineVertex):
                continue
            # Record the unused rate of product
            available = machine_vertex.out_available()
            unused_products = available.copy()
            # Find the MachineVertex that receives the product
            for product in available:
                for vertex in self.vertices:
                    if not isinstance(vertex, MachineVertex) or product not in remaining_demands.get(vertex, {}):
                        continue
                    remaining_demand = remaining_demands[vertex][product]
                    if remaining_demand < 0:
                        raise ValueError(f"Remaining demand cannot be negative: {product}, {remaining_demand}. The program is wrong.")
                    if remaining_demand == 0:
                        continue
                    # Assign the edge with just-enough rate
                    assign = min(unused_products[product], remaining_demand)
                    edge = FlowEdge(product, round_float_to_2(assign), round_float_to_2(assign))
                    self.add_edge(edge)
                    machine_vertex.add_dst(vertex, edge)
                    vertex.add_src(machine_vertex, edge)
                    remaining_demands[vertex][product] -= assign
                    unused_products[product] -= assign
                    if unused_products[product] < 0:
                        raise ValueError(f"Unused rate cannot be negative: {product}, {unused_products[product]}. The program is wrong.")
            # If the product is output product, deliver to target output vertex
            for product, remain in unused_products.items():
                if product not in outputs or remain == 0:
                    continue
                # Locate the target output vertex
                for out_vertex in self.vertices:
                    if not isinstance(out_vertex, SinkVertex):
                        continue
                    if out_vertex.receive_product != product:
                        continue
                    # Create a new edge and record it in involved instances
                    edge = FlowEdge(product, round_float_to_2(remain), round_float_to_2(remain))
                    self.add_edge(edge)
                    machine_vertex.add_dst(out_vertex, edge)
                    out_vertex.add_src(machine_vertex, edge)
                    # Add the output value to the sink
                    out_vertex.receive_rate += remain
                    # Set unused to 0
                    unused_products[product] = round_float_to_2(0)
                    break
            # Record wasted product with WasteVertex
            for product, unused_rate in unused_products.items():
                if unused_rate > 0:
                    waste_vertex = WasteVertex(product, round_float_to_2(unused_rate))
                    self.add_vertex(waste_vertex)
                    # Create a new edge and record it in involved instances
                    waste_edge = FlowEdge(product, round_float_to_2(unused_rate), round_float_to_2(unused_rate))
                    self.add_edge(waste_edge)
                    machine_vertex.add_dst(waste_vertex, waste_edge)
                    waste_vertex.add_src(machine_vertex, waste_edge)
    
    
    def terminal_display(self):
        """ Display the graph """
        print("\n=== Production Graph ===")
        
        # Display vertices with details
        for i, vertex in enumerate(self.vertices):
            if isinstance(vertex, SourceVertex):
                print(f"[{i}] SOURCE: {vertex.provide_product} (rate: {vertex.provide_rate})")
            elif isinstance(vertex, SinkVertex):
                print(f"[{i}] SINK: {vertex.receive_product} (rate: {vertex.receive_rate})")
            elif isinstance(vertex, MachineVertex):
                print(f"[{i}] MACHINE: {vertex.recipe} (scale: {vertex.scale})")
            elif isinstance(vertex, WasteVertex):
                print(f"[{i}] WASTE: {vertex.wasted_product} (rate: {vertex.wasted_rate})")
            
        print("\n=== Connections ===")
        # Display connections
        for i, vertex in enumerate(self.vertices):
            if vertex.dst:
                for dst_vertex, edge in vertex.dst.items():
                    dst_idx = self.vertices.index(dst_vertex)
                    print(f"[{i}] -> [{dst_idx}]: {edge.product} ({edge.provide}/{edge.consume})")
    
    
    def visualize(self, save_path, title):
        """ Visualize the graph with graphviz """
        # Validate that the graph is created
        if not self.vertices:
            print("No graph created yet. Please call create() first.")
            return
        
        # Create a new directed graph
        dot = Digraph(comment=title)
        dot.attr(label=title, fontsize='24', labelloc='t', fontname='Helvetica-Bold')

        # Add vertices
        for i, vertex in enumerate(self.vertices):
            if isinstance(vertex, SourceVertex):
                dot.node(str(i), f"{vertex.provide_product} (Rate: {vertex.provide_rate})", color='blue')
            elif isinstance(vertex, SinkVertex):
                dot.node(str(i), f"{vertex.receive_product} (Rate: {vertex.receive_rate})", color='green')
            elif isinstance(vertex, MachineVertex):
                dot.node(str(i), f"{vertex.recipe} (Scale: {vertex.scale})")
            elif isinstance(vertex, WasteVertex):
                dot.node(str(i), f"{vertex.wasted_product} (Wasted: {vertex.wasted_rate})", color='red')

        # Add edges
        for i, vertex in enumerate(self.vertices):
            if not vertex.dst:
                continue
            for dst_vertex, edge in vertex.dst.items():
                dst_idx = self.vertices.index(dst_vertex)
                color = ''
                # (Highest priority) Color the edge red if the destination is waste
                if isinstance(dst_vertex, WasteVertex):
                    color = 'red'
                # Color the edge green if the destination is sink
                elif isinstance(dst_vertex, SinkVertex):
                    color = 'green'
                # Color the edge blue if the source is source
                elif isinstance(vertex, SourceVertex):
                    color = 'blue'
                # Add the edge with label
                dot.edge(str(i), str(dst_idx), label=f"{edge.product} ({edge.provide}/{edge.consume})", color=color, fontcolor=color)
                
        # Render the graph
        dot.render(save_path, format='png', cleanup=True)
        print(f"Graph visualization saved as {save_path}")
        # dot.view()