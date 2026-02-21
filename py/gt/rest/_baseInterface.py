
"""Abstract base interface for a REST API"""
from abc import abstractmethod
import requests
from urllib.parse import urljoin

from typing import Any, Callable, Dict, Mapping, Optional, Union
from requests.auth import AuthBase

from gt.metaclasses import ABCSingleton

from ._captureException import CaptureException



__all__ = [
    "BaseInterface",
    "RestException"
]



class RestException(Exception):
    """Base exception for REST API"""
    ...
    

class BaseInterface(metaclass=ABCSingleton):
    """Object for interfacing with a REST API
    
    ## Example:
    ```python
    from t2.rest import BaseInterface
    
    class WoWCreator(BaseInterface):
        def __init__(self, port: int = 6014) -> None:
            super().__init__()
            
            # Instance attributes - __init__ only runs once due to ABCSingleton
            self.port = port
            self.my_var = "value"
    
    # To force re-initialization:
    wc = WoWCreator(_reinit=True)
            
    ```
    
    Class Attributes:
        session (requests.Session): Session used for all requests
        timeout (int): Timeout passed to all requests
    
    """
    # Using requests.Session reduces API overhead by reusing the same TCP 
    # connection and reduces the call time by roughly 50%
    session = requests.Session()
    timeout = 60
        
    @property
    @abstractmethod
    def base_url(self) -> str:
        """Get the base URL for the blsever REST API"""
        raise NotImplementedError
       
    @property
    def headers(self) -> Mapping[str, str | bytes]:
        """Get the headers for the blsever REST API requests"""
        return self.session.headers
    
    @headers.setter
    def headers(self, value: Dict[str, str]) -> None:
        self.session.headers.update(value)
        
    @property
    def auth(self) -> Union[None, tuple[str, str], AuthBase]:
        """Get the auth attribute of self.session"""
        return self.session.auth  # type: ignore[return-value]
    
    @auth.setter
    def auth(self, value: Union[None, tuple[str, str], AuthBase]) -> None:
        if value is None or isinstance(value, AuthBase) or \
            (isinstance(value, tuple) and len(value) == 2):
            self.session.auth = value  # type: ignore[assignment]
        else:
            raise TypeError("auth must be None, a tuple (username, password), "
                            "or an AuthBase instance")
    
    @CaptureException
    def _request(self, method: Callable, endpoint: str,
                 data: Optional[dict]=None, json: Optional[dict]=None,
                 params: Optional[dict]=None) -> Any:
        """Perform a request to the REST API
        
        Args:
            method(str): The method to use for the request.
            endpoint(str): The endpoint to request.
            data(dict): The data to send as form-encoded (application/x-www-form-urlencoded).
            json(dict): The data to send as JSON (application/json).
            params(dict): The query parameters for the request.
            
        Returns:
            Any: The JSON object from the response.
        
        """
        url = urljoin(self.base_url, endpoint)
        response = method(url, data=data, json=json, params=params, timeout=self.timeout)
        
        if not response:
            raise RestException(f"{response.status_code}: {response.text}")
        return response.json()

    def get(self, endpoint: str, data: Optional[dict]=None, json: Optional[dict]=None,
            params: Optional[dict]=None) -> Any:
        """Perform a GET request to the REST API
        
        Args:
            endpoint(str): The endpoint to request.
            data(dict): The data to send as form-encoded.
            json(dict): The data to send as JSON.
            params(dict): The query parameters for the request.
            
        Returns:
            Any: The JSON object from the response.
        
        """
        return self._request(self.session.get, endpoint, data=data, json=json,
                           params=params)
    
    def patch(self, endpoint: str, data: Optional[dict]=None, json: Optional[dict]=None,
              params: Optional[dict]=None) -> Any:
        """Perform a PATCH request to the REST API
        
        Args:
            endpoint(str): The endpoint to send the request to.
            data(dict): The data to send as form-encoded.
            json(dict): The data to send as JSON.
            params(dict): The query parameters for the request.

        Returns:
            Any: The JSON object from the response.
        
        """
        return self._request(self.session.patch, endpoint, data=data, json=json,
                           params=params)
    
    def post(self, endpoint: str, data: Optional[dict]=None, json: Optional[dict]=None,
             params: Optional[dict]=None) -> Any:
        """Perform a POST request to the REST API
        
        Args:
            endpoint(str): The endpoint to send the request to.
            data(dict): The data to send as form-encoded.
            json(dict): The data to send as JSON.
            params(dict): The query parameters for the request.

        Returns:
            Any: The JSON object from the response.
        
        """
        return self._request(self.session.post, endpoint, data=data, json=json,
                           params=params)

    def put(self, endpoint: str, data: Optional[dict]=None, json: Optional[dict]=None,
            params: Optional[dict]=None) -> Any:
        """Perform a PUT request to the REST API
        
        Args:
            endpoint(str): The endpoint to send the request to.
            data(dict): The data to send as form-encoded.
            json(dict): The data to send as JSON.
            params(dict): The query parameters for the request.

        Returns:
            Any: The JSON object from the response.
            
        """
        return self._request(self.session.put, endpoint, data=data, json=json,
                           params=params)
    
    def delete(self, endpoint: str) -> Any:
        """Perform a DELETE request to the REST API
        
        Args:
            endpoint(str): The endpoint to send the request to.
            
        Returns:
            Any: The JSON object from the response.
        
        """
        return self._request(self.session.delete, endpoint)
