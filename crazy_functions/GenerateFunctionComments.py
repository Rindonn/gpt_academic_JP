from toolbox import update_ui
from toolbox import CatchException, report_exception
from toolbox import write_history_to_file, promote_file_to_downloadzone
from .crazy_utils import request_gpt_model_in_new_thread_with_ui_alive
fast_debug = False

def GenerateFunctionComments(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt):
    import time, os
    print('begin analysis on:', file_manifest)
    for index, fp in enumerate(file_manifest):
        with open(fp, 'r', encoding='utf-8', errors='replace') as f:
            file_content = f.read()

        i_say = f'以下のプログラムファイルについて概要を説明してください，すべての関数にコメントを生成する，markdownテーブルを使用するして結果を出力する，ファイル名は{os.path.relpath(fp, project_folder)}，ファイルの内容は ```{file_content}```'
        i_say_show_user = f'[{index}/{len(file_manifest)}] 以下のプログラムファイルについて概要を説明してください，すべての関数にコメントを生成する: {os.path.abspath(fp)}'
        chatbot.append((i_say_show_user, "[Local Message] waiting gpt response."))
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する

        if not fast_debug:
            msg = '正常'
            # ** gpt request **
            gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(
                i_say, i_say_show_user, llm_kwargs, chatbot, history=[], sys_prompt=system_prompt)   # タイムアウトカウントダウン付き

            chatbot[-1] = (i_say_show_user, gpt_say)
            history.append(i_say_show_user); history.append(gpt_say)
            yield from update_ui(chatbot=chatbot, history=history, msg=msg) # 画面を更新する
            if not fast_debug: time.sleep(2)

    if not fast_debug:
        res = write_history_to_file(history)
        promote_file_to_downloadzone(res, chatbot=chatbot)
        chatbot.append(("完了しましたか？", res))
        yield from update_ui(chatbot=chatbot, history=history, msg=msg) # 画面を更新する



@CatchException
def BatchGenerateFunctionComments(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    history = []    # 履歴をクリアする，オーバーフローを防ぐために
    import glob, os
    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空の入力欄'
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f"ローカルプロジェクトが見つからないか、アクセス権がありません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.py', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/*.cpp', recursive=True)]

    if len(file_manifest) == 0:
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f"テキストの翻訳: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    yield from GenerateFunctionComments(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt)
