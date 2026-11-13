# Changelog

Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html) (`<major>`.`<minor>`.`<patch>`)

## `[v1.1.0]`

### Changed

* `--extensions`, `--app-exclude`, and `--core-exclude` now take a single comma-separated value (e.g. `--app-exclude=Application,Company`) rather than space-separated values
* Extension and tag values are now validated; invalid values exit with an error

### Fixed

* Fix incorrect default `core.xml` tag; `"creator"` is the correct tag, rather than `"Creator"`
* Fix `--extensions`, `--app-exclude`, and `--core-exclude` consuming the filenames passed by pre-commit, which caused the hook to silently check no files
* Report non-zip (e.g. password-protected) and malformed Office files as errors rather than raising an unhandled exception
* Fix metadata XML being decoded using the system locale encoding rather than the encoding declared in the file

## `[v1.0.0]`

Initial release 🎉
