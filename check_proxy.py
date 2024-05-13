
def check_proxy(proxies):
    import requests
    proxies_https = proxies['https'] if proxies is not None else 'なし'
    try:
        response = requests.get("https://ipapi.co/json/", proxies=proxies, timeout=4)
        data = response.json()
        if 'country_name' in data:
            country = data['country_name']
            result = f"プロキシの設定 {proxies_https}, Location of the proxy：{country}"
        elif 'error' in data:
            alternative = _check_with_backup_source(proxies)
            if alternative is None:
                result = f"プロキシの設定 {proxies_https}, Location of the proxy：不明，IPクエリ頻度が制限されています"
            else:
                result = f"プロキシの設定 {proxies_https}, Location of the proxy：{alternative}"
        else:
            result = f"プロキシの設定 {proxies_https}, プロキシデータの解析に失敗しました：{data}"
        print(result)
        return result
    except:
        result = f"プロキシの設定 {proxies_https}, プロキシの場所のクエリがタイムアウトしました，プロキシは無効かもしれません"
        print(result)
        return result

def _check_with_backup_source(proxies):
    import random, string, requests
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    try: return requests.get(f"http://{random_string}.edns.ip-api.com/json", proxies=proxies, timeout=4).json()['dns']['geo']
    except: return None

def backup_and_download(current_version, remote_version):
    """
    One-click update agreement：バックアップとダウンロード
    """
    from toolbox import get_conf
    import shutil
    import os
    import requests
    import zipfile
    os.makedirs(f'./history', exist_ok=True)
    backup_dir = f'./history/backup-{current_version}/'
    new_version_dir = f'./history/new-version-{remote_version}/'
    if os.path.exists(new_version_dir):
        return new_version_dir
    os.makedirs(new_version_dir)
    shutil.copytree('./', backup_dir, ignore=lambda x, y: ['history'])
    proxies = get_conf('proxies')
    try:    r = requests.get('https://github.com/binary-husky/chatgpt_academic/archive/refs/heads/master.zip', proxies=proxies, stream=True)
    except: r = requests.get('https://public.agent-matrix.com/publish/master.zip', proxies=proxies, stream=True)
    zip_file_path = backup_dir+'/master.zip'
    with open(zip_file_path, 'wb+') as f:
        f.write(r.content)
    dst_path = new_version_dir
    with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
        for zip_info in zip_ref.infolist():
            dst_file_path = os.path.join(dst_path, zip_info.filename)
            if os.path.exists(dst_file_path):
                os.remove(dst_file_path)
            zip_ref.extract(zip_info, dst_path)
    return new_version_dir


def patch_and_restart(path):
    """
    One-click update agreement：上書きして再起動する
    """
    from distutils import dir_util
    import shutil
    import os
    import sys
    import time
    import glob
    from colorful import PrintBrightYellow, PrintBrightGreen, PrintBrightRed
    # if not using config_private, move origin config.py as config_private.py
    if not os.path.exists('config_private.py'):
        PrintBrightYellow('config_private.pyのプライベート設定が設定されていないため，Now move your existing configuration to config_private.py to prevent configuration loss，',
              'また、いつでもhistoryサブフォルダーで古いバージョンのプログラムを取得できます。')
        shutil.copyfile('config.py', 'config_private.py')
    path_new_version = glob.glob(path + '/*-master')[0]
    dir_util.copy_tree(path_new_version, './')
    PrintBrightGreen('コードはすでに更新されています，pipパッケージ依存関係を更新する予定...')
    for i in reversed(range(5)): time.sleep(1); print(i)
    try:
        import subprocess
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
    except:
        PrintBrightRed('pipパッケージの依存関係のインストールに問題が発生しました，新しい依存ライブラリを手動でインストールする必要があります `python -m pip install -r requirements.txt`，その後、通常のテキストの翻訳を使用するする`python main.py`のテキストの翻訳で起動する。')
    PrintBrightGreen('更新が完了しました，いつでもhistoryサブフォルダーで以前のバージョンのプログラムを取得できます，5秒後に再起動します')
    PrintBrightRed('再起動に失敗した場合，You may need to manually install the new dependency library `python -m pip install -r requirements.txt`，その後、通常のテキストの翻訳を使用するする`python main.py`のテキストの翻訳で起動する。')
    print(' ------------------------------ -----------------------------------')
    for i in reversed(range(8)): time.sleep(1); print(i)
    os.execl(sys.executable, sys.executable, *sys.argv)


def get_current_version():
    import json
    try:
        with open('./version', 'r', encoding='utf8') as f:
            current_version = json.loads(f.read())['version']
    except:
        current_version = ""
    return current_version


def auto_update(raise_error=False):
    """
    One-click update agreement：バージョンとユーザーの意見を検索する
    """
    try:
        from toolbox import get_conf
        import requests
        import json
        proxies = get_conf('proxies')
        try:    response = requests.get("https://raw.githubusercontent.com/binary-husky/chatgpt_academic/master/version", proxies=proxies, timeout=5)
        except: response = requests.get("https://public.agent-matrix.com/publish/version", proxies=proxies, timeout=5)
        remote_json_data = json.loads(response.text)
        remote_version = remote_json_data['version']
        if remote_json_data["show_feature"]:
            new_feature = "新機能：" + remote_json_data["new_feature"]
        else:
            new_feature = ""
        with open('./version', 'r', encoding='utf8') as f:
            current_version = f.read()
            current_version = json.loads(current_version)['version']
        if (remote_version - current_version) >= 0.01-1e-5:
            from colorful import PrintBrightYellow
            PrintBrightYellow(f'\n新しいバージョンが利用可能です。新しいバージョン:{remote_version}，Current version:{current_version}。{new_feature}')
            print('（1）Githubの更新アドレス:\nhttps://github.com/binary-husky/chatgpt_academic\n')
            user_instruction = input('（2）コードをワンクリックで更新するかどうか（Y+Enter=確認，他の入力/入力なし+ Enter = 更新しない）？')
            if user_instruction in ['Y', 'y']:
                path = backup_and_download(current_version, remote_version)
                try:
                    patch_and_restart(path)
                except:
                    msg = '更新に失敗しました。'
                    if raise_error:
                        from toolbox import trimmed_format_exc
                        msg += trimmed_format_exc()
                    print(msg)
            else:
                print('Automatic update program：テキストの翻訳')
                return
        else:
            return
    except:
        msg = 'Automatic update program：テキストの翻訳。トラブルシューティングの提案：プロキシネットワークの設定。'
        if raise_error:
            from toolbox import trimmed_format_exc
            msg += trimmed_format_exc()
        print(msg)

def warm_up_modules():
    print('モジュールのプレウォームを実行しています ...')
    from toolbox import ProxyNetworkActivate
    from request_llms.bridge_all import model_info
    with ProxyNetworkActivate("Warmup_Modules"):
        enc = model_info["gpt-3.5-turbo"]['tokenizer']
        enc.encode("モジュールのプレヒート", disallowed_special=())
        enc = model_info["gpt-4"]['tokenizer']
        enc.encode("モジュールのプレヒート", disallowed_special=())

def warm_up_vectordb():
    print('モジュールのプレウォームを実行しています ...')
    from toolbox import ProxyNetworkActivate
    with ProxyNetworkActivate("Warmup_Modules"):
        import nltk
        with ProxyNetworkActivate("Warmup_Modules"): nltk.download("punkt")


if __name__ == '__main__':
    import os
    os.environ['no_proxy'] = '*'  # プロキシネットワークによる予期しない汚染を回避する
    from toolbox import get_conf
    proxies = get_conf('proxies')
    check_proxy(proxies)
