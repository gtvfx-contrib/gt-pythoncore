"""Convenience methods for working with an XML tree"""
import xml.etree.cElementTree as ET


__all__ = [
    "getRoot",
    "createRoot",
    "createSubelement",
    "getChildrenRecursive",
    "filterNodeList",
    "find",
    "findRecursive",
    "prettyPrintElement",
    "writeFile"
]


def getRoot(filepath):
    """Parse the xml file provided and return the result of getroot()
    
    Args:
        filepath (str): path to XML file
    
    Returns:
        (xml.etree.cElementTree.Element)
    
    """
    xml = ET.parse(filepath)
    return xml.getroot()


def createRoot(tag, **kwargs):
    """Create a top-level node in the element tree
    
    Args:
        tag (str): tag name of the element
        **kwargs: meta data you want on the element
    
    Returns
        ET.Element

    """
    return ET.Element(tag, **kwargs)
    

def createSubelement(element, tag, **kwargs):
    """Create a child element of the input element
    
    Args:
        element (ET.Element): The parent element to create your element under
        tag (str): tag name of the element
        **kwargs: meta data you want on the element
    
    Returns:
        ET.Element

    """
    return ET.SubElement(element, tag, **kwargs)


def getChildrenRecursive(element, _elementList=None):
    """Get all descendants of the supplied element.
    
    Args:
        element (ET.Element)
    
    Returns:
        (list)

    """
    if _elementList is None:
        _elementList = []

    children = list(element)

    if children:
        _elementList.extend(children)
        for child in children:
            getChildrenRecursive(child, _elementList=_elementList)

    return _elementList


def filterNodeList(nodeList, **kwargs):
    """Filters the supplied nodeList using the node.attrib dict against the
    kwargs. Returns all nodes that match.
    
    Args:
        nodeList (list): list of ET.Element nodes
        **kwargs: key/value pairs to match against the node.attrib dict
    
    Returns:
        (list)

    """
    if not kwargs:
        return nodeList
    
    nodeMatchList = []

    for node in nodeList:
        # for each node filter the node.attrib dict against the kwargs dict
        # to find key/value pairs that match.
        sitems = {k: kwargs[k] for k in kwargs if k in node.attrib and kwargs[k] == node.attrib[k]}

        # if the resultant dict is a match to the kwargs then we found
        # a node to return
        if sitems == kwargs:
            nodeMatchList.append(node)
    
    return nodeMatchList


def find(element, tag, **kwargs):
    """This extends the behavior of the cElementTree.find() method by
    allowing for kwargs to match against.

    Args:
        element (ET.Element): The element to search beneath
        tag (str): The tag of the elment you wish to find
        **kwargs: key/value pairs to match against the node.attrib dict

    Returns:
        (list)

    """
    nodeList = element.findall(tag)
    return filterNodeList(nodeList, **kwargs)


def findRecursive(element, tag, **kwargs):
    """Recurses through all descendants of the supplied element looking for
    elements that match the supplied tag. If kwargs are supplied then this
    will do a comparison of the supplied kwargs and the attributes of the
    elements matching the tag. Only elements that match the supplied tag and
    any supplied kwargs are returned.

    Args:
        element (ET.Element): The element to search beneath
        tag (str): The tag of the elment you wish to find
        **kwargs: key/value pairs to match against the node.attrib dict

    Returns:
        (list)

    """
    nodeList = [node for node in getChildrenRecursive(element) if node.tag == tag]
    return filterNodeList(nodeList, **kwargs)


def _indent(elem, _level=0, _moreSibs=False):
    """This ensures legible indentation of the XML code within the
    resultant file.
    
    Args:
        elem (ElementTree Object): The element node you want to start indenting
            from. Likely the root of your XML tree
        _level=0 (int): Controls how many tabs to use for each child
        _moreSibs=False (bool): This is queried during recursion and makes
            different indentation if True than when False.
    
    Returns:
        None

    """
    i = "\n"
    if _level:
        i += (_level-1) * '  '
    numKids = len(elem)
    if numKids:
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
            if _level:
                elem.text += '  '
        count = 0
        for kid in elem:
            _indent(kid, _level+1, count < numKids - 1)
            count += 1
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
            if _moreSibs:
                elem.tail += '  '
    else:
        if _level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
            if _moreSibs:
                elem.tail += '  '


def prettyPrintElement(element):
    """Prints the down-stream tree start at the supplied element.
    Prints in xml format using utf8 encoding.
    
    Args:
        element (ET.Element)
    
    Returns:
        None

    """
    print(ET.tostring(element, encoding='utf8', method='xml'))


def writeFile(root, filename):
    """Write the full element tree out ot a file on disk.
    Passes the element tree through the _indent method.
    
    Args:
        root (ET.Element): The element you want to start writing from
        filename (str): full filename path where you want the file written
   
    Returns:
        None

    """
    tree = ET.ElementTree(root)
    _indent(root)
    tree.write(filename)
    