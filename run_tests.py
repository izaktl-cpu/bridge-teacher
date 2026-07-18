import subprocess, sys, os, re

py = sys.executable
proj = r'D:\bridge-teacher1'

test_files = [
    'test_auction','test_comprehensive','test_deep','test_direct','test_double',
    'test_lessons','test_level34','test_logic','test_minor_rebid',
    'test_negative_double','test_overcall','test_overcall_response',
    'test_preempts','test_redouble','test_slam','test_stayman','test_transfer',
    'deep_analyzer',
]

results = []
for tf in test_files:
    script = os.path.join(proj, tf + '.py')
    # patch old path on-the-fly via env
    env = os.environ.copy()
    env['PYTHONPATH'] = proj
    r = subprocess.run(
        [py, script],
        cwd=proj, capture_output=True, text=True, encoding='utf-8', errors='replace',
        env=env
    )
    out = (r.stdout + r.stderr).strip()
    results.append((tf, r.returncode, out))

with open(os.path.join(proj, 'test_results.txt'), 'w', encoding='utf-8') as f:
    for tf, rc, out in results:
        status = '✓' if rc == 0 else '✗'
        # last meaningful line as summary
        lines = [l for l in out.splitlines() if l.strip()]
        summary = lines[-1] if lines else '(no output)'
        f.write(f'{status} {tf}: {summary}\n')
        if rc != 0:
            for l in out.splitlines():
                f.write('    ' + l + '\n')
            f.write('\n')
    pass_count = sum(1 for _,rc,_ in results if rc == 0)
    f.write(f'\n=== {pass_count}/{len(results)} קבצי בדיקה עברו ===\n')
