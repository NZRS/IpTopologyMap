__author__ = 'aaron'

import re

companies = ["vocus", "fx", "snap", "nzix", "acsdata", "global-gateway", "massey",
             "nztechnologygroup", "orcon", "reannz", "tranzpeer"]

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
    return re.compile(string, re.IGNORECASE)

def regex_company(company):

    # vocus routers look like this: XXXXXXXXX.alb105.akl.vocus.net.nz
    if company == "vocus":
        return "(" + _st(3) + _nm() + "\." + _st(3) + "\.vocus\.net\.nz)"

    # fx routers look like this: XXXXXXXX.aktnz-rt1.fx.net.nz
    elif company == "fx":
        return "(" + _st(5) + "-rt" + _nm() + "\.fx\.net\.nz" + ")"

    # snap routers look like this: XXXXXXXX.akl.snap.net.nz
    elif company == "snap":
        return "(" + _st(3) + "\.snap\.net\.nz)"

    # nzix routers look like this: XXXXXXX.ape.nzix.net or XXXXXXX.wlg.nzix.net
    elif company == "nzix":
        exchanges = ["ape", "hix", "pnix", "wix", "chiz"]
        xchange = "(" + "|".join(exchanges) + ")"
        return "(" + xchange + "\.nzix\.net)"

    # massey routers look like this: XXXXXXXX-vlan802.massey.ac.nz
    elif company == "massey":
        return "(-vlan" + _nm() + "\.massey\.ac\.nz)"

    # reannz routers look like this: XXXXXXXX.anr01-akl.reannz.co.nz
    elif company == "reannz":
        return "(" + _st(3) + _nm() + "-" + _st(3) + "\.reannz\.co\.nz)"

    # global-gateway routers look like this: XXXXXX.akbr7.global-gateway.net.nz
    elif company == "global-gateway":
        return "(" + _st(4) + _nm() + "\.global-gateway\.net\.nz)"

    # orcon routers look like this: XXXXXXX.cre2.nct.orcon.net.nz
    elif company == "orcon":
        return "(" + _st(3) + _nm(1) + "\." + _st(3) + "\.orcon\.net\.nz)"

    # acsdata routers look like this: XXXXXXX.v4akl1.acsdata.co.nz
    elif company == "acsdata":
        return "(v" + _nm() + _st(3) + _nm() + "\.acsdata\.co\.nz)"

    # tranzpeer routers look like this: XXXXXX.cpcak4-r1.tranzpeer.net
    elif company == "tranzpeer":
        return "(" + _st(5) + _nm() + "-r" + _nm() + "\.tranzpeer\.net)"

    # nztechnology routers look like this: XXXXXXXX-mdr-cr1.nztechnologygroup.com
    elif company == "nztechnologygroup":
        return "(-" + _st(3) + "-" + _st(2) + _nm(1) + "\.nztechnologygroup\.com)"

    else:
        raise ValueError("No regex for {}".format(company))

def regex_string():
    '''
    Get the string representation of the regex pattern for matching nz routers.
    :return: string
    '''
    global companies
    return "|".join(regex_company(c) for c in companies)