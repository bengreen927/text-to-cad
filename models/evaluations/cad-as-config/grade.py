#!/usr/bin/env python3
"""Independent STEP geometry grader. No candidate-reported measurements are trusted.
Usage: python3 grade.py {fixture,enclosure} OUTPUT_DIR
Grading is saved at OUTPUT_DIR.parent/grading.json. Worker code is not a sandbox.
"""
import argparse
import importlib.util
import json
import math
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import time

PYTHON = sys.executable
SOURCE = Path(__file__).parent / 'inputs/pcb.step'
TOL = 0.015
VTOL = 0.025


def worker(model, destination, variants):
    import build123d as b
    sys.path.insert(0, str(model.parent))
    os.chdir(model.parent)
    spec = importlib.util.spec_from_file_location('candidate_model', model)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for i, variant in enumerate(variants):
        shape = module.gen_step() if variant == 'nominal' else module.gen_step(variant='wide')
        # Original labels checked before STEP sanitizes punctuation.
        metadata = {'labels': [x.label for x in shape.children]}
        (destination / f'{i}.json').write_text(json.dumps(metadata))
        if not b.export_step(shape, destination / f'{i}.step'):
            raise RuntimeError('STEP export failed')


def volume(shape):
    if shape is None:
        return 0.0
    solids = shape.solids() if hasattr(shape, 'solids') else [s for x in shape for s in x.solids()]
    values = [float(s.volume) for s in solids]
    if not all(math.isfinite(x) and x >= -1e-8 for x in values):
        raise ValueError('nonfinite or negative volume')
    return sum(values)


def as_shape(shape):
    import build123d as b
    if shape is None:
        return b.Compound([])
    return shape if hasattr(shape, "wrapped") else b.Compound(list(shape))


def bounds(shape):
    q = as_shape(shape).bounding_box()
    values = [*q.min, *q.max]
    if not all(math.isfinite(x) for x in values):
        raise ValueError('nonfinite bounding box')
    return values


def world_parts(root):
    """Walk leaves, composing each ancestor location once; never move aggregate solids."""
    import build123d as b
    def leaves(node, parent):
        loc = parent * node.location
        if node.children:
            return [s for child in node.children for s in leaves(child, loc)]
        local = node.moved(node.location.inverse())
        return list(local.moved(loc).solids())
    return {child.label: b.Compound(leaves(child, root.location)) for child in root.children}


def difference(a, b):
    return volume(a.cut(b)) + volume(b.cut(a))


def intersection(a, b):
    # Solid pairs are already in world coordinates. No compound relocation here.
    return sum(volume(x.intersect(y)) for x in a.solids() for y in b.solids())


class Report:
    def __init__(self):
        self.expectations = []
        self.metrics = {}
    def check(self, name, fn):
        try:
            passed, evidence = fn()
            self.expectations.append({'text': name, 'passed': bool(passed), 'evidence': str(evidence)})
        except Exception as exc:
            self.expectations.append({'text': name, 'passed': False, 'evidence': f'{type(exc).__name__}: {exc}'})
    def near(self, name, measured, expected, tolerance=TOL):
        self.check(name, lambda: (len(measured) == len(expected) and all(math.isfinite(a) and abs(a-b) <= tolerance for a,b in zip(measured, expected)), f'measured={measured}; expected={expected}; tolerance={tolerance}'))
    def zero(self, name, fn):
        self.check(name, lambda: self._zero(fn()))
    @staticmethod
    def _zero(value):
        return math.isfinite(value) and value <= VTOL, f'volume={value:.9g} mm^3; limit={VTOL}'


