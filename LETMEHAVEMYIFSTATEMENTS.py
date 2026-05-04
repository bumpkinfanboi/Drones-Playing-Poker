import sys
import time
import typing
import inspect as _inspect
import traceback
from functools import wraps  # wraps copies the original function's name/doc into the wrapper


def _short_repr(value, limit=100):
    # turns any value into a string safely and cuts it if it's too long
    try:
        text = repr(value)
    except Exception:
        return "<unrepr>"
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _ms_since(start):
    # returns milliseconds elapsed since the given perf_counter() start
    return (time.perf_counter() - start) * 1000


class _TimedContext:
    # object returned by Util.Timed("label") so it works with the "with" statement
    __slots__ = ("label", "_start")

    def __init__(self, label):
        self.label = label

    def __enter__(self):
        self._start = time.perf_counter()  # perf_counter is the most precise clock in python
        return self

    def __exit__(self, exc_type, exc, tb):
        print(f"[Timed] {self.label}: {_ms_since(self._start):.3f} ms")


class Util:
    @staticmethod
    def InputError(
        Message=None,
        InputType=int,
        ErrorMessage="The input is invalid because",
        Symbol=":",
    ):
        # validate the options the caller passed in
        if not isinstance(ErrorMessage, str):
            raise TypeError("ErrorMessage must be a string")
        if not isinstance(Symbol, str):
            raise TypeError("Symbol must be a string")
        if not (isinstance(InputType, type) and issubclass(InputType, (int, float, str))):
            raise TypeError("InputType must be int, float, or str")

        # build a default prompt if none was provided
        if Message is None:
            Message = f"Enter a {InputType.__name__}{Symbol} "
        elif not isinstance(Message, str):
            raise TypeError("Message must be a string")
        elif not Message.rstrip().endswith(Symbol):  # rstrip removes the spaces at the right and then check if ends with the symbol
            Message = f"{Message.rstrip()}{Symbol} "

        # keep asking until the user types something valid
        while True:
            try:
                return InputType(input(Message))
            except (ValueError, TypeError) as error:
                print(f"{ErrorMessage} {error}")

    @staticmethod
    def Timed(target):
        # dual use: @Util.Timed on a function, OR  with Util.Timed("label"):
        if isinstance(target, str):
            return _TimedContext(target)

        func = target
        name = func.__qualname__  # cached once so the wrapper doesn't look it up every call

        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                # "finally" runs even if the function raises, so we always print the time
                print(f"[Timed] {name}: {_ms_since(start):.3f} ms")

        return wrapper

    @staticmethod
    def TypeCheck(func):
        # read the type hints once when the decorator is applied (not on every call)
        hints = typing.get_type_hints(func)
        if not hints:
            return func  # nothing to check, return the function untouched (zero overhead)

        sig = _inspect.signature(func)
        qualname = func.__qualname__
        return_hint = hints.pop("return", None)  # separate return type from argument types

        # pre-compute each argument's accepted python types so we don't re-parse on every call
        checks = {}
        for arg_name, expected in hints.items():
            origin = typing.get_origin(expected)
            if origin is typing.Union:
                # Union[int, str] -> accept any of (int, str)
                accepted = tuple(a for a in typing.get_args(expected) if isinstance(a, type))
            elif isinstance(origin, type):
                accepted = (origin,)  # e.g. list[int] -> accept list
            elif isinstance(expected, type):
                accepted = (expected,)
            else:
                accepted = ()  # hint we can't check (like a TypeVar) -> skip
            if accepted:
                checks[arg_name] = (accepted, expected)

        ret_check = None
        if return_hint is not None:
            origin = typing.get_origin(return_hint)
            if origin is typing.Union:
                accepted = tuple(a for a in typing.get_args(return_hint) if isinstance(a, type))
            elif isinstance(origin, type):
                accepted = (origin,)
            elif isinstance(return_hint, type):
                accepted = (return_hint,)
            else:
                accepted = ()
            if accepted:
                ret_check = (accepted, return_hint)

        @wraps(func)
        def wrapper(*args, **kwargs):
            bound = sig.bind(*args, **kwargs)  # match args/kwargs to parameter names
            bound.apply_defaults()              # fill in default values for anything missing
            for arg_name, value in bound.arguments.items():
                check = checks.get(arg_name)
                if check is not None and not isinstance(value, check[0]):
                    raise TypeError(
                        f"{qualname}: '{arg_name}' expected {check[1]}, got {type(value).__name__}"
                    )
            result = func(*args, **kwargs)
            if ret_check is not None and not isinstance(result, ret_check[0]):
                raise TypeError(
                    f"{qualname}: return expected {ret_check[1]}, got {type(result).__name__}"
                )
            return result

        return wrapper

    @staticmethod
    def Inspect(obj):
        # print a neat summary of any python object
        out = [
            f"=== Inspect: {type(obj).__name__} ===",
            f"Repr:   {_short_repr(obj, 200)}",
            f"Id:     {hex(id(obj))}",  # unique memory address, useful to tell two objects apart
        ]
        try:
            out.append(f"Size:   {sys.getsizeof(obj)} bytes")
        except TypeError:
            pass  # some objects don't support getsizeof, ignore

        doc = _inspect.getdoc(obj)
        if doc:
            out.append(f"Doc:    {doc.splitlines()[0]}")  # show only the first docstring line

        attrs, methods = [], []
        for name in dir(obj):
            if name.startswith("_"):  # hide private/dunder stuff like __init__
                continue
            try:
                value = getattr(obj, name)
            except Exception as e:
                attrs.append((name, f"<error: {e}>"))
                continue
            (methods if callable(value) else attrs).append((name, value))

        if attrs:
            out.append("Attributes:")
            for name, value in attrs:
                out.append(f"  {name} = {_short_repr(value, 80)}")

        if methods:
            out.append("Methods:")
            for name, value in methods:
                try:
                    sig = str(_inspect.signature(value))  # shows the method's parameters
                except (TypeError, ValueError):
                    sig = "(...)"  # builtins often don't expose a signature
                out.append(f"  {name}{sig}")

        # one single print is faster than many -- less flushing to the terminal
        print("\n".join(out))

    @staticmethod
    def Debug(func):
        name = func.__qualname__  # cache once

        @wraps(func)
        def wrapper(*args, **kwargs):
            # build a readable "func(a, b, k=v)" string for the log line
            parts = [repr(a) for a in args]
            parts.extend(f"{k}={v!r}" for k, v in kwargs.items())
            print(f"[Debug] -> {name}({', '.join(parts)})")

            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                elapsed = _ms_since(start)
                print(f"[Debug] !! {name} raised {type(e).__name__}: {e}  ({elapsed:.3f} ms)")

                # walk down the traceback to the deepest frame = where it actually crashed
                tb = sys.exc_info()[2]
                while tb is not None and tb.tb_next is not None:
                    tb = tb.tb_next
                if tb is not None:
                    print("[Debug]    locals at failure:")
                    # dump every local variable so you can see the state at crash time
                    for var_name, value in tb.tb_frame.f_locals.items():
                        print(f"[Debug]      {var_name} = {_short_repr(value)}")

                traceback.print_exc()
                raise  # re-raise so the caller still sees the error

            elapsed = _ms_since(start)
            print(f"[Debug] <- {name} = {_short_repr(result)}  ({elapsed:.3f} ms)")
            return result

        return wrapper
