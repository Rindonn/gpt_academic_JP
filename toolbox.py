import importlib
import time
import inspect
import re
import os
import base64
import gradio
import shutil
import glob
import logging
import uuid
from functools import wraps
from shared_utils.config_loader import get_conf
from shared_utils.config_loader import set_conf
from shared_utils.config_loader import set_multi_conf
from shared_utils.config_loader import read_single_conf_with_lru_cache
from shared_utils.advanced_markdown_format import format_io
from shared_utils.advanced_markdown_format import markdown_convertion
from shared_utils.key_pattern_manager import select_api_key
from shared_utils.key_pattern_manager import is_any_api_key
from shared_utils.key_pattern_manager import what_keys
from shared_utils.connect_void_terminal import get_chat_handle
from shared_utils.connect_void_terminal import get_plugin_handle
from shared_utils.connect_void_terminal import get_plugin_default_kwargs
from shared_utils.connect_void_terminal import get_chat_default_kwargs
from shared_utils.text_mask import apply_gpt_academic_string_mask
from shared_utils.text_mask import build_gpt_academic_masked_string
from shared_utils.text_mask import apply_gpt_academic_string_mask_langbased
from shared_utils.text_mask import build_gpt_academic_masked_string_langbased
from shared_utils.map_names import map_friendly_names_to_model
from shared_utils.map_names import map_model_to_friendly_names
from shared_utils.map_names import read_one_api_model_name
from shared_utils.handle_upload import html_local_file
from shared_utils.handle_upload import html_local_img
from shared_utils.handle_upload import file_manifest_filter_type
from shared_utils.handle_upload import extract_archive
from typing import List
pj = os.path.join
default_user_name = "default_user"

"""
=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
第1部分
関数プラグインの入出力接続エリア
    - ChatBotWithCookies:   Cookieを持つChatbotクラス，より強力な機能を実現するための基盤となる
    - ArgsGeneralWrapper:   デコレータ関数，入力パラメーターを再構成するために使用するされます，入力パラメータの順序と構造を変更する
    - update_ui:            UIを更新するには、yield from update_uiを使用するします(chatbot, history)
    - CatchException:       すべての問題をインターフェースに表示する
    - HotReload:            プラグインのホット更新を実現する
    - trimmed_format_exc:   トレースバックを印刷する，安全のために絶対アドレスを隠す
=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
"""


class ChatBotWithCookies(list):
    def __init__(self, cookie):
        """
        cookies = {
            'top_p': top_p,
            'temperature': temperature,
            'lock_plugin': bool,
            "files_to_promote": ["file1", "file2"],
            "most_recent_uploaded": {
                "path": "uploaded_path",
                "time": time.time(),
                "time_str": "timestr",
            }
        }
        """
        self._cookies = cookie

    def write_list(self, list):
        for t in list:
            self.append(t)

    def get_list(self):
        return [t for t in self]

    def get_cookies(self):
        return self._cookies


