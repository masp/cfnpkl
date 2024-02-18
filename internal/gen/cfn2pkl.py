import glob
import json
import os
import sys
import traceback
from gen import pkl, cfn

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 Resource-gen.py <input> <output>")
        sys.exit(1)

    input = sys.argv[1]
    # Iterate through every file in directory
    if os.path.isdir(input):
        files = glob.glob(os.path.join(input, "*.json"))
    else:
        files = [input]
    ok = 0
    fail = 0
    for file in files:
        try:
            sys.stdout.write(f"{file:<84}...")
            sys.stdout.flush()
            gen_resource(file, sys.argv[2])
            sys.stdout.write(" OK\n")
            ok += 1
        except Exception:
            sys.stdout.write(f" FAIL\n")
            traceback.print_exc()
            if len(files) == 1:
                raise
            fail += 1

    print(f"{ok} OK, {fail} FAIL")

def gen_resource(input: str, outdir: str):
    with open(input) as f:
        data = json.load(f)

    parts = data["typeName"].split("::")
    parts[-1] += ".pkl"
    outputfile = os.path.join(outdir, *parts)
    os.makedirs(os.path.dirname(outputfile), exist_ok=True)
    output = open(outputfile, 'w+')

    file = pkl.File(name=".".join(parts), extends=[".../AWS/Resource.pkl"], description=data["description"])
    file.properties = [
        pkl.Property(name="Type", value=data["typeName"]),
        pkl.Property(name="Properties", type=pkl.TypeConstr("Props"))
    ]

    ctx = cfn.Context(root=data, definitions={})
    propClass = pkl.Class(name="Props")
    propClass.properties = []
    for name, prop_schema in data["properties"].items():
        prop = cfn.parse_property(ctx, name, prop_schema)
        propClass.properties.append(prop)

    file.classes = [propClass] + list(ctx.definitions.values())
    p = pkl.Printer(output)
    file.write(p)

if __name__ == "__main__":
    main()