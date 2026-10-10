#!/usr/bin/env python3
# Splices generated layers into a plate JSON file by id, leaving the rest of the file's formatting untouched.
"""Splice layers into a plate JSON file by id, text-level, so the rest of the
file keeps its formatting. Usage: splice.py <plate.json> <layers.json> [--before <id>]
A layer whose id exists is replaced in place; a new one goes before --before
(or at the end of the layers list)."""
import json, sys

def scal(x): return not isinstance(x,(list,dict))
def f(x,ind=0):
    p='  '*(ind+1); q='  '*ind
    if isinstance(x,dict):
        if not x: return '{}'
        return '{\n'+',\n'.join(p+json.dumps(k,ensure_ascii=False)+': '+f(v,ind+1) for k,v in x.items())+'\n'+q+'}'
    if isinstance(x,list):
        if all(scal(i) for i in x): return '['+', '.join(json.dumps(i,ensure_ascii=False) for i in x)+']'
        return '[\n'+',\n'.join(p+f(i,ind+1) for i in x)+'\n'+q+']'
    return json.dumps(x,ensure_ascii=False)
def dump(o): return f(o)+'\n'

path, src = sys.argv[1], sys.argv[2]
before = sys.argv[sys.argv.index('--before') + 1] if '--before' in sys.argv else None
s = open(path).read()
new = json.load(open(src))
def span(s, lid):
    key = f'    {{\n      "id": {json.dumps(lid, ensure_ascii=False)},\n'
    a = s.find(key)
    if a < 0: return None
    b = a
    while True:
        b = s.index('\n    }', b + 1)
        # the layer object closes at 4-space indent
        if s[b+1:b+6] == '    }': break
    return a, b + 6  # through '    }'
def text(layer):
    body = f(layer, 2)
    return '    ' + body
for layer in new:
    sp = span(s, layer['id'])
    if sp:
        s = s[:sp[0]] + text(layer) + s[sp[1]:]
    else:
        if before:
            bs = span(s, before)
            assert bs, before
            s = s[:bs[0]] + text(layer) + ',\n' + s[bs[0]:]
        else:
            raise SystemExit('no --before and layer not present: ' + layer['id'])
json.loads(s)
open(path, 'w').write(s)
print('ok', len(new))