def ArgsGeneralWrapper(f):
    """
    デコレータ関数ArgsGeneralWrapper，入力パラメーターを再構成するために使用するされます，入力パラメータの順序と構造を変更する。
    该装饰器是大多数功能调用的入口。
    函数示意图：https://mermaid.live/edit#pako:eNqNVFtPGkEY_StkntoEDQtLoTw0sWqapjQxVWPabmOm7AiEZZcsQ9QiiW012qixqdeqqIn10geBh6ZR8PJnmAWe-hc6l3VhrWnLEzNzzvnO953ZyYOYoSIQAWOaMR5LQBN7hvoU3UN_g5iu7imAXEyT4wUF3Pd0dT3y9KGYYUJsmK8V0GPGs0-QjkyojZgwk0Fm82C2dVghX08U8EaoOHjOfoEMU0XmADRhOksVWnNLjdpM82qFzB6S5Q_WWsUhuqCc3JtAsVR_OoMnhyZwXgHWwbS1d4gnsLVZJp-P6mfVxveqAgqC70Jz_pQCOGDKM5xFdNNPDdilF6uSU_hOYqu4a3MHYDZLDzq5fodrC3PWcEaFGPUaRiqJWK_W9g9rvRITa4dhy_0nw67SiePMp3oSR6PPn41DGgllkvkizYwsrmtaejTFd8V4yekGmT1zqrt4XGlAy8WTuiPULF01LksZvukSajfQQRAxmYi5S0D81sDcyzapVdn6sYFHkjhhGyel3frVQnvsnbR23lEjlhIlaOJiFPWzU5G4tfNJo8ejwp47-TbvJkKKZvmxA6SKo16oaazJysfG6klr9T0pbTW2ZqzlL_XaT8fYbQLXe4mSmvoCZXMaa7FePW6s7jVqK9bujvse3WFjY5_Z4KfsA4oiPY4T7Drvn1tLJTbG1to1qR79ulgk89-oJbvZzbIwJty6u20LOReWa9BvwserUd9s9MIKc3x5TUWEoAhUyJK5y85w_yG-dFu_R9waoU7K581y8W_qLle35-rG9Nxcrz8QHRsc0K-r9NViYRT36KsFvCCNzDRMqvSVyzOKAnACpZECIvSvCs2UAhS9QHEwh43BST0GItjMIS_I8e-sLwnj9A262cxA_ZVh0OUY1LJiDSJ5MAEiUijYLUtBORR6KElyQPaCSRDpksNSd8AfluSgHPaFC17wjrOlbgbzyyFf4IFPDvoD_sJvnkdK-g
    """
    def decorated(request: gradio.Request, cookies:dict, max_length:int, llm_model:str,
                  txt:str, txt2:str, top_p:float, temperature:float, chatbot:list,
                  history:list, system_prompt:str, plugin_advanced_arg:str, *args):
        txt_passon = txt
        if txt == "" and txt2 != "": txt_passon = txt2
        # cookieを持つchatbotを導入する
        if request.username is not None:
            user_name = request.username
        else:
            user_name = default_user_name
        cookies.update({
            'top_p': top_p,
            'api_key': cookies['api_key'],
            'llm_model': llm_model,
            'temperature': temperature,
            'user_name': user_name,
        })
        llm_kwargs = {
            'api_key': cookies['api_key'],
            'llm_model': llm_model,
            'top_p': top_p,
            'max_length': max_length,
            'temperature': temperature,
            'client_ip': request.client.host,
            'most_recent_uploaded': cookies.get('most_recent_uploaded')
        }
        plugin_kwargs = {
            "advanced_arg": plugin_advanced_arg,
        }
        chatbot_with_cookie = ChatBotWithCookies(cookies)
        chatbot_with_cookie.write_list(chatbot)

        if cookies.get('lock_plugin', None) is None:
            # 正常な状態
            if len(args) == 0:  # プラグイン通道
                yield from f(txt_passon, llm_kwargs, plugin_kwargs, chatbot_with_cookie, history, system_prompt, request)
            else:               # 对话通道，または基础功能通道
                yield from f(txt_passon, llm_kwargs, plugin_kwargs, chatbot_with_cookie, history, system_prompt, *args)
        else:
            # 处理少数情况下的特殊プラグイン的锁定ステータス
            module, fn_name = cookies['lock_plugin'].split('->')
            f_hot_reload = getattr(importlib.import_module(module, fn_name), fn_name)
            yield from f_hot_reload(txt_passon, llm_kwargs, plugin_kwargs, chatbot_with_cookie, history, system_prompt, request)
            # 判断一下用户是否错误地通过对话通道进入，如果是，则进行提醒
            final_cookies = chatbot_with_cookie.get_cookies()
            # len(args) != 0 代表“提出”键对话通道，または基础功能通道
            if len(args) != 0 and 'files_to_promote' in final_cookies and len(final_cookies['files_to_promote']) > 0:
                chatbot_with_cookie.append(
                    ["検出された**滞留的缓存文档**，请及時处理。", "请及時点击“**現在の対話を保存する**”获取所有滞留文档。"])
                yield from update_ui(chatbot_with_cookie, final_cookies['history'], msg="検出された被滞留的缓存文档")

    return decorated


def update_ui(chatbot:ChatBotWithCookies, history, msg="正常", **kwargs):  # 画面を更新する
    """
    ユーザーインターフェースを更新する
    """
    assert isinstance(
        chatbot, ChatBotWithCookies
    ), "Do not discard it in the process of passing chatbot。必要に応じて, clearを使用するしてクリアできます, for+appendループを使用するして値を再割り当てする。"
    cookies = chatbot.get_cookies()
    # 备份一份History作为记录
    cookies.update({"history": history})
    # プラグインのロック時のインターフェース表示の問題を解決する
    if cookies.get("lock_plugin", None):
        label = (
            cookies.get("llm_model", "")
            + " | "
            + "正在锁定プラグイン"
            + cookies.get("lock_plugin", None)
        )
        chatbot_gr = gradio.update(value=chatbot, label=label)
        if cookies.get("label", "") != label:
            cookies["label"] = label  # 记住当前的label
    elif cookies.get("label", None):
        chatbot_gr = gradio.update(value=chatbot, label=cookies.get("llm_model", ""))
        cookies["label"] = None  # ラベルをクリアする
    else:
        chatbot_gr = chatbot

    yield cookies, chatbot_gr, history, msg


def update_ui_lastest_msg(lastmsg:str, chatbot:ChatBotWithCookies, history:list, delay=1):  # 画面を更新する
    """
    ユーザーインターフェースを更新する
    """
    if len(chatbot) == 0:
        chatbot.append(["update_ui_last_msg", lastmsg])
    chatbot[-1] = list(chatbot[-1])
    chatbot[-1][-1] = lastmsg
    yield from update_ui(chatbot=chatbot, history=history)
    time.sleep(delay)


