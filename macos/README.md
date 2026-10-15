# Native macOS packaging

Developer: **Caimankekw**. Authored source is AGPL-3.0-only. See the root LICENSE,
NOTICE and DISCLAIMER documents for scope and limitations.

This layer packages the already reviewed firmware in the corresponding stock
macOS updater. It does not alter camera, HSS, radio or AIR2 firmware logic. The
transport HEX is extracted from the pinned published Windows updater, and is
byte-identical across the Mac and Windows packages for that release.

`model.json` binds one model, the supplied stock Mac ZIP, the reviewed Windows
portable package, their exact members, and the original app/resource hashes.
The full corresponding-source ZIP has an externally supplied SHA256 to avoid
a circular self-hash. Every source member is checked against both its manifest
and the clean tracked checkout at the requested Git commit.

## Build

Use macOS 11 or newer with Python 3.9+, Git and Apple's `hdiutil`, `ditto`, and
`codesign`. The GitHub workflow uses `macos-15-intel`. No updater is executed.

```sh
python3 -B -m unittest discover -s macos -p 'test_*.py' -v
python3 -B macos/build_package.py \
  --stock-maczip /path/to/pinned-stock-mac.zip \
  --windows-package /path/to/pinned-windows-portable.zip \
  --source-archive /path/to/corresponding-source.zip \
  --source-sha256 VERIFIED_SOURCE_SHA256 \
  --source-commit FULL_GIT_COMMIT \
  --output /path/to/new-output-directory
```

Output directories must be new. Build work, signed candidate apps and logs are
retained; the builder does not delete existing files. The source checkout must
be clean. Downloaded assets and generated output belong outside the checkout.

## Preserved behavior and signing

The stock app is mounted read-only and copied with `ditto`. Only its firmware
resource is replaced. Info.plist, helper bytes, UI assets, executable permissions
and other resources must remain identical. The original updater name inside the
app is retained; custom attribution appears on the DMG and in accompanying docs.

Changing a sealed resource invalidates the vendor's outer signature. The builder
ad-hoc signs only the outer app, without `--deep`, preserving the helper and its
signature. The main executable's old/new bytes are compared after normalizing
only its embedded signature and associated allocation metadata. Its code and
other linkage data must remain unchanged. `codesign --verify --deep --strict`,
native DMG mounting, and final readback must all succeed.

The custom app has no Developer ID signature or notarization. Ad-hoc signature
validity is not Gatekeeper approval or a guarantee that the original GUI runs on
every Mac. The x86_64 GUI may need Rosetta 2 on Apple Silicon. Hardware startup,
USB flashing and photographic behavior are not validated by this build.

The final ZIP contains the custom APFS/UDZO DMG, unchanged original recovery DMG,
vendor FAQ/license, bilingual docs and disclaimers, AGPL license, corresponding
source, SHA256 inventory and the static verification report. Recovery is not
guaranteed. CI has read-only repository permissions and only uploads build
artifacts; publication requires separate review.
