from collections import namedtuple
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parents[2]))

from pyodide_build.pywasmcross import handle_command  # noqa: E402
from pyodide_build.pywasmcross import f2c  # noqa: E402


def _args_wrapper(func):
    """Convert function to take as input / return a string instead of a
    list of arguments

    Also sets dryrun=True
    """

    def _inner(line, *pargs):
        args = line.split()
        res = func(args, *pargs, dryrun=True)
        if hasattr(res, "__len__"):
            return " ".join(res)
        else:
            return res

    return _inner


handle_command_wrap = _args_wrapper(handle_command)
f2c_wrap = _args_wrapper(f2c)


def test_handle_command():
    Args = namedtuple("args", ["cflags", "cxxflags", "ldflags", "host", "replace_libs"])
    args = Args(cflags="", cxxflags="", ldflags="", host="", replace_libs="")
    assert handle_command_wrap("gcc -print-multiarch", args) is None
    assert handle_command_wrap("gcc test.c", args) == "emcc test.c"
    assert (
        handle_command_wrap("gcc -shared -c test.o -o test.so", args)
        == "emcc -shared -c test.o -o test.wasm"
    )

    # check cxxflags injection and cpp detection
    args = Args(
        cflags="-I./lib2",
        cxxflags="-std=c++11",
        ldflags="-lm",
        host="",
        replace_libs="",
    )
    assert (
        handle_command_wrap("gcc -I./lib1 test.cpp -o test.o", args)
        == "em++ -I./lib2 -std=c++11 -I./lib1 test.cpp -o test.o"
    )

    # check ldflags injection
    args = Args(cflags="", cxxflags="", ldflags="-lm", host="", replace_libs="")
    assert (
        handle_command_wrap("gcc -shared -c test.o -o test.so", args)
        == "emcc -lm -shared -c test.o -o test.wasm"
    )

    # check library replacement
    args = Args(cflags="", cxxflags="", ldflags="", host="", replace_libs="bob=fred")
    assert (
        handle_command_wrap("gcc -shared -c test.o -lbob -o test.so", args)
        == "emcc -shared -c test.o -lfred -o test.wasm"
    )

    # compilation checks in numpy
    assert handle_command_wrap("gcc /usr/file.c", args) is None


def test_f2c():
    assert f2c_wrap("gfortran test.f") == "gfortran test.c"
    assert f2c_wrap("gcc test.c") is None
    assert f2c_wrap("gfortran --version") is None
    assert (
        f2c_wrap("gfortran --shared -c test.o -o test.so")
        == "gfortran --shared -c test.o -o test.so"
    )


def test_conda_compiler_compat():
    Args = namedtuple("args", ["cflags", "cxxflags", "ldflags", "host", "replace_libs"])
    args = Args(cflags="", cxxflags="", ldflags="", host="", replace_libs="")
    assert handle_command_wrap(
        "gcc -shared -c test.o -B /compiler_compat -o test.so", args
    ) == ("emcc -shared -c test.o -o test.wasm")
