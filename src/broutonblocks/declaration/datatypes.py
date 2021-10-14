import copy


class TypeBase:
    def __init__(self):
        pass

    def equal(self, other) -> bool:
        return self.contains(other) and other.contains(self)

    def contains(self, other):
        raise Exception("Method is not implemented")

    def contains_value(self, value):
        raise Exception("Method is not implemented")

    @property
    def is_composite(self):
        return False

    @property
    def name(self):
        return "TypeBase"

    def __str__(self):
        return self.name

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


class Object(TypeBase):
    def __init__(self):
        super().__init__()

    def contains(self, other) -> bool:
        if type(self) == Object:
            return True
        if type(self) is not Object and type(other) is not Object:
            if type(other) == type(self):
                return True
        raise Exception(
            "{}.contains({}): Method is not implemented".format(self.name, other.name)
        )

    @property
    def name(self):
        return "ObjectType"


class Void(Object):
    def __init__(self):
        super().__init__()

    def contains_value(self, value):
        return False

    @property
    def name(self):
        return "VoidType"


class Float(Object):
    def __init__(self):
        super().__init__()

    def contains_value(self, value):
        return isinstance(value, (float, int))

    @property
    def name(self):
        return "FloatType"


class Int(Object):
    def __init__(self):
        super().__init__()

    def contains_value(self, value):
        return isinstance(value, int)

    @property
    def name(self):
        return "IntegerType"


class Boolean(Object):
    def __init__(self):
        super().__init__()

    def contains_value(self, value):
        return isinstance(value, bool)

    @property
    def name(self):
        return "BooleanType"


class String(Object):
    def __init__(self):
        super().__init__()

    def contains_value(self, value):
        return type(value) is str

    @property
    def name(self):
        return "StringType"


class Image(Object):
    def __init__(self):
        super().__init__()

    @property
    def name(self):
        return "ImageType"


class BinaryArray(Object):
    def __init__(self):
        super().__init__()

    @property
    def name(self):
        return "BinaryFileType"


class VideoStream(Object):
    def __init__(self):
        super(VideoStream, self).__init__()

    @property
    def name(self):
        return "VideoStreamType"


class Rect(Object):
    def __init__(self):
        super().__init__()

    @property
    def name(self):
        return "RectType"


class List(Object):
    def __init__(self, basic_type: Object):
        super().__init__()
        self.basic_type = basic_type

    def contains_value(self, value):
        if not type(value) is list:
            return False
        return True

    @property
    def name(self):
        return "ListType({basicType})".format(basicType=self.basic_type.name)


class DataSource(Object):
    def __init__(self):
        super().__init__()

    def contains_value(self, value):
        return type(value) is str

    @property
    def name(self):
        return "DataSourceType"


class Tuple(Object):
    def __init__(self, *types):
        super().__init__()
        self.item_types = list(types)

    @property
    def type_count(self):
        return len(self.item_types)

    def item_type(self, index):
        return self.item_types[index]

    @staticmethod
    def create_from(input_tuple, index, newType):
        types = [copy.deepcopy(type_) for type_ in input_tuple.item_types]
        types[index] = copy.deepcopy(newType)
        return Tuple(types)

    def contains_value(self, value):
        if not type(value) is tuple:
            return False
        for v, t in zip(value, self.item_types):
            if not t.contains_value(v):
                return False
        return True

    @property
    def is_composite(self):
        return True

    @property
    def name(self):
        return "TupleType({args})".format(
            args=", ".join([x.name for x in self.item_types])
        )

    def intersect(self, other):
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