def trimmed_format_exc():
    import os, traceback

    str = traceback.format_exc()
    current_path = os.getcwd()
    replace_path = "."
    return str.replace(current_path, replace_path)


def CatchException(f):
    """
    デコレータ関数，関数fで例外をキャッチして、ジェネレータにエンコードして返す，チャットに表示される。
    """

    @wraps(f)
    def decorated(main_input:str, llm_kwargs:dict, plugin_kwargs:dict,
                  chatbot_with_cookie:ChatBotWithCookies, history:list, *args, **kwargs):
        try:
            yield from f(main_input, llm_kwargs, plugin_kwargs, chatbot_with_cookie, history, *args, **kwargs)
        except Exception as e:
            from toolbox import get_conf
            tb_str = '```\n' + trimmed_format_exc() + '```'
            if len(chatbot_with_cookie) == 0:
                chatbot_with_cookie.clear()
                chatbot_with_cookie.append(["プラグインスケジューリングの例外", "異常の原因"])
            chatbot_with_cookie[-1] = (chatbot_with_cookie[-1][0], f"[Local Message] プラグイン调用出错: \n\n{tb_str} \n")
            yield from update_ui(chatbot=chatbot_with_cookie, history=history, msg=f'Exception {e}')  # 画面を更新する

    return decorated


def HotReload(f):
    """
    HotReloadのデコレーター関数，Python関数プラグインのホット更新を実現するために使用するされます。
    関数のホットアップデートとは、プログラムの実行を停止せずに行うことを指します，関数コードを更新する，これにより、リアルタイム更新機能が実現されます。
    デコレーターの内部で，wrapsを使用するする(f)関数のメタ情報を保持するために，内部関数decoratedを定義しました。
    内部関数は、importlibモジュールのreload関数とinspectモジュールのgetmodule関数を使用するして、関数モジュールを再ロードおよび取得します，
    その後、getattr関数を使用するして関数名を取得します，新しいモジュールで関数を再読み込みする。
    最後に，yield fromステートメントを使用するして再読み込みされた関数を返す，デコレートされた関数で実行する。
    最終的に，デコレーター関数は内部関数を返します。この内部関数は、関数の元の定義を最新バージョンに更新できます，関数の新バージョンを実行する。
    """
    if get_conf("PLUGIN_HOT_RELOAD"):

        @wraps(f)
        def decorated(*args, **kwargs):
            fn_name = f.__name__
            f_hot_reload = getattr(importlib.reload(inspect.getmodule(f)), fn_name)
            yield from f_hot_reload(*args, **kwargs)

        return decorated
    else:
        return f


"""
=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
第2部分
Other small tools:
    - write_history_to_file:    Write the result to a markdown file
    - regular_txt_to_markdown:  通常のテキストをMarkdown形式のテキストに変換する。
    - report_exception:         チャットボットに簡単な予期しないエラーメッセージを追加する
    - text_divide_paragraph:    テキストを段落区切り文字で分割する，段落タグを持つHTMLコードを生成する。
    - markdown_convertion:      複数のテキストの翻訳を組み合わせる，Markdownを美しいHTMLに変換する
    - format_io:                gradioのデフォルトのmarkdown処理テキストの翻訳を接管する
    - on_file_uploaded:         Handle file upload（自動解凍）
    - on_report_generated:      Automatically project the generated report to the file upload area
    - clip_history:             履歴のコンテキストが長すぎる場合，自動切断
    - get_conf:                 設定を取得する
    - select_api_key:           現在のモデルタイプに基づいて，利用可能なAPIキーを抽出する
=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
"""


def get_reduce_token_percent(text:str):
    """
    * この関数は置き換える来的に廃止されます
    """
    try:
        # text = "maximum context length is 4097 tokens. However, your messages resulted in 4870 tokens"
        pattern = r"(\d+)\s+tokens\b"
        match = re.findall(pattern, text)
        EXCEED_ALLO = 500  # 少し余裕を持たせる，そうしないと、返信時に余裕が少なすぎて問題が発生する可能性があります
        max_limit = float(match[0]) - EXCEED_ALLO
        current_tokens = float(match[1])
        ratio = max_limit / current_tokens
        assert ratio > 0 and ratio < 1
        return ratio, str(int(current_tokens - max_limit))
    except:
        return 0.5, "詳細不明"


