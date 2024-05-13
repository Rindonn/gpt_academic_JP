import importlib
import time
import os
from functools import lru_cache
from colorful import PrintBrightRed, PrintBrightGreen, PrintBrightBlue

pj = os.path.join
default_user_name = 'default_user'

def read_env_variable(arg, default_value):
    """
    環境変数は次のようにすることができます `GPT_ACADEMIC_CONFIG`(優先)，直接であることもできます`CONFIG`
    例えば、Windowsのcmdで，書くことができます：
        set USE_PROXY=True
        set API_KEY=sk-j7caBpkRoxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        set proxies={"http":"http://127.0.0.1:10085", "https":"http://127.0.0.1:10085",}
        set AVAIL_LLM_MODELS=["gpt-3.5-turbo", "chatglm"]
        set AUTHENTICATION=[("username", "password"), ("username2", "password2")]
    書くこともできます：
        set GPT_ACADEMIC_USE_PROXY=True
        set GPT_ACADEMIC_API_KEY=sk-j7caBpkRoxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        set GPT_ACADEMIC_proxies={"http":"http://127.0.0.1:10085", "https":"http://127.0.0.1:10085",}
        set GPT_ACADEMIC_AVAIL_LLM_MODELS=["gpt-3.5-turbo", "chatglm"]
        set GPT_ACADEMIC_AUTHENTICATION=[("username", "password"), ("username2", "password2")]
    """
    arg_with_prefix = "GPT_ACADEMIC_" + arg
    if arg_with_prefix in os.environ:
        env_arg = os.environ[arg_with_prefix]
    elif arg in os.environ:
        env_arg = os.environ[arg]
    else:
        raise KeyError
    print(f"[ENV_VAR] 読み込みを試みる{arg}，デフォルト値：{default_value} --> 修正値：{env_arg}")
    try:
        if isinstance(default_value, bool):
            env_arg = env_arg.strip()
            if env_arg == 'True': r = True
            elif env_arg == 'False': r = False
            else: print('Enter True or False, but have:', env_arg); r = default_value
        elif isinstance(default_value, int):
            r = int(env_arg)
        elif isinstance(default_value, float):
            r = float(env_arg)
        elif isinstance(default_value, str):
            r = env_arg.strip()
        elif isinstance(default_value, dict):
            r = eval(env_arg)
        elif isinstance(default_value, list):
            r = eval(env_arg)
        elif default_value is None:
            assert arg == "proxies"
            r = eval(env_arg)
        else:
            PrintBrightRed(f"[ENV_VAR] 環境変数{arg}環境変数を介して設定することはできません！ ")
            raise KeyError
    except:
        PrintBrightRed(f"[ENV_VAR] 環境変数{arg}読み込みに失敗しました！ ")
        raise KeyError(f"[ENV_VAR] 環境変数{arg}読み込みに失敗しました！ ")

    PrintBrightGreen(f"[ENV_VAR] 環境変数の読み取りに成功しました{arg}")
    return r


@lru_cache(maxsize=128)
def read_single_conf_with_lru_cache(arg):
    from shared_utils.key_pattern_manager import is_any_api_key
    try:
        # 優先度1. 環境変数を設定として取得する
        default_ref = getattr(importlib.import_module('config'), arg) # デフォルト値を読み取り、データ型変換の参考にする
        r = read_env_variable(arg, default_ref)
    except:
        try:
            # 優先度2. config_privateから設定を取得する
            r = getattr(importlib.import_module('config_private'), arg)
        except:
            # 優先度3. configから設定を取得する
            r = getattr(importlib.import_module('config'), arg)

    # API_KEYの読み取り時，configを変更するのを忘れていないか確認してください
    if arg == 'API_URL_REDIRECT':
        oai_rd = r.get("https://api.openai.com/v1/chat/completions", None) # API_URL_REDIRECT入力フォーマットは错误的，请阅读`https://github.com/binary-husky/gpt_academic/wiki/项目配置言う明`
        if oai_rd and not oai_rd.endswith('/completions'):
            PrintBrightRed("\n\n[API_URL_REDIRECT] API_URL_REDIRECT填错了。请阅读`https://github.com/binary-husky/gpt_academic/wiki/项目配置言う明`。如果您确信自己没填错，なし视此消息即可。")
            time.sleep(5)
    if arg == 'API_KEY':
        PrintBrightBlue(f"[API_KEY] このプロジェクトは、OpenAIおよびAzureのAPIキーをサポートしています。複数のAPIキーを同時に入力することもできます，如API_KEY=\"openai-key1,openai-key2,azure-key3\"")
        PrintBrightBlue(f"[API_KEY] config.pyでapi-keyを変更することができます(s)，You can also enter a temporary api-key in the question input area(s)，Enterキーを押して送信すると有効になります。")
        if is_any_api_key(r):
            PrintBrightGreen(f"[API_KEY] あなたのAPI_KEYは: {r[:15]}*** API_KEY imported successfully")
        else:
            PrintBrightRed("[API_KEY] テキストの翻訳，APIキーを変更した後にconfigファイルで実行してください。")
    if arg == 'proxies':
        if not read_single_conf_with_lru_cache('USE_PROXY'): r = None # USE_PROXYを確認する，防止proxies单独起作用
        if r is None:
            PrintBrightRed('[PROXY] ネットワークプロキシの状態：設定されていません。It is very likely that you cannot access the OpenAI family of models without a proxy。提案する：USE_PROXYオプションが変更されているかどうかを確認してください。')
        else:
            PrintBrightGreen('[PROXY] ネットワークプロキシの状態：設定済み。以下は構成情報です：', r)
            assert isinstance(r, dict), 'プロキシの形式が正しくありません，proxiesオプションの形式に注意してください，括弧を省略しないでください。'
    return r


@lru_cache(maxsize=128)
def get_conf(*args):
    """
    本项目的所有配置都集中在config.py中。 修改配置有三种テキストの翻訳，您只需要选择其中一种即可：
        - 直接修改config.py
        - 创建并修改config_private.py
        - 修改環境変数（修改docker-compose.yml等价于修改容器内部的環境変数）

    注意：如果您使用するdocker-compose部署，请修改docker-compose（等价于修改容器内部的環境変数）
    """
    res = []
    for arg in args:
        r = read_single_conf_with_lru_cache(arg)
        res.append(r)
    if len(res) == 1: return res[0]
    return res


def set_conf(key, value):
    from toolbox import read_single_conf_with_lru_cache
    read_single_conf_with_lru_cache.cache_clear()
    get_conf.cache_clear()
    os.environ[key] = str(value)
    altered = get_conf(key)
    return altered


def set_multi_conf(dic):
    for k, v in dic.items(): set_conf(k, v)
    return
