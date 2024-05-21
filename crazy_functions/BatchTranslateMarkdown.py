#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@ Author: Rindon
@ Date: 2024-05-13 09:42:46
@ LastEditors: Rindon
@ LastEditTime: 2024-05-21 15:30:55
@ Description: prompt、インターフェースを日本語に変更
'''
import glob, time, os, re, logging
from toolbox import update_ui, trimmed_format_exc, gen_time_str, disable_auto_promotion
from toolbox import CatchException, report_exception, get_log_folder
from toolbox import write_history_to_file, promote_file_to_downloadzone
fast_debug = False

class PaperFileGroup():
    def __init__(self):
        self.file_paths = []
        self.file_contents = []
        self.sp_file_contents = []
        self.sp_file_index = []
        self.sp_file_tag = []

        # count_token
        from request_llms.bridge_all import model_info
        enc = model_info["gpt-3.5-turbo"]['tokenizer']
        def get_token_num(txt): return len(enc.encode(txt, disallowed_special=()))
        self.get_token_num = get_token_num

    def run_file_split(self, max_token_limit=1900):
        """
        長いテキストを分離する
        """
        for index, file_content in enumerate(self.file_contents):
            if self.get_token_num(file_content) < max_token_limit:
                self.sp_file_contents.append(file_content)
                self.sp_file_index.append(index)
                self.sp_file_tag.append(self.file_paths[index])
            else:
                from crazy_functions.pdf_fns.breakdown_txt import breakdown_text_to_satisfy_token_limit
                segments = breakdown_text_to_satisfy_token_limit(file_content, max_token_limit)
                for j, segment in enumerate(segments):
                    self.sp_file_contents.append(segment)
                    self.sp_file_index.append(index)
                    self.sp_file_tag.append(self.file_paths[index] + f".part-{j}.md")
        logging.info('Segmentation: done')

    def merge_result(self):
        self.file_result = ["" for _ in range(len(self.file_paths))]
        for r, k in zip(self.sp_file_result, self.sp_file_index):
            self.file_result[k] += r

    def write_result(self, language):
        manifest = []
        for path, res in zip(self.file_paths, self.file_result):
            dst_file = os.path.join(get_log_folder(), f'{gen_time_str()}.md')
            with open(dst_file, 'w', encoding='utf8') as f:
                manifest.append(dst_file)
                f.write(res)
        return manifest

def TranslateMultipleFiles(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, language='en'):
    from .crazy_utils import request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency

    #  <-------- Markdownファイルを読み込む，すべてのコメントを削除する ---------->
    pfg = PaperFileGroup()

    for index, fp in enumerate(file_manifest):
        with open(fp, 'r', encoding='utf-8', errors='replace') as f:
            file_content = f.read()
            # コメントを削除したテキストを記録する
            pfg.file_paths.append(fp)
            pfg.file_contents.append(file_content)

    #  <-------- 長すぎるMarkdownファイルを分割する ---------->
    pfg.run_file_split(max_token_limit=1500)
    n_split = len(pfg.sp_file_contents)

    #  <-------- マルチスレッド翻訳が開始されました ---------->
    if language == 'en->zh':
        inputs_array = ["This is a Markdown file, translate it into japanese, do not modify any existing Markdown commands:" +
                        f"\n\n{frag}" for frag in pfg.sp_file_contents]
        inputs_show_user_array = [f"翻訳 {f}" for f in pfg.sp_file_tag]
        sys_prompt_array = ["You are a professional academic paper translator." for _ in range(n_split)]
    elif language == 'zh->en':
        inputs_array = [f"This is a Markdown file, translate it into English, do not modify any existing Markdown commands:" +
                        f"\n\n{frag}" for frag in pfg.sp_file_contents]
        inputs_show_user_array = [f"翻訳 {f}" for f in pfg.sp_file_tag]
        sys_prompt_array = ["You are a professional academic paper translator." for _ in range(n_split)]
    else:
        inputs_array = [f"This is a Markdown file, translate it into {language}, do not modify any existing Markdown commands, only answer me with translated results:" +
                        f"\n\n{frag}" for frag in pfg.sp_file_contents]
        inputs_show_user_array = [f"翻訳 {f}" for f in pfg.sp_file_tag]
        sys_prompt_array = ["You are a professional academic paper translator." for _ in range(n_split)]

    gpt_response_collection = yield from request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency(
        inputs_array=inputs_array,
        inputs_show_user_array=inputs_show_user_array,
        llm_kwargs=llm_kwargs,
        chatbot=chatbot,
        history_array=[[""] for _ in range(n_split)],
        sys_prompt_array=sys_prompt_array,
        # max_workers=5,  # OpenAIが許可する最大並列過負荷
        scroller_max_len = 80
    )
    try:
        pfg.sp_file_result = []
        for i_say, gpt_say in zip(gpt_response_collection[0::2], gpt_response_collection[1::2]):
            pfg.sp_file_result.append(gpt_say)
        pfg.merge_result()
        pfg.write_result(language)
    except:
        logging.error(trimmed_format_exc())

    #  <-------- Organized results，終了 ---------->
    create_report_file_name = gen_time_str() + f"-chatgpt.md"
    res = write_history_to_file(gpt_response_collection, file_basename=create_report_file_name)
    promote_file_to_downloadzone(res, chatbot=chatbot)
    history = gpt_response_collection
    chatbot.append((f"{fp}完了したか？", res))
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する


def get_files_from_everything(txt, preference=''):
    if txt == "": return False, None, None
    success = True
    if txt.startswith('http'):
        import requests
        from toolbox import get_conf
        proxies = get_conf('proxies')
        # リモートファイルのネットワーク
        if preference == 'Github':
            logging.info('GitHubからリソースをダウンロードしています ...')
            if not txt.endswith('.md'):
                # Make a request to the GitHub API to retrieve the repository information
                url = txt.replace("https://github.com/", "https://api.github.com/repos/") + '/readme'
                response = requests.get(url, proxies=proxies)
                txt = response.json()['download_url']
            else:
                txt = txt.replace("https://github.com/", "https://raw.githubusercontent.com/")
                txt = txt.replace("/blob/", "/")

        r = requests.get(txt, proxies=proxies)
        download_local = f'{get_log_folder(plugin_name="BatchTranslateMarkdown")}/raw-readme-{gen_time_str()}.md'
        project_folder = f'{get_log_folder(plugin_name="BatchTranslateMarkdown")}'
        with open(download_local, 'wb+') as f: f.write(r.content)
        file_manifest = [download_local]
    elif txt.endswith('.md'):
        # ファイルを直接指定する
        file_manifest = [txt]
        project_folder = os.path.dirname(txt)
    elif os.path.exists(txt):
        # ローカルパス，Recursive search
        project_folder = txt
        file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.md', recursive=True)]
    else:
        project_folder = None
        file_manifest = []
        success = False

    return success, file_manifest, project_folder


@CatchException
def TranslateMarkdownFromEnglishToChinese(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    # 基本情報：機能、貢献者
    chatbot.append([
        "関数プラグイン機能？",
        "Markdownプロジェクトを翻訳する。関数プラグインの貢献者: Binary-Husky"])
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
    disable_auto_promotion(chatbot)

    # 依存関係のインポートを試みる，依存関係が不足している場合，インストールの提案を行います
    try:
        import tiktoken
    except:
        report_exception(chatbot, history,
                         a=f"プロジェクトを解析する: {txt}",
                         b=f"ソフトウェアの依存関係のインポートに失敗しました。このモジュールを使用するするには、追加の依存関係が必要です，インストールテキストの翻訳```pip install --upgrade tiktoken```。")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    history = []    # 履歴をクリアする，オーバーフローを防ぐために

    success, file_manifest, project_folder = get_files_from_everything(txt, preference="Github")

    if not success:
        # テキストの翻訳
        if txt == "": txt = '空の入力欄'
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f"ローカルプロジェクトが見つからないか、アクセス権がありません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return

    if len(file_manifest) == 0:
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f".mdファイルが見つかりません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return

    yield from TranslateMultipleFiles(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, language='en->zh')





@CatchException
def MarkdownChineseToEnglish(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    # 基本情報：機能、貢献者
    chatbot.append([
        "関数プラグイン機能？",
        "Markdownプロジェクトを翻訳する。関数プラグインの貢献者: Binary-Husky"])
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
    disable_auto_promotion(chatbot)

    # 依存関係のインポートを試みる，依存関係が不足している場合，インストールの提案を行います
    try:
        import tiktoken
    except:
        report_exception(chatbot, history,
                         a=f"プロジェクトを解析する: {txt}",
                         b=f"ソフトウェアの依存関係のインポートに失敗しました。このモジュールを使用するするには、追加の依存関係が必要です，インストールテキストの翻訳```pip install --upgrade tiktoken```。")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    history = []    # 履歴をクリアする，オーバーフローを防ぐために
    success, file_manifest, project_folder = get_files_from_everything(txt)
    if not success:
        # テキストの翻訳
        if txt == "": txt = '空の入力欄'
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f"ローカルプロジェクトが見つからないか、アクセス権がありません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f".mdファイルが見つかりません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    yield from TranslateMultipleFiles(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, language='zh->en')


@CatchException
def TranslateMarkdownToSpecifiedLanguage(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    # 基本情報：機能、貢献者
    chatbot.append([
        "関数プラグイン機能？",
        "Markdownプロジェクトを翻訳する。関数プラグインの貢献者: Binary-Husky"])
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
    disable_auto_promotion(chatbot)

    # 依存関係のインポートを試みる，依存関係が不足している場合，インストールの提案を行います
    try:
        import tiktoken
    except:
        report_exception(chatbot, history,
                         a=f"プロジェクトを解析する: {txt}",
                         b=f"ソフトウェアの依存関係のインポートに失敗しました。このモジュールを使用するするには、追加の依存関係が必要です，インストールテキストの翻訳```pip install --upgrade tiktoken```。")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    history = []    # 履歴をクリアする，オーバーフローを防ぐために
    success, file_manifest, project_folder = get_files_from_everything(txt)
    if not success:
        # テキストの翻訳
        if txt == "": txt = '空の入力欄'
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f"ローカルプロジェクトが見つからないか、アクセス権がありません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f".mdファイルが見つかりません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return

    if ("advanced_arg" in plugin_kwargs) and (plugin_kwargs["advanced_arg"] == ""): plugin_kwargs.pop("advanced_arg")
    language = plugin_kwargs.get("advanced_arg", 'japanese')
    yield from TranslateMultipleFiles(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, language=language)