def write_history_to_file(
    history:list, file_basename:str=None, file_fullname:str=None, auto_caption:bool=True
):
    """
    対話履歴をMarkdown形式でファイルに書き込む。ファイル名が指定されていない場合，Then use the current time to generate the file name。
    """
    import os
    import time

    if file_fullname is None:
        if file_basename is not None:
            file_fullname = pj(get_log_folder(), file_basename)
        else:
            file_fullname = pj(get_log_folder(), f"GPT-Academic-{gen_time_str()}.md")
    os.makedirs(os.path.dirname(file_fullname), exist_ok=True)
    with open(file_fullname, "w", encoding="utf8") as f:
        f.write("# GPT-Academic Report\n")
        for i, content in enumerate(history):
            try:
                if type(content) != str:
                    content = str(content)
            except:
                continue
            if i % 2 == 0 and auto_caption:
                f.write("## ")
            try:
                f.write(content)
            except:
                # remove everything that cannot be handled by utf8
                f.write(content.encode("utf-8", "ignore").decode())
            f.write("\n\n")
    res = os.path.abspath(file_fullname)
    return res


def regular_txt_to_markdown(text:str):
    """
    通常のテキストをMarkdown形式のテキストに変換する。
    """
    text = text.replace("\n", "\n\n")
    text = text.replace("\n\n\n", "\n\n")
    text = text.replace("\n\n\n", "\n\n")
    return text


def report_exception(chatbot:ChatBotWithCookies, history:list, a:str, b:str):
    """
    Add error message to chatbot
    """
    chatbot.append((a, b))
    history.extend([a, b])


def find_free_port()->int:
    """
    現在のシステムで使用する可能な未使用するのポートを返す。
    """
    import socket
    from contextlib import closing

    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def find_recent_files(directory:str)->List[str]:
    """
    Find files that is created with in one minutes under a directory with python, write a function
    """
    import os
    import time

    current_time = time.time()
    one_minute_ago = current_time - 60
    recent_files = []
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    for filename in os.listdir(directory):
        file_path = pj(directory, filename)
        if file_path.endswith(".log"):
            continue
        created_time = os.path.getmtime(file_path)
        if created_time >= one_minute_ago:
            if os.path.isdir(file_path):
                continue
            recent_files.append(file_path)

    return recent_files


def file_already_in_downloadzone(file:str, user_path:str):
    try:
        parent_path = os.path.abspath(user_path)
        child_path = os.path.abspath(file)
        if os.path.samefile(os.path.commonpath([parent_path, child_path]), parent_path):
            return True
        else:
            return False
    except:
        return False


def promote_file_to_downloadzone(file:str, rename_file:str=None, chatbot:ChatBotWithCookies=None):
    # 置き換える文件复制一份到下载区
    import shutil

    if chatbot is not None:
        user_name = get_user(chatbot)
    else:
        user_name = default_user_name
    if not os.path.exists(file):
        raise FileNotFoundError(f"文件{file}不存在")
    user_path = get_log_folder(user_name, plugin_name=None)
    if file_already_in_downloadzone(file, user_path):
        new_path = file
    else:
        user_path = get_log_folder(user_name, plugin_name="downloadzone")
        if rename_file is None:
            rename_file = f"{gen_time_str()}-{os.path.basename(file)}"
        new_path = pj(user_path, rename_file)
        # 既に存在する場合，テキストの翻訳
        if os.path.exists(new_path) and not os.path.samefile(new_path, file):
            os.remove(new_path)
        # ファイルをコピーする
        if not os.path.exists(new_path):
            shutil.copyfile(file, new_path)
    # 原始文本
    if chatbot is not None:
        if "files_to_promote" in chatbot._cookies:
            current = chatbot._cookies["files_to_promote"]
        else:
            current = []
        if new_path not in current:  # 避免把同一pieces文件添加多次
            chatbot._cookies.update({"files_to_promote": [new_path] + current})
    return new_path


def disable_auto_promotion(chatbot:ChatBotWithCookies):
    chatbot._cookies.update({"files_to_promote": []})
    return


def del_outdated_uploads(outdate_time_seconds:float, target_path_base:str=None):
    if target_path_base is None:
        user_upload_dir = get_conf("PATH_PRIVATE_UPLOAD")
    else:
        user_upload_dir = target_path_base
    current_time = time.time()
    one_hour_ago = current_time - outdate_time_seconds
    # Get a list of all subdirectories in the user_upload_dir folder
    # Remove subdirectories that are older than one hour
    for subdirectory in glob.glob(f"{user_upload_dir}/*"):
        subdirectory_time = os.path.getmtime(subdirectory)
        if subdirectory_time < one_hour_ago:
            try:
                shutil.rmtree(subdirectory)
            except:
                pass
    return



