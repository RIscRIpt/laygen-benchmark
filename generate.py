import argparse
import random
from collections import defaultdict
from enum import Enum

FIELD_COUNT_LIMIT = (1, 10)
ARG_COUNT_LIMIT = (1, 8)

NEXT_STRUC_ID = 1
STRUCS = dict()

NEXT_FUNC_ID = 1
FUNCS = dict()


class Type(Enum):
    Int = 0
    UInt = 1
    Float = 2
    Pointer = 3
    Struc = 4


class Struc:
    def __init__(self, id):
        self.id = id
        self.name = "rs_{}".format(id)
        self.fields = []
        self.field_by_type = defaultdict(list)

    def __str__(self):
        s = "struct {} {{\n".format(self.name)
        for field in self.fields:
            s += "    " + str(field) + "\n"
        s += "};\n"
        return s

    def add_field(self, field):
        self.fields.append(field)
        self.field_by_type[field.type].append(field)

    @staticmethod
    def get_by_id(id):
        return STRUCS[id]

    @staticmethod
    def generate_random():
        global NEXT_STRUC_ID
        struc_id = NEXT_STRUC_ID
        NEXT_STRUC_ID += 1
        struc = Struc(struc_id)
        STRUCS[struc.id] = struc
        field_count = random.randint(*FIELD_COUNT_LIMIT)
        for i in range(field_count):
            field_name = "_{}".format(i)
            if NEXT_STRUC_ID <= 2:
                field_type = random.choice(
                    [Type.Int, Type.UInt, Type.Float])
            else:
                field_type = random.choice(list(Type))
            field_size = Field.get_random_size(field_type)
            field_struc = None
            if field_type == Type.Struc or field_type == Type.Pointer:
                field_struc = Struc.get_by_id(
                    random.randrange(1, NEXT_STRUC_ID - 1))
            struc.add_field(
                Field(field_name, field_type, field_size, field_struc))
        return struc


class Field:
    def __init__(self, name, type_, size, struc):
        self.name = name
        self.type = type_
        self.size = size
        self.struc = struc

    @property
    def type_name(self):
        s = ""
        if self.type == Type.UInt:
            s += "u"
        if self.type == Type.Int or self.type == Type.UInt:
            s += "int" + str(self.size * 8) + "_t"
        elif self.type == Type.Float:
            s += "f" + str(self.size * 8) + "_t"
        elif self.type == Type.Pointer:
            if self.struc is None:
                s += "void*"
            else:
                s += self.struc.name + "*"
        elif self.type == Type.Struc:
            s += self.struc.name
        else:
            assert False
        return s

    def __str__(self):
        return "{} {};".format(self.type_name, self.name)

    @staticmethod
    def get_random_size(t: Type):
        if t == Type.Int or t == Type.UInt:
            return 2 ** random.randint(0, 3)  # 1, 2, 4, 8
        elif t == Type.Float:
            return 2 ** random.randint(2, 3)  # 4, 8
        elif t == Type.Pointer:
            return 8
        return 0


