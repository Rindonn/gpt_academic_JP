"""
    このファイルには主に3つの関数が含まれています

    マルチスレッド機能を持たない関数：
    1. predict: 通常の会話時に使用するするする，完全なインタラクティブ機能を備えています，マルチスレッドはできません

    マルチスレッド呼び出し機能を備えた関数
    2. predict_no_ui_long_connection：支持マルチスレッド
"""

import json
import time
import logging
import requests
import base64
import os
import glob
from toolbox import get_conf, update_ui, is_any_api_key, select_api_key, what_keys, clip_history, trimmed_format_exc, is_the_upload_folder, \
    update_ui_lastest_msg, get_max_token, encode_image, have_any_recent_upload_image_files


proxies, TIMEOUT_SECONDS, MAX_RETRY, API_ORG, AZURE_CFG_ARRAY = \
    get_conf('proxies', 'TIMEOUT_SECONDS', 'MAX_RETRY', 'API_ORG', 'AZURE_CFG_ARRAY')

timeout_bot_msg = '[Local Message] Request timeout. Network error. Please check proxy settings in config.py.' + \
                  'ネットワークエラー，プロキシサーバーが利用可能かどうかを確認する，およびプロキシ設定の形式が正しいかどうか，フォーマットは次のようにする必要があります[プロトコル]://[Address]:[ポート]，欠かせない。'


def report_invalid_key(key):
    if get_conf("BLOCK_INVALID_APIKEY"):
        # 实验性功能，自动检测并屏蔽失效的KEY，请勿使用するする
        from request_llms.key_manager import ApiKeyManager
        api_key = ApiKeyManager().add_key_to_blacklist(key)

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
    # 提前读取一些信息 （用于判断Exception）
    chunk_decoded = chunk.decode()
    chunkjson = None
    has_choices = False
    choice_valid = False
    has_content = False
    has_role = False
    try:
        chunkjson = json.loads(chunk_decoded[6:])
        has_choices = 'choices' in chunkjson
        if has_choices: choice_valid = (len(chunkjson['choices']) > 0)
        if has_choices and choice_valid: has_content = "content" in chunkjson['choices'][0]["delta"]
        if has_choices and choice_valid: has_role = "role" in chunkjson['choices'][0]["delta"]
    except:
        pass
    return chunk_decoded, chunkjson, has_choices, choice_valid, has_content, has_role

from functools import lru_cache
@lru_cache(maxsize=32)
def verify_endpoint(endpoint):
    """
        检查endpoint是否可用
    """
    return endpoint

def predict_no_ui_long_connection(inputs, llm_kwargs, history=[], sys_prompt="", observe_window=None, console_slience=False):
    raise NotImplementedError


