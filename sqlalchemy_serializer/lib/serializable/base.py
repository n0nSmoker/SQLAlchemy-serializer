class Base:
    def __call__(self, value) -> str:
        raise NotImplementedError(f'Method should implement serialization logic for{value}')
