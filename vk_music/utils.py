from __future__ import print_function


def prnt(*args, **kwargs):
    args = list(args)
    for (i, v) in enumerate(args):
        # v = str(v)
        if isinstance(v, basestring):
            try:
                args[i] = unicode(v, "utf-8")
            except (TypeError, UnicodeDecodeError):
                try:
                    args[i] = v.encode("utf-8")
                except UnicodeDecodeError:
                    pass

    return print(*args, **kwargs)


def replace_chars(string, chars, char=''):
    for to_replace in chars:
        string = string.replace(to_replace, char)
    return string