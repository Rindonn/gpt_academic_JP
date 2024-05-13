# 借鉴自同目录下的bridge_chatgpt.py

"""
    このファイルには主に3つの関数が含まれています

    マルチスレッド機能を持たない関数：
    1. predict: 通常の会話時に使用するする，完全なインタラクティブ機能を備えています，マルチスレッドはできません

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
import random

# config_private.pyに自分のAPIやプロキシアドレスなどの秘密を入力する
# 読み取り時に、まずconfig_private構成ファイルが存在するかどうかを確認します（Gitの管理外），ある場合，元のconfigファイルを上書きする
from toolbox import get_conf, update_ui, trimmed_format_exc, is_the_upload_folder, read_one_api_model_name
proxies, TIMEOUT_SECONDS, MAX_RETRY, YIMODEL_API_KEY = \
    get_conf('proxies', 'TIMEOUT_SECONDS', 'MAX_RETRY', 'YIMODEL_API_KEY')

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

def decode_chunk(chunk):
    # 提前读取一些信息（用于判断Exception）
    chunk_decoded = chunk.decode()
    chunkjson = None
    is_last_chunk = False
    try:
        chunkjson = json.loads(chunk_decoded[6:])
        is_last_chunk = chunkjson.get("lastOne", False)
    except:
        pass
    return chunk_decoded, chunkjson, is_last_chunk

def predict_no_ui_long_connection(inputs, llm_kwargs, history=[], sys_prompt="", observe_window=None, console_slience=False):
    """
    chatGPTに送信，返信を待つ，一度に完了する，Do not display intermediate processes。ただし、途中でネットワーク接続が切断されることを避けるために、内部ではストリームを使用するしています。
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
    if inputs == "":     inputs = "空の入力欄"
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
            if MAX_RETRY!=0: print(f'リクエストがタイムアウトしました，再試行中 ({retry}/{MAX_RETRY}) ……')

    stream_response = response.iter_lines()
    result = ''
    is_head_of_the_stream = True
    while True:
        try: chunk = next(stream_response)
        except StopIteration:
            break
        except requests.exceptions.ConnectionError:
            chunk = next(stream_response) # 失敗しました，もう一度やり直す？もう失敗したらどうしようもない。
        chunk_decoded, chunkjson, is_last_chunk = decode_chunk(chunk)
        if is_head_of_the_stream and (r'"object":"error"' not in chunk_decoded) and (r'"role":"assistant"' in chunk_decoded):
            # データストリームの最初のフレームにはcontentが含まれていません
            is_head_of_the_stream = False; continue
        if chunk:
            try:
                if is_last_chunk:
                    # データフローの終了と判断されます，gpt_replying_bufferも書き終わりました
                    logging.info(f'[response] {result}')
                    break
                result += chunkjson['choices'][0]["delta"]["content"]
                if not console_slience: print(chunkjson['choices'][0]["delta"]["content"], end='')
                if observe_window is not None:
                    # Observation window，取得したデータを表示する
                    if len(observe_window) >= 1:
                        observe_window[0] += chunkjson['choices'][0]["delta"]["content"]
                    # ウォッチドッグ，期限を過ぎてもフィードしない場合，停止する
                    if len(observe_window) >= 2:
                        if (time.time()-observe_window[1]) > watch_dog_patience:
                            raise RuntimeError("ユーザーがプログラムをキャンセルしました。")
            except Exception as e:
                chunk = get_full_error(chunk, stream_response)
                chunk_decoded = chunk.decode()
                error_msg = chunk_decoded
                print(error_msg)
                raise RuntimeError("Json解析が通常と異なる")
    return result