def geometry(report, case, variant, step, meta, prefix):
    import build123d as b
    def box(x,y,z,cx=0,cy=0,z0=0):
        return b.Pos(cx,cy,z0) * b.Box(x,y,z,align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN))
    def cylinder(radius,height,x=0,y=0,z=0):
        return b.Pos(x,y,z) * b.Cylinder(radius,height,align=(b.Align.CENTER,b.Align.CENTER,b.Align.MIN))
    def rounded(x,y,z,r):
        return b.extrude(b.RectangleRounded(x,y,r),amount=z)
    def near(name, actual, expected): report.near(prefix+name,actual,expected)
    def zero(name, fn): report.zero(prefix+name,fn)
    root = b.import_step(step)
    expected_labels = ['plate','insert'] if case == 'fixture' else ['base','lid','pcb']
    labels = json.loads(meta.read_text())['labels']
    # STEP can introduce an extra assembly instance for a located root.
    while len(root.children)==1 and root.children[0].children:
        child = root.children[0]
        root = child.moved(root.location)
    report.check(prefix+'exact top-level labels',lambda:(sorted(labels)==sorted(expected_labels) and sorted(x.label for x in root.children)==sorted(expected_labels),f'original={labels}; STEP={[x.label for x in root.children]}'))
    parts = world_parts(root)
    for name in expected_labels:
        def valid(name=name):
            solids = list(parts[name].solids())
            values = [float(s.volume) for s in solids]
            return len(solids)==(2 if name=='pcb' else 1) and all(s.is_valid and math.isfinite(v) and v>0 for s,v in zip(solids,values)), f'solids={len(solids)}; volumes={values}'
        report.check(prefix+name+' valid positive solids', valid)
    if any(x not in parts for x in expected_labels):
        raise ValueError('required part missing')
    for i, a in enumerate(expected_labels):
        for c in expected_labels[i+1:]: zero(a+'/'+c+' zero interference',lambda a=a,c=c:intersection(parts[a],parts[c]))
    wide = variant == 'wide'
    if case == 'fixture':
        x,y,hx,hy,d = (100,70,40,25,24) if wide else (80,60,30,20,20)
        plate,insert = parts['plate'],parts['insert']
        near('plate bbox and origin',bounds(plate),[-x/2,-y/2,0,x/2,y/2,8])
        ideal = rounded(x,y,8,4)
        for xx in [-hx,hx]:
            for yy in [-hy,hy]:
                hole = cylinder(2.25,8,xx,yy)
                ideal = ideal.cut(hole)
                zero(f'D4.5 through hole at {xx},{yy}',lambda hole=hole:intersection(plate,hole))
        bore = cylinder((d+.4)/2,8)
        ideal = ideal.cut(bore)
        zero('plate exact geometry: radius4, four holes, through bore',lambda:difference(plate,ideal))
        zero(f'D{d+.4} bore open through Z0..8',lambda:intersection(plate,bore))
        expected_insert = cylinder(d/2,8).fuse(cylinder((d+8)/2,3,z=8))
        zero('insert exact stem, flange and 0.2 radial clearance',lambda:difference(insert,expected_insert))
        near('insert bbox and origin',bounds(insert),[-(d+8)/2,-(d+8)/2,0,(d+8)/2,(d+8)/2,11])
    else:
        cx,cy = (70,48) if wide else (64,44)
        base,lid,pcb = (parts[n] for n in expected_labels)
        near('base bbox and bottom datum',bounds(base),[-(cx+4)/2,-(cy+4)/2,0,(cx+4)/2,(cy+4)/2,16])
        source = b.import_step(SOURCE)
        srcparts = world_parts(source)
        source_world = b.Compound([s for p in srcparts.values() for s in p.solids()]).moved(b.Pos(0,0,6.8))
        zero('exact imported board and connector preserved at seat Z6',lambda:difference(pcb,source_world))
        placed_node = next(c for c in root.children if c.label == 'pcb')
        report.check(prefix+'PCB exact nested labels',lambda:(sorted(c.label for c in placed_node.children)==['pcb_board','usb_c'],f'labels={[c.label for c in placed_node.children]}'))
        # Board axes come from ground-truth STEP, not generator metadata.
        axes = sorted({(round(f.axis_of_rotation.position.X,6),round(f.axis_of_rotation.position.Y,6)) for f in srcparts['pcb_board'].faces() if f.geom_type==b.GeomType.CYLINDER and abs(f.radius-1.6)<TOL})
        report.check(prefix+'four source mounting axes',lambda:(len(axes)==4,f'axes={axes}'))
        connector = srcparts['usb_c'].moved(b.Pos(0,0,6.8))
        bb = bounds(connector)
        ux,uz = (bb[0]+bb[3])/2,(bb[2]+bb[5])/2
        near('actual connector centre', [ux,uz],[10,9.2])
        usb = box(10,cy+8,4.5,ux,(cy+8)/2,uz-2.25)
        shell = rounded(cx+4,cy+4,16,3).cut(box(cx,cy,14,z0=2)).cut(usb)
        # The cavity corner radius is unspecified; allow square corners through
        # the R1 inset of the R3 exterior, without relaxing flat wall dimensions.
        max_shell = rounded(cx+4,cy+4,16,3).cut(b.Pos(0,0,2)*rounded(cx,cy,14,1)).cut(usb)
        # Standoff outside diameter is deliberately unspecified. Exempt only the
        # lower cavity, then require supports, holes and absence above the seat.
        for xx,yy in axes:
            shell = shell.cut(cylinder(1.25,6,xx,yy))
            max_shell = max_shell.cut(cylinder(1.25,6,xx,yy))
        lower = box(cx,cy,4,z0=2)
        supports = list(as_shape(base.cut(max_shell).intersect(lower)).solids())
        report.check(prefix+'four separate standoffs',lambda:(len(supports)==4,f'count={len(supports)}; bboxes={[bounds(s) for s in supports]}'))
        zero('wall2 floor2 depth14 radius3 and exact USB10x4.5 position',lambda:volume(shell.cut(lower).cut(base))+volume(base.cut(lower).cut(max_shell)))
        for xx,yy in axes:
            bore = cylinder(1.25,6,xx,yy)
            support = cylinder(1.6,4,xx,yy,2).cut(cylinder(1.25,4,xx,yy,2))
            zero(f'tap D2.5 depth6 coaxial {xx},{yy}',lambda bore=bore:intersection(base,bore))
            zero(f'standoff material to seat Z6 at {xx},{yy}',lambda support=support:volume(support.cut(base)))
            # Check cylindrical tap wall, preventing an oversized clearance hole.
            cylfaces = [(f.radius,f.axis_of_rotation.position.X,f.axis_of_rotation.position.Y,bounds(f)[2],bounds(f)[5]) for f in base.faces() if f.geom_type==b.GeomType.CYLINDER]
            report.check(prefix+f'tap cylindrical wall {xx},{yy}', lambda xx=xx,yy=yy:(any(abs(r-1.25)<TOL and abs(a-xx)<TOL and abs(c-yy)<TOL and z0<TOL and abs(z1-6)<TOL for r,a,c,z0,z1 in cylfaces),str(cylfaces)))
        near('lid bbox and assembled datum',bounds(lid),[-(cx+4)/2,-(cy+4)/2,13,(cx+4)/2,(cy+4)/2,18])
        plate = as_shape(lid.intersect(box(cx+10,cy+10,2,z0=16)))
        required_plate = b.Pos(0,0,16)*rounded(cx+4,cy+4,2,3)
        zero('lid 2mm plate covers entire rim',lambda:volume(required_plate.cut(plate)))
        lip = as_shape(lid.intersect(box(cx+10,cy+10,3,z0=13)))
        near('lip3 and 0.3 clearance on every positioned side',bounds(lip),[-cx/2+.3,-cy/2+.3,13,cx/2-.3,cy/2-.3,16])
        # Require full-depth perimeter, allowing unspecified inner lip thickness.
        perimeter = b.Compound([box(.05,cy-6.6,3,cx/2-.325,0,13), box(.05,cy-6.6,3,-cx/2+.325,0,13), box(cx-6.6,.05,3,0,cy/2-.325,13), box(cx-6.6,.05,3,0,-cy/2+.325,13)])
        zero('lip outer perimeter maintains clearance throughout depth',lambda:volume(perimeter.cut(lip)))
    report.metrics[prefix.rstrip('/')] = {name:{'volume_mm3':volume(p),'bbox_mm':bounds(p),'solid_count':len(p.solids())} for name,p in parts.items()}
    return parts


