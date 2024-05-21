import time
from toolbox import update_ui, get_conf, update_ui_lastest_msg
from toolbox import check_packages, report_exception

model_name = '云雀大模型'

def validate_key():
    YUNQUE_SECRET_KEY = get_conf("YUNQUE_SECRET_KEY")
    if YUNQUE_SECRET_KEY == '': return False
    return True

def predict_no_ui_long_connection(inputs, llm_kwargs, history=[], sys_prompt="", observe_window=[], console_slience=False):
    """
        ⭐ Multi-threaded method
        関数の説明については、request_llms/bridge_all.pyを参照してください
    """
    watch_dog_patience = 5
    response = ""

    if validate_key() is False:
        raise RuntimeError('请配置YUNQUE_SECRET_KEY')

    from .com_skylark2api import YUNQUERequestInstance
    sri = YUNQUERequestInstance()
    for response in sri.generate(inputs, llm_kwargs, history, sys_prompt):
        if len(observe_window) >= 1:
            observe_window[0] = response
        if len(observe_window) >= 2:
            if (time.time()-observe_window[1]) > watch_dog_patience: raise RuntimeError("プログラムの終了。")
    return response

def predict(inputs, llm_kwargs, plugin_kwargs, chatbot, history=[], system_prompt='', stream = True, additional_fn=None):
    """
        ⭐ シングルスレッドメソッド
        関数の説明については、request_llms/bridge_all.pyを参照してください
    """
    chatbot.append((inputs, ""))
    yield from update_ui(chatbot=chatbot, history=history)

    # 依存関係のインポートを試みる，依存関係が不足している場合，インストールの提案をOKいます
    try:
        check_packages(["zhipuai"])
    except:
        yield from update_ui_lastest_msg(f"ソフトウェアの依存関係のインポートに失敗しました。使用するする该模型需要额外依赖，インストールテキストの翻訳```pip install --upgrade zhipuai```。",
                                         chatbot=chatbot, history=history, delay=0)
        return

    if validate_key() is False:
        yield from update_ui_lastest_msg(lastmsg="[Local Message] 请配置HUOSHAN_API_KEY", chatbot=chatbot, history=history, delay=0)
        return

    if additional_fn is not None:
        from core_functional import handle_core_functionality
        inputs, history = handle_core_functionality(additional_fn, inputs, history, chatbot)

    # 開始接收回复
    from .com_skylark2api import YUNQUERequestInstance
    sri = YUNQUERequestInstance()
    response = f"[Local Message] 待つ{model_name}テキストの翻訳 ..."
    for response in sri.generate(inputs, llm_kwargs, history, system_prompt):
        chatbot[-1] = (inputs, response)
        yield from update_ui(chatbot=chatbot, history=history)

    # 出力をまとめる
    if response == f"[Local Message] 待つ{model_name}テキストの翻訳 ...":
        response = f"[Local Message] {model_name}响应Exception ..."
    history.extend([inputs, response])
    yield from update_ui(chatbot=chatbot, history=history)