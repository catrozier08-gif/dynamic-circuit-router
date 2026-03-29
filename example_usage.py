from dynamic_placement_optimizer import (
    PlanarGridTopology,
    DynamicCircuitRouter,
    generate_clustered_dynamic_dependencies,
)

topology = PlanarGridTopology(width=10, height=10)
router = DynamicCircuitRouter(topology)

dependencies = generate_clustered_dynamic_dependencies(
    num_qubits=topology.num_qubits,
    num_clusters=4,
    num_measurements=30,
    seed=42,
)

naive_mapping = {q: q for q in range(topology.num_qubits)}
naive_delay = router.calculate_total_delay(dependencies, naive_mapping)

best_mapping, best_delay = router.optimize_placement(dependencies)

reduction_pct = ((naive_delay - best_delay) / naive_delay) * 100 if naive_delay > 0 else 0.0

print("============================================================")
print("Dynamic Circuit Delay-Aware Placement Optimizer")
print("============================================================")
print(f"Naive modeled delay:      {naive_delay:.1f} ns")
print(f"Optimized modeled delay:  {best_delay:.1f} ns")
print(f"Delay reduction:          {reduction_pct:.1f}%")