def predict(inputs, llm_kwargs, plugin_kwargs, chatbot, history=[], system_prompt='', stream = True, additional_fn=None):
    """
    chatGPTに送信，ストリームで出力を取得する。
    基本的な対話機能に使用するされます。
    inputsは今回の問い合わせの入力です
    top_p, temperatureはchatGPTの内部調整パラメータです
    historyは以前の対話リストです（inputsまたはhistoryである場合でも注意してください，コンテンツが長すぎると、トークン数がオーバーフローするエラーが発生する可能性があります）
    Chatbot is the list of conversations displayed in WebUI，それを変更する，そして出力する，対話インターフェースの内容を直接変更できます
    additional_fnは、クリックされたボタンを表します，functional.pyにあるボタン
    """
    if len(YIMODEL_API_KEY) == 0:
        raise RuntimeError("没有设置YIMODEL_API_KEY选项")
    if inputs == "":     inputs = "空の入力欄"
    user_input = inputs
    if additional_fn is not None:
        from core_functional import handle_core_functionality
        inputs, history = handle_core_functionality(additional_fn, inputs, history, chatbot)

    raw_input = inputs
    logging.info(f'[raw_input] {raw_input}')
    chatbot.append((inputs, ""))
    yield from update_ui(chatbot=chatbot, history=history, msg="レスポンスを待っています") # 画面を更新する

    # check mis-behavior
    if is_the_upload_folder(user_input):
        chatbot[-1] = (inputs, f"[Local Message] 検出された操作错误！当您上传文档之后，需点击“**関数プラグインエリア**”按钮进行处理，请勿点击“提出”按钮または“基本機能エリア”按钮。")
        yield from update_ui(chatbot=chatbot, history=history, msg="正常") # 画面を更新する
        time.sleep(2)

    headers, payload = generate_payload(inputs, llm_kwargs, history, system_prompt, stream)

    from .bridge_all import model_info
    endpoint = model_info[llm_kwargs['llm_model']]['endpoint']

    history.append(inputs); history.append("")

    retry = 0
    while True:
        try:
            # make a POST request to the API endpoint, stream=True
            response = requests.post(endpoint, headers=headers, proxies=proxies,
                                    json=payload, stream=True, timeout=TIMEOUT_SECONDS);break
        except:
            retry += 1
            chatbot[-1] = ((chatbot[-1][0], timeout_bot_msg))
            retry_msg = f"，再試行中 ({retry}/{MAX_RETRY}) ……" if MAX_RETRY > 0 else ""
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
                break
            except requests.exceptions.ConnectionError:
                chunk = next(stream_response) # 失敗しました，もう一度やり直す？もう失敗したらどうしようもない。

            # 提前读取一些信息 （用于判断Exception）
            chunk_decoded, chunkjson, is_last_chunk = decode_chunk(chunk)

            if is_head_of_the_stream and (r'"object":"error"' not in chunk_decoded) and (r'"role":"assistant"' in chunk_decoded):
                # データストリームの最初のフレームにはcontentが含まれていません
                is_head_of_the_stream = False; continue

            if chunk:
                try:
                    if is_last_chunk:
                        # データフローの終了と判断されます，gpt_replying_bufferも書き終わりました
                        logging.info(f'[response] {gpt_replying_buffer}')
                        break
                    # データフローの本体を処理する
                    status_text = f"finish_reason: {chunkjson['choices'][0].get('finish_reason', 'null')}"
                    gpt_replying_buffer = gpt_replying_buffer + chunkjson['choices'][0]["delta"]["content"]
                    # ここで例外が発生した場合，通常、テキストが長すぎます，get_full_errorの出力を参照してください
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
    if "bad_request" in error_msg:
        chatbot[-1] = (chatbot[-1][0], "[Local Message] 已经超过了模型的最大文脈或是模型フォーマット错误,请Try削减单次入力的文本量。")
    elif "authentication_error" in error_msg:
        chatbot[-1] = (chatbot[-1][0], "[Local Message] Incorrect API key. 请确保API key有效。")
    elif "not_found" in error_msg:
        chatbot[-1] = (chatbot[-1][0], f"[Local Message] {llm_kwargs['llm_model']} なし效，请确保使用する小写的模型名称。")
    elif "rate_limit" in error_msg:
        chatbot[-1] = (chatbot[-1][0], "[Local Message] 遇到了控制请求速率限制，请一分钟后重试。")
    elif "system_busy" in error_msg:
        chatbot[-1] = (chatbot[-1][0], "[Local Message] 系统繁忙，请一分钟后重试。")
    else:
        from toolbox import regular_txt_to_markdown
        tb_str = '```\n' + trimmed_format_exc() + '```'
        chatbot[-1] = (chatbot[-1][0], f"[Local Message] Exception \n\n{tb_str} \n\n{regular_txt_to_markdown(chunk_decoded)}")
    return chatbot, history

def generate_payload(inputs, llm_kwargs, history, system_prompt, stream):
    """
    すべての情報を統合する，LLMモデルを選択する，httpリクエストを生成する，リクエストの準備をする
    """
    api_key = f"Bearer {YIMODEL_API_KEY}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": api_key
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
    model = llm_kwargs['llm_model']
    if llm_kwargs['llm_model'].startswith('one-api-'):
        model = llm_kwargs['llm_model'][len('one-api-'):]
        model, _ = read_one_api_model_name(model)
    tokens = 600 if llm_kwargs['llm_model'] == 'yi-34b-chat-0205' else 4096    #yi-34b-chat-0205只有4k文脈...
    payload = {
        "model": model,
        "messages": messages,
        "temperature": llm_kwargs['temperature'],  # 1.0,
        "stream": stream,
        "max_tokens": tokens
    }
    try:
        print(f" {llm_kwargs['llm_model']} : {conversation_cnt} : {inputs[:100]} ..........")
    except:
        print('入力には文字化けが含まれる可能性があります。')
    return headers,payload