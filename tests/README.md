# Offline verification

English | [简体中文](README.zh-CN.md)

Run from the repository root with Python 3.9+; no pip dependencies or device are needed:

```console
python -I -B tests/test_reference_codec.py -v
python -I -B tests/test_container.py --original "path/to/C11.exe" -v
python -I -B tests/test_build.py --original "path/to/C11.exe" -v
python -I -B tests/test_isolated_build.py --original "path/to/C11.exe"
```

The first three suites cover 7 codec, 13 container and 13 source-build/boundary cases. Official-input tests explicitly skip if that input is omitted. The final test copies the source closure to a fresh temporary directory and runs Python with `-I`; its file-access audit rejects reads outside that copy, the explicit official EXE and the Python installation. Scratch directories are retained. The vendor updater is read as data, never executed; these tests do not access USB.

[VERIFICATION.json](VERIFICATION.json) separates two records:

- `current_fix1.frozen_candidate_report` is a complete copy of the frozen FIX1 release verification report. Its source archive hash identifies the earlier 35-file input ZIP, not the newly integrated release source ZIP. Firmware and updater hashes bind the reported results to FIX1.
- `historical_p8.report` preserves the old P8 standalone verification unchanged. Its hashes, source inventory and pass results belong to P8 and do not certify FIX1 or its new packaging.

The frozen FIX1 report records UI 470, radio 1,944, persistence 717, integration 333 and native idle-expiry 77 cases, plus the 33 standalone checks above and an isolated rebuild. The 77 expiry cases include 24 frozen-P8 failure controls. The development-only `verify_idle_expiry.py` and full behavioral regressions require the surrounding reverse-engineering workspace and are not included in this compact source ZIP. Report fingerprints preserve their evidence identity; they are not a claim that the compact package contains those harnesses.

FIX1 has not been booted or tested with a camera on hardware. Replay uses bounded clock, UART, Flash and LCD models, not a complete MCU/ISR or physical RF model. These checks do not establish hardware boot, physical key-rate capacity, RF reception, exposure or power-loss behavior. HSS-P3 bytes are unchanged; the old P8 HSS totals do not represent a new FIX1 HSS replay or physical measurement.
