import os
import subprocess
import tempfile
from difflib import SequenceMatcher
import pyopencl as cl

from coriander.resources.cocl_env_replace import COCL_PATH, COCL_BIN, COCL_LIB, COCL_IR_TO_CL, CLANG_HOME, \
    COCL_CMAKE_DIR, COCL_INCLUDE

try:
    import pycuda.driver as cuda
    cuda_available = True
except ImportError:
    cuda_available = False


# TODO:// If cuda is available, return the cuda kernel, otherwise, compile to opencl and return that.

def cu_to_cl(context, cu_filepath, kernelname, num_args):
    ll_sourcecode = _cu_to_ll(cu_filepath)

    # This is the name of the function in the IR.
    defines = []
    for line in ll_sourcecode.split('\n'):
        if line.startswith("define"):
            define_mangled_name = line.split('@')[1].split('(')[0]
            defines.append(define_mangled_name)

    # TODO:// Get closest name when names are subsets of each other.
    mangled_dist = list(zip(defines, list(
        map(lambda func: SequenceMatcher(None, func, kernelname, autojunk = False).ratio(), defines))))
    mangled_dist.sort(key = lambda x: x[1])

    mangledname = mangled_dist[-1][0]  # Grab the minimum one, and from there, grab the name.
    print(mangled_dist)

    assert mangledname is not None, "Could not find function: " + kernelname

    print('mangledname', mangledname)

    # Count the number of arguments to function...
    cl_code = _cu_to_cl(cu_filepath, mangledname, num_clmems = num_args)
    print('got cl_code')

    kernel = _build_kernel(context, cl_code, mangledname)
    print('after build kernel')
    return kernel


def _get_cocl_path():
    env = os.environ
    # export CLANG_HOME=/tmp/coriander/release/soft/llvm-4.0
    # export COCL_PATH=/tmp/coriander/release/bin/cocl.py
    # export COCL_CMAKE_DIR=/tmp/coriander/cmake
    # export COCL_BIN=/tmp/coriander/release/bin
    # export COCL_LIB=/tmp/coriander/release/lib
    # export COCL_INCLUDE=/tmp/coriander/release/include
    # export PYTHON27_PATH=/usr/local/bin/python2
    env["CLANG_HOME"] = CLANG_HOME
    env['COCL_PATH'] = COCL_PATH
    # env['COCL_CMAKE_DIR'] = COCL_CMAKE_DIR
    env['COCL_BIN'] = COCL_BIN
    env['COCL_LIB'] = COCL_LIB
    env['COCL_INCLUDE'] = COCL_INCLUDE
    return COCL_PATH, env


def _cu_to_ll(cu_source_file):
    cocl_path, env = _get_cocl_path()

    new_file, filename = tempfile.mkstemp()
    os.close(new_file)

    device_ll = filename + "-device.ll"

    _run_process([
        'python2',
        cocl_path,
        '-c',
        cu_source_file,
        '-o',
        filename
    ], env = env)

    with open(device_ll, "r") as f:
        ll_sourcecode = "\n".join(f.readlines())
    return ll_sourcecode


def _cu_to_cl(cu_source_file, kernelName, num_clmems):
    assert num_clmems > 0, "Function must accept 1 parameter"
    clmemIndexes = ','.join(map(str, range(num_clmems)))

    cocl_path, env = _get_cocl_path()

    new_file, filename = tempfile.mkstemp()
    os.close(new_file)

    device_ll = filename + "-device.ll"
    device_cl = filename + "-device.cl"

    _run_process([
        'python2',
        cocl_path,
        '-c',
        cu_source_file,
        '-o',
        filename
    ], env = env)

    _run_process([
        COCL_IR_TO_CL,
        '--inputfile', device_ll,
        '--outputfile', device_cl,
        '--kernelname', kernelName,
        '--cmem-indexes', clmemIndexes,
        '--add_ir_to_cl'
    ])

    with open(device_cl, 'r') as f:
        cl_sourcecode = "\n".join(f.readlines())
    return cl_sourcecode


def _build_kernel(context, cl_sourcecode, kernelName):
    print('building sourcecode')
    print('cl_sourcecode', cl_sourcecode)
    prog = cl.Program(context, cl_sourcecode).build()
    print('built prog')
    for kernel in prog.all_kernels():
        if kernel.function_name == kernelName:
            return kernel


def _run_process(cmdline_list, cwd = None, env = None):
    print('running [%s]' % ' '.join(cmdline_list))
    fout = open('/tmp/pout.txt', 'w')
    res = subprocess.run(cmdline_list, stdout = fout, stderr = subprocess.STDOUT, cwd = cwd, env = env)
    fout.close()
    with open('/tmp/pout.txt', 'r') as f:
        output = f.read()
    if res.returncode != 0:
        print(output)
        exit(1)
    return output
