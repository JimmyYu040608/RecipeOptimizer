from typing import List, Dict, Tuple, Optional
from graphviz import Digraph
from PIL import Image, ImageDraw, ImageFont

from src.utils import custom_round_float
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
        self.src: Dict['Vertex', List[FlowEdge]] = {}
        self.dst: Dict['Vertex', List[FlowEdge]] = {}
    
    def add_src(self, vertex: 'Vertex', flow: FlowEdge):
        if vertex not in self.src:
            self.src[vertex] = []
        self.src[vertex].append(flow)
    
    def add_dst(self, vertex: 'Vertex', flow: FlowEdge):
        if vertex not in self.dst:
            self.dst[vertex] = []
        self.dst[vertex].append(flow)


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
        d = {}
        for product, rate in self.recipe.outputs.items():
            if product in self.recipe.inputs:
                continue
            d[product] = rate * self.scale
        return d
    
    def satisfied(self) -> bool:
        """ Check if the machine's in-flows and out-flows satisfy the recipe demands """
        # Check all demands
        for product, demand in self.in_demands().items():
            # Sum all flows of that product
            total_in_flow = sum(flow.provide for vertex, flows in self.src.items() for flow in flows if flow.product == product)
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
        self.vertices: List[Vertex] = []
        self.edges: List[FlowEdge] = []

    def add_vertex(self, vertex: Vertex):
        self.vertices.append(vertex)

    def add_edge(self, edge: FlowEdge):
        self.edges.append(edge)


    def validate_machine_satisfaction(self):
        """ Validate that all machine vertices receive enough inflow for every demanded product """
        issues = []
        # Check all machine-demand pairs
        for vertex in self.vertices:
            if not isinstance(vertex, MachineVertex):
                continue
            for product, demand in vertex.in_demands().items():
                total_in = sum(flow.provide for src_vertex, flows in vertex.src.items() for flow in flows if flow.product == product)
                if total_in + 0.5 < demand:
                    issues.append(f"{vertex.recipe.name}: {product.name} received {custom_round_float(total_in)} / demand {custom_round_float(demand)}")
        return len(issues) == 0, issues
    
    
    def create(self, recipe_count_pairs: List[Tuple[Recipe, int]], inputs: Dict[Product, float], outputs: Dict[Product, float]):
        """ Create the production graph from recipes and their scale """
        # Create vertices
        source_vertices: List[SourceVertex] = []
        sink_vertices: List[SinkVertex] = []
        machine_vertices: List[MachineVertex] = []
        
        # Add source vertices
        for product, rate in inputs.items():
            vertex = SourceVertex(product, custom_round_float(rate))
            self.add_vertex(vertex)
            source_vertices.append(vertex)
              
        # Add sink vertices
        for product, score in outputs.items():
            vertex = SinkVertex(product, 0)
            self.add_vertex(vertex)
            sink_vertices.append(vertex)
            
        # Add machine vertices
        for recipe, scale in recipe_count_pairs:
            if scale == 0:
                continue
            vertex = MachineVertex(recipe, scale)
            self.add_vertex(vertex)
            machine_vertices.append(vertex)

        # Precompute fixed production rates from solver
        machine_inputs: Dict[MachineVertex, Dict[Product, float]] = {}
        machine_outputs: Dict[MachineVertex, Dict[Product, float]] = {}
        for vertex in machine_vertices:
            machine_inputs[vertex] = {p: rate * vertex.scale for p, rate in vertex.recipe.inputs.items()}
            machine_outputs[vertex] = {p: rate * vertex.scale for p, rate in vertex.recipe.outputs.items() if p not in vertex.recipe.inputs}

        # Collect every product that appears anywhere in this problem
        all_products: set = set()
        for src in source_vertices:
            all_products.add(src.provide_product)
        for machine in machine_vertices:
            all_products.update(machine_inputs[machine].keys())
            all_products.update(machine_outputs[machine].keys())

        # Global per-product flow allocation strategy:
        # For each product, track every supplier's remaining available amount and every consumer's remaining unmet demand
        # Prevents early suppliers from over-filling consumers that are also served by later suppliers
        for product in all_products:
            # Obtain all suppliers
            suppliers: List[list] = []
            for src in source_vertices:
                if src.provide_product == product:
                    suppliers.append([src, src.provide_rate])
            for machine in machine_vertices:
                if product in machine_outputs[machine]:
                    suppliers.append([machine, machine_outputs[machine][product]])

            if not suppliers:
                continue

            # Track remaining unmet demand per consumer
            consumer_need: Dict[MachineVertex, float] = {machine: machine_inputs[machine][product] for machine in machine_vertices if product in machine_inputs[machine]}

            # Assign products to consumers
            for supply_entry in suppliers:
                supply_vertex = supply_entry[0]
                for consumer in list(consumer_need.keys()):
                    if supply_entry[1] <= 1e-6:
                        break # This supplier is empty
                    need = consumer_need[consumer]
                    if need <= 1e-6:
                        continue # This consumer is already satisfied
                    assign = min(need, supply_entry[1])
                    edge = FlowEdge(product, custom_round_float(assign), custom_round_float(machine_inputs[consumer][product]))
                    self.add_edge(edge)
                    supply_vertex.add_dst(consumer, edge)
                    consumer.add_src(supply_vertex, edge)
                    supply_entry[1] -= assign
                    consumer_need[consumer] -= assign

            # Throw all remaining products to sinks (target products) or waste (otherwise)
            for supply_entry in suppliers:
                supply_vertex = supply_entry[0]
                remaining = supply_entry[1]
                if remaining <= 1e-6:
                    continue
                if product in outputs:
                    sink = next((v for v in sink_vertices if v.receive_product == product), None)
                    if sink is not None:
                        edge = FlowEdge(product, custom_round_float(remaining), custom_round_float(remaining))
                        self.add_edge(edge)
                        supply_vertex.add_dst(sink, edge)
                        sink.add_src(supply_vertex, edge)
                        sink.receive_rate += remaining
                        continue
                # Not a target output, or no matching sink found
                waste_vertex = WasteVertex(product, custom_round_float(remaining))
                self.add_vertex(waste_vertex)
                edge = FlowEdge(product, custom_round_float(remaining), custom_round_float(remaining))
                self.add_edge(edge)
                supply_vertex.add_dst(waste_vertex, edge)
                waste_vertex.add_src(supply_vertex, edge)
    
    
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
                for dst_vertex, edges in vertex.dst.items():
                    for edge in edges:
                        dst_idx = self.vertices.index(dst_vertex)
                        print(f"[{i}] -> [{dst_idx}]: {edge.product} ({edge.provide}/{edge.consume})")
    
    
    def _legend_rows(self, stats: Optional[Dict[str, object]] = None):
        """ Build legend rows to be overlaid on PNG """
        rows = []
        stats = stats or {}
        for key, value in stats.items():
            rows.append((str(key), str(value), (0, 0, 0), (0, 0, 0)))
        rows.append(("Blue", "Input flow", (0, 0, 255), (0, 0, 0)))
        rows.append(("Green", "Output flow", (0, 128, 0), (0, 0, 0)))
        rows.append(("Red", "Waste flow", (255, 0, 0), (0, 0, 0)))
        return rows


    def _split_into_band_rows(self, cell_texts, cell_widths, cell_pad_x, divider_gap, img_width):
        """
        Split cells into the minimum number of equal-ish rows so every row's
        natural content width fits within img_width.
        Returns a list of row slices: each slice is a list of (text, width) pairs.
        """
        def natural_row_w(indices):
            return (sum(cell_pad_x * 2 + cell_widths[i] for i in indices)
                    + divider_gap * (len(indices) - 1))

        n = len(cell_texts)
        # Try 1 row first, then 2, etc. until everything fits.
        for num_rows in range(1, n + 1):
            per_row = (n + num_rows - 1) // num_rows   # ceil division
            slices = [list(range(r * per_row, min((r + 1) * per_row, n)))
                      for r in range(num_rows)
                      if r * per_row < n]
            if all(natural_row_w(s) <= img_width for s in slices):
                return slices
        # Fallback: one cell per row
        return [[i] for i in range(n)]


    def _draw_legend_on_png(self, image_path: str, stats: Optional[Dict[str, object]] = None):
        """ Extend the PNG canvas downward with a flat band of legend cells, auto-wrapping rows if needed """

        rows = self._legend_rows(stats)
        if not rows:
            return

        with Image.open(image_path).convert("RGBA") as img:
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except OSError:
                font = ImageFont.load_default()

            cell_pad_x = 16
            cell_pad_y = 10
            divider_gap = 32

            tmp_draw = ImageDraw.Draw(img)

            cell_texts = []
            cell_colors = []
            for left_text, right_text, left_color, _ in rows:
                cell_texts.append(f"{left_text}: {right_text}")
                cell_colors.append(left_color)

            cell_widths = []
            row_h = 0
            for text in cell_texts:
                bb = tmp_draw.textbbox((0, 0), text, font=font)
                cell_widths.append(bb[2] - bb[0])
                row_h = max(row_h, bb[3] - bb[1])

            cell_h = row_h + cell_pad_y * 2

            # Decide how many band-rows are needed so content fits the image width
            band_rows = self._split_into_band_rows(cell_texts, cell_widths, cell_pad_x, divider_gap, img.width)
            num_band_rows = len(band_rows)
            strip_h = cell_h * num_band_rows + 2   # +2 for outer border

            # Create new canvas: original graph on top, legend strip below
            new_img = Image.new("RGBA", (img.width, img.height + strip_h), (255, 255, 255, 255))
            new_img.paste(img, (0, 0))
            draw = ImageDraw.Draw(new_img)

            strip_y0 = img.height
            strip_y1 = img.height + strip_h
            draw.rectangle((0, strip_y0, img.width - 1, strip_y1 - 1),
                            fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=2)

            for band_idx, indices in enumerate(band_rows):
                # Horizontal separator between band rows (not before the first)
                if band_idx > 0:
                    sep_y = strip_y0 + band_idx * cell_h
                    draw.line((0, sep_y, img.width, sep_y), fill=(0, 0, 0, 255), width=1)

                # Distribute extra space evenly across cells in this band row
                natural_w = (sum(cell_pad_x * 2 + cell_widths[i] for i in indices)
                             + divider_gap * (len(indices) - 1))
                extra = max(0, img.width - natural_w)
                per_cell_extra = extra // len(indices)

                y0 = strip_y0 + band_idx * cell_h
                current_x = 0
                for pos, i in enumerate(indices):
                    cell_w = cell_pad_x * 2 + cell_widths[i] + per_cell_extra
                    if pos < len(indices) - 1:
                        cell_w += divider_gap

                    draw.text((current_x + cell_pad_x, y0 + cell_pad_y),
                              cell_texts[i], font=font, fill=cell_colors[i])

                    if pos < len(indices) - 1:
                        div_x = current_x + cell_w
                        draw.line((div_x, y0, div_x, y0 + cell_h), fill=(0, 0, 0, 255), width=1)

                    current_x += cell_w

            new_img.save(image_path)


    def visualize(self, save_path, title, stats: Optional[Dict[str, object]] = None):
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
                dot.node(str(i), f"{vertex.provide_product} (Supplied: {vertex.provide_rate})", color='blue')
            elif isinstance(vertex, SinkVertex):
                dot.node(str(i), f"{vertex.receive_product} (Received: {vertex.receive_rate})", color='green')
            elif isinstance(vertex, MachineVertex):
                dot.node(str(i), f"{vertex.recipe} (Scale: {vertex.scale})", shape="box")
            elif isinstance(vertex, WasteVertex):
                dot.node(str(i), f"{vertex.wasted_product} (Wasted: {vertex.wasted_rate})", color='red')

        # Add edges
        for i, vertex in enumerate(self.vertices):
            if not vertex.dst:
                continue
            for dst_vertex, edges in vertex.dst.items():
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
                for edge in edges:
                    dot.edge(str(i), str(dst_idx), label=f"{edge.product} ({edge.provide}/{edge.consume})", color=color, fontcolor=color)

        # Render the graph
        rendered_path = dot.render(save_path, format='png', cleanup=True)
        # Render legend overlaying on the png
        self._draw_legend_on_png(rendered_path, stats)
        print(f"Graph visualization saved as {save_path}")
        # dot.view()