# 本源代码中, ⭐ = 关键步骤
"""
测试：
    - show me the solution of $x^2=cos(x)$, solve this problem with figure, and plot and save image to t.jpg

"""


from toolbox import CatchException, update_ui, gen_time_str, trimmed_format_exc, ProxyNetworkActivate
from toolbox import get_conf, select_api_key, update_ui_lastest_msg, Singleton
from crazy_functions.crazy_utils import request_gpt_model_in_new_thread_with_ui_alive, get_plugin_arg
from crazy_functions.crazy_utils import input_clipping, try_install_deps
from crazy_functions.agent_fns.persistent import GradioMultiuserManagerForPersistentClasses
from crazy_functions.agent_fns.auto_agent import AutoGenMath
import time

def remove_model_prefix(llm):
    if llm.startswith('api2d-'): llm = llm.replace('api2d-', '')
    if llm.startswith('azure-'): llm = llm.replace('azure-', '')
    return llm


@CatchException
def MultiAgentTerminal(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    """
    txt             入力欄にユーザーが入力したテキスト，翻訳が必要な例文，処理待ちのファイルを含むパスの例
    llm_kwargs      GPTモデルのパラメータ，温度やtop_pなど，通常はそのまま渡すだけでよい
    plugin_kwargs   プラグインモデルのパラメータ
    chatbot         チャット表示ボックスのハンドル，ユーザーに表示するために使用するされます
    history         チャット履歴，前提の要約
    system_prompt   GPTに対するサイレントリマインダー
    user_request    当前用户的请求信息（IPAddress等）
    """
    # 检查当前的模型是否符合要求
    supported_llms = [
        "gpt-3.5-turbo-16k",
        'gpt-3.5-turbo-1106',
        "gpt-4",
        "gpt-4-32k",
        'gpt-4-1106-preview',
        "azure-gpt-3.5-turbo-16k",
        "azure-gpt-3.5-16k",
        "azure-gpt-4",
        "azure-gpt-4-32k",
    ]
    from request_llms.bridge_all import model_info
    if model_info[llm_kwargs['llm_model']]["max_token"] < 8000: # 至少是8k文脈的模型
        chatbot.append([f"处理任务: {txt}", f"当前プラグイン只支持{str(supported_llms)}, Current model{llm_kwargs['llm_model']}的最大文脈长度太短, 不能支撑AutoGen运行。"])
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    if model_info[llm_kwargs['llm_model']]["endpoint"] is not None: # 如果不是本地模型，加载API_KEY
        llm_kwargs['api_key'] = select_api_key(llm_kwargs['api_key'], llm_kwargs['llm_model'])

    # 依存関係のインポートを試みる，依存関係が不足している場合，インストールの提案を行います
    try:
        import autogen
        if get_conf("AUTOGEN_USE_DOCKER"):
            import docker
    except:
        chatbot.append([ f"处理任务: {txt}",
            f"ソフトウェアの依存関係のインポートに失敗しました。このモジュールを使用するするには、追加の依存関係が必要です，インストールテキストの翻訳```pip install --upgrade pyautogen docker```。"])
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return

    # 依存関係のインポートを試みる，依存関係が不足している場合，インストールの提案を行います
    try:
        import autogen
        import glob, os, time, subprocess
        if get_conf("AUTOGEN_USE_DOCKER"):
            subprocess.Popen(["docker", "--version"])
    except:
        chatbot.append([f"处理任务: {txt}", f"不足していますdocker运行环境！"])
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return

    # 解锁プラグイン
    chatbot.get_cookies()['lock_plugin'] = None
    persistent_class_multi_user_manager = GradioMultiuserManagerForPersistentClasses()
    user_uuid = chatbot.get_cookies().get('uuid')
    persistent_key = f"{user_uuid}->MultiAgentTerminal"
    if persistent_class_multi_user_manager.already_alive(persistent_key):
        # 当已经存在一pieces正在运行的MultiAgentTerminal時，直接置き換える用户入力传递给它，而不是再次启动一pieces新的MultiAgentTerminal
        print('[debug] feed new user input')
        executor = persistent_class_multi_user_manager.get(persistent_key)
        exit_reason = yield from executor.main_process_ui_control(txt, create_or_resume="resume")
    else:
        # 运行MultiAgentTerminal (首次)
        print('[debug] create new executor instance')
        history = []
        chatbot.append(["正在启动: MultiAgentTerminal", "プラグイン动态生成, 执行開始, 著者 Microsoft & Binary-Husky."])
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        executor = AutoGenMath(llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request)
        persistent_class_multi_user_manager.set(persistent_key, executor)
        exit_reason = yield from executor.main_process_ui_control(txt, create_or_resume="create")

    if exit_reason == "wait_feedback":
        # 当用户点击了“待つ反馈”按钮時，置き換えるexecutor存储到cookie中，ユーザーの再呼び出しを待っています
        executor.chatbot.get_cookies()['lock_plugin'] = 'crazy_functions.MultiAgent->MultiAgentTerminal'
    else:
        executor.chatbot.get_cookies()['lock_plugin'] = None
    yield from update_ui(chatbot=executor.chatbot, history=executor.history) # 更新ステータス
