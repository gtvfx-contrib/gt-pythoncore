"""Generic Windows Registry utility functions."""

__all__ = [
    "getRegistryValue",
    "getRegistryValues", 
    "getRegistrySubkeys",
    "getRegistryKeyInfo",
    "getRegistryValuesDetailed",
    "registryKeyExists",
    "setRegistryValue",
    "setRegistryValueString", 
    "setRegistryValueDWord",
    "deleteRegistryValue",
    "createRegistryKey"
]

import logging
import winreg

from functools import cache
from typing import Optional, Dict, List, Tuple, Any, Union


log = logging.getLogger(__name__)



def registryKeyExists(reg_path: Tuple[int, str]) -> bool:
    """Check if a registry key exists."""
    try:
        with winreg.OpenKey(*reg_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY):
            return True
    except (FileNotFoundError, OSError):
        return False


@cache
def getRegistryValue(reg_path: Tuple[int, str], value_name: str) -> Optional[Any]:
    """Get a single registry value.
    
    Args:
        reg_path: Tuple of (root_key, subkey_path)
        value_name: Name of the value to retrieve
        
    Returns:
        The registry value data, or None if not found
        
    """
    try:
        with winreg.OpenKey(*reg_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            return winreg.QueryValueEx(key, value_name)[0]
    except (FileNotFoundError, OSError):
        log.debug(f"Registry value not found: {reg_path[1]}\\{value_name}")
        return None


@cache
def getRegistryValues(reg_path: Tuple[int, str]) -> Optional[Dict[str, Any]]:
    """Get all values from a registry key.

    Args:
        reg_path: Tuple of (root_key, subkey_path)
        
    Returns:
        Dictionary of value_name: value_data pairs, or None if key not found
        
    """
    try:
        values = {}
        with winreg.OpenKey(*reg_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            _, num_values, _ = winreg.QueryInfoKey(key)
            
            for i in range(num_values):
                try:
                    value_name, value_data, _ = winreg.EnumValue(key, i)
                    values[value_name] = value_data
                except OSError:
                    continue
                    
        return values if values else None
        
    except (FileNotFoundError, OSError):
        log.debug(f"Registry key not found: {reg_path[1]}")
        return None


def getRegistrySubkeys(reg_path: Tuple[int, str]) -> Optional[List[str]]:
    """Get all subkey names from a registry key.
    
    Args:
        reg_path: Tuple of (root_key, subkey_path)
        
    Returns:
        List of subkey names, or None if key not found
        
    """
    try:
        subkeys = []
        with winreg.OpenKey(*reg_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            num_subkeys, _, _ = winreg.QueryInfoKey(key)
            
            for i in range(num_subkeys):
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    subkeys.append(subkey_name)
                except OSError:
                    continue
                    
        return subkeys if subkeys else None
        
    except (FileNotFoundError, OSError):
        log.debug(f"Registry key not found: {reg_path[1]}")
        return None


def getRegistryKeyInfo(reg_path: Tuple[int, str]) -> Optional[Dict[str, Union[Dict[str, Any], List[str]]]]:
    """Get complete information about a registry key (values and subkeys).
    
    Args:
        reg_path: Tuple of (root_key, subkey_path)
        
    Returns:
        Dictionary with 'values' and 'subkeys' keys, or None if key not found
        
    """
    try:
        result = {'values': {}, 'subkeys': []}
        
        with winreg.OpenKey(*reg_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            num_subkeys, num_values, _ = winreg.QueryInfoKey(key)
            
            # Get all values
            for i in range(num_values):
                try:
                    value_name, value_data, _ = winreg.EnumValue(key, i)
                    result['values'][value_name] = value_data
                except OSError:
                    continue
            
            # Get all subkeys
            for i in range(num_subkeys):
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    result['subkeys'].append(subkey_name)
                except OSError:
                    continue
                    
        return result if result['values'] or result['subkeys'] else None
        
    except (FileNotFoundError, OSError):
        log.debug(f"Registry key not found: {reg_path[1]}")
        return None


@cache
def getRegistryValuesDetailed(reg_path: Tuple[int, str]) -> Optional[Dict[str, Dict[str, Any]]]:
    """Get all values from a registry key with detailed type information.
    
    Args:
        reg_path: Tuple of (root_key, subkey_path)
        
    Returns:
        Dictionary with detailed value info, or None if key not found
        
    """
    try:
        values = {}
        with winreg.OpenKey(*reg_path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            _, num_values, _ = winreg.QueryInfoKey(key)
            
            for i in range(num_values):
                try:
                    value_name, value_data, value_type = winreg.EnumValue(key, i)
                    values[value_name] = {
                        'data': value_data,
                        'type': value_type,
                        'type_name': _getRegistryTypeName(value_type)
                    }
                except OSError:
                    continue
                    
        return values if values else None
        
    except (FileNotFoundError, OSError):
        log.debug(f"Registry key not found: {reg_path[1]}")
        return None


def _getRegistryTypeName(reg_type: int) -> str:
    """Convert registry type constant to readable name."""
    type_names = {
        winreg.REG_SZ: "REG_SZ",
        winreg.REG_EXPAND_SZ: "REG_EXPAND_SZ", 
        winreg.REG_BINARY: "REG_BINARY",
        winreg.REG_DWORD: "REG_DWORD",
        winreg.REG_QWORD: "REG_QWORD",
        winreg.REG_MULTI_SZ: "REG_MULTI_SZ",
    }
    return type_names.get(reg_type, f"UNKNOWN_TYPE_{reg_type}")


def _clearRegistryCache(reg_path: Tuple[int, str]) -> None:
    """Clear cached registry values for the given path."""
    try:
        getRegistryValue.cache_clear()
        getRegistryValues.cache_clear() 
        getRegistryValuesDetailed.cache_clear()
    except AttributeError:
        pass  # No cache to clear


def setRegistryValue(reg_path: Tuple[int, str], value_name: str, value_data: Any, 
                     value_type: int = winreg.REG_SZ) -> bool:
    """Set a registry value, creating the key if it doesn't exist.
    
    Args:
        reg_path: Tuple of (root_key, subkey_path)
        value_name: Name of the value to set
        value_data: Data to store in the value
        value_type: Registry data type (defaults to REG_SZ)
        
    Returns:
        True if successful, False otherwise
        
    """
    try:
        root_key, subkey_path = reg_path
        
        # Use CreateKeyEx with full access and 64-bit registry view
        with winreg.CreateKeyEx(
            root_key, 
            subkey_path, 
            0, 
            winreg.KEY_ALL_ACCESS | winreg.KEY_WOW64_64KEY
        ) as key:
            winreg.SetValueEx(key, value_name, 0, value_type, value_data)
            winreg.FlushKey(key)  # Force immediate write
            
        # Clear any cached values
        _clearRegistryCache(reg_path)
        return True
                
    except (OSError, PermissionError) as e:
        log.error(f"Failed to set registry value {reg_path[1]}\\{value_name}: {e}")
        return False


def setRegistryValueString(reg_path: Tuple[int, str], value_name: str, value_data: str) -> bool:
    """Set a string registry value.
    
    Args:
        reg_path: Tuple of (root_key, subkey_path)
        value_name: Name of the value to set
        value_data: String data to store
        
    Returns:
        True if successful, False otherwise
        
    """
    return setRegistryValue(reg_path, value_name, value_data, winreg.REG_SZ)


def setRegistryValueDWord(reg_path: Tuple[int, str], value_name: str, value_data: int) -> bool:
    """Set a DWORD registry value.
    
    Args:
        reg_path: Tuple of (root_key, subkey_path)
        value_name: Name of the value to set
        value_data: Integer data to store
        
    Returns:
        True if successful, False otherwise
        
    """
    return setRegistryValue(reg_path, value_name, value_data, winreg.REG_DWORD)


def deleteRegistryValue(reg_path: Tuple[int, str], value_name: str) -> bool:
    """Delete a registry value.
    
    Args:
        reg_path: Tuple of (root_key, subkey_path)
        value_name: Name of the value to delete
        
    Returns:
        True if successful, False otherwise
        
    """
    try:
        with winreg.OpenKey(*reg_path, 0, winreg.KEY_ALL_ACCESS | winreg.KEY_WOW64_64KEY) as key:
            winreg.DeleteValue(key, value_name)
            
        # Clear any cached values
        _clearRegistryCache(reg_path)
        return True
            
    except (FileNotFoundError, OSError) as e:
        log.debug(f"Failed to delete registry value {reg_path[1]}\\{value_name}: {e}")
        return False


def createRegistryKey(reg_path: Tuple[int, str]) -> bool:
    """Create a registry key.
    
    Args:
        reg_path: Tuple of (root_key, subkey_path)
        
    Returns:
        True if successful, False otherwise
    
    """
    try:
        with winreg.CreateKeyEx(reg_path[0], reg_path[1], 0, winreg.KEY_ALL_ACCESS | winreg.KEY_WOW64_64KEY):
            return True
            
    except (OSError, PermissionError) as e:
        log.error(f"Failed to create registry key {reg_path[1]}: {e}")
        return False
