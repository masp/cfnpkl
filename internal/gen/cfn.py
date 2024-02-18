from dataclasses import dataclass
from typing import Any, NotRequired, Self, TypedDict
from gen import pkl

# We go through all definitions and make an index of all the schemas. We define a class
# for each one. Then we go through properties and convert those to properties on the Props class.

class Schema(TypedDict):
    type: str
    properties: NotRequired[dict[str, Self]]
    description: NotRequired[str]
    items: NotRequired[Self]

@dataclass
class Context:
    root: dict # to lookup JSON pointers
    definitions: dict[str, pkl.Class]

    def lookup(self, ref: str) -> Schema:
        parts = ref.split("/")
        if parts[0] != "#" or parts[1] != "definitions":
            raise ValueError("unsupported reference: " + ref)
        schema = self.root
        for part in parts[1:]:
            schema = schema[part]
        
        if not isinstance(schema, dict):
            raise ValueError("unsupported reference to: " + ref)
        return Schema(schema) # type: ignore

def parse_definition(ctx: Context, name: str, schema: Schema) -> pkl.Class:
    """
    parse_definition takes a name like #/definitions/MyType and its schema and returns a class.
    It automatically resolves references to other definitions and adds them.
    """
    if name in ctx.definitions:
        return ctx.definitions[name]
        # raise ValueError("cycle found: " + name)
    cls = pkl.Class(name=name)
    ctx.definitions[name] = cls # prevent 
    cls.description = schema.get("description", "")
    cls.properties = [parse_property(ctx, k, v) for k, v in schema.get("properties", {}).items()]
    for prop in cls.properties:
        if prop.name in schema.get("required", []):
            prop.required = True
    return cls

def parse_property(ctx: Context, name: str, schema: Schema) -> pkl.Property:
    prop = pkl.Property(name=name, type=parse_type(ctx, name, schema), description=schema.get("description", ""))
    return prop

def parse_type(ctx: Context, name: str, schema: Schema) -> pkl.TypeConstr:
    ref = schema.get("$ref")
    if ref is not None:
        if not ref.startswith("#/definitions/"):
            raise ValueError("unsupported reference: " + ref)
        if ref in ctx.definitions:
            return pkl.TypeConstr(ctx.definitions[ref])
        return parse_type(ctx, ref, ctx.lookup(ref))
    
    one_of = schema.get("oneOf")
    if one_of is not None:
        options = []
        for i, sch in enumerate(one_of):
            options.append(parse_type(ctx, name+"/"+ name + str(i), sch))
        return pkl.TypeConstr(pkl.Union(options))

    typeField = schema.get("type", "object")
    if isinstance(typeField, list):
        if len(typeField) == 1:
            typeField = typeField[0]
        else:
            return pkl.TypeConstr(pkl.Union([parse_type(ctx, name, {"type": t}) for t in typeField]))
    match typeField:
        case "object":
            if "properties" in schema:
                return pkl.TypeConstr(parse_definition(ctx, name, schema))
            else:
                return pkl.TypeConstr(pkl.MAPPING)
        case "string":
            if "enum" in schema:
                type = pkl.TypeConstr(pkl.Enum(schema["enum"]))
            else:
                type = pkl.TypeConstr(pkl.STRING)
            if "maxLength" in schema:
                type.add_constranint(f"length <= {schema["maxLength"]}")
            if "minLength" in schema:
                type.add_constranint(f"length >= {schema["minLength"]}")
            if "pattern" in schema:
                type.add_constranint(f'matches(Regex(#"{schema["pattern"]}"#))')
            return type
        case "number":
            return pkl.TypeConstr(pkl.FLOAT)
        case "integer":
            return pkl.TypeConstr(pkl.INT)
        case "array":
            items = schema.get("items", {"type": "object"})
            return pkl.TypeConstr(pkl.ListingType(parse_type(ctx, name, items)))
        case "boolean":
            return pkl.TypeConstr(pkl.BOOL)
        case _:
            raise ValueError("unsupported JSON schema type: " + str(schema.get("type", "")))
