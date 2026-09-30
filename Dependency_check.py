"""
Reproducible dependency analysis for the library management system.

usage (from the repo root):
    python dependency_check.py library-management-system/src

prints:
    1. Package-level import edges (who imports whom, and from how many files)
    2. Cycles between packages
    3. Every UI file that calls the database directly(db.<function>), which is a violation of the architecture
"""
import ast
import os
import sys
import collections
import re

SRC = sys.argv[1] if len(sys.argv) > 1 else "src"
INTERNAL = {"database", "models", "ui", "app", "logger", "main"}

def package_of(rel_path: str) -> str:
    parts = rel_path.split(os.sep)
    return parts[0] if len(parts) > 1 else parts[0].replace(".py", "")

edges = collections.defaultdict(lambda: collections.defaultdict(set))

for dirpath, _, files in os.walk(SRC):
    if "__pycache__" in dirpath or ".venv" in dirpath:
        continue
    for name in files:
        if not name.endswith(".py"):
            continue
        full = os.path.join(dirpath, name)
        rel = os.path.relpath(full, SRC)
        src_pkg = package_of(rel)
        tree = ast.parse(open(full, encoding="utf-8").read())
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                mods = [node.module]
            for m in mods:
                top = m.split(".")[0]
                if top in INTERNAL and top != src_pkg:
                    edges[src_pkg][top].add(rel)

print("=" * 60)
print("1. PACKAGE-LEVEL DEPENDENCIES (A -> B means A imports B)")
print("=" * 60)
for s in sorted(edges):
    for t in sorted(edges[s]):
        files = sorted(edges[s][t])
        print(f"{s:10} -> {t:10} ({len(files)} file{'s' if len(files) != 1 else ''})")
        if len(files) <= 6:
            for f in files:
                print(f"{'':14} {f}")

print()
print("=" * 60)
print("2. CYCLES (mutual dependencies between packages)")
print("=" * 60)
found = False
for a in sorted(edges):
    for b in sorted(edges[a]):
        if a < b and a in edges.get(b, {}):
            found = True
            print(f"CYCLE: {a} <-> {b}")
            print(f" {a} -> {b} via: {sorted(edges[a][b])}")
            print(f" {b} -> {a} via: {sorted(edges[b][a])}")
if not found:
    print("none")

print()
print("=" * 60)
print("3. UI -> DATABASE DIRECT CALLS  (file:line  function)")
print("=" * 60)
pattern = re.compile(r"\bdb\.([A-Za-z_][A-Za-z_0-9\.]*)\(")
counts = collections.Counter()
for dirpath, _, files in os.walk(os.path.join(SRC, "ui")):
    if "__pycache__" in dirpath:
        continue
    for name in sorted(files):
        if not name.endswith(".py"):
            continue
        full = os.path.join(dirpath, name)
        for i, line in enumerate(open(full, encoding="utf-8"), 1):
            for m in pattern.finditer(line):
                rel = os.path.relpath(full, SRC)
                print(f"{rel}:{i:<4} db.{m.group(1)}")
                counts[rel] += 1
print()
print("Calls per file:")
for f, n in counts.most_common():
    print(f"  {n:3}  {f}")
print(f"  ---\n  {sum(counts.values()):3}  total direct UI->db calls")