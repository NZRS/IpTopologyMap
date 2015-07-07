__author__ = 'aaron'

import re

def _st(len=None):
    '''
    Construct a regex which matches alphabetic strings.
    :param len: exact number of chars to match. e.g.: len = 3 means
                "abc" will match, but "ab" and "abcd" won't.
    :return: a string containing the regex pattern.
    '''
    if len is None: return "[a-z]+"
    else: return "[a-z]{" + str(len) + "," + str(len) + "}(?![a-z])"

def _nm(len=None):
    '''
    Construct a regex which matches numeric strings.
    :param len: exact number of digits to match. e.g.: len = 3 means
                "123" will match, but "12" and "1234" won't.
    :return: a string containing the regex pattern.
    '''
    if len is None: return "[0-9]+"
    else: return "[0-9]{" + str(len) + "," + str(len) + "}(?![0-9])"

def regex():
    '''
    Get the compiled regex pattern for matching nz routers.
    :return: compiled regex pattern.
    '''

    string = regex_string()
    return re.compile(string)

def regex_string():
    '''
    Get the string representation of the regex pattern for matching nz routers.
    :return: string
    '''

    # vocus routers look like this: XXXXXXXXX.alb105.akl.vocus.net.nz
    str_vocus = "(" + _st(3) + _nm() + "\." + _st(3) + "\.vocus\.net\.nz)"

    # fx routers look like this: XXXXXXXX.aktnz-rt1.fx.net.nz
    str_fx = "(" + _st(5) + "-rt" + _nm() + "\.fx\.net\.nz" + ")"

    # snap routers look like this: XXXXXXXX.akl.snap.net.nz
    str_snap = "(" + _st(3) + "\.snap\.net\.nz)"

    # nzix routers look like this: XXXXXXX.ape.nzix.net or XXXXXXX.wlg.nzix.net
    exchanges = ["ape", "hix", "pnix", "wix", "chiz"]
    xchange = "(" + "|".join(exchanges) + ")"
    str_nzix = "(" + xchange + "\.nzix\.net)"

    # OR the regex strings together
    strs = [str_vocus, str_fx, str_snap, str_nzix]
    return "|".join(strs)