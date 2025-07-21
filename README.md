# pyprivate
Private Attributes and Methods for Python Classes
---
I mean it's pretty self explanatory

One thing to mind, the `@private` and `@private_method` decorator classes aren't actually overriding the types. All they do is let the metaclass know they represent private attributes, then they get reverted soon as the SupportsPrivate class is inherited

```python

  from private import SupportsPrivate, private, private_method

  class TestPrivateAttrs(SupportsPrivate):
        def __init__(self) -> None:
            self.a = 1
            print(self.test) # Works
            print(type(self.secret)) # Prints <class 'str'>
            print(self.secret) # Works
            print(type(self.private_property)) # Works, prints property instead of private

            self.secret = "Foo" # works and updates the attribute as expected

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

    t.secret = 1 # Raises AttributeError
    
    hash(t._authorize) # Overriding _authorize does not work

    def _authorize(name, accessed_by):
        return True
    
    t._authorize = _authorize

    hash(t._authorize) # Same exact hash as before

    print(t.get_secret()) # Works via the instance method

    print(t.test) # Raises AttributeError
    print(t.private_property) # Raises AttributeError



```