def predict(inputs, llm_kwargs, plugin_kwargs, chatbot, history=[], system_prompt='', stream = True, additional_fn=None):

    have_recent_file, image_paths = have_any_recent_upload_image_files(chatbot)

    if is_any_api_key(inputs):
        chatbot._cookies['api_key'] = inputs
        chatbot.append(("openaiのapi_keyとして認識された入力", what_keys(inputs)))
        yield from update_ui(chatbot=chatbot, history=history, msg="api_keyがインポートされました") # 画面を更新する
        return
    elif not is_any_api_key(chatbot._cookies['api_key']):
        chatbot.append((inputs, "api_keyが不足しています。\n\n1. Temporary solution：Enter the api_key directly in the input area，そしてEnterを押して提出してください。\n\n長期的な解決策：config.pyに設定する。"))
        yield from update_ui(chatbot=chatbot, history=history, msg="api_keyが不足しています") # 画面を更新する
        return
    if not have_recent_file:
        chatbot.append((inputs, "没有検出された任何近期上传的图像文件，请上传jpgフォーマット的图片，さらに，注意してください拓展名需要小写"))
        yield from update_ui(chatbot=chatbot, history=history, msg="待つ图片") # 画面を更新する
        return
    if os.path.exists(inputs):
        chatbot.append((inputs, "已经接受信您上传のファイル，您不需要再重复强调该文件的路径了，请直接入力您的問題。"))
        yield from update_ui(chatbot=chatbot, history=history, msg="待つ指令") # 画面を更新する
        return


    user_input = inputs
    if additional_fn is not None:
        from core_functional import handle_core_functionality
        inputs, history = handle_core_functionality(additional_fn, inputs, history, chatbot)

    raw_input = inputs
    logging.info(f'[raw_input] {raw_input}')
    def make_media_input(inputs, image_paths):
        for image_path in image_paths:
            inputs = inputs + f'<br/><br/><div align="center"><img src="file={os.path.abspath(image_path)}"></div>'
        return inputs
    chatbot.append((make_media_input(inputs, image_paths), ""))
    yield from update_ui(chatbot=chatbot, history=history, msg="レスポンスを待っています") # 画面を更新する

    # check mis-behavior
    if is_the_upload_folder(user_input):
        chatbot[-1] = (inputs, f"[Local Message] 検出された操作错误！当您上传文档之后，需点击“**関数プラグインエリア**”按钮进OK处理，请勿点击“提出”按钮または“基本機能エリア”按钮。")
        yield from update_ui(chatbot=chatbot, history=history, msg="正常") # 画面を更新する
        time.sleep(2)

    try:
        headers, payload, api_key = generate_payload(inputs, llm_kwargs, history, system_prompt, image_paths)
    except RuntimeError as e:
        chatbot[-1] = (inputs, f"提供されたAPIキーが要件を満たしていません，使用するするできるものは含まれていません{llm_kwargs['llm_model']}のAPIキー。間違ったモデルまたはリクエストソースを選択した可能性があります。")
        yield from update_ui(chatbot=chatbot, history=history, msg="api-keyが要件を満たしていない") # 画面を更新する
        return

    # 检查endpoint是否合法
    try:
        from .bridge_all import model_info
        endpoint = verify_endpoint(model_info[llm_kwargs['llm_model']]['endpoint'])
    except:
        tb_str = '```\n' + trimmed_format_exc() + '```'
        chatbot[-1] = (inputs, tb_str)
        yield from update_ui(chatbot=chatbot, history=history, msg="Endpoint不满足要求") # 画面を更新する
        return

    history.append(make_media_input(inputs, image_paths))
    history.append("")

    retry = 0
    while True:
        try:
            # make a POST request to the API endpoint, stream=True
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
                # 首先排除一piecesone-api没有done数据包の三方Bug情形
                if len(gpt_replying_buffer.strip()) > 0 and len(error_msg) == 0:
                    yield from update_ui(chatbot=chatbot, history=history, msg="検出された有缺陷的非OpenAI官方接口，提案する选择更稳定的接口。")
                    break
                # 其他情况，直接戻る报错
                chatbot, history = handle_error(inputs, llm_kwargs, chatbot, history, chunk_decoded, error_msg, api_key)
                yield from update_ui(chatbot=chatbot, history=history, msg="非OpenAI官方接口戻る了错误:" + chunk.decode()) # 画面を更新する
                return

            # 提前读取一些信息 （用于判断Exception）
            chunk_decoded, chunkjson, has_choices, choice_valid, has_content, has_role = decode_chunk(chunk)

            if is_head_of_the_stream and (r'"object":"error"' not in chunk_decoded) and (r"content" not in chunk_decoded):
                # データストリームの最初のフレームにはcontentが含まれていません
                is_head_of_the_stream = False; continue

            if chunk:
                try:
                    if has_choices and not choice_valid:
                        # 一些垃圾第三方接口的出现这样的错误
                        continue
                    # 前者はAPI2Dの終了条項項件です，テキストの翻訳
                    if ('data: [DONE]' in chunk_decoded) or (len(chunkjson['choices'][0]["delta"]) == 0):
                        # データフローの終了と判断されます，gpt_replying_bufferも書き終わりました
                        lastmsg = chatbot[-1][-1] + f"\n\n\n\n「{llm_kwargs['llm_model']}呼び出す終了する，该模型不具备文脈对话能力，如需追问，请及時切换模型。」"
                        yield from update_ui_lastest_msg(lastmsg, chatbot, history, delay=1)
                        logging.info(f'[response] {gpt_replying_buffer}')
                        break
                    # データフローの本体を処理する
                    status_text = f"finish_reason: {chunkjson['choices'][0].get('finish_reason', 'null')}"
                    # ここで例外が発生した場合，通常、テキストが長すぎます，get_full_errorの出力を参照してください
                    if has_content:
                        # 正常情况
                        gpt_replying_buffer = gpt_replying_buffer + chunkjson['choices'][0]["delta"]["content"]
                    elif has_role:
                        # 一些第三方接口的出现这样的错误，兼容一下吧
                        continue
                    else:
                        # 一些垃圾第三方接口的出现这样的错误
                        gpt_replying_buffer = gpt_replying_buffer + chunkjson['choices'][0]["delta"]["content"]

                    history[-1] = gpt_replying_buffer
                    chatbot[-1] = (history[-2], history[-1])
                    yield from update_ui(chatbot=chatbot, history=history, msg=status_text) # 画面を更新する
                except Exception as e:
                    yield from update_ui(chatbot=chatbot, history=history, msg="Json解析が通常と異なる") # 画面を更新する
                    chunk = get_full_error(chunk, stream_response)
                    chunk_decoded = chunk.decode()
                    error_msg = chunk_decoded
                    chatbot, history = handle_error(inputs, llm_kwargs, chatbot, history, chunk_decoded, error_msg, api_key)
                    yield from update_ui(chatbot=chatbot, history=history, msg="Json例外" + error_msg) # 画面を更新する
                    print(error_msg)
                    return

