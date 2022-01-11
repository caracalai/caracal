import copy
import typing

import numpy as np


class TypeBase:
    def __init__(self):
        pass

    def equal(self, other) -> bool:
        return self.contains(other) and other.contains(self)

    def contains(self, other) -> bool:
        raise Exception("Method is not implemented")

    def contains_value(self, value) -> bool:
        raise Exception("Method is not implemented")

    @property
    def is_composite(self) -> bool:
        return False

    @property
    def name(self) -> str:
        return "TypeBase"

    def intersect(self, other):
        if type(self) == type(other):
            return copy.deepcopy(other)
        assert not self.is_composite

        if type(self) == Object:
            return copy.deepcopy(other)
        if type(other) == Object:
            return copy.deepcopy(self)

        if other.is_composite:
            return other.intersect(self)
        return None

    def __str__(self):
        return self.name


class Object(TypeBase):
    def __init__(self):
        super().__init__()

    def contains(self, other) -> bool:
        if type(self) == Object:
            return True
        if type(self) is not Object and type(other) is not Object:
            if type(other) == type(self):
                return True
        raise Exception(f"{self.name}.contains({other.name}): Method is not implemented")

    @property
    def name(self) -> str:
        return "object"


class Void(Object):
    def __init__(self):
        super().__init__()

    def contains_value(self, value) -> bool:
        return False

    @property
    def name(self) -> str:
        return "void"


class Float(Object):
    def __init__(self):
        super().__init__()

    def contains_value(self, value) -> bool:
        return isinstance(value, (float, int))

    @property
    def name(self) -> str:
        return "float"


class Int(Object):
    def __init__(self):
        super().__init__()

    def contains_value(self, value) -> bool:
        return isinstance(value, int)

    @property
    def name(self) -> str:
        return "int"


class Boolean(Object):
    def __init__(self):
        super().__init__()

    def contains_value(self, value) -> bool:
        return isinstance(value, bool)

    @property
    def name(self) -> str:
        return "boolean"


class String(Object):
    def __init__(self):
        super().__init__()

    def contains_value(self, value) -> bool:
        return type(value) is str

    @property
    def name(self) -> str:
        return "string"


class Ndarray(Object):
    def __init__(self):
        super().__init__()

    def contains_value(self, value) -> bool:
        return isinstance(value, np.ndarray)

    @property
    def name(self) -> str:
        return "ndarray"


class List(Object):
    def __init__(self, basic_type: Object):
        super().__init__()
        self.basic_type: Object = basic_type

    def contains_value(self, value) -> bool:
        if not isinstance(value, list):
            return False
        return True

    @property
    def name(self) -> str:
        return f"list({self.basic_type.name})"


class Tuple(Object):
    def __init__(self, *types):
        super().__init__()
        self.item_types: list = list(types)

    @property
    def type_count(self) -> int:
        return len(self.item_types)

    def item_type(self, index: int) -> Object:
        return self.item_types[index]

    @staticmethod
    def create_from(input_tuple: "Tuple", index: int, new_type: Object) -> "Tuple":
        types = [copy.deepcopy(type_) for type_ in input_tuple.item_types]
        types[index] = copy.deepcopy(new_type)
        return Tuple(types)

    def contains_value(self, value) -> bool:
        if not isinstance(value, tuple):
            return False
        for v, t in zip(value, self.item_types):
            if not t.contains_value(v):
                return False
        return True

    @property
    def is_composite(self) -> bool:
        return True

    @property
    def name(self) -> str:
        return f'tuple({", ".join([x.name for x in self.item_types])})'

    def intersect(self, other) -> typing.Union[Object, None]:
        if type(other) == Object:
            return other.intersect(self)
        if type(other) != type(self):
            return None
        if len(self.item_types) != len(other.item_types):
            if len(self.item_types) == 0:
                return copy.deepcopy(other)
            if len(other.item_types) == 0:
                return copy.deepcopy(self)
            return None

        result = []
        for t1, t2 in zip(self.item_types, other.item_types):
            val = t1.intersect(t2)
            if val is None:
                return None
            result.append(val)

        return Tuple(*result)
