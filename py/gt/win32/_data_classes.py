"""Helper objects for working with win32 data"""

__all__ = [
    "FileVersion"
]

from dataclasses import dataclass


@dataclass(frozen=True, order=False)
class FileVersion:
    """A custom file version object
    
    Can be compared directly with a string for convenience.
    Provides properties for meaningful semantic components.
    
    """
    version: str
    major: int
    minor: int
    subminor: int
    revision: int
    
    def __str__(self) -> str:
        """Return the version string when converted to string."""
        return self.version
    
    def __eq__(self, other) -> bool:
        """Allow comparison with strings and other FileVersion objects."""
        if isinstance(other, str):
            return self._normalize_version(self.version) == self._normalize_version(other)
        elif isinstance(other, FileVersion):
            return (self.major, self.minor, self.subminor, self.revision) == \
                   (other.major, other.minor, other.subminor, other.revision)
        return False
    
    def __lt__(self, other) -> bool:
        """Allow version comparison using < operator."""
        if isinstance(other, str):
            return self._compare_with_string(other) < 0
        elif isinstance(other, FileVersion):
            return (self.major, self.minor, self.subminor, self.revision) < \
                   (other.major, other.minor, other.subminor, other.revision)
        return NotImplemented
    
    def __le__(self, other) -> bool:
        """Less than or equal comparison."""
        return self.__lt__(other) or self.__eq__(other)
    
    def __gt__(self, other) -> bool:
        """Greater than comparison."""
        if isinstance(other, str):
            return self._compare_with_string(other) > 0
        elif isinstance(other, FileVersion):
            return (self.major, self.minor, self.subminor, self.revision) > \
                   (other.major, other.minor, other.subminor, other.revision)
        return NotImplemented
    
    def __ge__(self, other) -> bool:
        """Greater than or equal comparison."""
        return self.__gt__(other) or self.__eq__(other)
    
    @staticmethod
    def _normalize_version(version_str: str) -> str:
        """Normalize version string by removing leading zeros from each component."""
        try:
            parts = version_str.split('.')
            # Remove leading zeros but keep at least one digit
            normalized_parts = [str(int(part)) for part in parts]
            return '.'.join(normalized_parts)
        except (ValueError, AttributeError):
            return version_str
    
    def _compare_with_string(self, version_str: str) -> int:
        """Compare with version string. Returns -1, 0, or 1."""
        try:
            # Parse the other version string into integer components
            other_parts = tuple(int(part) for part in version_str.split('.'))
            my_parts = (self.major, self.minor, self.subminor, self.revision)
            
            # Pad shorter tuple with zeros for fair comparison
            max_len = max(len(my_parts), len(other_parts))
            my_padded = my_parts + (0,) * (max_len - len(my_parts))
            other_padded = other_parts + (0,) * (max_len - len(other_parts))
            
            if my_padded < other_padded:
                return -1
            elif my_padded > other_padded:
                return 1
            else:
                return 0
        except ValueError:
            # Fall back to string comparison if parsing fails
            return -1 if self.version < version_str else (1 if self.version > version_str else 0)
    
    def matches(self, pattern: str) -> bool:
        """Check if this version matches a pattern, handling zero-padding."""
        return self._normalize_version(self.version) == self._normalize_version(pattern)
