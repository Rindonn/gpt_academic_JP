# 本源代码中, ⭐ = 关键步骤
"""
测试：
    - 裁剪图像，保留下半部分
    - 交换图像的青色通道and赤色通道
    - 置き換える图像转为灰度图像
    - 置き換えるcsv文件转excel表格

Testing:
    - Crop the image, keeping the bottom half.
    - Swap the blue channel and red channel of the image.
    - Convert the image to grayscale.
    - Convert the CSV file to an Excel spreadsheet.
"""


from toolbox import CatchException, update_ui, gen_time_str, trimmed_format_exc, is_the_upload_folder
from toolbox import promote_file_to_downloadzone, get_log_folder, update_ui_lastest_msg
from .crazy_utils import request_gpt_model_in_new_thread_with_ui_alive, get_plugin_arg
from .crazy_utils import input_clipping, try_install_deps
from crazy_functions.gen_fns.gen_fns_shared import is_function_successfully_generated
from crazy_functions.gen_fns.gen_fns_shared import get_class_name
from crazy_functions.gen_fns.gen_fns_shared import subprocess_worker
from crazy_functions.gen_fns.gen_fns_shared import try_make_module
import os
import time
import glob
import multiprocessing

templete = """
```python
import ...  # Put dependencies here, e.g. import numpy as np.

class TerminalFunction(object): # Do not change the name of the class, The name of the class must be `TerminalFunction`

    def run(self, path):    # The name of the function must be `run`, it takes only a positional argument.
        # rewrite the function you have just written here
        ...
        return generated_file_path
```
"""

def inspect_dependency(chatbot, history):
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
    return True

def get_code_block(reply):
    import re
    pattern = r"```([\s\S]*?)```" # regex pattern to match code blocks
    matches = re.findall(pattern, reply) # find all code blocks in text
    if len(matches) == 1:
        return matches[0].strip('python') #  code block
    for match in matches:
        if 'class TerminalFunction' in match:
            return match.strip('python') #  code block
    raise RuntimeError("GPT is not generating proper code.")

def gpt_interact_multi_step(txt, file_type, llm_kwargs, chatbot, history):
    # 入力
    prompt_compose = [
        f'Your job:\n'
        f'1. write a single Python function, which takes a path of a `{file_type}` file as the only argument and returns a `string` containing the result of analysis or the path of generated files. \n',
        f"2. You should write this function to perform following task: " + txt + "\n",
        f"3. Wrap the output python function with markdown codeblock."
    ]
    i_say = "".join(prompt_compose)
    demo = []

    # ステップ1
    gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(
        inputs=i_say, inputs_show_user=i_say,
        llm_kwargs=llm_kwargs, chatbot=chatbot, history=demo,
        sys_prompt= r"You are a world-class programmer."
    )
    history.extend([i_say, gpt_say])
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する # インターフェースの更新

    # 2番目のステップ
    prompt_compose = [
        "If previous stage is successful, rewrite the function you have just written to satisfy following templete: \n",
        templete
    ]
    i_say = "".join(prompt_compose); inputs_show_user = "If previous stage is successful, rewrite the function you have just written to satisfy executable templete. "
    gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(
        inputs=i_say, inputs_show_user=inputs_show_user,
        llm_kwargs=llm_kwargs, chatbot=chatbot, history=history,
        sys_prompt= r"You are a programmer. You need to replace `...` with valid packages, do not give `...` in your answer!"
    )
    code_to_return = gpt_say
    history.extend([i_say, gpt_say])
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する # インターフェースの更新

    # # 第三步
    # i_say = "Please list to packages to install to run the code above. Then show me how to use `try_install_deps` function to install them."
    # i_say += 'For instance. `try_install_deps(["opencv-python", "scipy", "numpy"])`'
    # installation_advance = yield from request_gpt_model_in_new_thread_with_ui_alive(
    #     inputs=i_say, inputs_show_user=inputs_show_user,
    #     llm_kwargs=llm_kwargs, chatbot=chatbot, history=history,
    #     sys_prompt= r"You are a programmer."
    # )

    # # # 第三步
    # i_say = "Show me how to use `pip` to install packages to run the code above. "
    # i_say += 'For instance. `pip install -r opencv-python scipy numpy`'
    # installation_advance = yield from request_gpt_model_in_new_thread_with_ui_alive(
    #     inputs=i_say, inputs_show_user=i_say,
    #     llm_kwargs=llm_kwargs, chatbot=chatbot, history=history,
    #     sys_prompt= r"You are a programmer."
    # )
    installation_advance = ""

    return code_to_return, installation_advance, txt, file_type, llm_kwargs, chatbot, history




def for_immediate_show_off_when_possible(file_type, fp, chatbot):
    if file_type in ['png', 'jpg']:
        image_path = os.path.abspath(fp)
        chatbot.append(['这是一张图片, 展示如下:',
            f'ローカルファイルアドレス: <br/>`{image_path}`<br/>'+
            f'ローカルファイルのプレビュー: <br/><div align="center"><img src="file={image_path}"></div>'
        ])
    return chatbot



def have_any_recent_upload_files(chatbot):
    _5min = 5 * 60
    if not chatbot: return False    # chatbot is None
    most_recent_uploaded = chatbot._cookies.get("most_recent_uploaded", None)
    if not most_recent_uploaded: return False   # most_recent_uploaded is None
    if time.time() - most_recent_uploaded["time"] < _5min: return True # most_recent_uploaded is new
    else: return False  # most_recent_uploaded is too old

def get_recent_file_prompt_support(chatbot):
    most_recent_uploaded = chatbot._cookies.get("most_recent_uploaded", None)
    path = most_recent_uploaded['path']
    return path

