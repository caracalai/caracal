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
        assert self.is_composite == False

        if type(self) == ObjectType:
            return copy.deepcopy(other)
        if type(other) == ObjectType:
            return copy.deepcopy(self)

        if other.is_composite:
            return other.intersect(self)
        return None


class ObjectType(TypeBase):
    def __init__(self):
        super().__init__()

    def contains(self, other) -> bool:
        if type(self) == ObjectType:
            return True
        if type(self) is not ObjectType and type(other) is not ObjectType:
            if type(other) == type(self):
                return True
        raise Exception("{}.contains({}): Method is not implemented".format(self.name, other.name))

    @property
    def name(self):
        return "ObjectType"



class VoidType(ObjectType):
    def __init__(self):
        super().__init__()

    def contains_value(self, value):
        return False

    @property
    def name(self):
        return "VoidType"

class NumberType(ObjectType):
    def __init__(self):
        super().__init__()

    def contains_value(self, value):
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    @property
    def name(self):
        return "NumberType"


class FloatType(ObjectType):
    def __init__(self):
        super().__init__()

    def contains_value(self, value):
        return isinstance(value, (float, int))

    @property
    def name(self):
        return "FloatType"

class IntType(ObjectType):
    def __init__(self):
        super().__init__()

    def contains_value(self, value):
        return isinstance(value, (int))

    @property
    def name(self):
        return "IntegerType"

class BooleanType(ObjectType):
    def __init__(self):
        super().__init__()

    def contains_value(self, value):
        return isinstance(value, bool)

    @property
    def name(self):
        return "BooleanType"


class StringType(ObjectType):
    def __init__(self):
        super().__init__()

    def contains_value(self, value):
        return type(value) is str

    @property
    def name(self):
        return "StringType"


class ImageType(ObjectType):
    def __init__(self):
        super().__init__()

    @property
    def name(self):
        return "ImageType"


class VideoStreamType(ObjectType):
    def __init__(self):
        super(VideoStreamType, self).__init__()

    @property
    def name(self):
        return "VideoStreamType"


class RectType(ObjectType):
    def __init__(self):
        super().__init__()

    @property
    def name(self):
        return "RectType"

class ListType(ObjectType):
    def __init__(self, basicType: ObjectType):
        super().__init__()
        self.basicType_ = basicType

    @property
    def basicType(self):
        return self.basicType_

    def contains_value(self, value):
        if not type(value) is list:
            return False
        return True

    @property
    def name(self):
        return "ListType({basicType})".format(basicType=self.basicType.name)


class DataSourceType(ObjectType):
    def __init__(self):
        super().__init__()

    def contains_value(self, value):
        return type(value) is str

    @property
    def name(self):
        return "DataSourceType"


class TableDataSourceType(DataSourceType):
    def __init__(self, basicType):
        super().__init__()
        self._basicType = basicType

    @property
    def basicType(self):
        return self._basicType

    @property
    def is_composite(self):
        return True

    def intersect(self, other):
        if type(other) != TableDataSourceType:
            return False
        basicTypeIntersection = other.basicType.intersect(self.basicType)
        if basicTypeIntersection == None:
            return None
        return TableDataSourceType(basicTypeIntersection)

    @property
    def name(self):
        return "TableDataSourceType({basicType})".format(basicType=self.basicType.name)

class TupleType(ObjectType):
    def __init__(self, *types):
        super().__init__()
        self._types = list(types)

    @property
    def names(self):
        return self._names

    @names.setter
    def names(self, nms):
        self._names = nms

    @property
    def typeCount(self):
        return len(self._types)

    def type(self, index):
        return self._types[index]

    def createFrom(input_tuple, index, newType):
        types = [copy.deepcopy(type) for type in input_tuple._types]
        types[index] = copy.deepcopy(newType)
        return TupleType(types)

    def contains_value(self, value):
        if not type(value) is tuple:
            return False
        for v, t in zip(value, self._types):
            if t.contains_value(v) == False:
                return False
        return True

    @property
    def is_composite(self):
        return True

    @property
    def name(self):
        return "TupleType({args})".format(args=", ".join([x.name for x in self._types]))


    def intersect(self, other):
        if type(other) == ObjectType:
            return other.intersect(self)
        if type(other) != type(self):
            return None
        if len(self._types) != len(other._types):
            if len(self._types) == 0:
                return copy.deepcopy(other)
            if len(other._types) == 0:
                return copy.deepcopy(self)
            return None

        result = []
        for t1, t2 in zip(self._types, other._types):
            val = t1.intersect(t2)
            if val == None:
                return None
            result.append(val)

        return TupleType(*result)
