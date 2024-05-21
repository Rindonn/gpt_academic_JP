#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@ Author: Rindon
@ Date: 2024-05-13 09:42:46
@ LastEditors: Rindon
@ LastEditTime: 2024-05-21 10:07:41
@ Description: prompt、インターフェースを日本語に変更
'''
from toolbox import CatchException, update_ui, promote_file_to_downloadzone, get_log_folder, get_user
import re

f_prefix = 'GPT-Academic对话存档'

def write_chat_to_file(chatbot, history=None, file_name=None):
    """
    対話履歴をMarkdown形式でファイルに書き込む。ファイル名が指定されていない場合，Then use the current time to generate the file name。
    """
    import os
    import time
    if file_name is None:
        file_name = f_prefix + time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()) + '.html'
    fp = os.path.join(get_log_folder(get_user(chatbot), plugin_name='chat_history'), file_name)
    with open(fp, 'w', encoding='utf8') as f:
        from themes.theme import advanced_css
        f.write(f'<!DOCTYPE html><head><meta charset="utf-8"><title>対話履歴</title><style>{advanced_css}</style></head>')
        for i, contents in enumerate(chatbot):
            for j, content in enumerate(contents):
                try:    # このバグのトリガー条項件が見つかりませんでした，一時的にこれで対処する
                    if type(content) != str: content = str(content)
                except:
                    continue
                f.write(content)
                if j == 0:
                    f.write('<hr style="border-top: dotted 3px #ccc;">')
            f.write('<hr color="red"> \n\n')
        f.write('<hr color="blue"> \n\n raw chat context:\n')
        f.write('<code>')
        for h in history:
            f.write("\n>>>" + h)
        f.write('</code>')
    promote_file_to_downloadzone(fp, rename_file=file_name, chatbot=chatbot)
    return 'Write conversation history：' + fp

def gen_file_preview(file_name):
    try:
        with open(file_name, 'r', encoding='utf8') as f:
            file_content = f.read()
        # pattern to match the text between <head> and </head>
        pattern = re.compile(r'<head>.*?</head>', flags=re.DOTALL)
        file_content = re.sub(pattern, '', file_content)
        html, history = file_content.split('<hr color="blue"> \n\n raw chat context:\n')
        history = history.strip('<code>')
        history = history.strip('</code>')
        history = history.split("\n>>>")
        return list(filter(lambda x:x!="", history))[0][:100]
    except:
        return ""

def read_file_to_chat(chatbot, history, file_name):
    with open(file_name, 'r', encoding='utf8') as f:
        file_content = f.read()
    # pattern to match the text between <head> and </head>
    pattern = re.compile(r'<head>.*?</head>', flags=re.DOTALL)
    file_content = re.sub(pattern, '', file_content)
    html, history = file_content.split('<hr color="blue"> \n\n raw chat context:\n')
    history = history.strip('<code>')
    history = history.strip('</code>')
    history = history.split("\n>>>")
    history = list(filter(lambda x:x!="", history))
    html = html.split('<hr color="red"> \n\n')
    html = list(filter(lambda x:x!="", html))
    chatbot.clear()
    for i, h in enumerate(html):
        i_say, gpt_say = h.split('<hr style="border-top: dotted 3px #ccc;">')
        chatbot.append([i_say, gpt_say])
    chatbot.append([f"アーカイブファイルの詳細？", f"[Local Message] 対話をロードする{len(html)}条項，文脈{len(history)}条項。"])
    return chatbot, history

@CatchException
def ConversationHistoryArchive(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    """
    txt             入力欄にユーザーが入力したテキスト，翻訳が必要な例文，処理待ちのファイルを含むパスの例
    llm_kwargs      GPTモデルのパラメータ，温度やtop_pなど，通常はそのまま渡すだけでよい
    plugin_kwargs   プラグインモデルのパラメータ，現時点では使用するされていません
    chatbot         チャット表示ボックスのハンドル，ユーザーに表示するために使用するされます
    history         チャット履歴，前提の要約
    system_prompt   GPTに対するサイレントリマインダー
    user_request    当前用户的请求信息（IPAddress等）
    """

    chatbot.append(("現在の対話を保存する",
        f"[Local Message] {write_chat_to_file(chatbot, history)}，メニューの“LoadConversationHistoryArchive”を使って対話履歴を読み込むことが出来ます。"))
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する # GPTのリクエストには時間がかかるため，まず、タイムリーに画面を更新します

def hide_cwd(str):
    import os
    current_path = os.getcwd()
    replace_path = "."
    return str.replace(current_path, replace_path)

@CatchException
def LoadConversationHistoryArchive(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    """
    txt             入力欄にユーザーが入力したテキスト，翻訳が必要な例文，処理待ちのファイルを含むパスの例
    llm_kwargs      GPTモデルのパラメータ，温度やtop_pなど，通常はそのまま渡すだけでよい
    plugin_kwargs   プラグインモデルのパラメータ，現時点では使用するされていません
    chatbot         チャット表示ボックスのハンドル，ユーザーに表示するために使用するされます
    history         チャット履歴，前提の要約
    system_prompt   GPTに対するサイレントリマインダー
    user_request    当前用户的请求信息（IPAddress等）
    """
    from .crazy_utils import get_files_from_everything
    success, file_manifest, _ = get_files_from_everything(txt, type='.html')

    if not success:
        if txt == "": txt = '空の入力欄'
        import glob
        local_history = "<br/>".join([
            "`"+hide_cwd(f)+f" ({gen_file_preview(f)})"+"`"
            for f in glob.glob(
                f'{get_log_folder(get_user(chatbot), plugin_name="chat_history")}/**/{f_prefix}*.html',
                recursive=True
            )])
        chatbot.append([f"会話履歴ファイルを検索しています（HTML形式）: {txt}", f"htmlファイルが見つかりません: {txt}。ただし、次の履歴ファイルがローカルに保存されています，任意のファイルパスを入力エリアに貼り付けることができます，その後、再試行してください：<br/>{local_history}"])
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return

    try:
        chatbot, history = read_file_to_chat(chatbot, history, file_manifest[0])
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
    except:
        chatbot.append([f"対話履歴ファイルを読み込む", f"対話履歴ファイルが破損しています！"])
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return

@CatchException
def DeleteAllLocalConversationHistoryRecords(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    """
    txt             入力欄にユーザーが入力したテキスト，翻訳が必要な例文，処理待ちのファイルを含むパスの例
    llm_kwargs      GPTモデルのパラメータ，温度やtop_pなど，通常はそのまま渡すだけでよい
    plugin_kwargs   プラグインモデルのパラメータ，現時点では使用するされていません
    chatbot         チャット表示ボックスのハンドル，ユーザーに表示するために使用するされます
    history         チャット履歴，前提の要約
    system_prompt   GPTに対するサイレントリマインダー
    user_request    当前用户的请求信息（IPAddress等）
    """

    import glob, os
    local_history = "<br/>".join([
        "`"+hide_cwd(f)+"`"
        for f in glob.glob(
            f'{get_log_folder(get_user(chatbot), plugin_name="chat_history")}/**/{f_prefix}*.html', recursive=True
        )])
    for f in glob.glob(f'{get_log_folder(get_user(chatbot), plugin_name="chat_history")}/**/{f_prefix}*.html', recursive=True):
        os.remove(f)
    chatbot.append([f"すべての履歴対話ファイルを削除する", f"削除されました<br/>{local_history}"])
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
    return