def saved_equivalence(saved, fresh):
    """Compare already-exported world geometry, including labels and solid counts."""
    import build123d as b
    def read(path):
        root = b.import_step(path)
        while len(root.children)==1 and root.children[0].children:
            root = root.children[0].moved(root.location)
        parts = world_parts(root)
        labels = sorted(c.label for c in root.children)
        solids = list(root.solids())
        if not solids or not all(s.is_valid and math.isfinite(s.volume) and s.volume>0 for s in solids):
            raise ValueError('saved/fresh STEP has invalid or nonpositive solids')
        return parts, labels
    actual, labels = read(saved)
    expected, expected_labels = read(fresh)
    if labels != expected_labels:
        return False, f'saved labels={labels}; fresh labels={expected_labels}'
    residuals = {name: difference(actual[name], expected[name]) for name in expected}
    counts = {name: [len(actual[name].solids()),len(expected[name].solids())] for name in expected}
    passed = all(math.isfinite(v) and v<=VTOL for v in residuals.values()) and all(a==b for a,b in counts.values())
    return passed, f'symmetric difference mm^3={residuals}; solid counts [saved,fresh]={counts}; limit={VTOL}'


def main():
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case', choices=['enclosure','fixture'])
    parser.add_argument('output_dir',type=Path)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    model = output/'model.step.py'
    report = Report()
    variants = ['nominal','wide','nominal']
    evaluated = []
    with tempfile.TemporaryDirectory(prefix='independent-grader-') as tmp:
        tmp = Path(tmp)
        saved = {}
        fresh = {}
        # Snapshot deliverables BEFORE candidate import/calls can overwrite them.
        for variant, filename in [('nominal','model.step'),('wide','wide.step')]:
            def capture(variant=variant, filename=filename):
                path = output/filename
                if not path.is_file():
                    return False, f'missing saved deliverable: {path}'
                snapshot = tmp/filename
                shutil.copyfile(path,snapshot)
                saved[variant] = snapshot
                return True, f'saved deliverable existed before execution; bytes={snapshot.stat().st_size}'
            report.check('saved/'+filename+'/exists',capture)
        def run(folder, calls):
            folder.mkdir()
            try:
                result = subprocess.run([PYTHON,str(Path(__file__).resolve()),'--worker',str(model),str(folder),*calls],capture_output=True,text=True,timeout=65)
                if result.returncode:
                    raise RuntimeError(f'worker exit {result.returncode}: {result.stderr[-2500:]}')
                report.check(folder.name+'/execution',lambda:(True,'worker completed'))
                return True
            except Exception as exc:
                report.check(folder.name+'/execution',lambda:(False,str(exc)))
                return False
        def evaluate(folder, index, variant, run_id, ready):
            result = None
            def evaluate_geometry():
                nonlocal result
                if not ready:
                    return False, 'not evaluated: worker did not complete'
                result = geometry(report,args.case,variant,folder/f'{index}.step',folder/f'{index}.json',run_id+'/')
                evaluated.append({'run':run_id,'variant':variant})
                return True, 'STEP imported and assertions evaluated'
            report.check(run_id+'/geometry evaluation',evaluate_geometry)
            return result
        for i,variant in enumerate(variants):
            folder = tmp/f'isolated-{i}-{variant}'
            ready = run(folder,[variant])
            if ready and variant not in fresh:
                fresh[variant] = folder/'0.step'
            evaluate(folder,0,variant,folder.name,ready)
        folder = tmp/'repeated'
        ready = run(folder,variants)
        snapshots = [evaluate(folder,i,variant,f'repeated-{i}-{variant}',ready) for i,variant in enumerate(variants)]
        names = ['plate','insert'] if args.case=='fixture' else ['base','lid','pcb']
        for name in names:
            def unchanged(name=name):
                if not snapshots[0] or not snapshots[2]:
                    raise ValueError('nominal comparison unavailable: geometry evaluation incomplete')
                return difference(snapshots[0][name],snapshots[2][name])
            report.zero('nominal-wide-nominal unchanged/'+name,unchanged)
        for variant, filename in [('nominal','model.step'),('wide','wide.step')]:
            def compare_saved(variant=variant):
                if variant not in saved:
                    return False, 'saved deliverable unavailable before execution'
                if variant not in fresh:
                    return False, 'fresh isolated export unavailable: worker did not complete'
                return saved_equivalence(saved[variant],fresh[variant])
            report.check('saved/'+filename+'/equivalent to fresh '+variant,compare_saved)
    passed = sum(e['passed'] for e in report.expectations)
    execution_complete = len(evaluated)==6
    observed_rate = passed/len(report.expectations) if report.expectations else 0
    runtime = round(time.monotonic()-started,3)
    summary = {'passed':passed,'failed':len(report.expectations)-passed,'total':len(report.expectations),
               'pass_rate':observed_rate if execution_complete else 0.0,
               'observed_check_pass_rate':observed_rate,'execution_complete':execution_complete,
               'variants_evaluated':sorted({r['variant'] for r in evaluated}),
               'runs_evaluated':len(evaluated),'runs_expected':6,'runtime_seconds':runtime}
    data={'expectations':report.expectations,'summary':summary,'metrics':report.metrics,
          'evaluated_runs':evaluated,'runtime_seconds':runtime}
    target=output.parent/'grading.json'
    target.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'grading':str(target),**summary}))
    return 0 if execution_complete and summary['failed']==0 else 1


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--worker':
        worker(Path(sys.argv[2]),Path(sys.argv[3]),sys.argv[4:])
    else:
        # Guarantee the requested CAD runtime even when invoked with system python3.
        if Path(sys.executable).resolve()!=Path(PYTHON).resolve():
            os.execv(PYTHON,[PYTHON,str(Path(__file__).resolve()),*sys.argv[1:]])
        raise SystemExit(main())
