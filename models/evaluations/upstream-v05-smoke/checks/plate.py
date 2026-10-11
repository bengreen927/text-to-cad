"""Check the smoke fixture's saved STEP; exits non-zero on any failed check."""
from math import isclose, pi
from pathlib import Path

from cadgen import read_scene, read_step
from cadgen.geometry import boundary_edges, topology_errors

STEP = Path(__file__).resolve().parents[1] / "STEP" / "plate.step"
EXPECTED_VOLUME_MM3 = 60 * 40 * 4 - 4 * pi * (4.5 / 2) ** 2 * 4
EXPECTED_SIZE_MM = (60, 40, 4)
EXPECTED_HOLES = sorted((x, y) for x in (-24, 24) for y in (-14, 14))
HOLE_RADIUS_MM = 2.25
TOL_MM = 1e-3

shape = read_step(STEP)
solids = shape.solids()
shells = shape.shells()
issues = topology_errors(shape)
free_edges = sum(len(boundary_edges(shell)) for shell in shells)
leaves = list(read_scene(STEP).leaves())
bounds = shape.bounding_box()
size = bounds.size
hole_centers = sorted(  # one circle per hole on the top face
    (round(edge.arc_center.X, 3), round(edge.arc_center.Y, 3))
    for edge in shape.edges()
    if edge.geom_type.name == "CIRCLE"
    and isclose(edge.radius, HOLE_RADIUS_MM, abs_tol=TOL_MM)
    and isclose(edge.arc_center.Z, bounds.max.Z, abs_tol=TOL_MM)
)

results = {
    "solid_count": (len(solids), len(solids) == 1),
    "volume_mm3": (solids[0].volume if solids else None,
                   bool(solids) and isclose(solids[0].volume, EXPECTED_VOLUME_MM3, rel_tol=1e-6)),
    "size_mm": (tuple(round(v, 4) for v in size),
                all(isclose(a, b, abs_tol=TOL_MM) for a, b in zip(size, EXPECTED_SIZE_MM))),
    "hole_centers_top_face": (hole_centers,
                              len(hole_centers) == len(EXPECTED_HOLES)
                              and all(isclose(a, b, abs_tol=TOL_MM)
                                      for got, want in zip(hole_centers, EXPECTED_HOLES)
                                      for a, b in zip(got, want))),
    "topology_errors": (len(issues), not issues),
    "free_edges": (free_edges, bool(shells) and free_edges == 0),
    "leaf_count": (len(leaves), len(leaves) == 1),
}
for name, (value, ok) in results.items():
    print(f"{'PASS' if ok else 'FAIL'} {name}: {value}")
raise SystemExit(0 if all(ok for _, ok in results.values()) else 1)