@CatchException
def DynamicFunctionGeneration(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    """
    txt             入力欄にユーザーが入力したテキスト，翻訳が必要な例文，処理待ちのファイルを含むパスの例
    llm_kwargs      GPTモデルのパラメータ，温度やtop_pなど，通常はそのまま渡すだけでよい
    plugin_kwargs   プラグインモデルのパラメータ，現時点では使用するされていません
    chatbot         チャット表示ボックスのハンドル，ユーザーに表示するために使用するされます
    history         チャット履歴，前提の要約
    system_prompt   GPTに対するサイレントリマインダー
    user_request    当前用户的请求信息（IPAddress等）
    """

    # 履歴をクリアする
    history = []

    # 基本情報：機能、貢献者
    chatbot.append(["正在启动: プラグイン动态生成プラグイン", "プラグイン动态生成, 执行開始, 著者Binary-Husky."])
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する

    # ⭐ ファイルアップロードエリア是否有东西
    # 1. ある場合文件: 作为函数パラメータ
    # 2. 如果没有文件：需要用GPT提取パラメータ （太懒了，以后再写，VoidTerminal已经实现了类似的代码）
    file_list = []
    if get_plugin_arg(plugin_kwargs, key="file_path_arg", default=False):
        file_path = get_plugin_arg(plugin_kwargs, key="file_path_arg", default=None)
        file_list.append(file_path)
        yield from update_ui_lastest_msg(f"当前文件: {file_path}", chatbot, history, 1)
    elif have_any_recent_upload_files(chatbot):
        file_dir = get_recent_file_prompt_support(chatbot)
        file_list = glob.glob(os.path.join(file_dir, '**/*'), recursive=True)
        yield from update_ui_lastest_msg(f"当前文件处理リスト: {file_list}", chatbot, history, 1)
    else:
        chatbot.append(["文件检索", "没有发现任何近期上传のファイル。"])
        yield from update_ui_lastest_msg("没有发现任何近期上传のファイル。", chatbot, history, 1)
        return  # 2. 如果没有文件
    if len(file_list) == 0:
        chatbot.append(["文件检索", "没有发现任何近期上传のファイル。"])
        yield from update_ui_lastest_msg("没有发现任何近期上传のファイル。", chatbot, history, 1)
        return  # 2. 如果没有文件

    # ファイルを読み込んでいます
    file_type = file_list[0].split('.')[-1]

    # 粗心检查
    if is_the_upload_folder(txt):
        yield from update_ui_lastest_msg(f"请在入力框内填写需求, 然后再次点击该プラグイン! 至于您のファイル，不用担心, 文件路径 {txt} 已经被记忆. ", chatbot, history, 1)
        return

    # 開始干正事
    MAX_TRY = 3
    for j in range(MAX_TRY):  # 最多重试5次
        traceback = ""
        try:
            # ⭐ 開始啦 ！
            code, installation_advance, txt, file_type, llm_kwargs, chatbot, history = \
                yield from gpt_interact_multi_step(txt, file_type, llm_kwargs, chatbot, history)
            chatbot.append(["代码生成阶段終了する", ""])
            yield from update_ui_lastest_msg(f"正在验证上述代码的有效性 ...", chatbot, history, 1)
            # ⭐ 分离代码块
            code = get_code_block(code)
            # ⭐ 检查模块
            ok, traceback = try_make_module(code, chatbot)
            # 搞定代码生成
            if ok: break
        except Exception as e:
            if not traceback: traceback = trimmed_format_exc()
        # 处理Exception
        if not traceback: traceback = trimmed_format_exc()
        yield from update_ui_lastest_msg(f"第 {j+1}/{MAX_TRY} 次代码生成Try, 失敗しました~ 别担心, 私たちは5秒后再试一次... \n\n此次私たちは的错误追踪是\n```\n{traceback}\n```\n", chatbot, history, 5)

    # 代码生成終了する, 開始执行
    TIME_LIMIT = 15
    yield from update_ui_lastest_msg(f"開始创建新进程并执行代码! 時间限制 {TIME_LIMIT} 秒. 请待つ任务完了... ", chatbot, history, 1)
    manager = multiprocessing.Manager()
    return_dict = manager.dict()

    # ⭐ 到最後に一步了，開始逐pieces文件进行处理
    for file_path in file_list:
        if os.path.exists(file_path):
            chatbot.append([f"処理中文件: {file_path}", f"お待ちください..."])
            chatbot = for_immediate_show_off_when_possible(file_type, file_path, chatbot)
            yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する # インターフェースの更新
        else:
            continue

        # ⭐⭐⭐ subprocess_worker ⭐⭐⭐
        p = multiprocessing.Process(target=subprocess_worker, args=(code, file_path, return_dict))
        # ⭐ 開始执行，時间限制TIME_LIMIT
        p.start(); p.join(timeout=TIME_LIMIT)
        if p.is_alive(): p.terminate(); p.join()
        p.close()
        res = return_dict['result']
        success = return_dict['success']
        traceback = return_dict['traceback']
        if not success:
            if not traceback: traceback = trimmed_format_exc()
            chatbot.append(["执行失敗しました", f"错误追踪\n```\n{trimmed_format_exc()}\n```\n"])
            # chatbot.append(["如果是缺乏依赖，请参考以下提案する", installation_advance])
            yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
            return

        # 顺利完了，收尾
        res = str(res)
        if os.path.exists(res):
            chatbot.append(["执行成功了，结果是一pieces有效文件", "结果：" + res])
            new_file_path = promote_file_to_downloadzone(res, chatbot=chatbot)
            chatbot = for_immediate_show_off_when_possible(file_type, new_file_path, chatbot)
            yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する # インターフェースの更新
        else:
            chatbot.append(["执行成功了，结果是一pieces文字列", "结果：" + res])
            yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する # インターフェースの更新

