# Used at bundle time to create a datafile module containing required data files
import os


# Define data bundle writers here
def data_requests_certs():
    from requests import certs
    certfile_contents = open(certs.where()).read()
    write_multiline("REQUESTS_CERTS_FILE", certfile_contents)


# End data bundle writers

DATA_BUNDLE_MODULE_NAME = 'data_bundle.py'
_data_bundle_file = None


# Used by bundler to create the datafiles module included in the bundle
def update_data_bundle_for_module(name):
    try:
        data_bundler_function_name = "data_%s" % name.replace('.', '_')
        globals()[data_bundler_function_name]()
    except KeyError:
        pass


MULTILINE_CONTENTS_TEMPLATE = """\
%s = u'''\\
%s
'''

"""


def write_multiline(name, contents):
    global _data_bundle_file
    if not _data_bundle_file:
        _data_bundle_file = open(DATA_BUNDLE_MODULE_NAME, 'wb')

    _data_bundle_file.write(MULTILINE_CONTENTS_TEMPLATE % (name, contents))


def close_data_bundle_file():
    global _data_bundle_file
    if _data_bundle_file:
        _data_bundle_file.close()
        _data_bundle_file = None

def remove_data_bundle_file():
    try:
        os.remove(DATA_BUNDLE_MODULE_NAME)
    except Exception:
        pass
