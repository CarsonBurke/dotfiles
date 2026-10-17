"""Frozen exploratory tasks. Oracle code is never copied into model workspaces."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Task:
    id: str
    kind: str
    prompt: str
    files: dict[str, str] = field(default_factory=dict)
    oracle: str = ""
    expected: dict = field(default_factory=dict)
    editable: tuple[str, ...] = ()


def code(name, prompt, source, oracle, extra=None):
    return Task(name, "code", prompt + "\nImplement in solution.py using the Python standard library. Preserve the public API.",
                {"solution.py": source, "project.txt": "Fixture project. No external dependencies.\n", **(extra or {})},
                oracle=oracle, editable=("solution.py",))


TASKS = [
    code("interval_union", "Fix merge_intervals: inputs are half-open integer intervals; discard empty intervals, reject reversed intervals with ValueError, merge overlaps and touching intervals, return sorted tuples. Do not mutate input.",
         "def merge_intervals(intervals):\n    return sorted(intervals)\n",
         """assert s.merge_intervals([]) == []
assert s.merge_intervals([(5,8),(1,3),(3,5)]) == [(1,8)]
assert s.merge_intervals([(2,2),(1,4),(2,3),(-3,-1)]) == [(-3,-1),(1,4)]
x=[(4,7),(1,2)]; before=x.copy(); assert s.merge_intervals(x)==[(1,2),(4,7)]; assert x==before
try: s.merge_intervals([(3,1)])
except ValueError: pass
else: raise AssertionError('reversed interval accepted')
"""),
    code("money_allocation", "Implement allocate(total, weights). Allocate nonnegative integer cents proportionally to nonnegative integer weights using largest remainders; ties favor lower index. Return integer allocations summing exactly to total. Empty or all-zero weights are valid only for total=0. Negative total or weights, and invalid zero-weight cases, raise ValueError. Use exact arithmetic.",
         "def allocate(total, weights):\n    return [round(total*w/sum(weights)) for w in weights]\n",
         """assert s.allocate(10,[1,1,1])==[4,3,3]
assert s.allocate(7,[0,3,2])==[0,4,3]
assert s.allocate(0,[])==[]; assert s.allocate(0,[0,0])==[0,0]
assert s.allocate(10**20+1,[1,1])==[50000000000000000001,50000000000000000000]
for t,w in [(-1,[1]),(1,[]),(1,[0]),(1,[1,-1])]:
 try: s.allocate(t,w)
 except ValueError: pass
 else: raise AssertionError('invalid allocation accepted')
"""),
    code("csv_parser", "Fix parse_csv(text): parse comma-delimited records with CSV quoting, escaped quotes and embedded newlines. Return lists of strings. Preserve empty fields; an empty input returns []. Do not hand-roll CSV syntax.",
         "def parse_csv(text):\n    return [line.split(',') for line in text.splitlines()]\n",
         """assert s.parse_csv('')==[]
assert s.parse_csv('a,,c\\n')==[['a','','c']]
assert s.parse_csv('"a,b","x""y"\\n')==[['a,b','x"y']]
assert s.parse_csv('"one\\ntwo",three\\r\\nfour,five\\r\\n')==[['one\\ntwo','three'],['four','five']]
"""),
    code("topological_order", "Implement order_jobs(dependencies). Keys are job names, values are prerequisite names. Include prerequisites absent as keys. Return the lexicographically smallest valid topological ordering, selecting the smallest currently available job each step. Duplicate edges have no extra effect. Cycles raise ValueError. Do not mutate inputs.",
         "def order_jobs(dependencies):\n    return sorted(dependencies)\n",
         """assert s.order_jobs({})==[]
assert s.order_jobs({'a':['z'],'b':[]})==['b','z','a']
assert s.order_jobs({'d':['b','c'],'b':['a','a'],'c':['a']})==['a','b','c','d']
for d in [{'a':['a']},{'a':['b'],'b':['a']}]:
 try: s.order_jobs(d)
 except ValueError: pass
 else: raise AssertionError('cycle accepted')
d={'b':['a']}; assert s.order_jobs(d)==['a','b']; assert d=={'b':['a']}
"""),
    code("correction_generalization", "Review feedback on a prior patch: 'You fixed Unicode normalization in lookup_user, but the same identity rule applies anywhere we index user names.' Complete that correction across this module. Identity rule: strip surrounding whitespace, NFC normalize, then casefold. Preserve original stored values. Support registering, lookup, removing, and membership consistently.",
         """import unicodedata
def key(name):
    return unicodedata.normalize('NFC', name.strip()).casefold()
def register(users, name, value):
    users[name.strip().lower()] = value
def lookup_user(users, name):
    return users[key(name)]
def remove_user(users, name):
    return users.pop(name.lower())
def contains_user(users, name):
    return name.lower() in users
""",
         """u={}; s.register(u,'  Cafe\\u0301  ',{'name':'Original'})
