class SessionContext(dict):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        else:
            if args or kwargs:
                raise ValueError(
                    "Context is a singleton and cannot be re-initialized with arguments."
                )
        return cls._instance