class Func:
    def __init__(self, id):
        self.id = id
        self.name = "f_{}".format(id)
        self.args = []
        self.type_dict = defaultdict(list)

    def add_argument(self, arg):
        self.args.append(arg)
        self.type_dict[arg.type_name].append(arg.name)
        if arg.struc is not None:
            self.add_types("{}->".format(arg.name), arg.struc.fields)

    def add_types(self, name, fields):
        for field in fields:
            self.type_dict[field.type_name].append(name + field.name)
            if field.struc is not None:
                if field.type == Type.Pointer:
                    self.add_types(
                        "{}{}->".format(name, field.name), field.struc.fields)
                else:
                    self.add_types("{}{}.".format(
                        name, field.name), field.struc.fields)

    @staticmethod
    def generate_random():
        global NEXT_FUNC_ID
        func_id = NEXT_FUNC_ID
        NEXT_FUNC_ID += 1
        func = Func(func_id)
        FUNCS[func_id] = func
        arg_count = random.randint(*ARG_COUNT_LIMIT)
        for i in range(arg_count):
            arg_name = "_{}".format(i)
            arg_type = random.choice(
                [Type.Int, Type.UInt, Type.Float, Type.Pointer])
            arg_size = Argument.get_random_size(arg_type)
            arg_struc = None
            if arg_type == Type.Pointer:
                arg_struc = random.choice(list(STRUCS.values()))
            func.add_argument(
                Argument(arg_name, arg_type, arg_size, arg_struc))
        return func

    @staticmethod
    def get_struc_usage(struc, name):
        s = ""
        for field in struc.fields:
            if field.type == Type.Pointer:
                s += Func.get_struc_usage(field.struc,
                                          "{}{}->".format(name, field.name))
            elif field.type == Type.Struc:
                s += Func.get_struc_usage(field.struc,
                                          "{}{}.".format(name, field.name))
            else:
                s += "    {0}{1} = use({0}{1});\n".format(name, field.name)
        return s

    @staticmethod
    def get_arg_usage(arg):
        if arg.type == Type.Pointer:
            return Func.get_struc_usage(arg.struc, "{}->".format(arg.name))
        else:
            return "    {0} = use({0});\n".format(arg.name)
    
    def get_signature(self):
        s = "void {}(".format(self.name)
        s += ", ".join(map(str, self.args))
        s += ")"
        return s
    
    def get_usages_by_funcs(self):
        s = ""
        for func in FUNCS:
            if func == self.id:
                continue
            func = FUNCS[func]
            s += "    {}(".format(func.name)
            args = []
            for arg in func.args:
                if self.type_dict[arg.type_name]:
                    args.append(random.choice(self.type_dict[arg.type_name]))
                elif arg.type == Type.Int or arg.type == Type.UInt:
                    args.append("0")
                elif arg.type == Type.Float:
                    if arg.size == 4:
                        args.append("0.0f")
                    else:
                        args.append("0.0")
                elif arg.type == Type.Pointer:
                    args.append("nullptr")
                elif arg.type == Type.Struc:
                    args.append("{}()".format(arg.struc.name))
            s += ", ".join(args)
            s += ");\n"
        return s

    def __str__(self):
        s = self.get_signature()
        s += " {\n"
        s += "".join(map(self.get_arg_usage, self.args))
        s += self.get_usages_by_funcs()
        s += "}\n"
        return s


class Argument:
    def __init__(self, name, type_, size, struc):
        self.name = name
        self.type = type_
        self.size = size
        self.struc = struc

    @staticmethod
    def get_random_size(t: Type):
        if t == Type.Int or t == Type.UInt:
            return 2 ** random.randint(0, 3)  # 1, 2, 4, 8
        elif t == Type.Float:
            return 2 ** random.randint(2, 3)  # 4, 8
        elif t == Type.Pointer:
            return 8
        return 0

    @property
    def type_name(self):
        s = ""
        if self.type == Type.UInt:
            s += "u"
        if self.type == Type.Int or self.type == Type.UInt:
            s += "int" + str(self.size * 8) + "_t"
        elif self.type == Type.Float:
            s += "f" + str(self.size * 8) + "_t"
        elif self.type == Type.Pointer:
            if self.struc is None:
                s += "void*"
            else:
                s += self.struc.name + "*"
        elif self.type == Type.Struc:
            s += self.struc.name
        else:
            assert False
        return s

    def __str__(self):
        return "{} {}".format(self.type_name, self.name)


class Main(Func):
    def __init__(self):
        super().__init__(0)

    def __str__(self):
        s = "int main() {\n"
        s += self.get_usages_by_funcs()
        s += "    return 0;\n}\n"
        return s


def generate(struc_count, func_count, output):
    for _ in range(struc_count):
        Struc.generate_random()
    for _ in range(func_count):
        Func.generate_random()
    with open(output, "w") as f:
        with open("preamble.cxx", "r") as preamble:
            f.write(preamble.read())
        f.write("\n")
        f.write("\n".join(map(str, STRUCS.values())))
        f.write("\n")
        for func in FUNCS:
            func = FUNCS[func]
            f.write("{};\n".format(func.get_signature()))
        f.write("\n")
        f.write("\n".join(map(str, FUNCS.values())))
        f.write("\n")
        f.write(str(Main()))


def main():
    parser = argparse.ArgumentParser("Test C++ file generator with random structs and their usages")
    parser.add_argument("-o", "--output", dest="output",
                        default="test.cxx", help="Generation output")
    parser.add_argument("-s", "--strucs", dest="struc_count", type=int,
                        default=10, help="Amount of strucs to generate")
    parser.add_argument("-f", "--funcs", dest="func_count", type=int,
                        default=100, help="Amount of functions to generate")
    args = parser.parse_args()
    generate(args.struc_count, args.func_count, args.output)


if __name__ == "__main__":
    main()
