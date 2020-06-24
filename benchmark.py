import os
import time
import argparse
import subprocess
from generate import generate as gen
from functools import wraps

RSBENCH = "{}\\build\\Release\\rs-bench.exe".format(
    os.path.dirname(os.path.realpath(__file__)))


def measure_time(desc=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if desc is not None:
                print(desc, "...")
            start = time.time()
            ret = f(*args, **kwargs)
            end = time.time()
            t = int((end - start) * 1000)
            if t >= 10000:
                print("{}: {}s".format(desc, t // 1000))
            else:
                print("{}: {}ms".format(desc, t))
            return ret
        return wrapper
    return decorator


@measure_time(desc="Generating test data")
def generate(struc_count, func_count, output):
    gen(struc_count, func_count, output)


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
    print("\n".join(stats))


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
                        default=None, choices=["generate", "build", "recover"])
    args = parser.parse_args()

    if args.only is not None:
        if args.only == "generate":
            generate(args.struc_count, args.func_count, args.output)
        elif args.only == "build":
            build()
        elif args.only == "recover":
            recover(args.restruc, args.recover)
        return

    generate(args.struc_count, args.func_count, args.output)
    build()
    recover(args.restruc, args.recover)


if __name__ == "__main__":
    main()