def to_markdown_tabs(head: list, tabs: list, alignment=":---:", column=False, omit_path=None):
    """
    Args:
        head: 表头：[]
        tabs: 表值：[[列1], [列2], [列3], [列4]]
        alignment: :--- 左对齐， :---: 居中对齐， ---: 右对齐
        column: True to keep data in columns, False to keep data in rows (default).
    Returns:
        A string representation of the markdown table.
    """
    if column:
        transposed_tabs = list(map(list, zip(*tabs)))
    else:
        transposed_tabs = tabs
    # Find the maximum length among the columns
    max_len = max(len(column) for column in transposed_tabs)

    tab_format = "| %s "
    tabs_list = "".join([tab_format % i for i in head]) + "|\n"
    tabs_list += "".join([tab_format % alignment for i in head]) + "|\n"

    for i in range(max_len):
        row_data = [tab[i] if i < len(tab) else "" for tab in transposed_tabs]
        row_data = file_manifest_filter_type(row_data, filter_=None)
        # for dat in row_data:
        #     if (omit_path is not None) and os.path.exists(dat):
        #         dat = os.path.relpath(dat, omit_path)
        tabs_list += "".join([tab_format % i for i in row_data]) + "|\n"

    return tabs_list


def on_file_uploaded(
    request: gradio.Request, files:List[str], chatbot:ChatBotWithCookies,
    txt:str, txt2:str, checkboxes:List[str], cookies:dict
):
    """
    ファイルがアップロードされたときのコールバック関数
    """
    if len(files) == 0:
        return chatbot, txt

    # 创建工作路径
    user_name = default_user_name if not request.username else request.username
    time_tag = gen_time_str()
    target_path_base = get_upload_folder(user_name, tag=time_tag)
    os.makedirs(target_path_base, exist_ok=True)

    # 移除过時的旧文件从而节省空间&保护隐私
    outdate_time_seconds = 3600  # 一小時
    del_outdated_uploads(outdate_time_seconds, get_upload_folder(user_name))

    # 逐pieces文件转移到目标路径
    upload_msg = ""
    for file in files:
        file_origin_name = os.path.basename(file.orig_name)
        this_file_path = pj(target_path_base, file_origin_name)
        shutil.move(file.name, this_file_path)
        upload_msg += extract_archive(
            file_path=this_file_path, dest_dir=this_file_path + ".extract"
        )

    # 整理文件集合 出力消息
    files = glob.glob(f"{target_path_base}/**/*", recursive=True)
    moved_files = [fp for fp in files]
    max_file_to_show = 10
    if len(moved_files) > max_file_to_show:
        moved_files = moved_files[:max_file_to_show//2] + [f'... ( 📌省略{len(moved_files) - max_file_to_show}pieces文件的显示 ) ...'] + \
                      moved_files[-max_file_to_show//2:]
    moved_files_str = to_markdown_tabs(head=["文件"], tabs=[moved_files], omit_path=target_path_base)
    chatbot.append(
        [
            "ファイルをアップロードしました，受信箱を確認してください",
            f"[Local Message] 以下のファイルを受け取りました （上传到路径：{target_path_base}）: " +
            f"\n\n{moved_files_str}" +
            f"\n\n呼び出しパスのパラメータが自動的に修正されました: \n\n{txt}" +
            f"\n\n今您点击任意関数プラグイン時，上記のファイルは入力パラメータとして使用するされます" +
            upload_msg,
        ]
    )

    txt, txt2 = target_path_base, ""
    if "浮动入力エリア" in checkboxes:
        txt, txt2 = txt2, txt

    # 记录近期文件
    cookies.update(
        {
            "most_recent_uploaded": {
                "path": target_path_base,
                "time": time.time(),
                "time_str": time_tag,
            }
        }
    )
    return chatbot, txt, txt2, cookies


def on_report_generated(cookies:dict, files:List[str], chatbot:ChatBotWithCookies):
    # from toolbox import find_recent_files
    # PATH_LOGGING = get_conf('PATH_LOGGING')
    if "files_to_promote" in cookies:
        report_files = cookies["files_to_promote"]
        cookies.pop("files_to_promote")
    else:
        report_files = []
    #     report_files = find_recent_files(PATH_LOGGING)
    if len(report_files) == 0:
        return cookies, None, chatbot
    # files.extend(report_files)
    file_links = ""
    for f in report_files:
        file_links += (
            f'<br/><a href="file={os.path.abspath(f)}" target="_blank">{f}</a>'
        )
    chatbot.append(["報告のリモート取得テキストの翻訳？", f"報告は右側の「ファイルアップロードエリア」に追加されました（折りたたみ状態になっている可能性があります），受信箱を確認してください。{file_links}"])
    return cookies, report_files, chatbot


def load_chat_cookies():
    API_KEY, LLM_MODEL, AZURE_API_KEY = get_conf(
        "API_KEY", "LLM_MODEL", "AZURE_API_KEY"
    )
    AZURE_CFG_ARRAY, NUM_CUSTOM_BASIC_BTN = get_conf(
        "AZURE_CFG_ARRAY", "NUM_CUSTOM_BASIC_BTN"
    )

    # deal with azure openai key
    if is_any_api_key(AZURE_API_KEY):
        if is_any_api_key(API_KEY):
            API_KEY = API_KEY + "," + AZURE_API_KEY
        else:
            API_KEY = AZURE_API_KEY
    if len(AZURE_CFG_ARRAY) > 0:
        for azure_model_name, azure_cfg_dict in AZURE_CFG_ARRAY.items():
            if not azure_model_name.startswith("azure"):
                raise ValueError("AZURE_CFG_ARRAY中配置的模型必须以azure开头")
            AZURE_API_KEY_ = azure_cfg_dict["AZURE_API_KEY"]
            if is_any_api_key(AZURE_API_KEY_):
                if is_any_api_key(API_KEY):
                    API_KEY = API_KEY + "," + AZURE_API_KEY_
                else:
                    API_KEY = AZURE_API_KEY_

    customize_fn_overwrite_ = {}
    for k in range(NUM_CUSTOM_BASIC_BTN):
        customize_fn_overwrite_.update(
            {
                "自定义按钮"
                + str(k + 1): {
                    "Title": r"",
                    "Prefix": r"请在自定义菜单中定义ヒント词テキストの翻訳.",
                    "Suffix": r"请在自定义菜单中定义ヒント词后缀",
                }
            }
        )
    return {
        "api_key": API_KEY,
        "llm_model": LLM_MODEL,
        "customize_fn_overwrite": customize_fn_overwrite_,
    }


def clear_line_break(txt):
    txt = txt.replace("\n", " ")
    txt = txt.replace("  ", " ")
    txt = txt.replace("  ", " ")
    return txt


class DummyWith:
    """
    このコードは、DummyWithという名前の空のコンテキストマネージャを定義しています，
    その役割は……ああ……機能しないことです，That is, replace other context managers without changing the code structure。
    コンテキストマネージャはPythonオブジェクトの一種です，with文と一緒に使用するする，
    いくつかのリソースがコードブロックの実行中に正しく初期化およびクリーンアップされるようにするため。
    コンテキストマネージャは2つのメソッドを実装する必要があります，They are __enter__ respectively()と __exit__()。
    When the context execution starts，__enter__()メソッドはコードブロックが実行される前に呼び出されます，
    While at the end of the context execution，__exit__()メソッドが呼び出されます。
    """

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return


def run_gradio_in_subpath(demo, auth, port, custom_path):
    """
    Gradioの実行アドレスを指定された2次パスに変更する
    """

    def is_path_legal(path: str) -> bool:
        """
        check path for sub url
        path: path to check
        return value: do sub url wrap
        """
        if path == "/":
            return True
        if len(path) == 0:
            print(
                "ilegal custom path: {}\npath must not be empty\ndeploy on root url".format(
                    path
                )
            )
            return False
        if path[0] == "/":
            if path[1] != "/":
                print("deploy on sub-path {}".format(path))
                return True
            return False
        print(
            "ilegal custom path: {}\npath should begin with '/'\ndeploy on root url".format(
                path
            )
        )
        return False

    if not is_path_legal(custom_path):
        raise RuntimeError("Ilegal custom path")
    import uvicorn
    import gradio as gr
    from fastapi import FastAPI

    app = FastAPI()
    if custom_path != "/":

        @app.get("/")
        def read_main():
            return {"message": f"Gradio is running at: {custom_path}"}

    app = gr.mount_gradio_app(app, demo, path=custom_path)
    uvicorn.run(app, host="0.0.0.0", port=port)  # , auth=auth


def clip_history(inputs, history, tokenizer, max_token_limit):
    """
    reduce the length of history by clipping.
    this function search for the longest entries to clip, little by little,
    until the number of token of history is reduced under threshold.
    履歴の長さを短くするためにトリミングを使用するする。
    この関数は徐々に最長のエントリを検索して編集します，
    直到履歴のマーク数が閾値以下になるまで。
    """
    import numpy as np
    from request_llms.bridge_all import model_info

    def get_token_num(txt):
        return len(tokenizer.encode(txt, disallowed_special=()))

    input_token_num = get_token_num(inputs)

    if max_token_limit < 5000:
        output_token_expect = 256  # 4k & 2k models
    elif max_token_limit < 9000:
        output_token_expect = 512  # 8k models
    else:
        output_token_expect = 1024  # 16k & 32k models

    if input_token_num < max_token_limit * 3 / 4:
        # 入力部分のトークンの割合が制限の3/4未満の場合，トリミング中
        # 1. 入力の余裕を残す
        max_token_limit = max_token_limit - input_token_num
        # 2. Leave room for the output
        max_token_limit = max_token_limit - output_token_expect
        # 3. もし余剰が少なすぎる場合，履歴を直接クリアする
        if max_token_limit < output_token_expect:
            history = []
            return history
    else:
        # When the token proportion of the input part is > 制限の3/4時，履歴を直接クリアする
        history = []
        return history

    everything = [""]
    everything.extend(history)
    n_token = get_token_num("\n".join(everything))
    everything_token = [get_token_num(e) for e in everything]

    # 切り捨て時の粒度
    delta = max(everything_token) // 16

    while n_token > max_token_limit:
        where = np.argmax(everything_token)
        encoded = tokenizer.encode(everything[where], disallowed_special=())
        clipped_encoded = encoded[: len(encoded) - delta]
        everything[where] = tokenizer.decode(clipped_encoded)[
            :-1
        ]  # -1 to remove the may-be illegal char
        everything_token[where] = get_token_num(everything[where])
        n_token = get_token_num("\n".join(everything))

    history = everything[1:]
    return history


"""
=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
第3部分
Other small tools:
    - zip_folder:    把某pieces路径下所有文件压缩，テキストの翻訳（gptで書かれた）
    - gen_time_str:  タイムスタンプの生成
    - ProxyNetworkActivate: 临時地启动代理网络（ある場合）
    - objdump/objload: 便利なデバッグ関数
=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
"""


def zip_folder(source_folder, dest_folder, zip_name):
    import zipfile
    import os

    # Make sure the source folder exists
    if not os.path.exists(source_folder):
        print(f"{source_folder} does not exist")
        return

    # Make sure the destination folder exists
    if not os.path.exists(dest_folder):
        print(f"{dest_folder} does not exist")
        return

    # Create the name for the zip file
    zip_file = pj(dest_folder, zip_name)

    # Create a ZipFile object
    with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Walk through the source folder and add files to the zip file
        for foldername, subfolders, filenames in os.walk(source_folder):
            for filename in filenames:
                filepath = pj(foldername, filename)
                zipf.write(filepath, arcname=os.path.relpath(filepath, source_folder))

    # Move the zip file to the destination folder (if it wasn't already there)
    if os.path.dirname(zip_file) != dest_folder:
        os.rename(zip_file, pj(dest_folder, os.path.basename(zip_file)))
        zip_file = pj(dest_folder, os.path.basename(zip_file))

    print(f"Zip file created at {zip_file}")


def zip_result(folder):
    t = gen_time_str()
    zip_folder(folder, get_log_folder(), f"{t}-result.zip")
    return pj(get_log_folder(), f"{t}-result.zip")


def gen_time_str():
    import time

    return time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())


def get_log_folder(user=default_user_name, plugin_name="shared"):
    if user is None:
        user = default_user_name
    PATH_LOGGING = get_conf("PATH_LOGGING")
    if plugin_name is None:
        _dir = pj(PATH_LOGGING, user)
    else:
        _dir = pj(PATH_LOGGING, user, plugin_name)
    if not os.path.exists(_dir):
        os.makedirs(_dir)
    return _dir


def get_upload_folder(user=default_user_name, tag=None):
    PATH_PRIVATE_UPLOAD = get_conf("PATH_PRIVATE_UPLOAD")
    if user is None:
        user = default_user_name
    if tag is None or len(tag) == 0:
        target_path_base = pj(PATH_PRIVATE_UPLOAD, user)
    else:
        target_path_base = pj(PATH_PRIVATE_UPLOAD, user, tag)
    return target_path_base


def is_the_upload_folder(string):
    PATH_PRIVATE_UPLOAD = get_conf("PATH_PRIVATE_UPLOAD")
    pattern = r"^PATH_PRIVATE_UPLOAD[\\/][A-Za-z0-9_-]+[\\/]\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}$"
    pattern = pattern.replace("PATH_PRIVATE_UPLOAD", PATH_PRIVATE_UPLOAD)
    if re.match(pattern, string):
        return True
    else:
        return False


def get_user(chatbotwithcookies:ChatBotWithCookies):
    return chatbotwithcookies._cookies.get("user_name", default_user_name)


class ProxyNetworkActivate:
    """
    这段代码定义了一pieces名为ProxyNetworkActivate的空文脈管理器, 一部のコードにプロキシを適用するために使用するされます
    """

    def __init__(self, task=None) -> None:
        self.task = task
        if not task:
            # 不给定task, 那么私たちは#代理生效
            self.valid = True
        else:
            # 给定了task, 私たちは检查一下
            from toolbox import get_conf

            WHEN_TO_USE_PROXY = get_conf("WHEN_TO_USE_PROXY")
            self.valid = task in WHEN_TO_USE_PROXY

    def __enter__(self):
        if not self.valid:
            return self
        from toolbox import get_conf

        proxies = get_conf("proxies")
        if "no_proxy" in os.environ:
            os.environ.pop("no_proxy")
        if proxies is not None:
            if "http" in proxies:
                os.environ["HTTP_PROXY"] = proxies["http"]
            if "https" in proxies:
                os.environ["HTTPS_PROXY"] = proxies["https"]
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        os.environ["no_proxy"] = "*"
        if "HTTP_PROXY" in os.environ:
            os.environ.pop("HTTP_PROXY")
        if "HTTPS_PROXY" in os.environ:
            os.environ.pop("HTTPS_PROXY")
        return


def objdump(obj, file="objdump.tmp"):
    import pickle

    with open(file, "wb+") as f:
        pickle.dump(obj, f)
    return


def objload(file="objdump.tmp"):
    import pickle, os

    if not os.path.exists(file):
        return
    with open(file, "rb") as f:
        return pickle.load(f)


def Singleton(cls):
    """
    単一のインスタンスデコレータ
    """
    _instance = {}

    def _singleton(*args, **kargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kargs)
        return _instance[cls]

    return _singleton


def get_pictures_list(path):
    file_manifest = [f for f in glob.glob(f"{path}/**/*.jpg", recursive=True)]
    file_manifest += [f for f in glob.glob(f"{path}/**/*.jpeg", recursive=True)]
    file_manifest += [f for f in glob.glob(f"{path}/**/*.png", recursive=True)]
    return file_manifest


def have_any_recent_upload_image_files(chatbot:ChatBotWithCookies):
    _5min = 5 * 60
    if chatbot is None:
        return False, None  # chatbot is None
    most_recent_uploaded = chatbot._cookies.get("most_recent_uploaded", None)
    if not most_recent_uploaded:
        return False, None  # most_recent_uploaded is None
    if time.time() - most_recent_uploaded["time"] < _5min:
        most_recent_uploaded = chatbot._cookies.get("most_recent_uploaded", None)
        path = most_recent_uploaded["path"]
        file_manifest = get_pictures_list(path)
        if len(file_manifest) == 0:
            return False, None
        return True, file_manifest  # most_recent_uploaded is new
    else:
        return False, None  # most_recent_uploaded is too old

# Claude3 model supports graphic context dialogue, reads all images
def every_image_file_in_path(chatbot:ChatBotWithCookies):
    if chatbot is None:
        return False, []  # chatbot is None
    most_recent_uploaded = chatbot._cookies.get("most_recent_uploaded", None)
    if not most_recent_uploaded:
        return False, []  # most_recent_uploaded is None
    path = most_recent_uploaded["path"]
    file_manifest = get_pictures_list(path)
    if len(file_manifest) == 0:
        return False, []
    return True, file_manifest

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def get_max_token(llm_kwargs):
    from request_llms.bridge_all import model_info

    return model_info[llm_kwargs["llm_model"]]["max_token"]


def check_packages(packages=[]):
    import importlib.util

    for p in packages:
        spam_spec = importlib.util.find_spec(p)
        if spam_spec is None:
            raise ModuleNotFoundError


def map_file_to_sha256(file_path):
    import hashlib

    with open(file_path, 'rb') as file:
        content = file.read()

    # Calculate the SHA-256 hash of the file contents
    sha_hash = hashlib.sha256(content).hexdigest()

    return sha_hash


def check_repeat_upload(new_pdf_path, pdf_hash):
    '''
    检查History上传のファイル是否与新上传のファイル相同，如果相同则戻る(True, 重复文件路径)，否则戻る(False，None)
    '''
    from toolbox import get_conf
    import PyPDF2

    user_upload_dir = os.path.dirname(os.path.dirname(new_pdf_path))
    file_name = os.path.basename(new_pdf_path)

    file_manifest = [f for f in glob.glob(f'{user_upload_dir}/**/{file_name}', recursive=True)]

    for saved_file in file_manifest:
        with open(new_pdf_path, 'rb') as file1, open(saved_file, 'rb') as file2:
            reader1 = PyPDF2.PdfFileReader(file1)
            reader2 = PyPDF2.PdfFileReader(file2)

            # 比较页数是否相同
            if reader1.getNumPages() != reader2.getNumPages():
                continue

            # 比较每一页的内容是否相同
            for page_num in range(reader1.getNumPages()):
                page1 = reader1.getPage(page_num).extractText()
                page2 = reader2.getPage(page_num).extractText()
                if page1 != page2:
                    continue

        maybe_project_dir = glob.glob('{}/**/{}'.format(get_log_folder(), pdf_hash + ".tag"), recursive=True)


        if len(maybe_project_dir) > 0:
            return True, os.path.dirname(maybe_project_dir[0])

    # 如果所有页的内容都相同，戻る True
    return False, None

def log_chat(llm_model: str, input_str: str, output_str: str):
    if output_str and input_str and llm_model:
        uid = str(uuid.uuid4().hex)
        logging.info(f"[Model({uid})] {llm_model}")
        input_str = input_str.rstrip('\n')
        logging.info(f"[Query({uid})]\n{input_str}")
        output_str = output_str.rstrip('\n')
        logging.info(f"[Response({uid})]\n{output_str}\n\n")
