import argparse
import imp
import marshal
import os
import sys
import base64
import tempfile
import zlib

import PyInstaller.depend.imptracker
import PyInstaller.depend.modules

import data_bundler
import patches

BUNDLE_IMPORTER_TEMPLATE = """\
import abc
import sys
import imp
import base64
import marshal
import types
import zlib

MAGIC_NUMBER = %(magic_number)r
BASE64_BUNDLE = '''\\
%(base64_bundle)s
'''

if imp.get_magic() != MAGIC_NUMBER:
    raise RuntimeError("Dependencies are incompatible with this Python runtime (wrong 'magic number')")


compressed_bundle = base64.decodestring(BASE64_BUNDLE)
marshaled_bundle = zlib.decompress(compressed_bundle)
module_bundle = marshal.loads(marshaled_bundle)


class BundleImporter(object):
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.load_depth = 0

    def find_module(self, fullname, path=None):
        if fullname in module_bundle:
            return self
        return None

    def debug(self, message):
        if self.verbose:
            print " "*self.load_depth + message

    def load_module(self, fullname):  # PEP302 dictates a lot of this behavior
        self.debug('loading module: ' + fullname)
        self.load_depth += 1
        try:
            try:
                module_is_package, module_code = module_bundle[fullname]
            except Exception:
                self.debug('unknown module: ' + fullname)
                raise ImportError

            remove_on_fail = fullname not in sys.modules

            module = sys.modules.setdefault(fullname, imp.new_module(fullname))
            module.__file__ = "<bundled: " + fullname + ">"
            module.__loader__ = self
            if module_is_package:
                module.__path__ = []
                module.__package__ == fullname
            else:
                module.__package__ == fullname.rpartition('.')[0]

            try:
                try:
                    exec module_code in module.__dict__
                except Exception, e:
                    self.debug('load failure: ' + fullname + ' - ' + repr(e))
                    raise ImportError()

                # Attempt to patch if a patch is provided
                try:
                    import patches  # Late import needed so we've already installed this loader hook
                    patch_code = patches.get_patch_code(fullname)
                    if patch_code:
                        self.debug("patching " + fullname)
                        patch = types.FunctionType(patch_code, globals(), "patch")
                        patch(module)
                except Exception, e:
                    self.debug('patch failure: ' + fullname + ' - ' + repr(e))
                    raise ImportError()

            except Exception:
                if remove_on_fail:
                    del sys.modules[fullname]
                    self.debug('removing from sys.modules: ' + fullname)
                raise

            return module

        finally:
            self.load_depth -= 1


sys.meta_path.insert(0, BundleImporter())
"""


def get_dependencies_for_script_name(script_name):
    script_dir = os.path.dirname(os.path.abspath(script_name))
    tracker = PyInstaller.depend.imptracker.ImportTracker(xpath=[script_dir,])

    dependencies = {}
    dependency_names = tracker.analyze_script(script_name)
    for name in dependency_names:
        dependency = tracker.modules[name]
        try:
            if 'site-packages' in dependency.__file__ or 'python2' not in dependency.__file__: # TODO: better way?
                dependencies[name] = (dependency.ispackage(), dependency.co)
        except Exception:
            pass

    # Fix-up script's own entry to have a more informative name
    script_entry = dependencies.pop('__main__')
    if script_entry:
        name = os.path.splitext(os.path.basename(script_name))[0]
        dependencies[name] = script_entry

    return dependencies


def main(outfile, script_names):
    dependencies = {}
    for script_name in script_names:
        dependencies.update(get_dependencies_for_script_name(script_name))

    # Create datafiles module for dependencies
    for dependency_name, dependency in dependencies.iteritems():
        data_bundler.update_data_bundle_for_module(dependency_name)
    data_bundler.close_data_bundle_file()

    # Setup data_bundle module for inclusion in bundle
    dependencies.update(get_dependencies_for_script_name(data_bundler.DATA_BUNDLE_MODULE_NAME))
    data_bundler.remove_data_bundle_file()
    
    # Setup patches for inclusion in bundle
    dependencies.update(get_dependencies_for_script_name(patches.__file__.replace('.pyc', '.py')))

    sys.stderr.write("Included modules:\n%s\n\n" % '\n'.join(sorted(dependencies.keys())))
    sys.stderr.flush()

    marshaled_bundle = marshal.dumps(dependencies)
    compressed_bundle = zlib.compress(marshaled_bundle)
    bundle = base64.encodestring(compressed_bundle)

    outfile.write(BUNDLE_IMPORTER_TEMPLATE % dict(magic_number=imp.get_magic(),
                                                  base64_bundle=bundle))
    outfile.close()


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.description = "Create a python script that will setup bundled dependency imports for the specified scripts"
    argparser.add_argument('--outfile', '-o', default='-', type=argparse.FileType('wb'),
                           help="the filename to user for writing the output python module (default: '%(default)s')")
    argparser.add_argument("script_names", nargs="+", metavar="SCRIPT",
                           help="the script filenames to be processed for dependencies")

    args = argparser.parse_args()
    main(args.outfile, args.script_names)
