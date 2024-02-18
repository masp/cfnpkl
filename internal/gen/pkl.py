from dataclasses import dataclass
from io import TextIOWrapper
import os
import textwrap
from io import StringIO

Value = str | int | float | bool | None

@dataclass
class Property:
    name: str
    type: "TypeConstr" = None # type: ignore
    value: Value = None
    required: bool = False
    description: str = ""

    def __str__(self):
        return f"{self.name} = {self.type}"

    def __repr__(self):
        return str(self)

    def write(self, output):
        if self.description:
            for line in textwrap.wrap(self.description):
                output.write(f"/// {line}")

        line = self.name
        if self.type:
            line += f": {self.type}"
            if not self.required:
                if isinstance(self.type.typ, Enum) or isinstance(self.type.typ, Union):
                    line += " | *Null"
                else:
                    line += "?"

        value = ""
        if self.value:
            if isinstance(self.value, str):
                value += f" = \"{self.value}\""
            else:
                value += f" = {self.value}"
        line += value
        output.write(line) 

@dataclass
class Class:
    name: str
    properties: list[Property] | None = None
    description: str = ""

    @property
    def basename(self):
        return os.path.basename(self.name)
    
    def __str__(self) -> str:
        return self.basename
    
    def __repr__(self) -> str:
        return self.name

    def write(self, output):
        if self.description:
            for line in textwrap.wrap(self.description):
                output.write(f"/// {line}")
        output.write(f"class {self.basename} " + "{")
        output.indent()
        for prop in self.properties or []:
            prop.write(output)
        output.dedent()
        output.write("}")

@dataclass
class File(Class):
    classes: list[Class] | None = None
    module_name: str | None = None
    extends: list[str] | None = None


    def write(self, output):
        if self.description:
            for line in textwrap.wrap(self.description):
                output.write(f"/// {line}")

        if self.module_name:
            output.write(f"module {self.module_name}")
        
        for e in self.extends or []:
            output.write(f"extends \"{e}\"")

        for prop in self.properties or []:
            prop.write(output)
    
        for cls in self.classes or []:
            cls.write(output)

@dataclass
class Enum:
    values: list[str]

    def write(self, output):
        output.write(" | ".join(self.values))

    def __str__(self):
        return " | ".join([f'"{v}"' for v in self.values])

    def __repr__(self):
        return str(self)
    
@dataclass
class Union:
    types: list['TypeConstr']

    def write(self, output):
        output.write(" | ".join([str(t) for t in self.types]))

    def __str__(self):
        return " | ".join([str(t) for t in self.types])

    def __repr__(self):
        return str(self)
    
@dataclass
class ListingType:
    element: 'TypeConstr'

    def __str__(self):
        return f"Listing<{self.element}>"

    def __repr__(self):
        return str(self)

    def write(self, output):
        output.write(f"Listing<{self.element}>")

@dataclass
class TypeConstr:
    typ: str | Class | Enum | ListingType | Union
    constraints: list[str] | None = None

    def add_constranint(self, constraint):
        if not self.constraints:
            self.constraints = []
        self.constraints.append(constraint)

    def write(self, output):
        line = StringIO()
        if isinstance(self.typ, str):
            line.write(self.typ)
        else:
            self.typ.write(line)

        if self.constraints:
            line.write(f"({" && ".join(self.constraints)})")
        output.write(line.getvalue())

    def __str__(self):
        line = str(self.typ)
        if self.constraints:
            line += f"({" && ".join(self.constraints)})"
        return line

INT = "Int"
FLOAT = "Float"
STRING = "String"
BOOL = "Boolean"
ANY = "Any"
MAPPING = "Mapping"

INDENT_SIZE = 4
@dataclass
class Printer:
    curr_indent = 0
    output: TextIOWrapper

    def write(self, s):
        self.output.write(" " * self.curr_indent * INDENT_SIZE + s + "\n")
    
    def indent(self):
        self.curr_indent += 1
    
    def dedent(self):
        self.curr_indent -= 1