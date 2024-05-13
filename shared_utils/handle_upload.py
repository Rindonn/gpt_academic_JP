import importlib
import time
import inspect
import re
import os
import base64
import gradio
import shutil
import glob
from shared_utils.config_loader import get_conf

def html_local_file(file):
    base_path = os.path.dirname(__file__)  # 项目目录
    if os.path.exists(str(file)):
        file = f'file={file.replace(base_path, ".")}'
    return file


def html_local_img(__file, layout="left", max_width=None, max_height=None, md=True):
    style = ""
    if max_width is not None:
        style += f"max-width: {max_width};"
    if max_height is not None:
        style += f"max-height: {max_height};"
    __file = html_local_file(__file)
    a = f'<div align="{layout}"><img src="{__file}" style="{style}"></div>'
    if md:
        a = f"![{__file}]({__file})"
    return a


def file_manifest_filter_type(file_list, filter_: list = None):
    new_list = []
    if not filter_:
        filter_ = ["png", "jpg", "jpeg"]
    for file in file_list:
        if str(os.path.basename(file)).split(".")[-1] in filter_:
            new_list.append(html_local_img(file, md=False))
        else:
            new_list.append(file)
    return new_list


def zip_extract_member_new(self, member, targetpath, pwd):
    # 修复中文乱码的問題
    """Extract the ZipInfo object 'member' to a physical
        file on the path targetpath.
    """
    import zipfile
    if not isinstance(member, zipfile.ZipInfo):
        member = self.getinfo(member)

    # build the destination pathname, replacing
    # forward slashes to platform specific separators.
    arcname = member.filename.replace('/', os.path.sep)
    arcname = arcname.encode('cp437', errors='replace').decode('gbk', errors='replace')

    if os.path.altsep:
        arcname = arcname.replace(os.path.altsep, os.path.sep)
    # interpret absolute pathname as relative, remove drive letter or
    # UNC path, redundant separators, "." and ".." components.
    arcname = os.path.splitdrive(arcname)[1]
    invalid_path_parts = ('', os.path.curdir, os.path.pardir)
    arcname = os.path.sep.join(x for x in arcname.split(os.path.sep)
                                if x not in invalid_path_parts)
    if os.path.sep == '\\':
        # filter illegal characters on Windows
        arcname = self._sanitize_windows_name(arcname, os.path.sep)

    targetpath = os.path.join(targetpath, arcname)
    targetpath = os.path.normpath(targetpath)

    # Create all upper directories if necessary.
    upperdirs = os.path.dirname(targetpath)
    if upperdirs and not os.path.exists(upperdirs):
        os.makedirs(upperdirs)

    if member.is_dir():
        if not os.path.isdir(targetpath):
            os.mkdir(targetpath)
        return targetpath

    with self.open(member, pwd=pwd) as source, \
            open(targetpath, "wb") as target:
        shutil.copyfileobj(source, target)

    return targetpath


def extract_archive(file_path, dest_dir):
    import zipfile
    import tarfile
    import os

    # Get the file extension of the input file
    file_extension = os.path.splitext(file_path)[1]

    # Extract the archive based on its extension
    if file_extension == ".zip":
        with zipfile.ZipFile(file_path, "r") as zipobj:
            zipobj._extract_member = lambda a,b,c: zip_extract_member_new(zipobj, a,b,c)    # 修复中文乱码的問題
            zipobj.extractall(path=dest_dir)
            print("Successfully extracted zip archive to {}".format(dest_dir))

    elif file_extension in [".tar", ".gz", ".bz2"]:
        with tarfile.open(file_path, "r:*") as tarobj:
            tarobj.extractall(path=dest_dir)
            print("Successfully extracted tar archive to {}".format(dest_dir))

    # サードパーティのライブラリ，rarfileを事前にpip installする必要があります
    # さらに，Windowsにはwinrarソフトウェアのインストールが必要です，そのPath環境変数を設定する，如"C:\Program Files\WinRAR"才可以
    elif file_extension == ".rar":
        try:
            import rarfile

            with rarfile.RarFile(file_path) as rf:
                rf.extractall(path=dest_dir)
                print("Successfully extracted rar archive to {}".format(dest_dir))
        except:
            print("Rar format requires additional dependencies to install")
            return "\n\n解凍に失敗しました！rarファイルを解凍するにはpip install rarfileをインストールする必要があります。提案する：使用するzip压缩フォーマット。"

    # サードパーティのライブラリ，事前にpip install py7zrが必要です
    elif file_extension == ".7z":
        try:
            import py7zr

            with py7zr.SevenZipFile(file_path, mode="r") as f:
                f.extractall(path=dest_dir)
                print("Successfully extracted 7z archive to {}".format(dest_dir))
        except:
            print("7z format requires additional dependencies to install")
            return "\n\n解凍に失敗しました！7zファイルを解凍するにはpip install py7zrをインストールする必要があります"
    else:
        return ""
    return ""

