# httpsを参考にしました://github.com/GaiZhenbiao/ChuanhuChatGPT 项目

"""
    このファイルには主に3つの関数が含まれています

    マルチスレッド機能を持たない関数：
    1. predict: 通常の会話時に使用するするする，完全なインタラクティブ機能を備えています，マルチスレッドはできません

    マルチスレッド呼び出し機能を備えた関数
    2. predict_no_ui_long_connection：支持マルチスレッド
"""

import json
import time
import gradio as gr
import logging
import traceback
import requests
import importlib

# config_private.pyに自分のAPIやプロキシアドレスなどの秘密を入力する
# 読み取り時に、まずconfig_private構成ファイルが存在するかどうかを確認します（Gitの管理外），ある場合，元のconfigファイルを上書きする
from toolbox import get_conf, update_ui, is_any_api_key, select_api_key, what_keys, clip_history, trimmed_format_exc
proxies, TIMEOUT_SECONDS, MAX_RETRY, API_ORG = \
    get_conf('proxies', 'TIMEOUT_SECONDS', 'MAX_RETRY', 'API_ORG')

timeout_bot_msg = '[Local Message] Request timeout. Network error. Please check proxy settings in config.py.' + \
                  'ネットワークエラー，プロキシサーバーが利用可能かどうかを確認する，およびプロキシ設定の形式が正しいかどうか，フォーマットは次のようにする必要があります[プロトコル]://[Address]:[ポート]，欠かせない。'

def get_full_error(chunk, stream_response):
    """
        Openaiから返された完全なエラーを取得する
    """
    while True:
        try:
            chunk += next(stream_response)
        except:
            break
    return chunk


def predict_no_ui_long_connection(inputs, llm_kwargs, history=[], sys_prompt="", observe_window=None, console_slience=False):
    """
    chatGPTに送信，返信を待つ，一度に完了する，Do not display intermediate processes。ただし、途中でネットワーク接続が切断されることを避けるために、内部ではストリームを使用するするしています。
    inputs：
        この問い合わせの入力です
    sys_prompt:
        システム静黙プロンプト
    llm_kwargs：
        chatGPTの内部調整パラメータ
    history：
        以前の会話リストです
    observe_window = None：
        スレッドを越えて出力された部分を転送する責任がある，ほとんどの場合、見栄えの良い視覚効果のためだけです，空白のままにしておくことができます。observe_window[0]：Observation window。observe_window[1]：ウォッチドッグ
    """
    watch_dog_patience = 5 # 監視犬の忍耐力, Set for 5 seconds
    headers, payload = generate_payload(inputs, llm_kwargs, history, system_prompt=sys_prompt, stream=True)
    retry = 0
    while True:
        try:
            # make a POST request to the API endpoint, stream=False
            from .bridge_all import model_info
            endpoint = model_info[llm_kwargs['llm_model']]['endpoint']
            response = requests.post(endpoint, headers=headers, proxies=proxies,
                                    json=payload, stream=True, timeout=TIMEOUT_SECONDS); break
        except requests.exceptions.ReadTimeout as e:
            retry += 1
            traceback.print_exc()
            if retry > MAX_RETRY: raise TimeoutError
            if MAX_RETRY!=0: print(f'リクエストがタイムアウトしました，再試OK中 ({retry}/{MAX_RETRY}) ……')

    stream_response =  response.iter_lines()
    result = ''
    while True:
        try: chunk = next(stream_response).decode()
        except StopIteration:
            break
        except requests.exceptions.ConnectionError:
            chunk = next(stream_response).decode() # 失敗しました，もう一度やり直す？もう失敗したらどうしようもない。
        if len(chunk)==0: continue
        if not chunk.startswith('data:'):
            error_msg = get_full_error(chunk.encode('utf8'), stream_response).decode()
            if "reduce the length" in error_msg:
                raise ConnectionAbortedError("OpenAIはリクエストを拒否しました:" + error_msg)
            else:
                raise RuntimeError("OpenAIはリクエストを拒否しました：" + error_msg)
        if ('data: [DONE]' in chunk): break # api2dが正常に完了しました
        json_data = json.loads(chunk.lstrip('data:'))['choices'][0]
        delta = json_data["delta"]
        if len(delta) == 0: break
        if "role" in delta: continue
        if "content" in delta:
            result += delta["content"]
            if not console_slience: print(delta["content"], end='')
            if observe_window is not None:
                # Observation window，取得したデータを表示する
                if len(observe_window) >= 1: observe_window[0] += delta["content"]
                # ウォッチドッグ，期限を過ぎてもフィードしない場合，停止する
                if len(observe_window) >= 2:
                    if (time.time()-observe_window[1]) > watch_dog_patience:
                        raise RuntimeError("ユーザーがプログラムをキャンセルしました。")
        else: raise RuntimeError("予期しないJson構造："+delta)
    if json_data['finish_reason'] == 'content_filter':
        raise RuntimeError("質問が規則に違反しているため、Azureによってフィルタリングされました。")
    if json_data['finish_reason'] == 'length':
        raise ConnectionAbortedError("正常に終了しました，ただし、トークンが不足していると表示されます，テキストの翻訳，一度に入力するテキスト量を減らしてください。")
    return result


