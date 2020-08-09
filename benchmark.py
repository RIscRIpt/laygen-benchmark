import os
import sys
import time
import argparse
import subprocess
import generate as g
import re
from functools import wraps

RSBENCH = "{}\\build\\Release\\rs-bench.exe".format(
    os.path.dirname(os.path.realpath(__file__)))

def measure_time(desc=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if desc is not None:
                print(desc, "...", file=sys.stderr)
            start = time.time()
            ret = f(*args, **kwargs)
            end = time.time()
            t = int((end - start) * 1000)
            if desc is not None and t >= 10000:
                print("{}: {}s".format(desc, t // 1000), file=sys.stderr)
            elif desc is not None:
                print("{}: {}ms".format(desc, t), file=sys.stderr)
            return ret
        return wrapper
    return decorator


@measure_time(desc="Generating test data")
def generate(struc_count, func_count, output, gen_opt):
    return g.generate(struc_count, func_count, output, gen_opt)


@measure_time(desc="Building rs-bench")
def build():
    return subprocess.check_output(
        "make.bat", stderr=subprocess.STDOUT)


@measure_time(desc="Recovering structs")
def recover(restruc, output):
    recovered = subprocess.check_output(
        [restruc, RSBENCH], stderr=subprocess.STDOUT, universal_newlines=True)
    with open(output, "w") as f:
        f.write(recovered)
    stats = []
    for line in recovered.split("\n"):
        if not line.startswith("// "):
            break
        stats.append("> " + line[3:])
    # print("\n".join(stats))


def parse_recovered(recover_file):
    recovered = []
    with open(recover_file, "r") as f:
        recovered = f.readlines()
    strucs = dict()
    current_struct: g.Struc = None
    for line in recovered:
        if line.startswith("struct"):
            assert current_struct is None
            m = re.match(r".*rs_(?P<rs>[0-9a-f_]+).*", line)
            assert m
            struc_id = m.group("rs")
            if struc_id in strucs:
                current_struct = strucs[struc_id]
            else:
                current_struct = g.Struc(struc_id)
        elif line.startswith("};"):
            assert current_struct is not None
            strucs[current_struct.id] = current_struct
            current_struct = None
        elif current_struct is not None:
            if "_padding_" in line:
                continue
            line = line.strip()
            t = line[:line.index(" ")]
            name = line[line.index(" ") + 1 : line.index(";")]
            if "int" in t:
                signed = not t.startswith("u")
                m = re.match(r"u?int(?P<size>\d+)_t", t)
                assert m
                size = int(m.group("size"))
                current_struct.add_field(
                    g.Field(name, g.Type.Int if signed else g.Type.UInt, size // 8, None))
            elif t == "float":
                current_struct.add_field(g.Field(name, g.Type.Float, 4, None))
            elif t == "double":
                current_struct.add_field(g.Field(name, g.Type.Float, 8, None))
            elif "*" in t:
                assert t.startswith("rs_")
                struc_id = t[3:-1]
                if struc_id not in strucs:
                    strucs[struc_id] = g.Struc(struc_id)
                current_struct.add_field(
                    g.Field(name, g.Type.Pointer, 8, strucs[struc_id]))
    return strucs
        

@measure_time(desc="Evaluating")
def evaluate(recover_file, generated):
    recovered = parse_recovered(recover_file)
    recovered = set(struc.fingerprint for struc in recovered.values())
    generated = set(struc.fingerprint for struc in generated.values())
    return len(generated.intersection(recovered)) / len(generated), \
        (len(generated) - len(generated.intersection(recovered))) / len(generated)

def main():
    parser = argparse.ArgumentParser(
        "Measures quality and speed of recovery of restruc")
    parser.add_argument("-r", "--restruc", dest="restruc",
                        default="restruc.exe", help="Path to restruc.exe")
    parser.add_argument("-R", "--recover", dest="recover",
                        default="recovered.hxx", help="Output file for restruc.exe")
    parser.add_argument("-s", "--strucs", dest="struc_count",
                        type=int, default=10, help="Amount of strucs to generate")
    parser.add_argument("-f", "--funcs", dest="func_count", type=int,
                        default=100, help="Amount of functions to generate")
    parser.add_argument("-o", "--output", dest="output",
                        default="test.cxx", help="Generation output")
    parser.add_argument("-O", "--only", dest="only",
                        default=None, choices=["generate", "build", "recover", "evaluate"])
    parser.add_argument("--gen-opt", dest="gen_opt", nargs="+",
                        help="Generator options")
    args = parser.parse_args()

    if args.only is not None:
        if args.only == "generate":
            generate(args.struc_count, args.func_count,
                     args.all_strucs_per_func, args.output)
        elif args.only == "build":
            build()
        elif args.only == "recover":
            recover(args.restruc, args.recover)
        return

    generated = generate(args.struc_count, args.func_count,
                         args.output, args.gen_opt)
    build()
    recover(args.restruc, args.recover)
    recovered, garbage = evaluate(args.recover, generated)
    print("{},{}".format(recovered, garbage))


if __name__ == "__main__":
    main()
