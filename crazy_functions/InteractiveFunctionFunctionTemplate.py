from toolbox import CatchException, update_ui
from .crazy_utils import request_gpt_model_in_new_thread_with_ui_alive


@CatchException
def InteractiveFunctionTemplateFunction(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    """
    txt             入力欄にユーザーが入力したテキスト，翻訳が必要な例文，処理待ちのファイルを含むパスの例
    llm_kwargs      GPTモデルのパラメータ, 温度やtop_pなど, 通常はそのまま渡すだけでよい
    plugin_kwargs   プラグインモデルのパラメータ, 温度やtop_pなど, 通常はそのまま渡すだけでよい
    chatbot         チャット表示ボックスのハンドル，ユーザーに表示するために使用するされます
    history         チャット履歴，前提の要約
    system_prompt   GPTに対するサイレントリマインダー
    user_request    当前用户的请求信息（IPAddress等）
    """
    history = []    # 履歴をクリアする，オーバーフローを防ぐために
    chatbot.append(("What is this function?？", "InteractiveFunctionFunctionTemplate。実行が完了した後, 自身の状態をcookieに保存することができます, ユーザーの再呼び出しを待っています。"))
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する

    state = chatbot._cookies.get('plugin_state_0001', None) # プラグインの状態を初期化する

    if state is None:
        chatbot._cookies['lock_plugin'] = 'crazy_functions.InteractiveFunctionFunctionTemplate->InteractiveFunctionTemplateFunction'      # プラグインにコールバックパスをロックする，次のユーザーの提出時に，テキストの翻訳
        chatbot._cookies['plugin_state_0001'] = 'wait_user_keyword'                              # プラグインの状態を付与する

        chatbot.append(("最初の呼び出し：", "キーワードを入力してください, 関連する壁紙を検索します, 英単語の使用するをお勧めします, プラグインがロックされています，直接提出してください。"))
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return

    if state == 'wait_user_keyword':
        chatbot._cookies['lock_plugin'] = None          # 解除プラグイン锁定，テキストの翻訳
        chatbot._cookies['plugin_state_0001'] = None    # プラグインの状態を解除します，テキストの翻訳

        # 解除プラグイン锁定
        chatbot.append((f"キーワードの取得：{txt}", ""))
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        page_return = get_image_page_by_keyword(txt)
        inputs=inputs_show_user=f"Extract all image urls in this html page, pick the first 5 images and show them with markdown format: \n\n {page_return}"
        gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(
            inputs=inputs, inputs_show_user=inputs_show_user,
            llm_kwargs=llm_kwargs, chatbot=chatbot, history=[],
            sys_prompt="When you want to show an image, use markdown format. e.g. ![image_description](image_url). If there are no image url provided, answer 'no image url provided'"
        )
        chatbot[-1] = [chatbot[-1][0], gpt_say]
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return



# ---------------------------------------------------------------------------------

def get_image_page_by_keyword(keyword):
    import requests
    from bs4 import BeautifulSoup
    response = requests.get(f'https://wallhaven.cc/search?q={keyword}', timeout=2)
    res = "image urls: \n"
    for image_element in BeautifulSoup(response.content, 'html.parser').findAll("img"):
        try:
            res += image_element["data-src"]
            res += "\n"
        except:
            pass
    return res
