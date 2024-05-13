from toolbox import CatchException, update_ui, gen_time_str
from .crazy_utils import request_gpt_model_in_new_thread_with_ui_alive
from .crazy_utils import input_clipping
import copy, json

@CatchException
def 命令行助手(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    """
    txt             入力欄にユーザーが入力したテキスト, 翻訳が必要な例文, 処理待ちのファイルを含むパスの例
    llm_kwargs      GPTモデルのパラメータ, 温度やtop_pなど, 通常はそのまま渡すだけでよい
    plugin_kwargs   プラグインモデルのパラメータ, 現時点では使用するされていません
    chatbot         チャット表示ボックスのハンドル, ユーザーに表示するために使用するされます
    history         チャット履歴, 前提の要約
    system_prompt   GPTに対するサイレントリマインダー
    user_request    当前用户的请求信息（IPAddress等）
    """
    # 履歴をクリアする, オーバーフローを防ぐために
    history = []

    # 入力
    i_say = "请写bash命令实现以下功能：" + txt
    # 開始
    gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(
        inputs=i_say, inputs_show_user=txt,
        llm_kwargs=llm_kwargs, chatbot=chatbot, history=[],
        sys_prompt="你是一piecesLinux大师级用户。注意，当我要求你写bash命令時，尽可能地仅用一行命令解决我的要求。"
    )
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する # インターフェースの更新



