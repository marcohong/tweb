class AttrDict(dict):
    '''
    Dictionary subclass enabling attribute lookup/assignment of keys/values.

    For example::

        >>> m = AttrDict({'foo': 'bar'})
        >>> m.foo
        'bar'
        >>> m.foo = 'not bar'
        >>> m['foo']
        'not bar'
    '''

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            # to conform with __getattr__ spec
            # raise AttributeError(key)
            return None

    def __setattr__(self, key, value):
        self[key] = value
