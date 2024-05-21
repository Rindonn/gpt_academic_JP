#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@ Author: Rindon
@ Date: 2024-05-13 09:42:46
@ LastEditors: Rindon
@ LastEditTime: 2024-05-21 13:50:40
@ Description: prompt、インターフェースを日本語に変更
'''
from toolbox import update_ui, trimmed_format_exc, promote_file_to_downloadzone, get_log_folder
from toolbox import CatchException, report_exception, write_history_to_file, zip_folder


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
                    self.sp_file_tag.append(self.file_paths[index] + f".part-{j}.tex")

        print('Segmentation: done')
    def merge_result(self):
        self.file_result = ["" for _ in range(len(self.file_paths))]
        for r, k in zip(self.sp_file_result, self.sp_file_index):
            self.file_result[k] += r

    def write_result(self):
        manifest = []
        for path, res in zip(self.file_paths, self.file_result):
            with open(path + '.polish.tex', 'w', encoding='utf8') as f:
                manifest.append(path + '.polish.tex')
                f.write(res)
        return manifest

    def zip_result(self):
        import os, time
        folder = os.path.dirname(self.file_paths[0])
        t = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
        zip_folder(folder, get_log_folder(), f'{t}-polished.zip')


def ProofreadMultipleFiles(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, language='en', mode='polish'):
    import time, os, re
    from .crazy_utils import request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency


    #  <-------- Latexファイルを読み込む，すべてのコメントを削除する ---------->
    pfg = PaperFileGroup()

    for index, fp in enumerate(file_manifest):
        with open(fp, 'r', encoding='utf-8', errors='replace') as f:
            file_content = f.read()
            # コメントの正規表現を定義する
            comment_pattern = r'(?<!\\)%.*'
            # Use regular expressions to find comments，空の文字列に置き換える
            clean_tex_content = re.sub(comment_pattern, '', file_content)
            # コメントを削除したテキストを記録する
            pfg.file_paths.append(fp)
            pfg.file_contents.append(clean_tex_content)

    #  <-------- Split overly long latex files ---------->
    pfg.run_file_split(max_token_limit=1024)
    n_split = len(pfg.sp_file_contents)


    #  <-------- マルチスレッドの改善が開始されました ---------->
    if language == 'en':
        if mode == 'polish':
            inputs_array = [r"Below is a section from an academic paper, polish this section to meet the academic standard, " +
                            r"improve the grammar, clarity and overall readability, do not modify any latex command such as \section, \cite and equations:" +
                            f"\n\n{frag}" for frag in pfg.sp_file_contents]
        else:
            inputs_array = [r"Below is a section from an academic paper, proofread this section." +
                            r"Do not modify any latex command such as \section, \cite, \begin, \item and equations. " +
                            r"Answer me only with the revised text:" +
                        f"\n\n{frag}" for frag in pfg.sp_file_contents]
        inputs_show_user_array = [f"Polish {f}" for f in pfg.sp_file_tag]
        sys_prompt_array = ["You are a professional academic paper writer." for _ in range(n_split)]
    elif language == 'zh':
        if mode == 'polish':
            inputs_array = [r"以下は学術論文の一部です，この部分を学術基準に合わせてタッチアップしてください，文法、明確さ、全体的な読みやすさを向上させて，LaTeXコマンドを変更しないでください，\section, \citeとequationsのように：" +
                            f"\n\n{frag}" for frag in pfg.sp_file_contents]
        else:
            inputs_array = [r"以下は学術論文の一部です，この部分の内容に文法修正を行ってください。LaTeXコマンドを変更しないでください，\section, \citeとequationsのように：" +
                            f"\n\n{frag}" for frag in pfg.sp_file_contents]
        inputs_show_user_array = [f"校正中 {f}" for f in pfg.sp_file_tag]
        sys_prompt_array=["あなたは専門の日本語学術論文作家です。" for _ in range(n_split)]


    gpt_response_collection = yield from request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency(
        inputs_array=inputs_array,
        inputs_show_user_array=inputs_show_user_array,
        llm_kwargs=llm_kwargs,
        chatbot=chatbot,
        history_array=[[""] for _ in range(n_split)],
        sys_prompt_array=sys_prompt_array,
        # max_workers=5,  # Parallel task quantity limit，同時に最大5つ実行できます，その他の待ち行列
        scroller_max_len = 80
    )

    #  <-------- 原始文本，Organized results为テキストの翻訳 ---------->
    try:
        pfg.sp_file_result = []
        for i_say, gpt_say in zip(gpt_response_collection[0::2], gpt_response_collection[1::2]):
            pfg.sp_file_result.append(gpt_say)
        pfg.merge_result()
        pfg.write_result()
        pfg.zip_result()
    except:
        print(trimmed_format_exc())

    #  <-------- Organized results，終了 ---------->
    create_report_file_name = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()) + f"-chatgpt.polish.md"
    res = write_history_to_file(gpt_response_collection, file_basename=create_report_file_name)
    promote_file_to_downloadzone(res, chatbot=chatbot)

    history = gpt_response_collection
    chatbot.append((f"{fp}完了したか？", res))
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する


@CatchException
def EnglishProofreadingForLatex(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    # 基本情報：機能、貢献者
    chatbot.append([
        "関数プラグイン機能？",
        "Latexプロジェクトをタッチアップする。関数プラグインの貢献者: Binary-Husky。（Latexを利用する場合：「LatexEnglishCorrection+ハイライト修正(LaTeXが必要)プラグイン」を利用してください"])
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する

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
    import glob, os
    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空の入力欄'
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f"ローカルプロジェクトが見つからないか、アクセス権がありません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.tex', recursive=True)]
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f"テキストの翻訳: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    yield from ProofreadMultipleFiles(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, language='en')






@CatchException
def LatexChineseProofreading(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    # 基本情報：機能、貢献者
    chatbot.append([
        "関数プラグイン機能？",
        "Latexプロジェクトをタッチアップする。関数プラグインの貢献者: Binary-Husky"])
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する

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
    import glob, os
    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空の入力欄'
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f"ローカルプロジェクトが見つからないか、アクセス権がありません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.tex', recursive=True)]
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f"テキストの翻訳: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    yield from ProofreadMultipleFiles(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, language='zh')




@CatchException
def LatexEnglishCorrection(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    # 基本情報：機能、貢献者
    chatbot.append([
        "関数プラグイン機能？",
        "Latexプロジェクトを修正する。関数プラグインの貢献者: Binary-Husky"])
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する

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
    import glob, os
    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空の入力欄'
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f"ローカルプロジェクトが見つからないか、アクセス権がありません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.tex', recursive=True)]
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f"テキストの翻訳: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    yield from ProofreadMultipleFiles(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, language='en', mode='proofread')



