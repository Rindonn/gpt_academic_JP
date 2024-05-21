#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@ Author: Rindon
@ Date: 2024-05-13 09:42:46
@ LastEditors: Rindon
@ LastEditTime: 2024-05-21 10:07:41
@ Description: prompt、インターフェースを日本語に変更
'''
from toolbox import CatchException, update_ui
from crazy_functions.crazy_utils import request_gpt_model_in_new_thread_with_ui_alive
import datetime

HighOrderFunctionTemplateDiagram = f"""
```mermaid
flowchart TD
    %% <gpt_academic_hide_mermaid_code> 一pieces特殊标记，用于在生成mermaid图表時隐藏代码块
    subgraph 函数调用["函数调用过程"]
        AA["入力欄にユーザーが入力したテキスト(txt)"] --> BB["GPTモデルのパラメータ(llm_kwargs)"]
        BB --> CC["プラグインテキストの翻訳(plugin_kwargs)"]
        CC --> DD["对话显示框的句柄(chatbot)"]
        DD --> EE["対話履歴(history)"]
        EE --> FF["系统ヒント词(system_prompt)"]
        FF --> GG["当前用户信息(web_port)"]

        A["開始(查询5天History事件)"]
        A --> B["获取当前月份and日期"]
        B --> C["生成History事件查询ヒント词"]
        C --> D["调用大模型"]
        D --> E["更新界面"]
        E --> F["记录History"]
        F --> |"下一天"| B
    end
```
"""

@CatchException
def HighOrderFunctionTemplateFunctions(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    """
    # HighOrderFunctionTemplateDiagram：https://mermaid.live/edit#pako:eNptk1tvEkEYhv8KmattQpvlvOyFCcdeeaVXuoYssBwie8gyhCIlqVoLhrbbtAWNUpEGUkyMEDW2Fmn_DDOL_8LZHdOwxrnamX3f7_3mmZk6yKhZCfAgV1KrmYKoQ9fDuKC4yChX0nld1Aou1JzjznQ5fWmejh8LYHW6vG2a47YAnlCLNSIRolnenKBXI_zRIBrcuqRT890u7jZx7zMDt-AaMbnW1--5olGiz2sQjwfoQxsZL0hxplSSU0-rop4vrzmKR6O2JxYjHmwcL2Y_HDatVMkXlf86YzHbGY9bO5j8XE7O8Nsbc3iNB3ukL2SMcH-XIQBgWoVOZzxuOxOJOyc63EPGV6ZQLENVrznViYStTiaJ2vw2M2d9bByRnOXkgCnXylCSU5quyto_IcmkbdvctELmJ-j1ASW3uB3g5xOmKqVTmqr_Na3AtuS_dtBFm8H90XJyHkDDT7S9xXWb4HGmRChx64AOL5HRpUm411rM5uh4H78Z4V7fCZzytjZz2seto9XaNPFue07clLaVZF8UNLygJ-VES8lah_n-O-5Ozc7-77NzJ0-K0yr0ZYrmHdqAk50t2RbA4qq9uNohBASw7YpSgaRkLWCCAtxAlnRZLGbJba9bPwUAC5IsCYAnn1kpJ1ZKUACC0iBSsQLVBzUlA3ioVyQ3qGhZEUrxokiehAz4nFgqk1VNVABfB1uAD_g2_AGPl-W8nMcbCvsDblADfNCz4feyobDPy3rYEMtxwYYbPFNVUoHdCPmDHBv2cP4AMfrCbiBli-Q-3afv0X6WdsIjW2-10fgDy1SAig

    txt             入力欄にユーザーが入力したテキスト，翻訳が必要な例文，処理待ちのファイルを含むパスの例
    llm_kwargs      GPTモデルのパラメータ，温度やtop_pなど，通常はそのまま渡すだけでよい
    plugin_kwargs   プラグインモデルのパラメータ，複雑な機能を柔軟に調整するためのさまざまなパラメータ
    chatbot         チャット表示ボックスのハンドル，ユーザーに表示するために使用するされます
    history         チャット履歴，前提の要約
    system_prompt   GPTに対するサイレントリマインダー
    user_request    当前用户的请求信息（IPAddress等）
    """
    history = []    # 履歴をクリアする，オーバーフローを防ぐために
    chatbot.append((
        "プラグインを利用しています：Today in history",
        "[Local Message] 注意してください，呼び出している[関数プラグイン]のテンプレート，この関数は、より多くの面白い機能を実装したい開発者を対象としています，It can serve as a template for creating new feature functions（その関数には20行以上のコードしかありません）。また、大量のファイルを同期的に処理するためのマルチスレッドデモも提供しています。If you want to share new functional modules，PRを遠慮なく提出してください！" + HighOrderFunctionTemplateDiagram))
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する # GPTのリクエストには時間がかかるため，まず、タイムリーに画面を更新します
    for i in range(5):
        currentMonth = (datetime.date.today() + datetime.timedelta(days=i)).month
        currentDay = (datetime.date.today() + datetime.timedelta(days=i)).day
        i_say = f'Which events happened in history{currentMonth}月{currentDay}日？List two and send related pictures。画像を送信するとき，Markdownを使用するしてください，Unsplash APIのPUT_YOUR_QUERY_HEREを、そのイベントを最もよく表す単語に置き換えます。'
        gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(
            inputs=i_say, inputs_show_user=i_say,
            llm_kwargs=llm_kwargs, chatbot=chatbot, history=[],
            sys_prompt="写真を送信したい場合，Markdownを使用するしてください, そしてバックスラッシュを含めないでください, コードブロックを使用するしないでください。Unsplash APIを使用するする (https://source.unsplash.com/1280x720/? < PUT_YOUR_QUERY_HERE >)。"
        )
        chatbot[-1] = (i_say, gpt_say)
        history.append(i_say);history.append(gpt_say)
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する # インターフェースの更新




PROMPT = """
“{subject}”に関するロジック関係を示して下さい，mermaid言語を利用してください，mermaid言語の例を挙げる：
```mermaid
graph TD
    P(プログラミング) --> L1(Python)
    P(プログラミング) --> L2(C)
    P(プログラミング) --> L3(C++)
    P(プログラミング) --> L4(Javascipt)
    P(プログラミング) --> L5(PHP)
```
"""
@CatchException
def 测试图表渲染(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
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
    chatbot.append(("What is this function?？", "mermaidでグラフを書く機能をテストする，まずキーワードを入力して，mermaid+llmを利用してグラフを書いて下さい。"))
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する # GPTのリクエストには時間がかかるため，まず、タイムリーに画面を更新します

    if txt == "": txt = "何も書いてない" # 调皮一下

    i_say_show_user = f'“{txt}”に関するロジックグラフを書いて下さい。'
    i_say = PROMPT.format(subject=txt)
    gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(
        inputs=i_say,
        inputs_show_user=i_say_show_user,
        llm_kwargs=llm_kwargs, chatbot=chatbot, history=[],
        sys_prompt=""
    )
    history.append(i_say); history.append(gpt_say)
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する # インターフェースの更新