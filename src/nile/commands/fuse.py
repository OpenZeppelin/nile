"""Fuse mutliple cairo contracts into one."""
import re
from collections import defaultdict


def fuse_command(contract_names, input_path, output_path, output_name):
    """Fuse mutliple cairo contracts into one."""
    final_contract = "%lang starknet\n"

    builtins = set()
    imports = defaultdict(set)
    storage = ""  # pack all storage variables together
    functions = ""  # pack all functions together

    for contract in contract_names:
        with open(f"{input_path}/{contract}.cairo", "r") as file:
            contract = file.readlines()

        # get builtins first
        cleaned_builtins = list(
            map(lambda x: x.rstrip("\n"), contract[1].split(" ")[1:])
        )
        builtins.update(cleaned_builtins)

        # move until we reach the imports
        index = 2
        while len(contract[index]) == 1:
            index += 1

        # get the imports
        while contract[index].startswith("from"):
            import_line = contract[index].split(" ")
            module = import_line[1]
            for function in import_line[3:]:
                cleaned_function = re.sub(
                    "[^a-zA-Z_0-9]+", "", function
                )  # remove commas
                imports[module].add(cleaned_function)
            index += 1

        # move until we encounter rest of the code
        while len(contract[index]) == 1:
            index += 1

        # get all functions and storage
        buffer, is_storage = "", False
        for line in contract[index:]:

            cleaned_line = re.sub("[^@_a-zA-Z]+", "", line)

            # pass if line is empty i.e. a whitespace
            if len(line) == 1:
                continue

            if cleaned_line == "@storage_var":
                is_storage = True

            if cleaned_line == "end":
                buffer += cleaned_line
                if is_storage:
                    storage += buffer + "\n\n"
                else:
                    functions += buffer + "\n\n"
                buffer, is_storage = "", False
                continue

            buffer += line

    # builtins have to be in a certain order
    final_builtins = "%builtins "
    for builtin in ["pedersen", "range_check", "ecdsa", "bitwise"]:
        if builtin in builtins:
            final_builtins += builtin + " "
    final_builtins += "\n"

    final_imports = ""
    for module in imports:
        final_imports += (
            "from " + module + " import " + ", ".join(list(imports[module])) + "\n"
        )
    final_contract += final_builtins + final_imports + "\n" + storage + functions

    with open(f"{output_path}/{output_name}.cairo", "w") as file:
        file.write(final_contract)