def predict(inputs, llm_kwargs, plugin_kwargs, chatbot, history=[], system_prompt='', stream = True, additional_fn=None):
    """
    chatGPTに送信，ストリームで出力を取得する。
    基本的な対話機能に使用するするされます。
    inputsは今回の問い合わせの入力です
    top_p, temperatureはchatGPTの内部調整パラメータです
    historyは以前の対話リストです（inputsまたはhistoryである場合でも注意してください，コンテンツが長すぎると、トークン数がオーバーフローするエラーが発生する可能性があります）
    Chatbot is the list of conversations displayed in WebUI，それを変更する，そして出力する，対話インターフェースの内容を直接変更できます
    additional_fnは、クリックされたボタンを表します，functional.pyにあるボタン
    """
    if additional_fn is not None:
        from core_functional import handle_core_functionality
        inputs, history = handle_core_functionality(additional_fn, inputs, history, chatbot)

    raw_input = inputs
    logging.info(f'[raw_input] {raw_input}')
    chatbot.append((inputs, ""))
    yield from update_ui(chatbot=chatbot, history=history, msg="レスポンスを待っています") # 画面を更新する

    try:
        headers, payload = generate_payload(inputs, llm_kwargs, history, system_prompt, stream)
    except RuntimeError as e:
        chatbot[-1] = (inputs, f"提供されたAPIキーが要件を満たしていません，使用するするできるものは含まれていません{llm_kwargs['llm_model']}のAPIキー。間違ったモデルまたはリクエストソースを選択した可能性があります。")
        yield from update_ui(chatbot=chatbot, history=history, msg="api-keyが要件を満たしていない") # 画面を更新する
        return

    history.append(inputs); history.append("")

    retry = 0
    while True:
        try:
            # make a POST request to the API endpoint, stream=True
            from .bridge_all import model_info
            endpoint = model_info[llm_kwargs['llm_model']]['endpoint']
            response = requests.post(endpoint, headers=headers, proxies=proxies,
                                    json=payload, stream=True, timeout=TIMEOUT_SECONDS);break
        except:
            retry += 1
            chatbot[-1] = ((chatbot[-1][0], timeout_bot_msg))
            retry_msg = f"，再試OK中 ({retry}/{MAX_RETRY}) ……" if MAX_RETRY > 0 else ""
            yield from update_ui(chatbot=chatbot, history=history, msg="リクエストがタイムアウトしました"+retry_msg) # 画面を更新する
            if retry > MAX_RETRY: raise TimeoutError

    gpt_replying_buffer = ""

    is_head_of_the_stream = True
    if stream:
        stream_response =  response.iter_lines()
        while True:
            try:
                chunk = next(stream_response)
            except StopIteration:
                # OpenAI公式インターフェース以外でこのようなエラーが発生する，OpenAIとAPI2Dはここを通過しません
                chunk_decoded = chunk.decode()
                error_msg = chunk_decoded
                chatbot, history = handle_error(inputs, llm_kwargs, chatbot, history, chunk_decoded, error_msg)
                yield from update_ui(chatbot=chatbot, history=history, msg="非公式のOpenAI APIがエラーを返しました:" + chunk.decode()) # 画面を更新する
                return

            # print(chunk.decode()[6:])
            if is_head_of_the_stream and (r'"object":"error"' not in chunk.decode()):
                # データストリームの最初のフレームにはcontentが含まれていません
                is_head_of_the_stream = False; continue

            if chunk:
                try:
                    chunk_decoded = chunk.decode()
                    # 前者はAPI2Dの終了条項項件です，テキストの翻訳
                    if 'data: [DONE]' in chunk_decoded:
                        # データフローの終了と判断されます，gpt_replying_bufferも書き終わりました
                        logging.info(f'[response] {gpt_replying_buffer}')
                        break
                    # データフローの本体を処理する
                    chunkjson = json.loads(chunk_decoded[6:])
                    status_text = f"finish_reason: {chunkjson['choices'][0]['finish_reason']}"
                    delta = chunkjson['choices'][0]["delta"]
                    if "content" in delta:
                        gpt_replying_buffer = gpt_replying_buffer + delta["content"]
                    history[-1] = gpt_replying_buffer
                    chatbot[-1] = (history[-2], history[-1])
                    yield from update_ui(chatbot=chatbot, history=history, msg=status_text) # 画面を更新する
                except Exception as e:
                    yield from update_ui(chatbot=chatbot, history=history, msg="Json解析が通常と異なる") # 画面を更新する
                    chunk = get_full_error(chunk, stream_response)
                    chunk_decoded = chunk.decode()
                    error_msg = chunk_decoded
                    chatbot, history = handle_error(inputs, llm_kwargs, chatbot, history, chunk_decoded, error_msg)
                    yield from update_ui(chatbot=chatbot, history=history, msg="Json例外" + error_msg) # 画面を更新する
                    print(error_msg)
                    return

