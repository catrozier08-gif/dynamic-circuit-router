"""
Dynamic Circuit Routing Optimizer - Quantum Software Suite
Minimizes signal delay (idle time) between mid-circuit measurements 
and their conditional target gates in 2D planar arrays.
"""

import numpy as np
import networkx as nx
import random
import matplotlib.pyplot as plt

# ============================================================================
# TOPOLOGY AND DELAY MODELING
# ============================================================================

class PlanarGridTopology:
    """Models a 2D planar grid of qubits (e.g., Heavy-Hex approximation)."""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.num_qubits = width * height
        self.grid = nx.grid_2d_graph(width, height)
        
        # Map (x,y) to integer indices
        self.coord_to_idx = {node: i for i, node in enumerate(self.grid.nodes())}
        self.idx_to_coord = {i: node for i, node in enumerate(self.grid.nodes())}

    def manhattan_distance(self, q1_idx, q2_idx):
        """Calculates routing distance between two qubits on the grid."""
        x1, y1 = self.idx_to_coord[q1_idx]
        x2, y2 = self.idx_to_coord[q2_idx]
        return abs(x1 - x2) + abs(y1 - y2)

    def calculate_signal_delay(self, distance):
        """
        Calculates the classical routing delay time based on distance.
        (Simplified model: base latency + distance penalty)
        Returns time in nanoseconds (ns).
        """
        base_latency_ns = 50.0   # Fast readout + control electronics base delay
        routing_penalty_ns = 15.0 # Delay per unit of physical distance traversed
        return base_latency_ns + (distance * routing_penalty_ns)


# ============================================================================
# CIRCUIT ANALYZER AND OPTIMIZER
# ============================================================================

class DynamicCircuitRouter:
    """Optimizes physical placement to minimize mid-circuit measurement delays."""
    
    def __init__(self, topology: PlanarGridTopology):
        self.topology = topology
        
    def _extract_dynamic_dependencies(self, circuit_instructions):
        """
        Extracts pairs of (Measured_Qubit, Conditional_Target_Qubit)
        In a real Qiskit circuit, we would parse c_if() conditions.
        Here we accept a list of dependencies for simulation.
        """
        return circuit_instructions
        
    def optimize_placement(self, dependencies, max_iterations=2000):
        """
        Uses Simulated Annealing to find a physical qubit layout that 
        minimizes the physical distance between dependent dynamic qubits.
        """
        # Start with a random naive placement
        current_placement = list(range(self.topology.num_qubits))
        random.shuffle(current_placement)
        
        def calculate_cost(placement):
            total_delay = 0
            for measure_q, target_q in dependencies:
                # Find where these logical qubits are physically placed
                phys_m = placement.index(measure_q)
                phys_t = placement.index(target_q)
                dist = self.topology.manhattan_distance(phys_m, phys_t)
                total_delay += self.topology.calculate_signal_delay(dist)
            return total_delay

        current_cost = calculate_cost(current_placement)
        best_placement = list(current_placement)
        best_cost = current_cost
        
        # Simulated Annealing
        temp = 100.0
        cooling_rate = 0.99
        
        print("   [Optimizer] Running Simulated Annealing for Dynamic Routing...")
        for i in range(max_iterations):
            # Propose a swap
            idx1, idx2 = random.sample(range(self.topology.num_qubits), 2)
            new_placement = list(current_placement)
            new_placement[idx1], new_placement[idx2] = new_placement[idx2], new_placement[idx1]
            
            new_cost = calculate_cost(new_placement)
            
            # Accept if better, or probabilistically if worse (to escape local minima)
            if new_cost < current_cost or random.random() < np.exp((current_cost - new_cost) / temp):
                current_placement = new_placement
                current_cost = new_cost
                
                if current_cost < best_cost:
                    best_cost = current_cost
                    best_placement = list(current_placement)
                    
            temp *= cooling_rate
            
        return best_placement, best_cost

# ============================================================================
# SIMULATION AND VISUALIZATION
# ============================================================================

def generate_random_dynamic_circuit(num_qubits, num_measurements):
    """Generates a mock list of (Measured_Qubit, Target_Qubit) dependencies."""
    dependencies = []
    for _ in range(num_measurements):
        m, t = random.sample(range(num_qubits), 2)
        dependencies.append((m, t))
    return dependencies

def run_dynamic_routing_test():
    print("============================================================")
    print("Dynamic Circuit Routing Optimizer")
    print("============================================================\n")
    
    # 10x10 grid = 100 Qubits
    width, height = 10, 10
    num_qubits = width * height
    topology = PlanarGridTopology(width, height)
    
    # 30 mid-circuit measurement triggers
    dependencies = generate_random_dynamic_circuit(num_qubits, 30)
    
    print(f"1. Simulating Dynamic Circuit on {width}x{height} Planar Array...")
    print(f"   Mid-Circuit Measurement triggers: {len(dependencies)}")
    
    # Calculate Naive placement cost
    naive_placement = list(range(num_qubits))
    router = DynamicCircuitRouter(topology)
    
    # We must calculate naive cost manually here for comparison
    naive_delay_total = 0
    for m, t in dependencies:
        dist = topology.manhattan_distance(naive_placement.index(m), naive_placement.index(t))
        naive_delay_total += topology.calculate_signal_delay(dist)
        
    print(f"\n2. BEFORE Optimization (Naive Layout):")
    print(f"   - Total routing delay penalty: {naive_delay_total:.1f} ns")
    print(f"   - Average delay per measurement: {naive_delay_total/len(dependencies):.1f} ns")
    
    # Optimize
    optimized_placement, optimized_delay_total = router.optimize_placement(dependencies)
    
    print(f"\n3. AFTER Optimization:")
    print(f"   - Total routing delay penalty: {optimized_delay_total:.1f} ns")
    print(f"   - Average delay per measurement: {optimized_delay_total/len(dependencies):.1f} ns")
    
    reduction = ((naive_delay_total - optimized_delay_total) / naive_delay_total) * 100
    
    print(f"\n4. Results:")
    print(f"   - Idle-time / Delay Reduction: {reduction:.1f}%")
    print(f"   [!] By minimizing the Manhattan distance between classical condition paths,")
    print(f"       qubit decoherence during mid-circuit measurements is massively reduced.\n")

if __name__ == "__main__":
    # Fix seed for reproducible output
    random.seed(42)
    np.random.seed(42)
    run_dynamic_routing_test()
