#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@ Author: Rindon
@ Date: 2024-05-13 09:42:46
@ LastEditors: Rindon
@ LastEditTime: 2024-05-21 15:13:53
@ Description: prompt、インターフェースを日本語に変更
'''
"""
Explanation of the Void Terminal Plugin:

Please describe in natural language what you want to do.

1. You can open the plugin's dropdown menu to explore various capabilities of this project, and then describe your needs in natural language, for example:
- "Please call the plugin to translate a PDF paper for me. I just uploaded the paper to the upload area."
- "Please use the plugin to translate a PDF paper, with the address being https://www.nature.com/articles/s41586-019-1724-z.pdf."
- "Generate an image with blooming flowers and lush green grass using the plugin."
- "Translate the README using the plugin. The GitHub URL is https://github.com/facebookresearch/co-tracker."
- "Translate an Arxiv paper for me. The Arxiv ID is 1812.10695. Remember to use the plugin and don't do it manually!"
- "I don't like the current interface color. Modify the configuration and change the theme to THEME="High-Contrast"."
- "Could you please explain the structure of the Transformer network?"

2. If you use keywords like "call the plugin xxx", "modify the configuration xxx", "please", etc., your intention can be recognized more accurately.

3. Your intention can be recognized more accurately when using powerful models like GPT4. This plugin is relatively new, so please feel free to provide feedback on GitHub.

4. Now, if you need to process a file, please upload the file (drag the file to the file upload area) or describe the path to the file.

5. If you don't need to upload a file, you can simply repeat your command again.
"""
explain_msg = """
## Void Terminal プラグインの説明

1.必要なことを**自然な言葉**で記述してください。 例えば
    - "アップロードエリアに入れたばかりのPDF論文を翻訳してくれるプラグインを呼んでください。"
    - "Please call the plugin to translate the PDF paper at https://openreview.net/pdf?id=rJl0r3R9KX".
    - "Arxivの論文をPDFに翻訳してください、Arxivの論文のIDは1812.10695です、プラグインを使うのを忘れないでください！
    - 花と緑の草が咲いている画像を生成し、プラグインを使用してそれを実現する".
    - プラグインを使ってREADMEを翻訳してください、GithubのURLはhttps://github.com/facebookresearch/co-tracker」。
    - "現在のインターフェイスの色が気に入らない、設定を変更して、テーマTHEMEをTHEME="High-Contrast "に変更してください。"
    - "Pythonソースコード・プロジェクトを解析するプラグインを呼び出してください。" "私はコードをアップロード領域にパックしてドラッグしただけです。"
    - Transformerネットワークの構造は何ですか？" 

2. プラグインのドロップダウンメニューを開くと、このプロジェクトの機能について詳しく知ることができます 

3. "プラグインxxxを呼び出す"、"コンフィギュレーションxxxを修正する"、"質問してください "などのキーワードを使用すると、あなたの意図をより正確に特定することができます

4.GPT3.5以上の機種を推奨します。弱い機種ではあなたの考えを理解できない可能性があります。 このプラグインが開発されてからまだ日が浅いので、Githubを訪れてフィードバックを得ることを歓迎します。

5.ファイルを処理する必要がある場合は、ファイルをアップロード（ファイルアップロードエリアにファイルをドラッグ）するか、ファイルがあるパスを記述してください。

6.ファイルをアップロードする必要がない場合は、もう一度指示を繰り返すだけです。
"""

from pydantic import BaseModel, Field
from typing import List
from toolbox import CatchException, update_ui, is_the_upload_folder
from toolbox import update_ui_lastest_msg, disable_auto_promotion
from request_llms.bridge_all import predict_no_ui_long_connection
from crazy_functions.crazy_utils import request_gpt_model_in_new_thread_with_ui_alive
from crazy_functions.crazy_utils import input_clipping
from crazy_functions.json_fns.pydantic_io import GptJsonIO, JsonStringError
from crazy_functions.vt_fns.vt_state import VoidTerminalState
from crazy_functions.vt_fns.vt_modify_config import modify_configuration_hot
from crazy_functions.vt_fns.vt_modify_config import modify_configuration_reboot
from crazy_functions.vt_fns.vt_call_plugin import execute_plugin

class UserIntention(BaseModel):
    user_prompt: str = Field(description="the content of user input", default="")
    intention_type: str = Field(description="the type of user intention, choose from ['ModifyConfiguration', 'ExecutePlugin', 'Chat']", default="ExecutePlugin")
    user_provide_file: bool = Field(description="whether the user provides a path to a file", default=False)
    user_provide_url: bool = Field(description="whether the user provides a url", default=False)


def chat(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_intention):
    gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(
        inputs=txt, inputs_show_user=txt,
        llm_kwargs=llm_kwargs, chatbot=chatbot, history=[],
        sys_prompt=system_prompt
    )
    chatbot[-1] = [txt, gpt_say]
    history.extend([txt, gpt_say])
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
    pass


explain_intention_to_user = {
    'Chat': "聊天对话",
    'ExecutePlugin': "调用プラグイン",
    'ModifyConfiguration': "修改配置",
}


def analyze_intention_with_simple_rules(txt):
    user_intention = UserIntention()
    user_intention.user_prompt = txt
    is_certain = False

    if '请问' in txt:
        is_certain = True
        user_intention.intention_type = 'Chat'

    if '用プラグイン' in txt:
        is_certain = True
        user_intention.intention_type = 'ExecutePlugin'

    if '修改配置' in txt:
        is_certain = True
        user_intention.intention_type = 'ModifyConfiguration'

    return is_certain, user_intention


@CatchException
def VoidTerminal(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    disable_auto_promotion(chatbot=chatbot)
    # 获取当前VoidTerminalステータス
    state = VoidTerminalState.get_state(chatbot)
    appendix_msg = ""

    # 用简单的关键词检测用户意图
    is_certain, _ = analyze_intention_with_simple_rules(txt)
    if is_the_upload_folder(txt):
        state.set_state(chatbot=chatbot, key='has_provided_explaination', value=False)
        appendix_msg = "\n\n**ファイルをアップロードした**，ニーズを入力してください。"

    if is_certain or (state.has_provided_explaination):
        # 如果意图明确，跳过ヒント环节
        state.set_state(chatbot=chatbot, key='has_provided_explaination', value=True)
        state.unlock_plugin(chatbot=chatbot)
        yield from update_ui(chatbot=chatbot, history=history)
        yield from VoidTerminalMainRoute(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request)
        return
    else:
        # 如果意图模糊，ヒント
        state.set_state(chatbot=chatbot, key='has_provided_explaination', value=True)
        state.lock_plugin(chatbot=chatbot)
        chatbot.append(("VoidTerminalステータス:", explain_msg+appendix_msg))
        yield from update_ui(chatbot=chatbot, history=history)
        return



def VoidTerminalMainRoute(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    history = []
    chatbot.append(("VoidTerminalステータス: ", f"正在执行任务: {txt}"))
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する

    # ⭐ ⭐ ⭐ 分析用户意图
    is_certain, user_intention = analyze_intention_with_simple_rules(txt)
    if not is_certain:
        yield from update_ui_lastest_msg(
            lastmsg=f"正在执行任务: {txt}\n\n分析用户意图中", chatbot=chatbot, history=history, delay=0)
        gpt_json_io = GptJsonIO(UserIntention)
        rf_req = "\nchoose from ['ModifyConfiguration', 'ExecutePlugin', 'Chat']"
        inputs = "Analyze the intention of the user according to following user input: \n\n" + \
            ">> " + (txt+rf_req).rstrip('\n').replace('\n','\n>> ') + '\n\n' + gpt_json_io.format_instructions
        run_gpt_fn = lambda inputs, sys_prompt: predict_no_ui_long_connection(
            inputs=inputs, llm_kwargs=llm_kwargs, history=[], sys_prompt=sys_prompt, observe_window=[])
        analyze_res = run_gpt_fn(inputs, "")
        try:
            user_intention = gpt_json_io.generate_output_auto_repair(analyze_res, run_gpt_fn)
            lastmsg=f"正在执行任务: {txt}\n\n用户意图理解: 意图={explain_intention_to_user[user_intention.intention_type]}",
        except JsonStringError as e:
            yield from update_ui_lastest_msg(
                lastmsg=f"正在执行任务: {txt}\n\n用户意图理解: 失敗しました 当前语言模型（{llm_kwargs['llm_model']}）不能理解您的意图", chatbot=chatbot, history=history, delay=0)
            return
    else:
        pass

    yield from update_ui_lastest_msg(
        lastmsg=f"正在执行任务: {txt}\n\n用户意图理解: 意图={explain_intention_to_user[user_intention.intention_type]}",
        chatbot=chatbot, history=history, delay=0)

    # 用户意图: 修改本项目の設定
    if user_intention.intention_type == 'ModifyConfiguration':
        yield from modify_configuration_reboot(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_intention)

    # 用户意图: 调度プラグイン
    if user_intention.intention_type == 'ExecutePlugin':
        yield from execute_plugin(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_intention)

    # 用户意图: 聊天
    if user_intention.intention_type == 'Chat':
        yield from chat(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_intention)

    return

