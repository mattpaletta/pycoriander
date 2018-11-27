import os
from pip._vendor.pkg_resources import resource_filename

_resource_dir = resource_filename("coriander", "resources/bin")

COCL_IR_TO_CL = os.path.join(_resource_dir, "ir-to-opencl")
# CLANG_HOME = os.path.join(_resource_dir, 'soft/llvm-4.0')
COCL_PATH = os.path.join(os.path.expanduser("~/.coriander"), 'bin', 'cocl_py')
# COCL_CMAKE_DIR = os.path.join(_resource_dir, 'share', "cocl")
# COCL_BIN = os.path.join(_resource_dir, 'bin')
# COCL_LIB = os.path.join(_resource_dir, 'lib')
# COCL_INCLUDE = os.path.join(_resource_dir, 'include')
# COCL_INSTALL_PREFIX = os.path.join(_resource_dir)
# PYTHON27_PATH = sys.executable.split("/")[-1]