"""Check the smoke fixture's saved STEP; exits non-zero on any failed check."""
from math import isclose, pi
from pathlib import Path

from cadgen import read_scene, read_step
from cadgen.geometry import boundary_edges, topology_errors

STEP = Path(__file__).resolve().parents[1] / "STEP" / "plate.step"
EXPECTED_VOLUME_MM3 = 60 * 40 * 4 - 4 * pi * (4.5 / 2) ** 2 * 4

shape = read_step(STEP)
solids = shape.solids()
results = {
    "solid_count": (len(solids), len(solids) == 1),
    "volume_mm3": (solids[0].volume if solids else None,
                   bool(solids) and isclose(solids[0].volume, EXPECTED_VOLUME_MM3, rel_tol=1e-6)),
    "topology_errors": (len(topology_errors(shape)), not topology_errors(shape)),
    "free_edges": (sum(len(boundary_edges(s)) for s in shape.shells()),
                   all(not boundary_edges(s) for s in shape.shells())),
    "leaf_count": (len(list(read_scene(STEP).leaves())), len(list(read_scene(STEP).leaves())) == 1),
}
for name, (value, ok) in results.items():
    print(f"{'PASS' if ok else 'FAIL'} {name}: {value}")
raise SystemExit(0 if all(ok for _, ok in results.values()) else 1)
