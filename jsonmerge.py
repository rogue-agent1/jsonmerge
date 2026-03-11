#!/usr/bin/env python3
"""jsonmerge - Merge, patch, and combine JSON files.

Single-file, zero-dependency CLI.
"""

import sys
import argparse
import json
import copy


def deep_merge(base, override):
    result = copy.deepcopy(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = copy.deepcopy(v)
    return result


def cmd_merge(args):
    result = {}
    for f in args.files:
        with open(f) as fh:
            data = json.load(fh)
        if args.deep:
            result = deep_merge(result, data)
        else:
            result.update(data)
    print(json.dumps(result, indent=2))


def cmd_patch(args):
    """Apply JSON patch (add/replace/remove keys)."""
    with open(args.file) as f:
        data = json.load(f)
    for op in args.ops:
        if "=" in op:
            path, value = op.split("=", 1)
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                pass  # treat as string
            _set_path(data, path, value)
        elif op.startswith("-"):
            _del_path(data, op[1:])
    if args.output:
        with open(args.output, "w") as f:
            json.dump(data, f, indent=2)
        print(f"  Written to {args.output}")
    else:
        print(json.dumps(data, indent=2))


def _set_path(data, path, value):
    keys = path.split(".")
    obj = data
    for k in keys[:-1]:
        if k not in obj or not isinstance(obj[k], dict):
            obj[k] = {}
        obj = obj[k]
    obj[keys[-1]] = value


def _del_path(data, path):
    keys = path.split(".")
    obj = data
    for k in keys[:-1]:
        if k not in obj: return
        obj = obj[k]
    obj.pop(keys[-1], None)


def cmd_concat(args):
    """Concatenate JSON arrays."""
    result = []
    for f in args.files:
        with open(f) as fh:
            data = json.load(fh)
        if isinstance(data, list):
            result.extend(data)
        else:
            result.append(data)
    if args.unique:
        seen = set()
        deduped = []
        for item in result:
            key = json.dumps(item, sort_keys=True)
            if key not in seen:
                seen.add(key)
                deduped.append(item)
        result = deduped
    print(json.dumps(result, indent=2))


def main():
    p = argparse.ArgumentParser(prog="jsonmerge", description="Merge and patch JSON")
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("merge", aliases=["m"], help="Merge JSON files")
    s.add_argument("files", nargs="+"); s.add_argument("-d", "--deep", action="store_true")
    s = sub.add_parser("patch", aliases=["p"], help="Patch JSON")
    s.add_argument("file"); s.add_argument("ops", nargs="+", help="key=value or -key")
    s.add_argument("-o", "--output")
    s = sub.add_parser("concat", aliases=["c"], help="Concatenate arrays")
    s.add_argument("files", nargs="+"); s.add_argument("-u", "--unique", action="store_true")
    args = p.parse_args()
    if not args.cmd: p.print_help(); return 1
    cmds = {"merge": cmd_merge, "m": cmd_merge, "patch": cmd_patch, "p": cmd_patch,
            "concat": cmd_concat, "c": cmd_concat}
    return cmds[args.cmd](args) or 0


if __name__ == "__main__":
    sys.exit(main())
