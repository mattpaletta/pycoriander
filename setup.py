import inspect
import os
import shutil
import subprocess
import tempfile
from distutils.command.build import build
from shutil import copytree, copyfile

from setuptools.command.install import install

try:
    from setuptools import setup, find_packages
except ImportError:
    import ez_setup

    ez_setup.use_setuptools()
    from setuptools import setup, find_packages


def _get_package_resources():
    x = [os.path.join(dp, f).replace("coriander/", "") for dp, dn, filenames in os.walk(local_resources_dir) for f in filenames]
    print("Got {0} Resources".format(len(x)))
    return x


local_resources_dir = "coriander/resources"
target_resources_dir = os.path.expanduser("~/.coriander")
# target_resources_dir = os.path.join("coriander/resources/lib")
package_filenames = _get_package_resources()
print(package_filenames)


def _get_target_source_dirs(coriander_dir):
    coriander_build_dir = target_resources_dir  # os.path.join(coriander_dir, "release")

    local_bin_dir = os.path.join(local_resources_dir, "bin")
    if not os.path.exists(local_bin_dir):
        os.mkdir(local_bin_dir)

    target_paths = [
        # os.path.join(target_resources_dir, "bin"),
        # os.path.join(target_resources_dir, "lib"),
        # os.path.join(target_resources_dir, "include"),
        # os.path.join(target_resources_dir, "soft/llvm-4.0"),
        # os.path.join(target_resources_dir, "share", "cocl"),
        os.path.join(local_resources_dir, "bin", "ir-to-opencl")
    ]

    source_paths = [
        # os.path.join(coriander_build_dir, "bin"),
        # os.path.join(coriander_build_dir, "lib"),
        # os.path.join(coriander_build_dir, "include"),
        # os.path.join(coriander_build_dir, "soft/llvm-4.0"),
        # os.path.join(coriander_build_dir, "share", "cocl"),
        os.path.join(coriander_dir, "build", "ir-to-opencl")
    ]

    return target_paths, source_paths, coriander_build_dir


def _does_need_to_compile(coriander_dir):
    target_paths, _, _ = _get_target_source_dirs(coriander_dir)
    num_missing = len(target_paths) - sum(map(int, map(os.path.exists, target_paths)))
    print("Missing: {0} files".format(num_missing))
    return num_missing


def compile_coriander(coriander_dir):
    # Run cmake
    target_paths, source_paths, coriander_build_dir = _get_target_source_dirs(coriander_dir)
    did_compile = _does_need_to_compile(coriander_dir)

    # Found missing files, so compile it.
    if did_compile:
        print("Compiling coriander")
        if os.path.exists(coriander_build_dir):
            shutil.rmtree(coriander_build_dir, ignore_errors = True)

        proc = subprocess.run(["python2 install_distro.py --install-dir " + coriander_build_dir],
                          cwd = coriander_dir,
                          shell = True,
                          stdout = subprocess.PIPE)
        if proc.returncode != 0:
            list(map(print, str(proc.stdout).split("\n")))
            exit(proc.returncode)
    else:
        print("Coriander already compiled, skipping recompile")

    print("Copying output")
    for src, dest in zip(source_paths, target_paths):
        # Check to make sure we're copying the right part
        src_tail = src.split("/")[-1]
        dest_tail = dest.split("/")[-1]

        assert src_tail == dest_tail, "invalid matching of copying"

        if not os.path.exists(dest):
            if os.path.isfile(src):
                copyfile(src = src, dst = dest)
            else:
                copytree(src = src, dst = dest)

    # print("Monkey patching")
    # copyfile(src = "coriander/resources/cocl_env_replace.py", dst = os.path.join(target_resources_dir, "cocl_env.py"))

    global package_filenames
    if did_compile or len(package_filenames) == 0:
        # Re-grab the new package resources.
        package_filenames = _get_package_resources()


def get_and_build_coriander():
    tmp_repo = os.path.join(tempfile.gettempdir(), "coriander")
    print("Only cloning if needs a compile")
    should_compile = _does_need_to_compile(tmp_repo)

    if should_compile and not os.path.exists(tmp_repo):
        print("Cloning repo")
        from git import Repo

        Repo.clone_from("https://github.com/hughperkins/coriander.git",
                        to_path = tmp_repo,
                        recursive = True)
    else:
        print("Does not need to re-clone repo")
    compile_coriander(tmp_repo)


class BuildCommand(build):
    def run(self):
        get_and_build_coriander()
        build.run(self)


class InstallCommand(install):
    def run(self):
        # Only build if
        if not os.path.exists(target_resources_dir) or len(package_filenames) == 0:
            get_and_build_coriander()
        if not self._called_from_setup(inspect.currentframe()):
            # Run in backward-compatibility mode to support bdist_* commands.
            install.run(self)
        else:
            install.do_egg_install(self)  # OR: install.do_egg_install(self)


# Requires cmake
setup(
    name="pycoriander",
    version="0.0.1",
    url='https://github.com/mattpaletta/pycoriander',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['pyopencl'],
    setup_requires=["gitpython"],
    author="Matthew Paletta",
    author_email="mattpaletta@gmail.com",
    description="Python bindings for coriander",
    license="BSD",
    zip_safe=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Communications',
    ],
    cmdclass = {
        'build': BuildCommand,
        'install': InstallCommand,
    },
    package_data = {'coriander': package_filenames}
)