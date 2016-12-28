import imp
import importlib
import os


"""
imp.find_module doesn't find namespace packages, consequently py2app fails to include needed packages
"""


def create_blank_init(path):
    assert not os.path.isfile(path), "File already exists"
    with open(path, "w") as init_file:
        pass
    return


def fix_imp_find_module(module_name, second_try=None):
    _root_module = module_name.split(".")[0]
    try:
        imp.find_module(_root_module)
        return True
    except ImportError:
        if second_try is not None:
            return False
        module = importlib.import_module(_root_module)
        init_path = os.path.join(module.__path__[0], "__init__.py")
        if not os.path.isfile(init_path):
            create_blank_init(init_path)
            return fix_imp_find_module(module_name, True)
    return False


def main():
    to_test = [
        "PyObjCTools.AppHelper",
        "zope.interface",
    ]

    for m_n in to_test:
        if fix_imp_find_module(m_n):
            print "imp found %s" % m_n
        else:
            print "imp cannot find %s" % m_n


if __name__ == "__main__":
    main()