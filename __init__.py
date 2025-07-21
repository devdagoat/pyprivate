import sys
import inspect

from typing import Any, Callable, ParamSpec, TypeVar
from types import FrameType, MethodType

_T = TypeVar("_T")
_P = ParamSpec("_P")

class private:

    def __init__(self, value=None):
        if isinstance(value, property):
            self.name = value.fget.__name__ #type: ignore
        else:
            self.name = value.__name__ #type: ignore
        self.value = value
        self.__doc__ = self.value.__doc__

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.value is None:
            raise AttributeError("unreadable attribute")
        if isinstance(self.value, property):
            return self.value.fget(obj) #type: ignore
        return self.value(obj) #type: ignore

    def __set__(self, obj, value):
        if not obj._authorize(self.name, sys._getframe(2)):
            raise AttributeError(f"'{type(obj).__name__}' object has no attribute '{self.name}'")
        self.value = lambda obj: value

    def __delete__(self, obj):
        del self.value

class private_method:

    def __init__(self, value: Callable[_P, _T]):
        self.name = value.__name__ #type: ignore
        self.value = value
        self.__doc__ = self.value.__doc__

    def __call__(self, *args, **kwds) -> Any:
        return self.value(*args, **kwds)

    def __get__(self: Callable[_P, _T], obj, objtype=None):
        if obj is None:
            return self
        if self.value is None:
            raise AttributeError("unreadable attribute")

        return MethodType(self.value, obj)

    def __set__(self, obj, value):
        if not obj._authorize(self.name, sys._getframe(2)):
            raise AttributeError(f"'{type(obj).__name__}' object has no attribute '{self.name}'")
        self.value = MethodType(value.__func__ if inspect.ismethod(value) else value, obj)

    def __delete__(self, obj):
        del self.value


class _SupportsPrivateType(type):
    def __new__(metacls, name: str, bases: tuple[type, ...], namespace: dict[str, Any], /, **kwds: Any):
        _private_ = []
        for k, v in namespace.items():
            if isinstance(v, (private, private_method)):
                _private_.append(k)
        
        namespace["_private_"] = property(lambda self: tuple(_private_))


        return super().__new__(metacls, name, bases, namespace, **kwds)
        



class SupportsPrivate(metaclass=_SupportsPrivateType):
    _private_ : property

    def _authorize(self, name: str, accessed_by: FrameType) -> bool:
        qualname = accessed_by.f_code.co_qualname
        code = accessed_by.f_code
        if qualname == "<module>":
            return False
        try:
            namespace, callername = qualname.split('.<locals>', 1)[0].rsplit('.', 1)
        except ValueError:
            return False
        module = inspect.getmodule(code)
        caller = getattr(getattr(module, namespace), callername)
        presumed_attr = getattr(self, caller.__name__, None)
        if inspect.ismethod(presumed_attr):
            presumed_attr = presumed_attr.__func__
        if presumed_attr != caller:
            return False

        return True
    
    def __init_subclass__(cls) -> None:
        for private in cls._private_.fget(cls): #type: ignore
            unwrapped = getattr(cls, private)
            setattr(cls, private, unwrapped)

    def __getattribute__(self, name: str):

        if name in ("_private_", "_authorize_func", "_authorize"):
            return super().__getattribute__(name)
        
        if name in self._private_:
            accessed_by = sys._getframe(1)
            if not self._authorize(name, accessed_by):
                raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        return super().__getattribute__(name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ("_authorize", "__getattribute__", "__setattr__"):
            return
        
        return super().__setattr__(name, value)

__all__ = ("SupportsPrivate", "private", "private_method",)

if __name__ == "__main__":

    class TestPrivateAttrs(SupportsPrivate):
        def __init__(self) -> None:
            self.a = 1
            print(self.test)
            print(type(self.secret))
            print(type(self.private_property))

        @private
        def secret(self):
            return 'cheese'

        @private_method
        def test(self, a):
            return a+5

        @private
        @property
        def private_property(self):
            return "cake"

        def get_secret(self):
            return self.secret

    t = TestPrivateAttrs()

    #t.secret = 1
    
    print(t._authorize)

    def _authorize(name, accessed_by):
        return True
    
    t._authorize = _authorize

    print(t._authorize)
    print(t.get_secret())
    print(t.test)
    print(t.test)


