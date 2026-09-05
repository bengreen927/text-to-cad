"""Run: text-to-cad/bin/python3 grader-smoke/check.py
Only these controlled smoke models are inspected; no evaluated candidate is read.
"""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import build123d as b

HERE=Path(__file__).resolve().parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

g=load('grader',HERE.parent/'grade.py')
m=load('smoke',HERE/'model.step.py')
results=[]
with tempfile.TemporaryDirectory(prefix='grader-smoke-') as tmp:
    tmp=Path(tmp)
    for case,mutations in [('fixture',['','radius','blind','interference','label','origin']),('enclosure',['','usb','lip','seat'])]:
        for mutation in mutations:
            os.environ['GRADER_SMOKE_CASE']=case
            os.environ['GRADER_SMOKE_MUTATION']=mutation
            for variant in (['nominal','wide'] if not mutation else ['nominal']):
                s=m.gen_step(variant)
                b.export_step(s,tmp/'shape.step')
                (tmp/'meta.json').write_text(json.dumps({'labels':[x.label for x in s.children]}))
                report=g.Report()
                try: g.geometry(report,case,variant,tmp/'shape.step',tmp/'meta.json','smoke/')
                except Exception as e: report.check('evaluation error',lambda:(False,str(e)))
                failed=[x for x in report.expectations if not x['passed']]
                result={'case':case,'variant':variant,'mutation':mutation or 'known-pass','passed':not failed,'failures':failed}
                results.append(result)
                print(case,variant,mutation or 'known-pass',len(failed),'failures',flush=True)
                assert bool(failed)==bool(mutation),result
    # Ancestor and child transforms must each be applied once.
    leaf=box=b.Box(2,3,4); leaf.label='leaf'
    nested=b.Compound(children=[leaf]).moved(b.Pos(5,0,0)); nested.label='nested'
    root=b.Compound(children=[nested]).moved(b.Pos(7,0,0))
    b.export_step(root,tmp/'transform.step')
    imported=b.import_step(tmp/'transform.step')
    measured=g.bounds(next(iter(g.world_parts(imported).values())))
    direct=g.bounds(b.Compound(imported.solids()))
    assert all(abs(a-c)<1e-6 for a,c in zip(measured,direct)),(measured,direct)
    assert all(abs(a-c)<1e-6 for a,c in zip(measured,[11,-1.5,-2,13,1.5,2])),measured
    results.append({'test':'nested world transforms applied once','passed':True,'bbox':measured})
guard=g.Report()
guard.near('nonfinite bbox',[float('nan')],[0])
guard.zero('nonfinite boolean',lambda:float('inf'))
assert all(not x['passed'] for x in guard.expectations)
results.append({'test':'nonfinite values rejected','passed':True})
(HERE/'results.json').write_text(json.dumps(results,indent=2)+'\n')
print('All known-pass, mutation, and world-transform checks passed.')
