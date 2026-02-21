"""Subclass of configparser.ConfigParser that adds conveniences"""

__all__ = [
    "ConfigParser",
    "detectEncoding"
]

import os
import chardet

from configparser import ConfigParser as _ConfigParser
from functools import wraps
from typing import Any, Optional


def detectEncoding(file_path: str) -> Optional[str]:
    """Detect the encoding of the supplied file_path
    
    Args:
        file_path (str): Full file path
    
    Returns:
        str: The encoding type of the file
    
    """
    with open(file_path, 'rb') as fpath:
        rawdata = fpath.read()
    result = chardet.detect(rawdata)
    if result is not None and result.get("confidence", 0) > 0.8:
        return result.get("encoding")
    return None


def confirmGet(default: Any=None):
    """Supplies a default return value to the wrapped method.
    
    Default value is returned if either section or option queried don't exist
    and a fallback arg is not supplied.
    
    Args:
        default (Any): Default return value. Should match type of decorated method.
        
    Returns:
        decorat
    
    """
    def _decorator(method):
        @wraps(method)
        def _wrapper(self, *args, **kwargs):
            """Decorator to confirm the section and option exist before calling
            the method. If the section or option does not exist, it returns the
            fallback value provided to the method or the supplied default value.
            
            """
            # Check if the section and option exist before calling the method
            if len(args) == 2:
                section, option = args
                # Per the method signature the first two args are section and option
                # so we'll unpack them here.
            elif len(args) < 2:
                # check **kwargs for section and option
                section = kwargs.get("section")
                option = kwargs.get("option")
                if not section or not option:
                    raise ValueError("Need to provide section and option")
            else:
                raise ValueError("Too many args provided")

            fallback = kwargs.get("fallback", default)
            kwargs["fallback"] = fallback
            # Respect the fallback value if provided otherwise use the default
            # value provided when decorating.
            
            if self.has_section(section) and self.has_option(section, option):
                return method(self, *args, **kwargs)
                # Ensure the section and option exist before calling the method
            
            self.set(section, option, value=fallback)
            # set the option in the config if it didn't exist prior.
            return fallback
            # Return the fallback value if unable to get value from config
        return _wrapper
    return _decorator  
    

class ConfigParser(_ConfigParser):
    """Subclass of configparser.ConfigParser that adds some conveniences.
    
    - Provide a 'filepath' to automatically read in the config file.
    - A self.filepath instance attribute to store the config filepath
    - The 'set' method will now check if the section exists and add it if it
        doesn't already exist.
    - The 'get' method now checks if the secion and option exist. Will return
        None if either doesn't exist.
    - The 'write' method will now default to using the 'self.filepath' attribute
        and handle opening the file for writing.
        You can just call <instance>.write()
    - Defaulting to automatically detect the encoding of the supplied file
    - Exposed optionxform during instantiation so it can be set before reading
        in the filepath.
        
    Args:
        filepath (str): The path to the config file
        encoding (str): Optional, the encoding to read and write the file with.
        optionxform (func): Exposing this attribute during init so we can set
            it before reading in the file. See configparser.ConfigParser.optionxform
    
    """
    def __init__(self, filepath=None, encoding=None, optionxform=None):
        super().__init__()
        self.filepath = filepath
        self.encoding = encoding
        
        if optionxform:
            # Chance to override optionxform
            # Ideally only needed to support legacy config files that don't
            # have lowered options.
            self.optionxform = optionxform
            
        if filepath:
            if not os.path.exists(filepath):
                # Create empty file if it doesn't exist.
                self.write(filepath, encoding=encoding or "utf-8")
            self.read(filepath, encoding=encoding)
            
    def read(self, filenames, encoding=None):
        """Override, Read the configuration from the file"""
        self.encoding = self.encoding or encoding 
        
        if self.encoding is None and isinstance(filenames, str):
            # detectEncoding is important as it's common for config files to be
            # utf-16 to support multi-language character sets.
            self.encoding = detectEncoding(filenames)
                
        if isinstance(filenames, str):
            self.filepath = filenames
            
        return super().read(filenames, encoding=encoding)
    
    # pylint: disable=W0221
    # Adding a new arg to the signature
    def write(self, fp=None, space_around_delimiters=True, encoding=None):
        """Override, Write the configuration to the file
        
        This will use the filepath instance attribute and manage the opening
        of the file to write to it.
        
        """
        if fp is None:
            if self.filepath is None:
                raise ValueError("Need to specify filepath")
            fp = self.filepath
        with open(fp, "w", encoding=(encoding or self.encoding)) as configfile:
            super().write(configfile, space_around_delimiters=space_around_delimiters)
    # pylint: enable=W0221
    
    def set(self, section, option, value=None):
        """Override, ensures section exists
        
        Rather than raising an exception if the section doesn't exist in the
        config file this method will create the section before setting the
        option value.
        
        """
        if not self.has_section(section):
            self.add_section(section)
        return super().set(section, option, value=str(value))
    
    # pylint: disable=W0622
    # vars is part of the built-in method signature
    @confirmGet(default=None)
    def get(self, section, option, *, raw=False, vars=None, # type: ignore[override]
            fallback=None) -> Optional[str]:
        """Override, Get an option value for a given section
        
        Rather than raising an exception if the section or option don't exist
        this method will return an empty string.

        If `vars' is provided, it must be a dictionary. The option is looked up
        in `vars' (if provided), `section', and in `DEFAULTSECT' in that order.
        If the key is not found and `fallback' is provided, it is used as
        a fallback value. `None' can be provided as a `fallback' value.

        If interpolation is enabled and the optional argument `raw' is False,
        all interpolations are expanded in the return values.

        Arguments `raw', `vars', and `fallback' are keyword only.

        The section DEFAULT is special.
        
        """
        if self.has_section(section) and self.has_option(section, option):
            return super().get(section, option, raw=raw, vars=vars, fallback=fallback)
        return ""
    
    @confirmGet(default=False)
    def getboolean(self, section, option, *, raw=False, vars=None, # type: ignore[override]
                   fallback=None, **kwargs) -> Optional[bool]:
        """Override, Get value from config as boolean
        
        Rather than raising an exception if the section or option don't exist
        this method will return False.
        
        See Also:
            get
        
        """
        return super().getboolean(section, option, raw=raw,
                                  vars=vars, fallback=fallback, **kwargs)
        
    @confirmGet(default=0.0)
    def getfloat(self, section, option, *, raw=False, vars=None, # type: ignore[override]
                 fallback=None, **kwargs) -> Optional[float]:
        """Override, Get value from config as boolean
        
        Rather than raising an exception if the section or option don't exist
        this method will return 0.0.
        
        See Also:
            get
        
        """
        return super().getfloat(section, option, raw=raw,
                                vars=vars, fallback=fallback, **kwargs)
        
    @confirmGet(default=0)
    def getint(self, section, option, *, raw=False, vars=None, # type: ignore[override]
               fallback=None, **kwargs) -> Optional[int]:
        """Override, Get value from config as boolean
        
        Rather than raising an exception if the section or option don't exist
        this method will return 0.
        
        See Also:
            get
        
        """
        return super().getint(section, option, raw=raw,
                              vars=vars, fallback=fallback, **kwargs)
    # pylint: enable=W0622
    