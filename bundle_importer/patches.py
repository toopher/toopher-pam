# Patch functions - all variables in function files must be local (e.g., imports must be done in local scope)


# Define patch functions here
def patch_requests_certs(module):
    """
    Restore cacerts.pem file missed by bundling

    Bundling does not pick up the cacerts.pem file required for SSL certificate
    validation.  This patch replaces the 'where' function in requests.cert to
    point to a temporary file initialized with the required pem-file contents.

    """

    import data_bundle
    import tempfile

    # Write certfile contents to a temporary file
    cert_file = tempfile.NamedTemporaryFile()
    cert_file.write(data_bundle.REQUESTS_CERTS_FILE.encode('utf-8'))
    cert_file.flush()

    # Keep a reference to the file so it doesn't get deleted
    module.cert_file = cert_file

    # Teach request.certs where the certfile is
    def new_where():
        return module.cert_file.name
    module.where = new_where


# End patch function definitions

def get_patch_code(name):
    try:
        patch_function_name = "patch_%s" % name.replace(".", "_")
        patch_function = globals()[patch_function_name]
        return patch_function.func_code
    except KeyError:
        return None