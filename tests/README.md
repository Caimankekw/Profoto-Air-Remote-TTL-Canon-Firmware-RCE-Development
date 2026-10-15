# Offline verification

Run from the repository root with Python 3.9+; no pip dependencies or device:

```console
python -I -B tests/test_reference_codec.py -v
python -I -B tests/test_container.py --original "path/to/C11.exe" -v
python -I -B tests/test_build.py --original "path/to/C11.exe" -v
python -I -B tests/test_isolated_build.py --original "path/to/C11.exe"
```

The first three suites cover 7 codec, 13 container and 13 source-build/boundary
cases. Official-input tests explicitly skip if that input is omitted. The last
test copies the source closure to a fresh temporary directory and runs Python
with `-I`; its file-access audit rejects reads outside that copy, the explicit
official EXE and the Python installation. Scratch directories are retained.

These checks establish source/output equivalence and packaging boundaries, not
physical hardware behavior. Earlier bounded P8 emulation validated the same
frozen image; the full historical VM/evidence workspace is not a build dependency
and is deliberately absent from this concise source package.
