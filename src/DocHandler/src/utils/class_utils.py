class MissingAttributeError(Exception):
    """Custom exception for missing attributes."""
    pass

def set_kwargs_or_default(self, kwargs, key, default):
    if hasattr(kwargs, key):
        setattr(self,key,kwargs[key])
    else:
        setattr(self,key,default)

def set_required_attribute(obj, data, key):
    """
    Sets an attribute on `obj` from the dictionary `data` using `key`.

    Parameters:
    obj (object): The object to set the attribute on.
    data (dict): The dictionary containing the attributes.
    key (str): The key whose value should be set as an attribute.

    Raises:
    MissingAttributeError: If the key is not found in the dictionary.
    """
    if key not in data:
        raise MissingAttributeError(f"Missing required attribute: '{key}'")

    setattr(obj, key, data[key])