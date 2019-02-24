from bs4 import UnicodeDammit

def representsInt(s):
    """
    Checks if string represents integer

    :param s:
    :type s: str
    :return: True if integer
    :rtype: bool
    """
    try:
        int(s)
        return True
    except ValueError:
        return False


def getFileEncoding(filename):
    """
    Returns the character encoding of a file using Dammit

    :param filename: path to the file
    :type filename: str
    :return: String of the type "latin-1"
    :rtype: str
    """
    raw = open(filename, "rb").read()
    dammit = UnicodeDammit(raw)

    return dammit.original_encoding
