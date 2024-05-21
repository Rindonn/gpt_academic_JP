#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@ Author: Rindon
@ Date: 2024-05-13 09:42:46
@ LastEditors: Rindon
@ LastEditTime: 2024-05-21 10:07:41
@ Description: prompt、インターフェースを日本語に変更
'''
from toolbox import update_ui, get_conf, trimmed_format_exc, get_max_token, Singleton
import threading
import os
import logging

def input_clipping(inputs, history, max_token_limit):
    import numpy as np
    from request_llms.bridge_all import model_info
    enc = model_info["gpt-3.5-turbo"]['tokenizer']
    def get_token_num(txt): return len(enc.encode(txt, disallowed_special=()))

    mode = 'input-and-history'
    # 入力部分のトークンの割合が全体の半分以下の場合，履歴のトリミングのみ
    input_token_num = get_token_num(inputs)
    if input_token_num < max_token_limit//2:
        mode = 'only-history'
        max_token_limit = max_token_limit - input_token_num

    everything = [inputs] if mode == 'input-and-history' else ['']
    everything.extend(history)
    n_token = get_token_num('\n'.join(everything))
    everything_token = [get_token_num(e) for e in everything]
    delta = max(everything_token) // 16 # 切り捨て時の粒度

    while n_token > max_token_limit:
        where = np.argmax(everything_token)
        encoded = enc.encode(everything[where], disallowed_special=())
        clipped_encoded = encoded[:len(encoded)-delta]
        everything[where] = enc.decode(clipped_encoded)[:-1]    # -1 to remove the may-be illegal char
        everything_token[where] = get_token_num(everything[where])
        n_token = get_token_num('\n'.join(everything))

    if mode == 'input-and-history':
        inputs = everything[0]
    else:
        pass
    history = everything[1:]
    return inputs, history

def request_gpt_model_in_new_thread_with_ui_alive(
        inputs, inputs_show_user, llm_kwargs,
        chatbot, history, sys_prompt, refresh_interval=0.2,
        handle_token_exceed=True,
        retry_times_at_unknown_error=2,
        ):
    """
    Request GPT model，GPTモデルにリクエストを送信しながら、ユーザーインターフェイスを活性化します。

    入力パラメータArgs （_arrayで終わる入力変数はすべてリストです，リストの長さはサブタスクの数です，実行時，リストを分解します，それぞれのサブスレッドに配置して実行する）:
        inputs (string): List of inputs （入力）
        inputs_show_user (string): List of inputs to show user（レポートに表示される入力，このパラメータを利用する，冗長な実際の入力をサマリーレポートで非表示にする，レポートの可読性を向上させる）
        top_p (float): Top p value for sampling from model distribution （GPTパラメータ，浮動小数点数）
        temperature (float): Temperature value for sampling from model distribution（GPTパラメータ，浮動小数点数）
        chatbot: chatbot inputs and outputs （ユーザーインターフェースの対話ウィンドウハンドル，データフローの可視化に使用するされる）
        history (list): List of chat history （History，会話履歴リスト）
        sys_prompt (string): List of system prompts （システム入力，リスト，GPTに入力するための前提条項件のヒント，例えば、あなたが翻訳者である場合のテキストの翻訳）
        refresh_interval (float, optional): Refresh interval for UI (default: 0.2) （Refresh time interval frequency，1未満をお勧めします，3を超えることはできません，Only serves visual effects）
        handle_token_exceed：トークンのオーバーフローを自動的に処理するかどうか，自動処理を選択した場合，オーバーフロー時に強制的に切り捨てられます，デフォルトで有効になっています
        retry_times_at_unknown_error：失敗時の再試行回数

    Returnsを出力する:
        future: 出力，GPTが返す結果
    """
    import time
    from concurrent.futures import ThreadPoolExecutor
    from request_llms.bridge_all import predict_no_ui_long_connection
    # ユーザーフィードバック
    chatbot.append([inputs_show_user, ""])
    yield from update_ui(chatbot=chatbot, history=[]) # 画面を更新する
    executor = ThreadPoolExecutor(max_workers=16)
    mutable = ["", time.time(), ""]
    # ウォッチドッグ耐心
    watch_dog_patience = 5
    # 请求任务
    def _req_gpt(inputs, history, sys_prompt):
        retry_op = retry_times_at_unknown_error
        exceeded_cnt = 0
        while True:
            # watchdog error
            if len(mutable) >= 2 and (time.time()-mutable[1]) > watch_dog_patience:
                raise RuntimeError("プログラムの終了が検出された。")
            try:
                # 【1つ目の場合】：顺利完了
                result = predict_no_ui_long_connection(
                    inputs=inputs, llm_kwargs=llm_kwargs,
                    history=history, sys_prompt=sys_prompt, observe_window=mutable)
                return result
            except ConnectionAbortedError as token_exceeded_error:
                # 【2番目の場合】：トークンオーバーフロー
                if handle_token_exceed:
                    exceeded_cnt += 1
                    # 【処理を選択する】 比率を計算しようとする，テキストをできるだけ多く保持する
                    from toolbox import get_reduce_token_percent
                    p_ratio, n_exceed = get_reduce_token_percent(str(token_exceeded_error))
                    MAX_TOKEN = get_max_token(llm_kwargs)
                    EXCEED_ALLO = 512 + 512 * exceeded_cnt
                    inputs, history = input_clipping(inputs, history, max_token_limit=MAX_TOKEN-EXCEED_ALLO)
                    mutable[0] += f'[Local Message] Warning，テキストが長すぎる場合は切り捨てられます，Tokenオーバーフロー数：{n_exceed}。\n\n'
                    continue # 戻って再試行する
                else:
                    # 【キャンセルする】
                    tb_str = '```\n' + trimmed_format_exc() + '```'
                    mutable[0] += f"[Local Message] Warning，実行中に問題が発生しました, Traceback：\n\n{tb_str}\n\n"
                    return mutable[0] # 放棄する
            except:
                # 【第3の場合】：その他のエラー：数回リトライする
                tb_str = '```\n' + trimmed_format_exc() + '```'
                print(tb_str)
                mutable[0] += f"[Local Message] Warning，実行中に問題が発生しました, Traceback：\n\n{tb_str}\n\n"
                if retry_op > 0:
                    retry_op -= 1
                    mutable[0] += f"[Local Message] 再試行中，お待ちください {retry_times_at_unknown_error-retry_op}/{retry_times_at_unknown_error}：\n\n"
                    if ("Rate limit reached" in tb_str) or ("Too Many Requests" in tb_str):
                        time.sleep(30)
                    time.sleep(5)
                    continue # 戻って再試行する
                else:
                    time.sleep(5)
                    return mutable[0] # 放棄する

    # タスクを提出する
    future = executor.submit(_req_gpt, inputs, history, sys_prompt)
    while True:
        # フロントエンドページを更新するためにyieldを1回実行します
        time.sleep(refresh_interval)
        # 「犬に餌をやる」（ウォッチドッグ）
        mutable[1] = time.time()
        if future.done():
            break
        chatbot[-1] = [chatbot[-1][0], mutable[0]]
        yield from update_ui(chatbot=chatbot, history=[]) # 画面を更新する

    final_result = future.result()
    chatbot[-1] = [chatbot[-1][0], final_result]
    yield from update_ui(chatbot=chatbot, history=[]) # 最後に成功した場合，エラーメッセージを削除する
    return final_result

def can_multi_process(llm) -> bool:
    from request_llms.bridge_all import model_info

    def default_condition(llm) -> bool:
        # legacy condition
        if llm.startswith('gpt-'): return True
        if llm.startswith('api2d-'): return True
        if llm.startswith('azure-'): return True
        if llm.startswith('spark'): return True
        if llm.startswith('zhipuai') or llm.startswith('glm-'): return True
        return False

    if llm in model_info:
        if 'can_multi_thread' in model_info[llm]:
            return model_info[llm]['can_multi_thread']
        else:
            return default_condition(llm)
    else:
        return default_condition(llm)

def request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency(
        inputs_array, inputs_show_user_array, llm_kwargs,
        chatbot, history_array, sys_prompt_array,
        refresh_interval=0.2, max_workers=-1, scroller_max_len=30,
        handle_token_exceed=True, show_user_at_complete=False,
        retry_times_at_unknown_error=2,
        ):
    """
    Request GPT model using multiple threads with UI and high efficiency
    GPTモデルのリクエスト[マルチスレッド]版。
    以下の機能を備えています：
        リアルタイムでUIにリモートデータストリームをフィードバックする
        スレッドプールを使用するする，OpenAIのトラフィック制限エラーを回避するためにスレッドプールのサイズを調整できます
        途中で処理を中止する場合
        ネットワークなどに問題が発生した場合，Will transfer traceback and received data to output

    入力パラメータArgs （_arrayで終わる入力変数はすべてリストです，リストの長さはサブタスクの数です，実行時，リストを分解します，それぞれのサブスレッドに配置して実行する）:
        inputs_array (list): List of inputs （Input for each subtask）
        inputs_show_user_array (list): List of inputs to show user（レポートに表示される各サブタスクの入力，このパラメータを利用する，冗長な実際の入力をサマリーレポートで非表示にする，レポートの可読性を向上させる）
        llm_kwargs: llm_kwargsパラメータ
        chatbot: chatbot （ユーザーインターフェースの対話ウィンドウハンドル，データフローの可視化に使用するされる）
        history_array (list): List of chat history （過去の対話入力，二重リスト，The first level list is subtask decomposition，2番目のリストは会話履歴です）
        sys_prompt_array (list): List of system prompts （システム入力，リスト，GPTに入力するための前提条項件のヒント，例えば、あなたが翻訳者である場合のテキストの翻訳）
        refresh_interval (float, optional): Refresh interval for UI (default: 0.2) （Refresh time interval frequency，1未満をお勧めします，3を超えることはできません，Only serves visual effects）
        max_workers (int, optional): Maximum number of threads (default: see config.py) （最大スレッド数，サブタスクが非常に多い場合，このオプションを使用するして、openaiへの高頻度のリクエストを防止し、エラーを引き起こす必要があります）
        scroller_max_len (int, optional): Maximum length for scroller (default: 30)（Display how many characters the data stream received last，Only serves visual effects）
        handle_token_exceed (bool, optional): （入力が長すぎる場合は，テキストを自動的に縮小する）
        handle_token_exceed：トークンのオーバーフローを自動的に処理するかどうか，自動処理を選択した場合，オーバーフロー時に強制的に切り捨てられます，デフォルトで有効になっています
        show_user_at_complete (bool, optional): (終了時に，完全な入力-出力結果をチャットボックスに表示する)
        retry_times_at_unknown_error：サブタスクが失敗した場合のリトライ回数

    Returnsを出力する:
        list: List of GPT model responses （各サブタスクの出力の集計，サブタスクのいずれかがエラーになった場合，response中会携带tracebackエラーメッセージ，デバッグと問題の特定を容易にする。）
    """
    import time, random
    from concurrent.futures import ThreadPoolExecutor
    from request_llms.bridge_all import predict_no_ui_long_connection
    assert len(inputs_array) == len(history_array)
    assert len(inputs_array) == len(sys_prompt_array)
    if max_workers == -1: # 設定ファイルを読み込む
        try: max_workers = get_conf('DEFAULT_WORKER_NUM')
        except: max_workers = 8
        if max_workers <= 0: max_workers = 3
    # chatglmのマルチスレッドをブロックする，重度のカクつきを引き起こす可能性がある
    if not can_multi_process(llm_kwargs['llm_model']):
        max_workers = 1

    executor = ThreadPoolExecutor(max_workers=max_workers)
    n_frag = len(inputs_array)
    # ユーザーフィードバック
    chatbot.append(["マルチスレッド操作を開始してください。", ""])
    yield from update_ui(chatbot=chatbot, history=[]) # 画面を更新する
    # スレッド間での伝達
    mutable = [["", time.time(), "待機中"] for _ in range(n_frag)]

    # ウォッチドッグ耐心
    watch_dog_patience = 5

    # サブスレッドタスク
    def _req_gpt(index, inputs, history, sys_prompt):
        gpt_say = ""
        retry_op = retry_times_at_unknown_error
        exceeded_cnt = 0
        mutable[index][2] = "実行中"
        detect_timeout = lambda: len(mutable[index]) >= 2 and (time.time()-mutable[index][1]) > watch_dog_patience
        while True:
            # watchdog error
            if detect_timeout(): raise RuntimeError("プログラムの終了が検出された。")
            try:
                # 【1つ目の場合】：顺利完了
                gpt_say = predict_no_ui_long_connection(
                    inputs=inputs, llm_kwargs=llm_kwargs, history=history,
                    sys_prompt=sys_prompt, observe_window=mutable[index], console_slience=True
                )
                mutable[index][2] = "成功した"
                return gpt_say
            except ConnectionAbortedError as token_exceeded_error:
                # 【2番目の場合】：トークンオーバーフロー
                if handle_token_exceed:
                    exceeded_cnt += 1
                    # 【処理を選択する】 比率を計算しようとする，テキストをできるだけ多く保持する
                    from toolbox import get_reduce_token_percent
                    p_ratio, n_exceed = get_reduce_token_percent(str(token_exceeded_error))
                    MAX_TOKEN = get_max_token(llm_kwargs)
                    EXCEED_ALLO = 512 + 512 * exceeded_cnt
                    inputs, history = input_clipping(inputs, history, max_token_limit=MAX_TOKEN-EXCEED_ALLO)
                    gpt_say += f'[Local Message] Warning，テキストが長すぎる場合は切り捨てられます，Tokenオーバーフロー数：{n_exceed}。\n\n'
                    mutable[index][2] = f"切り捨て再試行"
                    continue # 戻って再試行する
                else:
                    # 【キャンセルする】
                    tb_str = '```\n' + trimmed_format_exc() + '```'
                    gpt_say += f"[Local Message] Warning，スレッド{index}実行中に問題が発生しました, Traceback：\n\n{tb_str}\n\n"
                    if len(mutable[index][0]) > 0: gpt_say += "このスレッドが失敗する前に受け取った回答：\n\n" + mutable[index][0]
                    mutable[index][2] = "入力が長すぎるため、放棄しました"
                    return gpt_say # 放棄する
            except:
                # 【第3の場合】：その他のエラー
                if detect_timeout(): raise RuntimeError("プログラムの終了が検出されました。")
                tb_str = '```\n' + trimmed_format_exc() + '```'
                print(tb_str)
                gpt_say += f"[Local Message] Warning，スレッド{index}実行中に問題が発生しました, Traceback：\n\n{tb_str}\n\n"
                if len(mutable[index][0]) > 0: gpt_say += "このスレッドが失敗する前に受け取った回答：\n\n" + mutable[index][0]
                if retry_op > 0:
                    retry_op -= 1
                    wait = random.randint(5, 20)
                    if ("Rate limit reached" in tb_str) or ("Too Many Requests" in tb_str):
                        wait = wait * 3
                        fail_info = "OpenAIはクレジットカードをバインドして頻度制限を解除できます "
                    else:
                        fail_info = ""
                    # おそらく10秒以上待つ必要があります，状況は改善されます
                    for i in range(wait):
                        mutable[index][2] = f"{fail_info}再試行を待つ {wait-i}"; time.sleep(1)
                    # 再試行を開始する
                    if detect_timeout(): raise RuntimeError("プログラムの終了が検出されました。")
                    mutable[index][2] = f"再試行中 {retry_times_at_unknown_error-retry_op}/{retry_times_at_unknown_error}"
                    continue # 戻って再試行する
                else:
                    mutable[index][2] = "失敗した"
                    wait = 5
                    time.sleep(5)
                    return gpt_say # 放棄する

    # 非同期タスクが開始されました
    futures = [executor.submit(_req_gpt, index, inputs, history, sys_prompt) for index, inputs, history, sys_prompt in zip(
        range(len(inputs_array)), inputs_array, history_array, sys_prompt_array)]
    cnt = 0
    while True:
        # フロントエンドページを更新するためにyieldを1回実行します
        time.sleep(refresh_interval)
        cnt += 1
        worker_done = [h.done() for h in futures]
        # より良いUI視覚効果
        observe_win = []
        # 各スレッドは「犬に餌を与える」必要があります（ウォッチドッグ）
        for thread_index, _ in enumerate(worker_done):
            mutable[thread_index][1] = time.time()
        # フロントエンドで面白いものを印刷する
        for thread_index, _ in enumerate(worker_done):
            print_something_really_funny = "[ ...`"+mutable[thread_index][0][-scroller_max_len:].\
                replace('\n', '').replace('`', '.').replace(' ', '.').replace('<br/>', '.....').replace('$', '.')+"`... ]"
            observe_win.append(print_something_really_funny)
        # フロントエンドで面白いものを印刷する
        stat_str = ''.join([f'`{mutable[thread_index][2]}`: {obs}\n\n'
                            if not done else f'`{mutable[thread_index][2]}`\n\n'
                            for thread_index, done, obs in zip(range(len(worker_done)), worker_done, observe_win)])
        # フロントエンドで面白いものを印刷する
        chatbot[-1] = [chatbot[-1][0], f'マルチスレッド操作が開始された，完了状況: \n\n{stat_str}' + ''.join(['.']*(cnt % 10+1))]
        yield from update_ui(chatbot=chatbot, history=[]) # 画面を更新する
        if all(worker_done):
            executor.shutdown()
            break

    # 非同期タスクが終了しました
    gpt_response_collection = []
    for inputs_show_user, f in zip(inputs_show_user_array, futures):
        gpt_res = f.result()
        gpt_response_collection.extend([inputs_show_user, gpt_res])

    # Whether to write conversation history at the end，結果をインターフェースに表示する
    if show_user_at_complete:
        for inputs_show_user, f in zip(inputs_show_user_array, futures):
            gpt_res = f.result()
            chatbot.append([inputs_show_user, gpt_res])
            yield from update_ui(chatbot=chatbot, history=[]) # 画面を更新する
            time.sleep(0.5)
    return gpt_response_collection



def read_and_clean_pdf_text(fp):
    """
    この関数はPDFを分割するために使用するされます，多くのトリックを使用するしました，ロジックがやや乱雑です，効果が非常に良い

    **入力パラメータの説明**
    - `fp`：テキストを読み取り、クリーンアップする必要があるpdfファイルのパス

    **出力パラメータの説明**
    - `meta_txt`：クリーンアップされたテキストコンテンツ文字列
    - `page_one_meta`：最初のページのクリーンアップされたテキストコンテンツリスト

    **関数の機能**
    PDFファイルを読み取り、テキスト内容をクリーンアップする，クリーニングルールには以下が含まれます：
    - すべてのブロック要素のテキスト情報を抽出する，前のものを出力し、1つの文字列に結合します
    - 短いブロックを削除する（文字数が100未満です）改行文字に置換する
    - CleanUpExcessBlankLines
    - 小文字で始まる段落ブロックを結合して空白に置き換える
    - 重複する改行をクリアする
    - 各改行文字を2つの改行文字に置き換える，各段落の間に2つの改行を挿入する
    """
    import fitz, copy
    import re
    import numpy as np
    from colorful import PrintBrightYellow, PrintBrightGreen
    fc = 0  # インデックス0テキスト
    fs = 1  # フォント1のインデックス
    fb = 2  # インデックス2フレーム
    REMOVE_FOOT_NOTE = True # 本文でない内容を破棄するかどうか （本文より小さいフォントサイズ，参考文献、脚注、図のキャプションなど）
    REMOVE_FOOT_FFSIZE_PERCENT = 0.95 # 本文より小さい？時，Determined as not the main text（一部の記事の本文のフォントサイズが100％統一されていない場合があります，肉眼では見えない微小な変化があります）
    def primary_ffsize(l):
        """
        テキストブロックの主フォントを抽出する
        """
        fsize_statiscs = {}
        for wtf in l['spans']:
            if wtf['size'] not in fsize_statiscs: fsize_statiscs[wtf['size']] = 0
            fsize_statiscs[wtf['size']] += len(wtf['text'])
        return max(fsize_statiscs, key=fsize_statiscs.get)

    def ffsize_same(a,b):
        """
        フォントサイズを抽出して近似しているかどうかを確認する
        """
        return abs((a-b)/max(a,b)) < 0.02

    with fitz.open(fp) as doc:
        meta_txt = []
        meta_font = []

        meta_line = []
        meta_span = []
        ############################## <ステップ1，初期情報を収集する> ##################################
        for index, page in enumerate(doc):
            # file_content += page.get_text()
            text_areas = page.get_text("dict")  # ページからテキスト情報を取得する
            for t in text_areas['blocks']:
                if 'lines' in t:
                    pf = 998
                    for l in t['lines']:
                        txt_line = "".join([wtf['text'] for wtf in l['spans']])
                        if len(txt_line) == 0: continue
                        pf = primary_ffsize(l)
                        meta_line.append([txt_line, pf, l['bbox'], l])
                        for wtf in l['spans']: # for l in t['lines']:
                            meta_span.append([wtf['text'], wtf['size'], len(wtf['text'])])
                    # meta_line.append(["NEW_BLOCK", pf])
            # Block element extraction                           for each word segment with in line                       for each line         cross-line words                          for each block
            meta_txt.extend([" ".join(["".join([wtf['text'] for wtf in l['spans']]) for l in t['lines']]).replace(
                '- ', '') for t in text_areas['blocks'] if 'lines' in t])
            meta_font.extend([np.mean([np.mean([wtf['size'] for wtf in l['spans']])
                             for l in t['lines']]) for t in text_areas['blocks'] if 'lines' in t])
            if index == 0:
                page_one_meta = [" ".join(["".join([wtf['text'] for wtf in l['spans']]) for l in t['lines']]).replace(
                    '- ', '') for t in text_areas['blocks'] if 'lines' in t]

        ############################## <ステップ2，本文フォントを取得する> ##################################
        try:
            fsize_statiscs = {}
            for span in meta_span:
                if span[1] not in fsize_statiscs: fsize_statiscs[span[1]] = 0
                fsize_statiscs[span[1]] += span[2]
            main_fsize = max(fsize_statiscs, key=fsize_statiscs.get)
            if REMOVE_FOOT_NOTE:
                give_up_fize_threshold = main_fsize * REMOVE_FOOT_FFSIZE_PERCENT
        except:
            raise RuntimeError(f'すみません, このPDFを解析することが出来ません: {fp}。')
        ############################## <ステップ3，分割と再結合> ##################################
        mega_sec = []
        sec = []
        for index, line in enumerate(meta_line):
            if index == 0:
                sec.append(line[fc])
                continue
            if REMOVE_FOOT_NOTE:
                if meta_line[index][fs] <= give_up_fize_threshold:
                    continue
            if ffsize_same(meta_line[index][fs], meta_line[index-1][fs]):
                # 段落を認識しようとする
                if meta_line[index][fc].endswith('.') and\
                    (meta_line[index-1][fc] != 'NEW_BLOCK') and \
                    (meta_line[index][fb][2] - meta_line[index][fb][0]) < (meta_line[index-1][fb][2] - meta_line[index-1][fb][0]) * 0.7:
                    sec[-1] += line[fc]
                    sec[-1] += "\n\n"
                else:
                    sec[-1] += " "
                    sec[-1] += line[fc]
            else:
                if (index+1 < len(meta_line)) and \
                    meta_line[index][fs] > main_fsize:
                    # 1行+フォント大
                    mega_sec.append(copy.deepcopy(sec))
                    sec = []
                    sec.append("# " + line[fc])
                else:
                    # セクションを識別しようとしています
                    if meta_line[index-1][fs] > meta_line[index][fs]:
                        sec.append("\n" + line[fc])
                    else:
                        sec.append(line[fc])
        mega_sec.append(copy.deepcopy(sec))

        finals = []
        for ms in mega_sec:
            final = " ".join(ms)
            final = final.replace('- ', ' ')
            finals.append(final)
        meta_txt = finals

        ############################## <4番目のステップ，Messy post-processing> ##################################
        def ClearBlocksWithTooFewCharactersToNewline(meta_txt):
            for index, block_txt in enumerate(meta_txt):
                if len(block_txt) < 100:
                    meta_txt[index] = '\n'
            return meta_txt
        meta_txt = ClearBlocksWithTooFewCharactersToNewline(meta_txt)

        def CleanUpExcessBlankLines(meta_txt):
            for index in reversed(range(1, len(meta_txt))):
                if meta_txt[index] == '\n' and meta_txt[index-1] == '\n':
                    meta_txt.pop(index)
            return meta_txt
        meta_txt = CleanUpExcessBlankLines(meta_txt)

        def MergeLowercaseStartingParagraphBlocks(meta_txt):
            def starts_with_lowercase_word(s):
                pattern = r"^[a-z]+"
                match = re.match(pattern, s)
                if match:
                    return True
                else:
                    return False
            # 对于某些PDF会有第一pieces段落就以小写字母开头,为了避免索引错误置き換える其更改为大写
            if starts_with_lowercase_word(meta_txt[0]):
                meta_txt[0] = meta_txt[0].capitalize()
            for _ in range(100):
                for index, block_txt in enumerate(meta_txt):
                    if starts_with_lowercase_word(block_txt):
                        if meta_txt[index-1] != '\n':
                            meta_txt[index-1] += ' '
                        else:
                            meta_txt[index-1] = ''
                        meta_txt[index-1] += meta_txt[index]
                        meta_txt[index] = '\n'
            return meta_txt
        meta_txt = MergeLowercaseStartingParagraphBlocks(meta_txt)
        meta_txt = CleanUpExcessBlankLines(meta_txt)

        meta_txt = '\n'.join(meta_txt)
        # 重複する改行をクリアする
        for _ in range(5):
            meta_txt = meta_txt.replace('\n\n', '\n')

        # 改行 -> 二重改行
        meta_txt = meta_txt.replace('\n', '\n\n')

        ############################## <5番目のステップ，分割効果を表示する> ##################################
        # for f in finals:
        #    PrintBrightYellow(f)
        #    PrintBrightGreen('***************************')

    return meta_txt, page_one_meta


def get_files_from_everything(txt, type): # type='.md'
    """
    この関数は、指定されたディレクトリ内のすべての指定されたタイプを取得するために使用するされます（.mdのように）のファイル，そして、ネットワーク上のファイルに対して，それを取得することもできます。
    以下は各パラメーターおよび戻り値の説明です：
    パラメータ
    - txt: Path or URL，検索するファイルまたはフォルダのパスまたはネットワーク上のファイルを示す。
    - type: 文字列，検索するファイルタイプを示します。デフォルトは.mdです。
    戻り値
    - success: ブール値，関数が正常に実行されたかどうかを示す。
    - file_manifest: ファイルパスリスト，指定されたタイプの拡張子を持つすべてのファイルの絶対パスを含む。
    - project_folder: 文字列，Indicates the folder path where the file is located。ネットワーク上のファイルの場合，一時フォルダのパスです。
    この関数には詳細な注釈が追加されました，必要条項件を満たしているかどうかを確認してください。
    """
    import glob, os

    success = True
    if txt.startswith('http'):
        # リモートファイルのネットワーク
        import requests
        from toolbox import get_conf
        from toolbox import get_log_folder, gen_time_str
        proxies = get_conf('proxies')
        try:
            r = requests.get(txt, proxies=proxies)
        except:
            raise ConnectionRefusedError(f"ダウンロード出来ませんでした{txt}，チェックして下さい。")
        path = os.path.join(get_log_folder(plugin_name='web_download'), gen_time_str()+type)
        with open(path, 'wb+') as f: f.write(r.content)
        project_folder = get_log_folder(plugin_name='web_download')
        file_manifest = [path]
    elif txt.endswith(type):
        # ファイルを直接指定する
        file_manifest = [txt]
        project_folder = os.path.dirname(txt)
    elif os.path.exists(txt):
        # ローカルパス，Recursive search
        project_folder = txt
        file_manifest = [f for f in glob.glob(f'{project_folder}/**/*'+type, recursive=True)]
        if len(file_manifest) == 0:
            success = False
    else:
        project_folder = None
        file_manifest = []
        success = False

    return success, file_manifest, project_folder



@Singleton
class nougat_interface():
    def __init__(self):
        self.threadLock = threading.Lock()

    def nougat_with_timeout(self, command, cwd, timeout=3600):
        import subprocess
        from toolbox import ProxyNetworkActivate
        logging.info(f'正在执行命令 {command}')
        with ProxyNetworkActivate("Nougat_Download"):
            process = subprocess.Popen(command, shell=True, cwd=cwd, env=os.environ)
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            print("Process timed out!")
            return False
        return True


    def NOUGAT_parse_pdf(self, fp, chatbot, history):
        from toolbox import update_ui_lastest_msg

        yield from update_ui_lastest_msg("論文を解析しています, お待ちください。進度：列を並んでいます, スレッド锁を待っています...",
                                         chatbot=chatbot, history=history, delay=0)
        self.threadLock.acquire()
        import glob, threading, os
        from toolbox import get_log_folder, gen_time_str
        dst = os.path.join(get_log_folder(plugin_name='nougat'), gen_time_str())
        os.makedirs(dst)

        yield from update_ui_lastest_msg("論文を解析しています, お待ちください。進度：NOUGATをロードしています... （ヒント：初めて実行する際はNOUGATパラメータをダウンロードする必要がありますので時間がかかる場合があります）",
                                         chatbot=chatbot, history=history, delay=0)
        self.nougat_with_timeout(f'nougat --out "{os.path.abspath(dst)}" "{os.path.abspath(fp)}"', os.getcwd(), timeout=3600)
        res = glob.glob(os.path.join(dst,'*.mmd'))
        if len(res) == 0:
            self.threadLock.release()
            raise RuntimeError("Nougat論文解析が失敗しました。")
        self.threadLock.release()
        return res[0]




def try_install_deps(deps, reload_m=[]):
    import subprocess, sys, importlib
    for dep in deps:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', dep])
    import site
    importlib.reload(site)
    for m in reload_m:
        importlib.reload(__import__(m))


def get_plugin_arg(plugin_kwargs, key, default):
    # 如果パラメータ是空的
    if (key in plugin_kwargs) and (plugin_kwargs[key] == ""): plugin_kwargs.pop(key)
    # 正常情况
    return plugin_kwargs.get(key, default)
