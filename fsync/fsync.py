#!/usr/bin/env python3
import argparse
import hashlib
from pathlib import Path
import shutil
import os

from tqdm import tqdm


class DirData:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self.diff = []


class DirsData:
    def __init__(self, path_left, path_right):
        # The items present in left but absent in right.
        self.data_left = DirData(path_left)
        # The items present in right but absent in left.
        self.data_right = DirData(path_right)
        # The items present on either side but with different contents(hash).
        self.hash_diff = []


class FSync:
    def __init__(self, dir_path_left, dir_path_right, progress_bar=False):
        self.dirs_data = DirsData(dir_path_left, dir_path_right)
        self.progress_bar = progress_bar
        if not self.dirs_data.data_left.path.is_dir():
            error_msg = 'Left path "{}" is not a valid directory!'
            error_msg = error_msg.format(self.dirs_data.data_left.path)
            raise Exception(error_msg)
        if not self.dirs_data.data_right.path.is_dir():
            error_msg = 'Right path "{}" is not a valid directory!'
            error_msg = error_msg.format(self.dirs_data.data_right.path)
            raise Exception(error_msg)

    def _is_file_text(self, file_path):
        try:
            with open(file_path, "rt") as f:
                f.read(3)
            return True
        except UnicodeDecodeError:
            return False

    def _are_files_equal(self, path_left, path_right):
        # First check the file sizes.
        left_size = path_left.stat().st_size
        right_size = path_right.stat().st_size
        if left_size != right_size:
            return False
        if not self._is_file_text(path_left):
            if left_size > 1000000:
                return True
        contents = path_left.read_bytes()
        left_hash = hashlib.md5(contents).digest()
        contents = path_right.read_bytes()
        right_hash = hashlib.md5(contents).digest()
        return left_hash == right_hash

    def _compare_subfiles(self, left_dir_contents, right_dir_contents):
        left_files = [x for x in left_dir_contents if x.is_file()]
        right_files = [x for x in right_dir_contents if x.is_file()]

        left_iterator = 0
        right_iterator = 0

        while left_iterator < len(left_files) and right_iterator < len(
                right_files):
            self._mark_file_visit()
            left_entry = left_files[left_iterator]
            right_entry = right_files[right_iterator]
            left_entry_name = left_entry.name
            right_entry_name = right_entry.name
            if left_entry_name == right_entry_name:
                are_files_same = self._are_files_equal(left_entry, right_entry)
                if not are_files_same:
                    self.dirs_data.hash_diff.append((left_entry, right_entry))
                left_iterator += 1
                right_iterator += 1
                self._mark_file_visit()
            elif Path(left_entry_name) < Path(right_entry_name):
                self.dirs_data.data_left.diff.append(left_entry)
                left_iterator += 1
            else:
                self.dirs_data.data_right.diff.append(right_entry)
                right_iterator += 1

        while left_iterator < len(left_files):
            left_entry = left_files[left_iterator]
            self.dirs_data.data_left.diff.append(left_entry)
            left_iterator += 1
            self._mark_file_visit()

        while right_iterator < len(right_files):
            right_entry = right_files[right_iterator]
            self.dirs_data.data_right.diff.append(right_entry)
            right_iterator += 1
            self._mark_file_visit()

    def _compare_subdirs(self, left_dir_contents, right_dir_contents):
        left_subdirs = [x for x in left_dir_contents if x.is_dir()]
        right_subdirs = [x for x in right_dir_contents if x.is_dir()]
        # Directories (subdirectories) to explore next.
        next_subdirs = []

        left_iterator = 0
        right_iterator = 0

        while left_iterator < len(left_subdirs) and right_iterator < len(
                right_subdirs):
            self._mark_file_visit()
            left_entry = left_subdirs[left_iterator]
            right_entry = right_subdirs[right_iterator]
            left_entry_name = left_entry.name
            right_entry_name = right_entry.name
            if left_entry_name == right_entry_name:
                next_subdirs.append((left_entry, right_entry))
                left_iterator += 1
                right_iterator += 1
                self._mark_file_visit()
            elif Path(left_entry_name) < Path(right_entry_name):
                self.dirs_data.data_left.diff.append(left_entry)
                left_iterator += 1
            else:
                self.dirs_data.data_right.diff.append(right_entry)
                right_iterator += 1

        while left_iterator < len(left_subdirs):
            left_entry = left_subdirs[left_iterator]
            self.dirs_data.data_left.diff.append(left_entry)
            left_iterator += 1
            self._mark_file_visit()

        while right_iterator < len(right_subdirs):
            right_entry = right_subdirs[right_iterator]
            self.dirs_data.data_right.diff.append(right_entry)
            right_iterator += 1
            self._mark_file_visit()

        for dir_entry in next_subdirs:
            self._compare_dir_contents(dir_entry[0], dir_entry[1])

    def _compare_dir_contents(self, left_dir_path, right_dir_path):
        left_dir_contents = sorted([x for x in left_dir_path.iterdir()])
        right_dir_contents = sorted([x for x in right_dir_path.iterdir()])
        self._compare_subfiles(left_dir_contents, right_dir_contents)
        self._compare_subdirs(left_dir_contents, right_dir_contents)

    def check_differences(self):
        '''
        Checks and stores the differences between the sides
        '''
        # TODO: Handle recursive structures with symlinks.
        left_dir_path = self.dirs_data.data_left.path
        right_dir_path = self.dirs_data.data_right.path
        if self.progress_bar:
            left_dir_generator = left_dir_path.rglob('*')
            left_file_count_recursive = sum(1 for i in left_dir_generator)
            right_dir_generator = right_dir_path.rglob('*')
            right_file_count_recursive = sum(
                1 for i in right_dir_generator)
            total_files_count = left_file_count_recursive \
                + right_file_count_recursive
            self.progress_bar = tqdm(total=total_files_count,
                                     desc='Checking differences...')
        self._compare_dir_contents(left_dir_path, right_dir_path)
        if self.progress_bar:
            self.progress_bar.close()

    def _sync_items(self, item1, item2, overwrite=False):
        if item1.exists():
            if not overwrite and not item2.exists():
                if item1.is_dir():
                    shutil.copytree(item1, item2)
                else:
                    shutil.copyfile(item1, item2)
            elif overwrite:
                if item1.is_dir():
                    if item2.exists():
                        shutil.rmtree(item2)
                    shutil.copytree(item1, item2)
                else:
                    shutil.copyfile(item1, item2)

    def _remove_item(self, item):
        if item.exists():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    def sync_dirs(self, overwrite=False, add_missing=False,
                  remove_extra=False, reverse_direction=True):
        '''
        Copy all files to right not present there.
        `overwrite`: Whether to overwrite files whose content has changed.
        `add_missing`: Whether to copy files absent in the destination folder.
        `remove_extra`: Whether to remove files absent from the source folder.
        `direction`: If true, copies from left to right, otherwise in reverse.
        '''
        if self.progress_bar:
            total_files_count = 0
            if add_missing:
                total_files_count += len(self.dirs_data.data_left.diff) if\
                 not reverse_direction else len(self.dirs_data.data_right.diff)
            if remove_extra:
                total_files_count += len(self.dirs_data.data_right.diff) if\
                 not reverse_direction else len(self.dirs_data.data_left.diff)
            if overwrite:
                total_files_count += len(self.dirs_data.hash_diff)
            if total_files_count == 0:
                print('Directories already in sync!')
                return
            self.progress_bar = tqdm(total=total_files_count,
                                     desc='Syncing contents...')
        if add_missing:
            items_extra = self.dirs_data.data_left.diff if\
             not reverse_direction else self.dirs_data.data_right.diff
            for item_src in items_extra:
                src_base_path = self.dirs_data.data_left.path if\
                    not reverse_direction else self.dirs_data.data_right.path
                dst_base_path = self.dirs_data.data_right.path if\
                    not reverse_direction else self.dirs_data.data_left.path
                item_relative = item_src.relative_to(src_base_path)
                item_dst = dst_base_path / item_relative
                self._sync_items(item_src, item_dst, overwrite)
                self._mark_file_visit()
        if remove_extra:
            items_extra = self.dirs_data.data_right.diff if\
             not reverse_direction else self.dirs_data.data_left.diff
            for item in items_extra:
                self._remove_item(item)
                self._mark_file_visit()
        if overwrite:
            items_common = self.dirs_data.hash_diff
            for item in items_common:
                item_src = item[0] if not reverse_direction else item[1]
                item_dst = item[1] if not reverse_direction else item[0]
                self._sync_items(item_src, item_dst, True)
                self._mark_file_visit()
        if self.progress_bar:
            self.progress_bar.close()

    def _mark_file_visit(self):
        if not self.progress_bar:
            return
        self.progress_bar.update()

    def get_report(self):
        report_string = 'Left directory: "' + \
            str(self.dirs_data.data_left.path.resolve()) + '"\n'
        report_string += 'Right directory: "' + \
            str(self.dirs_data.data_right.path.resolve()) + '"\n\n'
        report_string += 'Comparison report:\n'
        report_string += '\n' + 'x' * 15 + '\n'
        report_string += 'Hashes different: (' + str(
            len(self.dirs_data.hash_diff)) + ')\n'
        for entry in self.dirs_data.hash_diff:
            report_string += '- ' + str(entry[0].relative_to(
                self.dirs_data.data_left.path)) + '\n'
        report_string += '-' * 15
        report_string += '\n\n' + '[' * 15 + '\n'
        report_string += 'Extra in left: (' + str(
            len(self.dirs_data.data_left.diff)) + ')\n'
        for entry in self.dirs_data.data_left.diff:
            report_string += '- ' + str(
                entry.relative_to(self.dirs_data.data_left.path)) + '\n'
        report_string += '-' * 15
        report_string += '\n\n' + ']' * 15 + '\n'
        report_string += 'Extra in right: (' + str(
            len(self.dirs_data.data_right.diff)) + ')\n'
        for entry in self.dirs_data.data_right.diff:
            report_string += '- ' + str(
                entry.relative_to(self.dirs_data.data_right.path)) + '\n'
        report_string += '-' * 15 + '\n\n'
        return report_string