def handle_error(inputs, llm_kwargs, chatbot, history, chunk_decoded, error_msg, api_key=""):
    from .bridge_all import model_info
    openai_website = ' テキストの翻訳://platform.openai.com/signup'
    if "reduce the length" in error_msg:
        if len(history) >= 2: history[-1] = ""; history[-2] = "" # 現在のオーバーフロー入力をクリアする：history[-2] これは今回の入力です, history[-1] 今回の出力です
        history = clip_history(inputs=inputs, history=history, tokenizer=model_info[llm_kwargs['llm_model']]['tokenizer'],
                                               max_token_limit=(model_info[llm_kwargs['llm_model']]['max_token'])) # historyは少なくとも半分解放する必要があります
        chatbot[-1] = (chatbot[-1][0], "[Local Message] 長さを短くしてください。入力が長すぎます, または履歴データが長すぎます。履歴キャッシュデータは一部解放されました, もう一度お試しください。 (再度失敗した場合、入力が長すぎる可能性が高いです。)")
    elif "does not exist" in error_msg:
        chatbot[-1] = (chatbot[-1][0], f"[Local Message] Model {llm_kwargs['llm_model']} 存在しません。モデルが存在しません, またはあなたは体験資格を持っていない.")
    elif "Incorrect API key" in error_msg:
        chatbot[-1] = (chatbot[-1][0], "[Local Message] Incorrect API key. OpenAI cites incorrect API_KEY as the reason, サービスを拒否する. " + openai_website); report_invalid_key(api_key)
    elif "exceeded your current quota" in error_msg:
        chatbot[-1] = (chatbot[-1][0], "[Local Message] 現在のクォータを超過しました。OpenAIはアカウントのクォータ不足を理由にしています, サービスを拒否する." + openai_website); report_invalid_key(api_key)
    elif "account is not active" in error_msg:
        chatbot[-1] = (chatbot[-1][0], "[Local Message] アカウントがアクティブではありません。OpenAIはアカウントの無効化を理由にしています, サービスを拒否する." + openai_website); report_invalid_key(api_key)
    elif "associated with a deactivated account" in error_msg:
        chatbot[-1] = (chatbot[-1][0], "[Local Message] You are associated with a deactivated account. OpenAIはアカウントが失効したのため, サービスを拒否する." + openai_website); report_invalid_key(api_key)
    elif "API key has been deactivated" in error_msg:
        chatbot[-1] = (chatbot[-1][0], "[Local Message] API key has been deactivated. OpenAI以账户失效为由, サービスを拒否する." + openai_website); report_invalid_key(api_key)
    elif "bad forward key" in error_msg:
        chatbot[-1] = (chatbot[-1][0], "[Local Message] 不正なフォワードキー。API2Dアカウントの残高が不足しています.")
    elif "Not enough point" in error_msg:
        chatbot[-1] = (chatbot[-1][0], "[Local Message] Not enough points. API2D account points are insufficient.")
    else:
        from toolbox import regular_txt_to_markdown
        tb_str = '```\n' + trimmed_format_exc() + '```'
        chatbot[-1] = (chatbot[-1][0], f"[Local Message] Exception \n\n{tb_str} \n\n{regular_txt_to_markdown(chunk_decoded)}")
    return chatbot, history


def generate_payload(inputs, llm_kwargs, history, system_prompt, image_paths):
    """
    すべての情報を統合する，LLMモデルを選択する，httpリクエストを生成する，リクエストの準備をする
    """
    if not is_any_api_key(llm_kwargs['api_key']):
        raise AssertionError("APIキーが間違っています。\n\n1. Temporary solution：Enter the api_key directly in the input area，そしてEnterを押して提出してください。\n\n長期的な解決策：config.pyに設定する。")

    api_key = select_api_key(llm_kwargs['api_key'], llm_kwargs['llm_model'])

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    if API_ORG.startswith('org-'): headers.update({"OpenAI-Organization": API_ORG})
    if llm_kwargs['llm_model'].startswith('azure-'):
        headers.update({"api-key": api_key})
        if llm_kwargs['llm_model'] in AZURE_CFG_ARRAY.keys():
            azure_api_key_unshared = AZURE_CFG_ARRAY[llm_kwargs['llm_model']]["AZURE_API_KEY"]
            headers.update({"api-key": azure_api_key_unshared})

    base64_images = []
    for image_path in image_paths:
        base64_images.append(encode_image(image_path))

    messages = []
    what_i_ask_now = {}
    what_i_ask_now["role"] = "user"
    what_i_ask_now["content"] = []
    what_i_ask_now["content"].append({
        "type": "text",
        "text": inputs
    })

    for image_path, base64_image in zip(image_paths, base64_images):
        what_i_ask_now["content"].append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
        })

    messages.append(what_i_ask_now)
    model = llm_kwargs['llm_model']
    if llm_kwargs['llm_model'].startswith('api2d-'):
        model = llm_kwargs['llm_model'][len('api2d-'):]

    payload = {
        "model": model,
        "messages": messages,
        "temperature": llm_kwargs['temperature'],   # 1.0,
        "top_p": llm_kwargs['top_p'],               # 1.0,
        "n": 1,
        "stream": True,
        "max_tokens": get_max_token(llm_kwargs),
        "presence_penalty": 0,
        "frequency_penalty": 0,
    }
    try:
        print(f" {llm_kwargs['llm_model']} : {inputs[:100]} ..........")
    except:
        print('入力には文字化けが含まれる可能性があります。')
    return headers, payload, api_key


