#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@ Author: Rindon
@ Date: 2024-05-13 09:42:46
@ LastEditors: Rindon
@ LastEditTime: 2024-05-21 14:55:36
@ Description: prompt、インターフェースを日本語に変更
'''
from toolbox import update_ui, promote_file_to_downloadzone, disable_auto_promotion
from toolbox import CatchException, report_exception, write_history_to_file
from .crazy_utils import input_clipping

def ParsingSourceCodeNew(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt):
    import os, copy
    from .crazy_utils import request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency
    from .crazy_utils import request_gpt_model_in_new_thread_with_ui_alive
    disable_auto_promotion(chatbot=chatbot)

    summary_batch_isolation = True
    inputs_array = []
    inputs_show_user_array = []
    history_array = []
    sys_prompt_array = []
    report_part_1 = []

    assert len(file_manifest) <= 512, "ソースファイルの数が多すぎます（512を超える）, 入力ファイルの数を減らしてください。"
    ############################## <ステップ1，ファイルを1つずつ分析する，マルチスレッド> ##################################
    for index, fp in enumerate(file_manifest):
        # ファイルを読み込んでいます
        with open(fp, 'r', encoding='utf-8', errors='replace') as f:
            file_content = f.read()
        prefix = "次に、以下のプロジェクトをファイルごとに分析してください" if index==0 else ""
        i_say = prefix + f'以下のプログラムファイルについて概要を説明してください。ファイル名は{os.path.relpath(fp, project_folder)}，ファイルのコードは ```{file_content}```'
        i_say_show_user = prefix + f'[{index}/{len(file_manifest)}] 以下のプログラムファイルについて概要を説明してください: {fp}'
        # リクエストコンテンツをロードする
        inputs_array.append(i_say)
        inputs_show_user_array.append(i_say_show_user)
        history_array.append([])
        sys_prompt_array.append("あなたはプログラムアーキテクチャアナリストです，ソースコードプロジェクトを分析しています。あなたの回答は簡潔で明確のが必要です。")

    # ファイルの読み込みが完了しました，各ソースコードファイルに対して，リクエストスレッドを生成する，chatgptに送信して分析する
    gpt_response_collection = yield from request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency(
        inputs_array = inputs_array,
        inputs_show_user_array = inputs_show_user_array,
        history_array = history_array,
        sys_prompt_array = sys_prompt_array,
        llm_kwargs = llm_kwargs,
        chatbot = chatbot,
        show_user_at_complete = True
    )

    # すべてのファイルの解析が完了しました，結果をファイルに書き込む，プロジェクトソースコードの集計分析を準備する
    report_part_1 = copy.deepcopy(gpt_response_collection)
    history_to_return = report_part_1
    res = write_history_to_file(report_part_1)
    promote_file_to_downloadzone(res, chatbot=chatbot)
    chatbot.append(("完了したか？", "1つずつファイルを分析した。" + res + "\n\n集計を開始しています。"))
    yield from update_ui(chatbot=chatbot, history=history_to_return) # 画面を更新する

    ############################## <2番目のステップ，総合，シングルスレッド，グループ化+反復処理> ##################################
    batchsize = 16  # 10ファイルを1グループとする
    report_part_2 = []
    previous_iteration_files = []
    last_iteration_result = ""
    while True:
        if len(file_manifest) == 0: break
        this_iteration_file_manifest = file_manifest[:batchsize]
        this_iteration_gpt_response_collection = gpt_response_collection[:batchsize*2]
        file_rel_path = [os.path.relpath(fp, project_folder) for index, fp in enumerate(this_iteration_file_manifest)]
        # 把“以下のプログラムファイルについて概要を説明してください” 替换成 精简的 "文件名：{all_file[index]}"
        for index, content in enumerate(this_iteration_gpt_response_collection):
            if index%2==0: this_iteration_gpt_response_collection[index] = f"{file_rel_path[index//2]}" # ファイル名のみを保持してトークンを節約する
        this_iteration_files = [os.path.relpath(fp, project_folder) for index, fp in enumerate(this_iteration_file_manifest)]
        previous_iteration_files.extend(this_iteration_files)
        previous_iteration_files_string = ', '.join(previous_iteration_files)
        current_iteration_focus = ', '.join(this_iteration_files)
        if summary_batch_isolation: focus = current_iteration_focus
        else:                       focus = previous_iteration_files_string
        i_say = f'以下のファイルの機能を簡単にMarkdownテーブルで説明してください：{focus}。上記の分析に基づいて，プログラムの全体的な機能を一言で示す。'
        if last_iteration_result != "":
            sys_prompt_additional = "あるコードが局所的に作用することが知られている：" + last_iteration_result + "\nプロジェクトの全体的な機能をより理解するために、ほかのコードを分析して下さい。"
        else:
            sys_prompt_additional = ""
        inputs_show_user = f'上記の分析に基づいて，プログラムの全体的な機能と構造をもう一度概要化して下さい，入力長の制限のため，グループ化処理が必要な場合があります，このグループのファイルは {current_iteration_focus} すでにまとめられたファイルグループ。'
        this_iteration_history = copy.deepcopy(this_iteration_gpt_response_collection)
        this_iteration_history.append(last_iteration_result)
        # inputをトリミングする
        inputs, this_iteration_history_feed = input_clipping(inputs=i_say, history=this_iteration_history, max_token_limit=2560)
        result = yield from request_gpt_model_in_new_thread_with_ui_alive(
            inputs=inputs, inputs_show_user=inputs_show_user, llm_kwargs=llm_kwargs, chatbot=chatbot,
            history=this_iteration_history_feed,   # Analysis before iteration
            sys_prompt="あなたはプログラムアーキテクチャアナリストです，プロジェクトのソースコードを分析しています。" + sys_prompt_additional)

        diagram_code = make_diagram(this_iteration_files, result, this_iteration_history_feed)
        summary = "これらのファイルの全体的な機能を一文で要約してください。\n\n" + diagram_code
        summary_result = yield from request_gpt_model_in_new_thread_with_ui_alive(
            inputs=summary,
            inputs_show_user=summary,
            llm_kwargs=llm_kwargs,
            chatbot=chatbot,
            history=[i_say, result],   # Analysis before iteration
            sys_prompt="あなたはプログラムアーキテクチャアナリストです，プロジェクトのソースコードを分析しています。" + sys_prompt_additional)

        report_part_2.extend([i_say, result])
        last_iteration_result = summary_result
        file_manifest = file_manifest[batchsize:]
        gpt_response_collection = gpt_response_collection[batchsize*2:]

    ############################## <END> ##################################
    history_to_return.extend(report_part_2)
    res = write_history_to_file(history_to_return)
    promote_file_to_downloadzone(res, chatbot=chatbot)
    chatbot.append(("完了したか？", res))
    yield from update_ui(chatbot=chatbot, history=history_to_return) # 画面を更新する

def make_diagram(this_iteration_files, result, this_iteration_history_feed):
    from crazy_functions.diagram_fns.file_tree import build_file_tree_mermaid_diagram
    return build_file_tree_mermaid_diagram(this_iteration_history_feed[0::2], this_iteration_history_feed[1::2], "项目示意图")

@CatchException
def ParseProjectItself(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    history = []    # 履歴をクリアする，オーバーフローを防ぐために
    import glob
    file_manifest = [f for f in glob.glob('./*.py')] + \
                    [f for f in glob.glob('./*/*.py')]
    project_folder = './'
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f"Pythonファイルが見つかりません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    yield from ParsingSourceCodeNew(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt)

@CatchException
def ParsePythonProject(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    history = []    # 履歴をクリアする，オーバーフローを防ぐために
    import glob, os
    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空の入力欄'
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f"ローカルプロジェクトが見つからないか、アクセス権がありません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.py', recursive=True)]
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f"Pythonファイルが見つかりません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    yield from ParsingSourceCodeNew(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt)

@CatchException
def AnalyzeAMatlabProject(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    history = []    # 履歴をクリアする，オーバーフローを防ぐために
    import glob, os
    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空の入力欄'
        report_exception(chatbot, history, a = f"解析Matlab项目: {txt}", b = f"ローカルプロジェクトが見つからないか、アクセス権がありません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.m', recursive=True)]
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a = f"解析Matlab项目: {txt}", b = f"見つかりません任何`.m`源文件: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    yield from ParsingSourceCodeNew(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt)

@CatchException
def ParseCProjectHeaderFiles(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    history = []    # 履歴をクリアする，オーバーフローを防ぐために
    import glob, os
    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空の入力欄'
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f"ローカルプロジェクトが見つからないか、アクセス権がありません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.h', recursive=True)]  + \
                    [f for f in glob.glob(f'{project_folder}/**/*.hpp', recursive=True)] #+ \
                    # [f for f in glob.glob(f'{project_folder}/**/*.c', recursive=True)]
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f".hヘッダーファイルが見つかりません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    yield from ParsingSourceCodeNew(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt)

@CatchException
def ParseCProject(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    history = []    # 履歴をクリアする，オーバーフローを防ぐために
    import glob, os
    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空の入力欄'
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f"ローカルプロジェクトが見つからないか、アクセス権がありません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.h', recursive=True)]  + \
                    [f for f in glob.glob(f'{project_folder}/**/*.cpp', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/*.hpp', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/*.c', recursive=True)]
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f".hヘッダーファイルが見つかりません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    yield from ParsingSourceCodeNew(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt)


@CatchException
def ParseJavaProject(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    history = []  # 履歴をクリアする，オーバーフローを防ぐために
    import glob, os
    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空の入力欄'
        report_exception(chatbot, history, a=f"プロジェクトを解析する: {txt}", b=f"ローカルプロジェクトが見つからないか、アクセス権がありません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.java', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/*.jar', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/*.xml', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/*.sh', recursive=True)]
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a=f"プロジェクトを解析する: {txt}", b=f"Javaファイルが見つかりません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    yield from ParsingSourceCodeNew(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt)


@CatchException
def ParseFrontendProject(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    history = []  # 履歴をクリアする，オーバーフローを防ぐために
    import glob, os
    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空の入力欄'
        report_exception(chatbot, history, a=f"プロジェクトを解析する: {txt}", b=f"ローカルプロジェクトが見つからないか、アクセス権がありません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.ts', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/*.tsx', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/*.json', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/*.js', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/*.vue', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/*.less', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/*.sass', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/*.wxml', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/*.wxss', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/*.css', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/*.jsx', recursive=True)]
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a=f"プロジェクトを解析する: {txt}", b=f"No frontend-related files can be found: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    yield from ParsingSourceCodeNew(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt)


@CatchException
def ParseGolangProject(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    history = []  # 履歴をクリアする，オーバーフローを防ぐために
    import glob, os
    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空の入力欄'
        report_exception(chatbot, history, a=f"プロジェクトを解析する: {txt}", b=f"ローカルプロジェクトが見つからないか、アクセス権がありません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.go', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/go.mod', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/go.sum', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/go.work', recursive=True)]
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a=f"プロジェクトを解析する: {txt}", b=f"Cannot find any golang files: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    yield from ParsingSourceCodeNew(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt)

@CatchException
def ParseRustProject(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    history = []  # 履歴をクリアする，オーバーフローを防ぐために
    import glob, os
    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空の入力欄'
        report_exception(chatbot, history, a=f"プロジェクトを解析する: {txt}", b=f"ローカルプロジェクトが見つからないか、アクセス権がありません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.rs', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/*.toml', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/*.lock', recursive=True)]
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a=f"プロジェクトを解析する: {txt}", b=f"Cannot find any golang files: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    yield from ParsingSourceCodeNew(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt)

@CatchException
def ParsingLuaProject(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    history = []    # 履歴をクリアする，オーバーフローを防ぐために
    import glob, os
    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空の入力欄'
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f"ローカルプロジェクトが見つからないか、アクセス権がありません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.lua', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/*.xml', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/*.json', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/*.toml', recursive=True)]
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f"luaファイルが見つかりません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    yield from ParsingSourceCodeNew(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt)


@CatchException
def ParsingCSharpProject(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    history = []    # 履歴をクリアする，オーバーフローを防ぐために
    import glob, os
    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空の入力欄'
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f"ローカルプロジェクトが見つからないか、アクセス権がありません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.cs', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/*.csproj', recursive=True)]
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f"CSharpファイルが見つかりません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    yield from ParsingSourceCodeNew(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt)


@CatchException
def ParseAnyCodeProject(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    txt_pattern = plugin_kwargs.get("advanced_arg")
    txt_pattern = txt_pattern.replace("，", ",")
    # マッチングするパターン(例えば: *.c, *.cpp, *.py, config.toml)
    pattern_include = [_.lstrip(" ,").rstrip(" ,") for _ in txt_pattern.split(",") if _ != "" and not _.strip().startswith("^")]
    if not pattern_include: pattern_include = ["*"] # No input means all matches
    # 一致するファイルの拡張子を無視する予定です(例えば: ^*.c, ^*.cpp, ^*.py)
    pattern_except_suffix = [_.lstrip(" ^*.,").rstrip(" ,") for _ in txt_pattern.split(" ") if _ != "" and _.strip().startswith("^*.")]
    pattern_except_suffix += ['zip', 'rar', '7z', 'tar', 'gz'] # 圧縮ファイルの解析を避ける
    # 一致するファイル名を無視する予定です(例えば: ^README.md)
    pattern_except_name = [_.lstrip(" ^*,").rstrip(" ,").replace(".", r"\.") # 移除左边通配符，移除右侧逗号，转义点号
                           for _ in txt_pattern.split(" ") # 以空格分割
                           if (_ != "" and _.strip().startswith("^") and not _.strip().startswith("^*."))   # ^開始，但不是^*.開始
                           ]
    # 正規表現を生成する
    pattern_except = r'/[^/]+\.(' + "|".join(pattern_except_suffix) + ')$'
    pattern_except += '|/(' + "|".join(pattern_except_name) + ')$' if pattern_except_name != [] else ''

    history.clear()
    import glob, os, re
    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空の入力欄'
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f"ローカルプロジェクトが見つからないか、アクセス権がありません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    # 圧縮ファイルをアップロードする場合, 解凍されたフォルダのパスを最初に検索する, 圧縮ファイルの解析を回避するため
    maybe_dir = [f for f in glob.glob(f'{project_folder}/*') if os.path.isdir(f)]
    if len(maybe_dir)>0 and maybe_dir[0].endswith('.extract'):
        extract_folder_path = maybe_dir[0]
    else:
        extract_folder_path = project_folder
    # Find uploaded uncompressed files and decompressed files according to the input matching mode
    file_manifest = [f for pattern in pattern_include for f in glob.glob(f'{extract_folder_path}/**/{pattern}', recursive=True) if "" != extract_folder_path and \
                      os.path.isfile(f) and (not re.search(pattern_except, f) or pattern.endswith('.' + re.search(pattern_except, f).group().split('.')[-1]))]
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f"ファイルが見つかりません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    yield from ParsingSourceCodeNew(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt)