# httpsを参考にしました://github.com/GaiZhenbiao/ChuanhuChatGPT 项目

"""
    このファイルには主に2つの関数が含まれています

    マルチスレッド機能を持たない関数：
    1. predict: 通常の会話時に使用するするする，完全なインタラクティブ機能を備えています，マルチスレッドはできません

    マルチスレッド呼び出し機能を備えた関数
    2. predict_no_ui_long_connection：支持マルチスレッド
"""
import logging
import os
import time
import traceback
from toolbox import get_conf, update_ui, trimmed_format_exc, encode_image, every_image_file_in_path
import json
import requests
picture_system_prompt = "\n当回复图像時,必须言う明正在回复哪张图像。所有图像仅在最後に一pieces問題中提供,即使它们在History记录中被提及。请使用するする'これは第X张图像:'的フォーマット来指明您正在描述的是哪张图像。"
Claude_3_Models = ["claude-3-sonnet-20240229", "claude-3-opus-20240229"]

# config_private.pyに自分のAPIやプロキシアドレスなどの秘密を入力する
# 読み取り時に、まずconfig_private構成ファイルが存在するかどうかを確認します（Gitの管理外），ある場合，元のconfigファイルを上書きする
from toolbox import get_conf, update_ui, trimmed_format_exc, ProxyNetworkActivate
proxies, TIMEOUT_SECONDS, MAX_RETRY, ANTHROPIC_API_KEY = \
    get_conf('proxies', 'TIMEOUT_SECONDS', 'MAX_RETRY', 'ANTHROPIC_API_KEY')

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
    need_to_pass = False
    if chunk_decoded.startswith('data:'):
        try:
            chunkjson = json.loads(chunk_decoded[6:])
        except:
            need_to_pass = True
            pass
    elif chunk_decoded.startswith('event:'):
        try:
            event_type = chunk_decoded.split(':')[1].strip()
            if event_type == 'content_block_stop' or event_type == 'message_stop':
                is_last_chunk = True
            elif event_type == 'content_block_start' or event_type == 'message_start':
                need_to_pass = True
                pass
        except:
            need_to_pass = True
            pass
    else:
        need_to_pass = True
        pass
    return need_to_pass, chunkjson, is_last_chunk


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
    if len(ANTHROPIC_API_KEY) == 0:
        raise RuntimeError("ANTHROPIC_API_KEYオプションが設定されていません")
    if inputs == "":     inputs = "空の入力欄"
    headers, message = generate_payload(inputs, llm_kwargs, history, sys_prompt, image_paths=None)
    retry = 0


    while True:
        try:
            # make a POST request to the API endpoint, stream=False
            from .bridge_all import model_info
            endpoint = model_info[llm_kwargs['llm_model']]['endpoint']
            response = requests.post(endpoint, headers=headers, json=message, 
                                     proxies=proxies, stream=True, timeout=TIMEOUT_SECONDS);break
        except requests.exceptions.ReadTimeout as e:
            retry += 1
            traceback.print_exc()
            if retry > MAX_RETRY: raise TimeoutError
            if MAX_RETRY!=0: print(f'リクエストがタイムアウトしました，再試OK中 ({retry}/{MAX_RETRY}) ……')
    stream_response = response.iter_lines()
    result = ''
    while True:
        try: chunk = next(stream_response)
        except StopIteration:
            break
        except requests.exceptions.ConnectionError:
            chunk = next(stream_response) # 失敗しました，もう一度やり直す？もう失敗したらどうしようもない。
        need_to_pass, chunkjson, is_last_chunk = decode_chunk(chunk)
        if chunk:
            try:
                if need_to_pass:
                    pass
                elif is_last_chunk:
                    logging.info(f'[response] {result}')
                    break
                else:
                    if chunkjson and chunkjson['type'] == 'content_block_delta':
                        result += chunkjson['delta']['text']
                        print(chunkjson['delta']['text'], end='')
                        if observe_window is not None:
                            # Observation window，取得したデータを表示する
                            if len(observe_window) >= 1:
                                observe_window[0] += chunkjson['delta']['text']
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

