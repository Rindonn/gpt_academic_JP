from toolbox import CatchException, update_ui, get_conf
from .crazy_utils import request_gpt_model_in_new_thread_with_ui_alive
import datetime
@CatchException
def SimultaneousInquiry(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    """
    txt             入力欄にユーザーが入力したテキスト，翻訳が必要な例文，処理待ちのファイルを含むパスの例
    llm_kwargs      GPTモデルのパラメータ，温度やtop_pなど，通常はそのまま渡すだけでよい
    plugin_kwargs   プラグインモデルのパラメータ，複雑な機能を柔軟に調整するためのさまざまなパラメータ
    chatbot         チャット表示ボックスのハンドル，ユーザーに表示するために使用するされます
    history         チャット履歴，前提の要約
    system_prompt   GPTに対するサイレントリマインダー
    user_request    当前用户的请求信息（IPAddress等）
    """
    history = []    # 履歴をクリアする，オーバーフローを防ぐために
    MULTI_QUERY_LLM_MODELS = get_conf('MULTI_QUERY_LLM_MODELS')
    chatbot.append((txt, "正在同時咨询" + MULTI_QUERY_LLM_MODELS))
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する # GPTのリクエストには時間がかかるため，まず、タイムリーに画面を更新します

    # llm_kwargs['llm_model'] = 'chatglm&gpt-3.5-turbo&api2d-gpt-3.5-turbo' # Support any number of llm interfaces，&記号で分割する
    llm_kwargs['llm_model'] = MULTI_QUERY_LLM_MODELS # Support any number of llm interfaces，&記号で分割する
    gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(
        inputs=txt, inputs_show_user=txt,
        llm_kwargs=llm_kwargs, chatbot=chatbot, history=history,
        sys_prompt=system_prompt,
        retry_times_at_unknown_error=0
    )

    history.append(txt)
    history.append(gpt_say)
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する # インターフェースの更新


@CatchException
def InquireSimultaneously_SpecifiedModel(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    """
    txt             入力欄にユーザーが入力したテキスト，翻訳が必要な例文，処理待ちのファイルを含むパスの例
    llm_kwargs      GPTモデルのパラメータ，温度やtop_pなど，通常はそのまま渡すだけでよい
    plugin_kwargs   プラグインモデルのパラメータ，複雑な機能を柔軟に調整するためのさまざまなパラメータ
    chatbot         チャット表示ボックスのハンドル，ユーザーに表示するために使用するされます
    history         チャット履歴，前提の要約
    system_prompt   GPTに対するサイレントリマインダー
    user_request    当前用户的请求信息（IPAddress等）
    """
    history = []    # 履歴をクリアする，オーバーフローを防ぐために

    if ("advanced_arg" in plugin_kwargs) and (plugin_kwargs["advanced_arg"] == ""): plugin_kwargs.pop("advanced_arg")
    # llm_kwargs['llm_model'] = 'chatglm&gpt-3.5-turbo&api2d-gpt-3.5-turbo' # Support any number of llm interfaces，&記号で分割する
    llm_kwargs['llm_model'] = plugin_kwargs.get("advanced_arg", 'chatglm&gpt-3.5-turbo') # 'chatglm&gpt-3.5-turbo' # Support any number of llm interfaces，&記号で分割する

    chatbot.append((txt, f"正在同時咨询{llm_kwargs['llm_model']}"))
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する # GPTのリクエストには時間がかかるため，まず、タイムリーに画面を更新します

    gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(
        inputs=txt, inputs_show_user=txt,
        llm_kwargs=llm_kwargs, chatbot=chatbot, history=history,
        sys_prompt=system_prompt,
        retry_times_at_unknown_error=0
    )

    history.append(txt)
    history.append(gpt_say)
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する # インターフェースの更新