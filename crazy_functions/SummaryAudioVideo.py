from toolbox import CatchException, report_exception, select_api_key, update_ui, get_conf
from .crazy_utils import request_gpt_model_in_new_thread_with_ui_alive
from toolbox import write_history_to_file, promote_file_to_downloadzone, get_log_folder

def split_audio_file(filename, split_duration=1000):
    """
    指定された分割時間に基づいてオーディオファイルを複数のセグメントに分割する。

    Args:
        filename (str): 分割する必要のある音声ファイル名。
        split_duration (int, optional): 各切り取り音声の長さ（秒単位で）。デフォルト値は1000です。

    Returns:
        filelist (list): テキストの翻訳。

    """
    from moviepy.editor import AudioFileClip
    import os
    os.makedirs(f"{get_log_folder(plugin_name='audio')}/mp3/cut/", exist_ok=True)  # 切り取られた音声を保存するフォルダの作成

    # 音声ファイルを読み取る
    audio = AudioFileClip(filename)

    # ファイルの総時間とカットポイントを計算する
    total_duration = audio.duration
    split_points = list(range(0, int(total_duration), split_duration))
    split_points.append(int(total_duration))
    filelist = []

    # テキストの翻訳
    for i in range(len(split_points) - 1):
        start_time = split_points[i]
        end_time = split_points[i + 1]
        split_audio = audio.subclip(start_time, end_time)
        split_audio.write_audiofile(f"{get_log_folder(plugin_name='audio')}/mp3/cut/{filename[0]}_{i}.mp3")
        filelist.append(f"{get_log_folder(plugin_name='audio')}/mp3/cut/{filename[0]}_{i}.mp3")

    audio.close()
    return filelist

def AnalyAudio(parse_prompt, file_manifest, llm_kwargs, chatbot, history):
    import os, requests
    from moviepy.editor import AudioFileClip
    from request_llms.bridge_all import model_info

    # OpenAIキーとモデルの設定
    api_key = select_api_key(llm_kwargs['api_key'], llm_kwargs['llm_model'])
    chat_endpoint = model_info[llm_kwargs['llm_model']]['endpoint']

    whisper_endpoint = chat_endpoint.replace('chat/completions', 'audio/transcriptions')
    url = whisper_endpoint
    headers = {
        'Authorization': f"Bearer {api_key}"
    }

    os.makedirs(f"{get_log_folder(plugin_name='audio')}/mp3/", exist_ok=True)
    for index, fp in enumerate(file_manifest):
        audio_history = []
        # ファイルの拡張子を抽出する
        ext = os.path.splitext(fp)[1]
        # 原始文本
        if ext not in [".mp3", ".wav", ".m4a", ".mpga"]:
            audio_clip = AudioFileClip(fp)
            audio_clip.write_audiofile(f"{get_log_folder(plugin_name='audio')}/mp3/output{index}.mp3")
            fp = f"{get_log_folder(plugin_name='audio')}/mp3/output{index}.mp3"
        # whisperモデルを使用するして音声をテキストに変換する
        voice = split_audio_file(fp)
        for j, i in enumerate(voice):
            with open(i, 'rb') as f:
                file_content = f.read()  # 読み込んだファイルの内容をメモリに保存する
                files = {
                    'file': (os.path.basename(i), file_content),
                }
                data = {
                    "model": "whisper-1",
                    "prompt": parse_prompt,
                    'response_format': "text"
                }

            chatbot.append([f"置き換える {i} openai音声解析端に送信する (whisper)，テキストの翻訳：{parse_prompt}", "処理中 ..."])
            yield from update_ui(chatbot=chatbot, history=history)  # 画面を更新する
            proxies = get_conf('proxies')
            response = requests.post(url, headers=headers, files=files, data=data, proxies=proxies).text

            chatbot.append(["音声解析結果", response])
            history.extend(["音声解析結果", response])
            yield from update_ui(chatbot=chatbot, history=history)  # 画面を更新する

            i_say = f'以下のオーディオフラグメントについて概要を作成してください，音声の内容は ```{response}```'
            i_say_show_user = f'第{index + 1}テキストの翻訳{j + 1} / {len(voice)}フラグメント。'
            gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(
                inputs=i_say,
                inputs_show_user=i_say_show_user,
                llm_kwargs=llm_kwargs,
                chatbot=chatbot,
                history=[],
                sys_prompt=f"音声をまとめる。オーディオファイル名{fp}"
            )

            chatbot[-1] = (i_say_show_user, gpt_say)
            history.extend([i_say_show_user, gpt_say])
            audio_history.extend([i_say_show_user, gpt_say])

        # 記事のすべてのセグメントを要約しました，記事が分割された場合
        result = "".join(audio_history)
        if len(audio_history) > 1:
            i_say = f"上記の対話に基づいて，中国語で音声を要約する{result}”の主な内容。"
            i_say_show_user = f'第{index + 1}テキストの翻訳：'
            gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(
                inputs=i_say,
                inputs_show_user=i_say_show_user,
                llm_kwargs=llm_kwargs,
                chatbot=chatbot,
                history=audio_history,
                sys_prompt="記事をまとめる。"
            )
            history.extend([i_say, gpt_say])
            audio_history.extend([i_say, gpt_say])

        res = write_history_to_file(history)
        promote_file_to_downloadzone(res, chatbot=chatbot)
        chatbot.append((f"第{index + 1}セグメントのオーディオは完了しましたか？", res))
        yield from update_ui(chatbot=chatbot, history=history)  # 画面を更新する

    # 中間フォルダを削除する
    import shutil
    shutil.rmtree(f"{get_log_folder(plugin_name='audio')}/mp3")
    res = write_history_to_file(history)
    promote_file_to_downloadzone(res, chatbot=chatbot)
    chatbot.append(("すべてのオーディオが要約されましたか？", res))
    yield from update_ui(chatbot=chatbot, history=history)


@CatchException
def SummaryAudioVideo(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, WEB_PORT):
    import glob, os

    # 基本情報：機能、貢献者
    chatbot.append([
        "関数プラグイン機能？",
        "SummaryAudioVideo内容，関数プラグインの貢献者: dalvqw & BinaryHusky"])
    yield from update_ui(chatbot=chatbot, history=history)  # 画面を更新する

    try:
        from moviepy.editor import AudioFileClip
    except:
        report_exception(chatbot, history,
                         a=f"プロジェクトを解析する: {txt}",
                         b=f"ソフトウェアの依存関係のインポートに失敗しました。このモジュールを使用するするには、追加の依存関係が必要です，インストールテキストの翻訳```pip install --upgrade moviepy```。")
        yield from update_ui(chatbot=chatbot, history=history)  # 画面を更新する
        return

    # 履歴をクリアする，オーバーフローを防ぐために
    history = []

    # 入力パラメータを検出する，入力パラメータが指定されていない場合，直接終了する
    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空の入力欄'
        report_exception(chatbot, history, a=f"プロジェクトを解析する: {txt}", b=f"ローカルプロジェクトが見つからないか、アクセス権がありません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history)  # 画面を更新する
        return

    # 処理する必要のあるファイルリストを検索する
    extensions = ['.mp4', '.m4a', '.wav', '.mpga', '.mpeg', '.mp3', '.avi', '.mkv', '.flac', '.aac']

    if txt.endswith(tuple(extensions)):
        file_manifest = [txt]
    else:
        file_manifest = []
        for extension in extensions:
            file_manifest.extend(glob.glob(f'{project_folder}/**/*{extension}', recursive=True))

    # ファイルが見つからなかった場合
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a=f"プロジェクトを解析する: {txt}", b=f"音声またはビデオファイルが見つかりません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history)  # 画面を更新する
        return

    # タスクを正式に実行する
    if ("advanced_arg" in plugin_kwargs) and (plugin_kwargs["advanced_arg"] == ""): plugin_kwargs.pop("advanced_arg")
    parse_prompt = plugin_kwargs.get("advanced_arg", '音声を簡体字中国語に解析する')
    yield from AnalyAudio(parse_prompt, file_manifest, llm_kwargs, chatbot, history)

    yield from update_ui(chatbot=chatbot, history=history)  # 画面を更新する
