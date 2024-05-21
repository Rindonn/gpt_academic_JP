#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@ Author: Rindon
@ Date: 2024-05-13 09:42:46
@ LastEditors: Rindon
@ LastEditTime: 2024-05-21 15:10:41
@ Description: prompt、インターフェースを日本語に変更
'''
from toolbox import update_ui
from toolbox import CatchException, report_exception
from toolbox import write_history_to_file, promote_file_to_downloadzone
from .crazy_utils import request_gpt_model_in_new_thread_with_ui_alive
fast_debug = False


def ParseDocx(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt):
    import time, os
    # pip install python-docxはdocx形式に使用するされます，クロスプラットフォーム
    # doc形式に使用するするためのpip install pywin32，Winプラットフォームのみサポート
    for index, fp in enumerate(file_manifest):
        if fp.split(".")[-1] == "docx":
            from docx import Document
            doc = Document(fp)
            file_content = "\n".join([para.text for para in doc.paragraphs])
        else:
            try:
                import win32com.client
                word = win32com.client.Dispatch("Word.Application")
                word.visible = False
                # ファイルを開く
                doc = word.Documents.Open(os.getcwd() + '/' + fp)
                # file_content = doc.Content.Text
                doc = word.ActiveDocument
                file_content = doc.Range().Text
                doc.Close()
                word.Quit()
            except:
                raise RuntimeError('.docドキュメントを.docxドキュメントに変換してください。')

        # private_upload内のファイル名は、zipを解凍すると文字化けしやすいです（rarおよび7z形式が正常である），So only the content of the article can be analyzed，Do not enter file name
        from crazy_functions.pdf_fns.breakdown_txt import breakdown_text_to_satisfy_token_limit
        from request_llms.bridge_all import model_info
        max_token = model_info[llm_kwargs['llm_model']]['max_token']
        TOKEN_LIMIT_PER_FRAGMENT = max_token * 3 // 4
        paper_fragments = breakdown_text_to_satisfy_token_limit(txt=file_content, limit=TOKEN_LIMIT_PER_FRAGMENT, llm_model=llm_kwargs['llm_model'])
        this_paper_history = []
        for i, paper_frag in enumerate(paper_fragments):
            i_say = f'以下の記事のセグメントについて、日本語で概要を説明してください，ファイル名は{os.path.relpath(fp, project_folder)}，The content of the article is ```{paper_frag}```'
            i_say_show_user = f'以下の記事のセグメントについて概要を説明してください: {os.path.abspath(fp)}の{i+1}/{len(paper_fragments)}フラグメント。'
            gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(
                inputs=i_say,
                inputs_show_user=i_say_show_user,
                llm_kwargs=llm_kwargs,
                chatbot=chatbot,
                history=[],
                sys_prompt="記事をまとめる。"
            )

            chatbot[-1] = (i_say_show_user, gpt_say)
            history.extend([i_say_show_user,gpt_say])
            this_paper_history.extend([i_say_show_user,gpt_say])

        # 記事のすべてのセグメントを要約しました，記事が分割された場合，
        if len(paper_fragments) > 1:
            i_say = f"上記の対話に基づいて，記事をまとめた{os.path.abspath(fp)}主な内容。"
            gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(
                inputs=i_say,
                inputs_show_user=i_say,
                llm_kwargs=llm_kwargs,
                chatbot=chatbot,
                history=this_paper_history,
                sys_prompt="記事をまとめる。"
            )

            history.extend([i_say,gpt_say])
            this_paper_history.extend([i_say,gpt_say])

        res = write_history_to_file(history)
        promote_file_to_downloadzone(res, chatbot=chatbot)
        chatbot.append(("完了したか？", res))
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する

    res = write_history_to_file(history)
    promote_file_to_downloadzone(res, chatbot=chatbot)
    chatbot.append(("すべてのファイルが要約されていますか？", res))
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する


@CatchException
def SummarizingWordDocuments(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    import glob, os

    # 基本情報：機能、貢献者
    chatbot.append([
        "関数プラグイン機能？",
        "Word文書を一括で要約する。関数プラグインの貢献者: JasonGuo1。注意, .docファイルの場合, まず.docx形式に変換してください。"])
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する

    # 依存関係のインポートを試みる，依存関係が不足している場合，インストールの提案を行います
    try:
        from docx import Document
    except:
        report_exception(chatbot, history,
                         a=f"プロジェクトを解析する: {txt}",
                         b=f"ソフトウェアの依存関係のインポートに失敗しました。このモジュールを使用するするには、追加の依存関係が必要です，インストールには：```pip install --upgrade python-docx pywin32```。")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return

    # 履歴をクリアする，オーバーフローを防ぐために
    history = []

    # 入力パラメータを検出する，入力パラメータが指定されていない場合，直接終了する
    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空の入力欄'
        report_exception(chatbot, history, a=f"プロジェクトを解析する: {txt}", b=f"ローカルプロジェクトが見つからないか、アクセス権がありません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return

    # 処理する必要のあるファイルリストを検索する
    if txt.endswith('.docx') or txt.endswith('.doc'):
        file_manifest = [txt]
    else:
        file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.docx', recursive=True)] + \
                        [f for f in glob.glob(f'{project_folder}/**/*.doc', recursive=True)]

    # ファイルが見つからなかった場合
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a=f"プロジェクトを解析する: {txt}", b=f"Cannot find any .docx or .doc files: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return

    # タスクを正式に実行する
    yield from ParseDocx(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt)
