from typing import Optional

from cgcore.configs.base_config import BaseConfig

class BaseEmbedderConfig(BaseConfig):
    def __init__(
            self,
            api_key: str,
            model_name: Optional[str] = None,
            encoding_format: Optional[str] = None,
            dimensions: Optional[int] = None,
            **kwargs,
    ):
        """
        Initializes a configuration class instance for the embedder.

        :param model_name: Name of the model, defaults to None
        :type model_name: Optional[str], optional
        :param encoding_format: Encoding format of the model, defaults to None
        :type encoding_format: Optional[str], optional
        :param dimensions: Number of dimensions in the model, defaults to None
        :type dimensions: Optional[int], optional
        :param kwargs: Additional keyword arguments
        :type kwargs: dict
        """
        self.api_key = api_key
        self.model_name = model_name
        self.encoding_format = encoding_format
        self.dimensions = dimensions
        # Assign additional keyword arguments
        if kwargs:
            for key, value in kwargs.items():
                setattr(self, key, value)