def get_version():
    about = {}
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, '__version__.py')) as f:
        exec(f.read(), about)
    return about['__version__']


def prepare_args_parser():
    description = 'fsync: An efficient and easy-to-use utility to'
    description += ' compare/synchronize/mirror folder contents.\n'
    description += 'Version ' + str(get_version()) + '\n'
    epilog = 'Copyright (C) 2019 Anmol Singh Jaggi'
    epilog += '\nhttps://anmol-singh-jaggi.github.io'
    epilog += '\nMIT License'
    parser = argparse.ArgumentParser(
        description=description, prog='fsync', epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        'left-path', help='The path of the left(source) directory.')
    parser.add_argument(
        'right-path', help='The path of the right(destination) directory.')
    parser.add_argument(
        '-no-pro',
        '--hide-progress-bar',
        action='store_true',
        help='Whether to hide the progress bar or not.')
    parser.add_argument(
        '-add',
        '--add-missing',
        action='store_true',
        help='Copy files from source which are absent in destination.')
    parser.add_argument(
        '-remove',
        '--remove-extra',
        action='store_true',
        help='Remove the files from destination which are absent in source.')
    parser.add_argument(
        '-overwrite',
        '--overwrite-hash',
        action='store_true',
        help='While syncing, overwrite the files having different hashes')
    parser.add_argument(
        '-reverse',
        '--reverse-sync-direction',
        action='store_true',
        help='Use the right folder as source and the left as destination.')
    parser.add_argument(
        '-mirror',
        '--mirror-contents',
        action='store_true',
        help='Make the destination directory exactly same as the source.\
            Shorthand for `-add -remove -overwrite`.')
    args = parser.parse_args()
    args = vars(args)
    return args


def main():
    args = prepare_args_parser()
    left_dir_path = args['left-path']
    right_dir_path = args['right-path']
    hide_progress_bar = args['hide_progress_bar']
    fsync = FSync(left_dir_path, right_dir_path,
                  progress_bar=not hide_progress_bar)
    fsync.check_differences()
    print(fsync.get_report())
    add_missing = args['add_missing']
    remove_extra = args['remove_extra']
    overwrite_hash = args['overwrite_hash']
    reverse_direction = args['reverse_sync_direction']
    mirror = args['mirror_contents']
    if mirror:
        add_missing = True
        remove_extra = True
        overwrite_hash = True
    if add_missing or remove_extra or overwrite_hash:
        fsync.sync_dirs(overwrite_hash, add_missing, remove_extra,
                        reverse_direction)
    print('')


if __name__ == "__main__":
    main()