def handle_error(inputs, llm_kwargs, chatbot, history, chunk_decoded, error_msg):
    from .bridge_all import model_info
    openai_website = ' テキストの翻訳://platform.openai.com/signup'
    if "reduce the length" in error_msg:
        if len(history) >= 2: history[-1] = ""; history[-2] = "" # 現在のオーバーフロー入力をクリアする：history[-2] これは今回の入力です, history[-1] 今回の出力です
        history = clip_history(inputs=inputs, history=history, tokenizer=model_info[llm_kwargs['llm_model']]['tokenizer'],
                                               max_token_limit=(model_info[llm_kwargs['llm_model']]['max_token'])) # historyは少なくとも半分解放する必要があります
        chatbot[-1] = (chatbot[-1][0], "[Local Message] 長さを短くしてください。入力が長すぎます, または履歴データが長すぎます。履歴キャッシュデータは一部解放されました, もう一度お試しください。 (再度失敗した場合、入力が長すぎる可能性が高いです。)")
                        # history = []    # 履歴をクリアする
    elif "does not exist" in error_msg:
        chatbot[-1] = (chatbot[-1][0], f"[Local Message] Model {llm_kwargs['llm_model']} 存在しません。モデルが存在しません, またはあなたは体験資格を持っていない.")
    elif "Incorrect API key" in error_msg:
        chatbot[-1] = (chatbot[-1][0], "[Local Message] Incorrect API key. OpenAI cites incorrect API_KEY as the reason, サービスを拒否する. " + openai_website)
    elif "exceeded your current quota" in error_msg:
        chatbot[-1] = (chatbot[-1][0], "[Local Message] 現在のクォータを超過しました。OpenAIはアカウントのクォータ不足を理由にしています, サービスを拒否する." + openai_website)
    elif "account is not active" in error_msg:
        chatbot[-1] = (chatbot[-1][0], "[Local Message] アカウントがアクティブではありません。OpenAIはアカウントの無効化を理由にしています, サービスを拒否する." + openai_website)
    elif "associated with a deactivated account" in error_msg:
        chatbot[-1] = (chatbot[-1][0], "[Local Message] You are associated with a deactivated account. OpenAIはアカウントが失効したのため, サービスを拒否する." + openai_website)
    elif "bad forward key" in error_msg:
        chatbot[-1] = (chatbot[-1][0], "[Local Message] 不正なフォワードキー。API2Dアカウントの残高が不足しています.")
    elif "Not enough point" in error_msg:
        chatbot[-1] = (chatbot[-1][0], "[Local Message] Not enough points. API2D account points are insufficient.")
    else:
        from toolbox import regular_txt_to_markdown
        tb_str = '```\n' + trimmed_format_exc() + '```'
        chatbot[-1] = (chatbot[-1][0], f"[Local Message] Exception \n\n{tb_str} \n\n{regular_txt_to_markdown(chunk_decoded)}")
    return chatbot, history

def generate_payload(inputs, llm_kwargs, history, system_prompt, stream):
    """
    すべての情報を統合する，LLMモデルを選択する，httpリクエストを生成する，リクエストの準備をする
    """
    if not is_any_api_key(llm_kwargs['api_key']):
        raise AssertionError("APIキーが間違っています。\n\n1. Temporary solution：Enter the api_key directly in the input area，そしてEnterを押して提出してください。\n\n長期的な解決策：config.pyに設定する。")

    headers = {
        "Content-Type": "application/json",
    }

    conversation_cnt = len(history) // 2

    messages = [{"role": "system", "content": system_prompt}]
    if conversation_cnt:
        for index in range(0, 2*conversation_cnt, 2):
            what_i_have_asked = {}
            what_i_have_asked["role"] = "user"
            what_i_have_asked["content"] = history[index]
            what_gpt_answer = {}
            what_gpt_answer["role"] = "assistant"
            what_gpt_answer["content"] = history[index+1]
            if what_i_have_asked["content"] != "":
                if what_gpt_answer["content"] == "": continue
                if what_gpt_answer["content"] == timeout_bot_msg: continue
                messages.append(what_i_have_asked)
                messages.append(what_gpt_answer)
            else:
                messages[-1]['content'] = what_gpt_answer['content']

    what_i_ask_now = {}
    what_i_ask_now["role"] = "user"
    what_i_ask_now["content"] = inputs
    messages.append(what_i_ask_now)

    payload = {
        "model": llm_kwargs['llm_model'].strip('api2d-'),
        "messages": messages,
        "temperature": llm_kwargs['temperature'],  # 1.0,
        "top_p": llm_kwargs['top_p'],  # 1.0,
        "n": 1,
        "stream": stream,
        "presence_penalty": 0,
        "frequency_penalty": 0,
    }
    try:
        print(f" {llm_kwargs['llm_model']} : {conversation_cnt} : {inputs[:100]} ..........")
    except:
        print('入力には文字化けが含まれる可能性があります。')
    return headers,payload


