from typing import Any

class BaseLoader:
    def __init__(self):
        pass

    def load_data(self, src) -> Any:
        """
        Implemented by child classes
        """
        pass