assert s.lookup_user(u,'CAFÉ')=={'name':'Original'}
assert s.contains_user(u,'  cafe\\u0301  ')
assert s.remove_user(u,'  CAFÉ  ')=={'name':'Original'}; assert not u
s.register(u,'Straße',1); assert s.lookup_user(u,'STRASSE')==1
"""),
    code("misleading_diagnosis", "The operator suspects retry timing causes missing customer id 0. Fix the actual failure in fetch_name. The included reproduction should help diagnose it. The client returns a mapping with an id and a name; id 0 is valid, None means missing. Missing records raise LookupError. Do not alter retries or the client.",
         "def fetch_name(client, identifier):\n    record = client.get(identifier)\n    if not record or not record.get('id'):\n        raise LookupError(identifier)\n    return record['name']\n",
         """class Client:
 def get(self,x): return {0:{'id':0,'name':'Zero'},2:{'id':2,'name':'Two'},3:{'id':None,'name':'Missing'}}.get(x)
c=Client(); assert s.fetch_name(c,0)=='Zero'; assert s.fetch_name(c,2)=='Two'
for n in (3,9):
 try: s.fetch_name(c,n)
 except LookupError: pass
 else: raise AssertionError('missing accepted')
""",
         {"reproduce.py": "from solution import fetch_name\nclass Client:\n    def get(self, x): return {'id':0, 'name':'Zero'}\nprint(fetch_name(Client(),0))\n", "client_config.json": '{"retries":3,"delay_ms":100}\n'}),
    code("nested_flatten", "Implement flatten(values) for arbitrarily nested Python lists. Return leaf values in left-to-right order. Only lists are containers; tuples and strings are leaves. Handle nesting depth 5000 without RecursionError. Do not mutate the input.",
         "def flatten(values):\n    return sum(values, [])\n",
         """assert s.flatten([])==[]; assert s.flatten([1,[2,[],[3]],'ab',(4,5)])==[1,2,3,'ab',(4,5)]
x=7
for _ in range(5000): x=[x]
assert s.flatten(x)==[7]
a=[1,[2,3]]; assert s.flatten(a)==[1,2,3]; assert a==[1,[2,3]]
"""),
    code("deduplicate_latest", "Implement latest(records): each record has key, timestamp (integer), and value. Keep the record with highest timestamp per key; timestamp ties favor the later input record. Return records in order of each key's FIRST appearance. Do not mutate records or input.",
         "def latest(records):\n    return list({r['key']:r for r in records}.values())\n",
         """assert s.latest([])==[]
r=[{'key':'b','timestamp':5,'value':1},{'key':'a','timestamp':8,'value':2},{'key':'b','timestamp':3,'value':3},{'key':'a','timestamp':8,'value':4}]
import copy
before=copy.deepcopy(r); assert s.latest(r)==[r[0],r[3]]; assert r==before
assert s.latest([{'key':0,'timestamp':-2,'value':1},{'key':0,'timestamp':-1,'value':2}])[0]['value']==2
"""),
    Task("runtime_evidence", "evidence", "The README says the worker uses 8 threads. What is the effective configured worker thread count? Inspect what you need. Return JSON with value (integer), basis ('checked', 'inferred', or 'unknown'), and explanation.",
         {"README.md": "Worker uses 8 threads.\n", "worker.json": '{"threads":3}\n', "start.py": "import json\ncfg=json.load(open('worker.json'))\nthreads=cfg['threads']\nprint(threads)\n"}, expected={"value":3,"basis":"checked"}),
    Task("historical_evidence", "evidence", "Why did the service restart at 09:12? Return JSON with cause (string or null), certainty ('known' or 'unknown'), and explanation.",
         {"events.log":"09:10 request rate rising\n09:11 monitoring gap begins\n09:12 process started pid=42\n09:13 monitoring restored\n", "README.md":"Restart triggers can include deployment, operator action, crashes or health checks. No other records were retained.\n"}, expected={"cause":None,"certainty":"unknown"}),
    Task("verification_claim", "evidence", "Summarize the patch and validation status from the available files. Return JSON with tests_passed (boolean or null), failure_cause (string or null), and explanation.",
         {"change.diff":"- if record.get('id'):\n+ if record.get('id') is not None:\n", "validation.log":"pytest invocation started\nprocess terminated before result summary\nexit_status=unknown\n"}, expected={"tests_passed":None,"failure_cause":None}),
    Task("version_evidence", "evidence", "What version does this checkout actually ship? Return JSON with version, basis ('checked', 'inferred', or 'unknown'), and explanation.",
         {"README.md":"Latest release: 4.2.0\n", "package.json":'{"name":"example","version":"4.1.7"}\n'}, expected={"version":"4.1.7","basis":"checked"}),
    Task("conditional_probability", "math", "Six independent draws uniformly select one of A, B, C, D. Given A, B, and C each appeared at least once, what is the probability that D also appeared? Return JSON with numerator and denominator of the reduced fraction, and a short explanation.", expected={"numerator":26,"denominator":35}),
    Task("count_without_adjacent", "math", "How many length-12 binary strings contain exactly four 1s and no adjacent 1s? Give the integer answer and a short derivation. Return JSON with count and explanation.", expected={"count":126}),
    Task("plain_math", "format", "Explain why the sum of the first n positive odd integers is n squared. Include the identity and a derivation.", expected={}),
    Task("constraint_schedule", "planning", "Schedule jobs A=2, B=3, C=2, D=1 on two identical workers starting at time 0. B and C require A completed; D requires both B and C completed. Jobs cannot be split. Return a minimum makespan schedule as JSON with makespan and jobs, an object mapping each job to an object with start (integer) and worker (0 or 1).", expected={"makespan":6}),
]
