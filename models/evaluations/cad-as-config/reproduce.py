"""Regenerate generic saved candidates and run the independent geometric grader."""
from pathlib import Path
import subprocess,sys,shutil,json
root=Path(__file__).parent.resolve()
subprocess.run([sys.executable,str(root/'make_inputs.py')],check=True)
results=[]
for source in sorted(root.glob('*/*/*/run-1/outputs/model.step.py')):
    out=source.parent
    p=subprocess.run([sys.executable,str(root/'grade.py'),'--worker',str(source),str(out),'nominal','wide'],capture_output=True,text=True,timeout=65)
    if p.returncode==0:
        shutil.copyfile(out/'0.step',out/'model.step'); shutil.copyfile(out/'1.step',out/'wide.step')
    q=subprocess.run([sys.executable,str(root/'grade.py'),source.relative_to(root).parts[1].split('-',2)[2],str(out)],capture_output=True,text=True,timeout=200)
    results.append({'candidate':str(source.relative_to(root)),'build_exit':p.returncode,'grade_exit':q.returncode,'stdout':q.stdout,'stderr':(p.stderr+q.stderr)[-3000:]})
    print(results[-1]['candidate'],q.returncode,flush=True)
    (root/'reproduced-results.json').write_text(json.dumps(results,indent=2))
raise SystemExit(0 if all(r['build_exit']==0 and r['grade_exit']==0 for r in results) else 1)
