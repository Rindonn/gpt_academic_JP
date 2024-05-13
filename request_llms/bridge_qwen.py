import time
import os
from toolbox import update_ui, get_conf, update_ui_lastest_msg
from toolbox import check_packages, report_exception

model_name = 'Qwen'

def predict_no_ui_long_connection(inputs, llm_kwargs, history=[], sys_prompt="", observe_window=[], console_slience=False):
    """
        マルチスレッドのテキストの翻訳
        関数の説明については、request_llms/bridge_all.pyを参照してください
    """
    watch_dog_patience = 5
    response = ""

    from .com_qwenapi import QwenRequestInstance
    sri = QwenRequestInstance()
    for response in sri.generate(inputs, llm_kwargs, history, sys_prompt):
        if len(observe_window) >= 1:
            observe_window[0] = response
        if len(observe_window) >= 2:
            if (time.time()-observe_window[1]) > watch_dog_patience: raise RuntimeError("プログラムの終了。")
    return response

def predict(inputs, llm_kwargs, plugin_kwargs, chatbot, history=[], system_prompt='', stream = True, additional_fn=None):
    """
        ⭐シングルスレッドメソッド
        関数の説明については、request_llms/bridge_all.pyを参照してください
    """
    chatbot.append((inputs, ""))
    yield from update_ui(chatbot=chatbot, history=history)

    # 依存関係のインポートを試みる，依存関係が不足している場合，インストールの提案を行います
    try:
        check_packages(["dashscope"])
    except:
        yield from update_ui_lastest_msg(f"ソフトウェアの依存関係のインポートに失敗しました。使用する该模型需要额外依赖，インストールテキストの翻訳```pip install --upgrade dashscope```。",
                                         chatbot=chatbot, history=history, delay=0)
        return

    # 检查DASHSCOPE_API_KEY
    if get_conf("DASHSCOPE_API_KEY") == "":
        yield from update_ui_lastest_msg(f"请配置 DASHSCOPE_API_KEY。",
                                         chatbot=chatbot, history=history, delay=0)
        return

    if additional_fn is not None:
        from core_functional import handle_core_functionality
        inputs, history = handle_core_functionality(additional_fn, inputs, history, chatbot)

    # 開始接收回复
    from .com_qwenapi import QwenRequestInstance
    sri = QwenRequestInstance()
    response = f"[Local Message] 待つ{model_name}テキストの翻訳 ..."
    for response in sri.generate(inputs, llm_kwargs, history, system_prompt):
        chatbot[-1] = (inputs, response)
        yield from update_ui(chatbot=chatbot, history=history)

    # 出力をまとめる
    if response == f"[Local Message] 待つ{model_name}テキストの翻訳 ...":
        response = f"[Local Message] {model_name}响应Exception ..."
    history.extend([inputs, response])
    yield from update_ui(chatbot=chatbot, history=history)