def make_media_input(history,inputs,image_paths):
    for image_path in image_paths:
        inputs = inputs + f'<br/><br/><div align="center"><img src="file={os.path.abspath(image_path)}"></div>'
    return inputs

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
    if inputs == "":     inputs = "空の入力欄"
    if len(ANTHROPIC_API_KEY) == 0:
        chatbot.append((inputs, "ANTHROPIC_API_KEYが設定されていません"))
        yield from update_ui(chatbot=chatbot, history=history, msg="レスポンスを待っています") # 画面を更新する
        return

    if additional_fn is not None:
        from core_functional import handle_core_functionality
        inputs, history = handle_core_functionality(additional_fn, inputs, history, chatbot)

    have_recent_file, image_paths = every_image_file_in_path(chatbot)
    if len(image_paths) > 20:
        chatbot.append((inputs, "图片数量超过api上限(20张)"))
        yield from update_ui(chatbot=chatbot, history=history, msg="レスポンスを待っています")
        return

    if any([llm_kwargs['llm_model'] == model for model in Claude_3_Models]) and have_recent_file:
        if inputs == "" or inputs == "空の入力欄":     inputs = "请描述给出的图片"
        system_prompt += picture_system_prompt  # 由于没有单独テキストの翻訳保存包含图片的History，所以只能通过ヒント词对第几张图片进OK定位
        chatbot.append((make_media_input(history,inputs, image_paths), ""))
        yield from update_ui(chatbot=chatbot, history=history, msg="レスポンスを待っています") # 画面を更新する
    else:
        chatbot.append((inputs, ""))
        yield from update_ui(chatbot=chatbot, history=history, msg="レスポンスを待っています") # 画面を更新する

    try:
        headers, message = generate_payload(inputs, llm_kwargs, history, system_prompt, image_paths)
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
            response = requests.post(endpoint, headers=headers, json=message, 
                                     proxies=proxies, stream=True, timeout=TIMEOUT_SECONDS);break
        except requests.exceptions.ReadTimeout as e:
            retry += 1
            traceback.print_exc()
            if retry > MAX_RETRY: raise TimeoutError
            if MAX_RETRY!=0: print(f'リクエストがタイムアウトしました，再試OK中 ({retry}/{MAX_RETRY}) ……')
    stream_response = response.iter_lines()
    gpt_replying_buffer = ""

    while True:
        try: chunk = next(stream_response)
        except StopIteration:
            break
        except requests.exceptions.ConnectionError:
            chunk = next(stream_response) # 失敗しました，もう一度やり直す？もう失敗したらどうしようもない。
        need_to_pass, chunkjson, is_last_chunk = decode_chunk(chunk)
        if chunk:
            try:
                if need_to_pass:
                    pass
                elif is_last_chunk:
                    logging.info(f'[response] {gpt_replying_buffer}')
                    break
                else:
                    if chunkjson and chunkjson['type'] == 'content_block_delta':
                        gpt_replying_buffer += chunkjson['delta']['text']
                        history[-1] = gpt_replying_buffer
                        chatbot[-1] = (history[-2], history[-1])
                        yield from update_ui(chatbot=chatbot, history=history, msg='正常') # 画面を更新する

            except Exception as e:
                chunk = get_full_error(chunk, stream_response)
                chunk_decoded = chunk.decode()
                error_msg = chunk_decoded
                print(error_msg)
                raise RuntimeError("Json解析が通常と異なる")

def multiple_picture_types(image_paths):
    """
    根据图片类型戻るimage/jpeg, image/png, image/gif, image/webp，なし法判断则戻るimage/jpeg
    """
    for image_path in image_paths:
        if image_path.endswith('.jpeg') or image_path.endswith('.jpg'):
            return 'image/jpeg'
        elif image_path.endswith('.png'):
            return 'image/png'
        elif image_path.endswith('.gif'):
            return 'image/gif'
        elif image_path.endswith('.webp'):
            return 'image/webp'
    return 'image/jpeg'

def generate_payload(inputs, llm_kwargs, history, system_prompt, image_paths):
    """
    すべての情報を統合する，LLMモデルを選択する，httpリクエストを生成する，リクエストの準備をする
    """

    conversation_cnt = len(history) // 2

    messages = []

    if conversation_cnt:
        for index in range(0, 2*conversation_cnt, 2):
            what_i_have_asked = {}
            what_i_have_asked["role"] = "user"
            what_i_have_asked["content"] = [{"type": "text", "text": history[index]}]
            what_gpt_answer = {}
            what_gpt_answer["role"] = "assistant"
            what_gpt_answer["content"] = [{"type": "text", "text": history[index+1]}]
            if what_i_have_asked["content"][0]["text"] != "":
                if what_i_have_asked["content"][0]["text"] == "": continue
                if what_i_have_asked["content"][0]["text"] == timeout_bot_msg: continue
                messages.append(what_i_have_asked)
                messages.append(what_gpt_answer)
            else:
                messages[-1]['content'][0]['text'] = what_gpt_answer['content'][0]['text']

    if any([llm_kwargs['llm_model'] == model for model in Claude_3_Models]) and image_paths:
        what_i_ask_now = {}
        what_i_ask_now["role"] = "user"
        what_i_ask_now["content"] = []
        for image_path in image_paths:
            what_i_ask_now["content"].append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": multiple_picture_types(image_paths),
                    "data": encode_image(image_path),
                }
            })
        what_i_ask_now["content"].append({"type": "text", "text": inputs})
    else:
        what_i_ask_now = {}
        what_i_ask_now["role"] = "user"
        what_i_ask_now["content"] = [{"type": "text", "text": inputs}]
    messages.append(what_i_ask_now)
    # 開始整理headers与message
    headers = {
        'x-api-key': ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json'
    }
    payload = {
        'model': llm_kwargs['llm_model'],
        'max_tokens': 4096,
        'messages': messages,
        'temperature': llm_kwargs['temperature'],
        'stream': True,
        'system': system_prompt
    }
    return headers, payload