#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@ Author: Rindon
@ Date: 2024-05-13 09:42:46
@ LastEditors: Rindon
@ LastEditTime: 2024-05-21 14:24:03
@ Description: prompt、インターフェースを日本語に変更
'''
from toolbox import CatchException, update_ui, report_exception
from .crazy_utils import request_gpt_model_in_new_thread_with_ui_alive
import datetime

#以下是每类图表的PROMPT
SELECT_PROMPT = """
“{subject}”
=============
以上は文章から抽出した要旨です。この内容を利用してグラフを作成してください。まず適当なクラフの種類を選択してください:
1 フローチャート
2 シーケンス図
3 クラス図
4 円グラフ
5 ガントチャート
6 ステータス図
7 実体関係図
8 象限ヒント図
その理由を説明する必要はなく、句読点を入れずにただ1つの数字を出力してください。
"""
#マインドマップはなし。テストによると、モデルは常にマインドマップを優先します。
#流程图
PROMPT_1 = """
“{subject}”を中心としたフローチャートを作成してください，mermaid言語を使用してください。mermaid言語の例を挙げる：
```mermaid
graph TD
    P(プログラミング) --> L1(Python)
    P(プログラミング) --> L2(C)
    P(プログラミング) --> L3(C++)
    P(プログラミング) --> L4(Javascipt)
    P(プログラミング) --> L5(PHP)
```
"""
#序列图
PROMPT_2 = """
“{subject}”を中心としたシーケンス図を作成してください，mermaid言語を使用してください。mermaid言語の例を挙げる：
```mermaid
sequenceDiagram
    participant A as ユーザー
    participant B as システム
    A->>B: 請求を登録
    B->>A: 登録完了
    A->>B: データを取得する
    B->>A: データを渡す
```
"""
#类图
PROMPT_3 = """
“{subject}”を中心としたクラス図を作成してください，mermaid言語を使用してください。mermaid言語の例を挙げる：
```mermaid
classDiagram
    Class01 <|-- AveryLongClass : Cool
    Class03 *-- Class04
    Class05 o-- Class06
    Class07 .. Class08
    Class09 --> C2 : Where am i?
    Class09 --* C3
    Class09 --|> Class07
    Class07 : equals()
    Class07 : Object[] elementData
    Class01 : size()
    Class01 : int chimp
    Class01 : int gorilla
    Class08 <--> C2: Cool label
```
"""
#饼图
PROMPT_4 = """
“{subject}”を中心とした円グラフを作成してください，mermaid言語を使用してください。mermaid言語の例を挙げる：
```mermaid
pie title Pets adopted by volunteers
    "犬" : 386
    "猫" : 85
    "ラビット" : 15
```
"""
#甘特图
PROMPT_5 = """
“{subject}”を中心としたガントチャートを作成してください，mermaid言語を使用してください。mermaid言語の例を挙げる：
```mermaid
gantt
    title プロジェクト開発の流れ
    dateFormat  YYYY-MM-DD
    section 設計
    ニーズ分析 :done, des1, 2024-01-06,2024-01-08
    プロトタイピング :active, des2, 2024-01-09, 3d
    UI設計 : des3, after des2, 5d
    section 開発
    フロントエンド開発 :2024-01-20, 10d
    バックエンド開発 :2024-01-20, 10d
```
"""
#ステータス图
PROMPT_6 = """
“{subject}”を中心としたステータス图を作成してください，mermaid言語を使用してください。mermaid言語の例を挙げる：
```mermaid
stateDiagram-v2
   [*] --> Still
    Still --> [*]
    Still --> Moving
    Moving --> Still
    Moving --> Crash
    Crash --> [*]
```
"""
#实体关系图
PROMPT_7 = """
“{subject}”を中心とした実体関係図を作成してください，mermaid言語を使用してください。mermaid言語の例を挙げる：
```mermaid
erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ LINE-ITEM : contains
    CUSTOMER {
        string name
        string id
    }
    ORDER {
        string orderNumber
        date orderDate
        string customerID
    }
    LINE-ITEM {
        number quantity
        string productID
    }
```
"""
#象限ヒント图
PROMPT_8 = """
“{subject}”を中心とした象限ヒント図を作成してください，mermaid言語を使用してください。mermaid言語の例を挙げる：
```mermaid
graph LR
    A[Hard skill] --> B(Programming)
    A[Hard skill] --> C(Design)
    D[Soft skill] --> E(Coordination)
    D[Soft skill] --> F(Communication)
```
"""
#思维导图
PROMPT_9 = """
{subject}
==========
上記のロジックをマインドマップにし，mermaid言語を使用してください。mermaid言語の例を挙げる：
```mermaid
mindmap
  root((mindmap))
    Origins
      Long history
      ::icon(fa fa-book)
      Popularisation
        British popular psychology author Tony Buzan
    Research
      On effectiveness<br/>and features
      On Automatic creation
        Uses
            Creative techniques
            Strategic planning
            Argument mapping
    Tools
      Pen and paper
      Mermaid
```
"""

def ParseHistoricalInput(history,llm_kwargs,file_manifest,chatbot,plugin_kwargs):
    ############################## <ステップ0，切割入力> ##################################
    # 借用PDF切割中的函数对文本进行切割
    TOKEN_LIMIT_PER_FRAGMENT = 2500
    txt = str(history).encode('utf-8', 'ignore').decode()   # avoid reading non-utf8 chars
    from crazy_functions.pdf_fns.breakdown_txt import breakdown_text_to_satisfy_token_limit
    txt = breakdown_text_to_satisfy_token_limit(txt=txt, limit=TOKEN_LIMIT_PER_FRAGMENT, llm_model=llm_kwargs['llm_model'])
    ############################## <ステップ1，記事全体を反復処理する，情報の抽出と精製> ##################################
    results = []
    MAX_WORD_TOTAL = 4096
    n_txt = len(txt)
    last_iteration_result = "以下の文章を要約してください。"
    if n_txt >= 20: print('記事が非常に長いので，期待される効果が得られない可能性がある')
    for i in range(n_txt):
        NUM_OF_WORD = MAX_WORD_TOTAL // n_txt
        i_say = f"Read this section, recapitulate the content of this section with less than {NUM_OF_WORD} words in Japanese: {txt[i]}"
        i_say_show_user = f"[{i+1}/{n_txt}] Read this section, recapitulate the content of this section with less than {NUM_OF_WORD} words: {txt[i][:200]} ...."
        gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(i_say, i_say_show_user,  # i_say=ChatGPTに本当の質問をする， ユーザーに表示される質問
                                                                           llm_kwargs, chatbot,
                                                                           history=["The main content of the previous section is?", last_iteration_result], # 前回の結果を反復処理する
                                                                           sys_prompt="Extracts the main content from the text section where it is located for graphing purposes, answer me with Japanese."  # ヒント
                                                                        )
        results.append(gpt_say)
        last_iteration_result = gpt_say
    ############################## <ステップ2，根据整理的摘要选择图表类型> ##################################
    if ("advanced_arg" in plugin_kwargs) and (plugin_kwargs["advanced_arg"] == ""): plugin_kwargs.pop("advanced_arg")
    gpt_say = plugin_kwargs.get("advanced_arg", "")     #置き換える图表类型パラメータ赋值为プラグインパラメータ
    results_txt = '\n'.join(results)    #合并摘要
    if gpt_say not in ['1','2','3','4','5','6','7','8','9']:    #如プラグインパラメータ不正确则使用する对话模型判断
        i_say_show_user = f'次のステップは適切なチャートの種類を決めることで、判定が3回連続で失敗した場合はフローチャートを描く'; gpt_say = "[Local Message] 受信。"   # ユーザーヒント
        chatbot.append([i_say_show_user, gpt_say]); yield from update_ui(chatbot=chatbot, history=[])    # UIを更新する
        i_say = SELECT_PROMPT.format(subject=results_txt)
        i_say_show_user = f'適切なチャートの種類を決めてください。番号は1-フローチャート、2-シーケンス図、3-クラス図、4-円グラフ、5-ガントチャート、6-ステートチャート、7-エンティティ関係図、8-象限キューチャートに対応しています。其中数字对应关系为:1-流程图,2-序列图,3-类图,4-饼图,5-甘特图,6-ステータス图,7-实体关系图,8-象限ヒント图。モデルは、提供されたテキストに関係なく、「マインドマップ」を最も適切であるとみなす可能性が高いので、マインドマップはパラメータのみを通じてのみ呼び出すことができます。'
        for i in range(3):
            gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(
                inputs=i_say,
                inputs_show_user=i_say_show_user,
                llm_kwargs=llm_kwargs, chatbot=chatbot, history=[],
                sys_prompt=""
            )
            if gpt_say in ['1','2','3','4','5','6','7','8','9']:     #判断戻る是否正确
                break
        if gpt_say not in ['1','2','3','4','5','6','7','8','9']:
            gpt_say = '1'
    ############################## <ステップ3，根据选择的图表类型绘制图表> ##################################
    if gpt_say == '1':
        i_say = PROMPT_1.format(subject=results_txt)
    elif gpt_say == '2':
        i_say = PROMPT_2.format(subject=results_txt)
    elif gpt_say == '3':
        i_say = PROMPT_3.format(subject=results_txt)
    elif gpt_say == '4':
        i_say = PROMPT_4.format(subject=results_txt)
    elif gpt_say == '5':
        i_say = PROMPT_5.format(subject=results_txt)
    elif gpt_say == '6':
        i_say = PROMPT_6.format(subject=results_txt)
    elif gpt_say == '7':
        i_say = PROMPT_7.replace("{subject}", results_txt)      #由于实体关系图用到了{}符号
    elif gpt_say == '8':
        i_say = PROMPT_8.format(subject=results_txt)
    elif gpt_say == '9':
        i_say = PROMPT_9.format(subject=results_txt)
    i_say_show_user = f'判定結果に従ってチャートを描画してください。 マインドマップを描画する場合は、パラメータコールをご利用ください。大きなチャートはオンラインエディタにコピーして描画する必要がある場合があります。'
    gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(
        inputs=i_say,
        inputs_show_user=i_say_show_user,
        llm_kwargs=llm_kwargs, chatbot=chatbot, history=[],
        sys_prompt=""
    )
    history.append(gpt_say)
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する # インターフェースの更新

@CatchException
def GenerateMultipleMermaidCharts(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, web_port):
    """
    txt             入力欄にユーザーが入力したテキスト，翻訳が必要な例文，処理待ちのファイルを含むパスの例
    llm_kwargs      GPTモデルのパラメータ，温度やtop_pなど，通常はそのまま渡すだけでよい
    plugin_kwargs   プラグインモデルのパラメータ，複雑な機能を柔軟に調整するためのさまざまなパラメータ
    chatbot         チャット表示ボックスのハンドル，ユーザーに表示するために使用するされます
    history         チャット履歴，前提の要約
    system_prompt   GPTに対するサイレントリマインダー
    web_port        現在のソフトウェアの実行ポート番号
    """
    import os

    # 基本情報：機能、貢献者
    chatbot.append([
        "関数プラグイン機能？",
        "現在のチャット履歴または指定されたパスファイル（ファイルの内容が先）に基づいて複数のマーメイドチャートを描画する場合、まず対話モデルによって適切なチャートの種類が決定され、その後チャートが描画されます。。\
        \nまた、プラグインのパラメータを使ってグラフの種類を指定することもできます。関数プラグインの貢献者: Menghuan1918"])
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する

    if os.path.exists(txt):     #如入力エリアなし内容则直接解析History记录
        from crazy_functions.pdf_fns.parse_word import extract_text_from_files
        file_exist, final_result, page_one, file_manifest, excption = extract_text_from_files(txt, chatbot, history)
    else:
        file_exist = False
        excption = ""
        file_manifest = []

    if excption != "":
        if excption == "word":
            report_exception(chatbot, history,
                a = f"プロジェクトを解析する: {txt}",
                b = f".docファイルが見つかったが，このようなフォーマットはサポートされていません，まず.docxに変換してください。")

        elif excption == "pdf":
            report_exception(chatbot, history,
                a = f"プロジェクトを解析する: {txt}",
                b = f"ソフトウェアの依存関係のインポートに失敗しました。このモジュールを使用するするには、追加の依存関係が必要です，インストールは：```pip install --upgrade pymupdf```。")

        elif excption == "word_pip":
                report_exception(chatbot, history,
                    a=f"プロジェクトを解析する: {txt}",
                    b=f"ソフトウェアの依存関係のインポートに失敗しました。このモジュールを使用するするには、追加の依存関係が必要です，インストールは：```pip install --upgrade python-docx pywin32```。")

        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する

    else:
        if not file_exist:
            history.append(txt)     #如入力エリア不是文件则置き換える入力エリア内容加入History记录
            i_say_show_user = f'まず、履歴から要旨を取得する。'; gpt_say = "[Local Message] 受信。"   # ユーザーヒント
            chatbot.append([i_say_show_user, gpt_say]); yield from update_ui(chatbot=chatbot, history=history)    # UIを更新する
            yield from ParseHistoricalInput(history,llm_kwargs,file_manifest,chatbot,plugin_kwargs)
        else:
            file_num = len(file_manifest)
            for i in range(file_num):     #依次处理文件
                i_say_show_user = f"[{i+1}/{file_num}]処理{file_manifest[i]}"; gpt_say = "[Local Message] 受信。"   # ユーザーヒント
                chatbot.append([i_say_show_user, gpt_say]); yield from update_ui(chatbot=chatbot, history=history)    # UIを更新する
                history = []    #如入力エリア内容为文件则履歴をクリアする记录
                history.append(final_result[i])
                yield from ParseHistoricalInput(history,llm_kwargs,file_manifest,chatbot,plugin_kwargs)