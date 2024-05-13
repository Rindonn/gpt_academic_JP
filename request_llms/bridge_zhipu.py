import time
import os
from toolbox import update_ui, get_conf, update_ui_lastest_msg
from toolbox import check_packages, report_exception, have_any_recent_upload_image_files

model_name = '智谱AI大模型'
zhipuai_default_model = 'glm-4'

def validate_key():
    ZHIPUAI_API_KEY = get_conf("ZHIPUAI_API_KEY")
    if ZHIPUAI_API_KEY == '': return False
    return True

def make_media_input(inputs, image_paths):
    for image_path in image_paths:
        inputs = inputs + f'<br/><br/><div align="center"><img src="file={os.path.abspath(image_path)}"></div>'
    return inputs

def predict_no_ui_long_connection(inputs, llm_kwargs, history=[], sys_prompt="", observe_window=[], console_slience=False):
    """
        マルチスレッドのテキストの翻訳
        関数の説明については、request_llms/bridge_all.pyを参照してください
    """
    watch_dog_patience = 5
    response = ""

    if llm_kwargs["llm_model"] == "zhipuai":
        llm_kwargs["llm_model"] = zhipuai_default_model

    if validate_key() is False:
        raise RuntimeError('请配置ZHIPUAI_API_KEY')

    # 開始接收回复
    from .com_zhipuglm import ZhipuChatInit
    zhipu_bro_init = ZhipuChatInit()
    for chunk, response in zhipu_bro_init.generate_chat(inputs, llm_kwargs, history, sys_prompt):
        if len(observe_window) >= 1:
            observe_window[0] = response
        if len(observe_window) >= 2:
            if (time.time() - observe_window[1]) > watch_dog_patience:
                raise RuntimeError("プログラムの終了。")
    return response


def predict(inputs, llm_kwargs, plugin_kwargs, chatbot, history=[], system_prompt='', stream=True, additional_fn=None):
    """
        ⭐シングルスレッドメソッド
        関数の説明については、request_llms/bridge_all.pyを参照してください
    """
    chatbot.append([inputs, ""])
    yield from update_ui(chatbot=chatbot, history=history)

    # 依存関係のインポートを試みる，依存関係が不足している場合，インストールの提案を行います
    try:
        check_packages(["zhipuai"])
    except:
        yield from update_ui_lastest_msg(f"ソフトウェアの依存関係のインポートに失敗しました。使用する该模型需要额外依赖，インストールテキストの翻訳```pip install --upgrade zhipuai```。",
            chatbot=chatbot, history=history, delay=0)
        return

    if validate_key() is False:
        yield from update_ui_lastest_msg(lastmsg="[Local Message] 请配置ZHIPUAI_API_KEY", chatbot=chatbot, history=history, delay=0)
        return

    if additional_fn is not None:
        from core_functional import handle_core_functionality
        inputs, history = handle_core_functionality(additional_fn, inputs, history, chatbot)
        chatbot[-1] = [inputs, ""]
        yield from update_ui(chatbot=chatbot, history=history)

    if llm_kwargs["llm_model"] == "zhipuai":
        llm_kwargs["llm_model"] = zhipuai_default_model

    if llm_kwargs["llm_model"] in ["glm-4v"]:
        have_recent_file, image_paths = have_any_recent_upload_image_files(chatbot)
        if not have_recent_file:
            chatbot.append((inputs, "没有検出された任何近期上传的图像文件，请上传jpgフォーマット的图片，さらに，注意してください拓展名需要小写"))
            yield from update_ui(chatbot=chatbot, history=history, msg="待つ图片") # 画面を更新する
            return
        if have_recent_file:
            inputs = make_media_input(inputs, image_paths)
            chatbot[-1] = [inputs, ""]
            yield from update_ui(chatbot=chatbot, history=history)


    # 開始接收回复
    from .com_zhipuglm import ZhipuChatInit
    zhipu_bro_init = ZhipuChatInit()
    for chunk, response in zhipu_bro_init.generate_chat(inputs, llm_kwargs, history, system_prompt):
        chatbot[-1] = [inputs, response]
        yield from update_ui(chatbot=chatbot, history=history)
    history.extend([inputs, response])
    yield from update_ui(chatbot=chatbot, history=history)