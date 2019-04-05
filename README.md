# DirectSync

[![PyPI version](https://badge.fury.io/py/directsync.svg)](https://badge.fury.io/py/directsync)
![MIT License](https://img.shields.io/badge/license-MIT-green.svg)
[![image](https://img.shields.io/badge/Say%20Thanks-!-1EAEDB.svg)](https://saythanks.io/to/Anmol-Singh-Jaggi)
[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2FAnmol-Singh-Jaggi%2Fdirectsync.svg?type=shield)](https://app.fossa.io/projects/git%2Bgithub.com%2FAnmol-Singh-Jaggi%2Fdirectsync?ref=badge_shield)

An efficient and easy-to-use utility to compare/synchronize/mirror folder contents.

**Demo**

![Demo gif](https://github.com/Anmol-Singh-Jaggi/directsync/raw/master/docs/demo.gif)

**Usage:**

    directsync [-h] [-add] [-rm] [-ovr] [-rev] [-mirr] [-trash] [-cache]
               [-dry] [-no-bar]
               left-path right-path

    positional arguments:
    left-path             The path of the left(source) directory.
    right-path            The path of the right(destination) directory.

    optional arguments:
      -h, --help            show this help message and exit
      -add, --add-missing   Copy files from source which are absent in
                            destination.
      -rm, --remove-extra   Remove the files from destination which are absent in
                            source.
      -ovr, --overwrite-content
                            Overwrite the files having same name but different
                            content.
      -rev, --reverse-sync-direction
                            Use the right folder as source and the left as
                            destination.
      -mirr, --mirror-contents
                            Make the destination directory exactly same as the
                            source. Shorthand for `-add -rm -ovr`.
      -trash, --use-trash   Send to trash/recycle bin while deleting/overwriting.
      -cache, --use-cache   Whether to use previously cached comparison-check
                            result from disk.
      -dry, --dry-run       Just simulate and report the file operations that will
                            be performed with the current configuration.
      -no-bar, --hide-progress-bar
                            Whether to hide the progress bar or not. Will result
                            in a huge speedup iff the 2 directories are structured
                            very differently.

**Installation:**
 - `pip install directsync`

**ToDo:**
 - Add `preserve-latest` option: Among the 2 files, the one with the latest modification date should be preserved.
 - Give more fine-tuned control of file comparison algorithm to the user.
 - Add `ignore-pattern` option to let the user ignore certain files based on the regex pattern provided.
 - Add test cases.
 - Add code coverage.
 - Setup `tox` and `Travis CI`.
 - Add coloured output.
 - Handle nested structures with symlinks.
 - Provide direct interface with online storage services.
 - Add developer guidelines.
 - ~~Add demo.~~
 - ~~Add `simulate` option.~~
 - ~~Add `use-trash` option to send to recycle bin instead of delete/overwrite.~~
 - ~~Add `cache` option to cache the results of the previous difference check to disk.~~

## License
[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2FAnmol-Singh-Jaggi%2Fdirectsync.svg?type=large)](https://app.fossa.io/projects/git%2Bgithub.com%2FAnmol-Singh-Jaggi%2Fdirectsync?ref=badge_large)