from toolbox import CatchException, update_ui, report_exception
from .crazy_utils import request_gpt_model_in_new_thread_with_ui_alive
import datetime

#以下是每类图表的PROMPT
SELECT_PROMPT = """
“{subject}”
=============
以上是从文章中提取的摘要,置き換える会使用する这些摘要绘制图表。请你选择一pieces合适的图表类型:
1 流程图
2 序列图
3 类图
4 饼图
5 甘特图
6 ステータス图
7 实体关系图
8 象限ヒント图
不需要解释原因，仅需要出力单pieces不带任何标点符号的数字。
"""
#没有思维导图!!!测试发现模型始终会優先选择思维导图
#流程图
PROMPT_1 = """
请你给出围绕“{subject}”的逻辑关系图，使用するmermaid语法，mermaid语法例を挙げる：
```mermaid
graph TD
    P(编程) --> L1(Python)
    P(编程) --> L2(C)
    P(编程) --> L3(C++)
    P(编程) --> L4(Javascipt)
    P(编程) --> L5(PHP)
```
"""
#序列图
PROMPT_2 = """
请你给出围绕“{subject}”的序列图，使用するmermaid语法，mermaid语法例を挙げる：
```mermaid
sequenceDiagram
    participant A as 用户
    participant B as 系统
    A->>B: 登录请求
    B->>A: 登录成功
    A->>B: 获取数据
    B->>A: 戻る数据
```
"""
#类图
PROMPT_3 = """
请你给出围绕“{subject}”的类图，使用するmermaid语法，mermaid语法例を挙げる：
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
请你给出围绕“{subject}”的饼图，使用するmermaid语法，mermaid语法例を挙げる：
```mermaid
pie title Pets adopted by volunteers
    "狗" : 386
    "猫" : 85
    "兔子" : 15
```
"""
#甘特图
PROMPT_5 = """
请你给出围绕“{subject}”的甘特图，使用するmermaid语法，mermaid语法例を挙げる：
```mermaid
gantt
    title 项目开发流程
    dateFormat  YYYY-MM-DD
    section 设计
    需求分析 :done, des1, 2024-01-06,2024-01-08
    原型设计 :active, des2, 2024-01-09, 3d
    UI设计 : des3, after des2, 5d
    section 开发
    前端开发 :2024-01-20, 10d
    后端开发 :2024-01-20, 10d
```
"""
#ステータス图
PROMPT_6 = """
请你给出围绕“{subject}”的ステータス图，使用するmermaid语法，mermaid语法例を挙げる：
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
请你给出围绕“{subject}”的实体关系图，使用するmermaid语法，mermaid语法例を挙げる：
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
请你给出围绕“{subject}”的象限图，使用するmermaid语法，mermaid语法例を挙げる：
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
请给出上方内容的思维导图，充分考虑其之间的逻辑，使用するmermaid语法，mermaid语法例を挙げる：
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
    last_iteration_result = "从以下文本中要約を抽出する。"
    if n_txt >= 20: print('記事が非常に長い，期待される効果が得られない')
    for i in range(n_txt):
        NUM_OF_WORD = MAX_WORD_TOTAL // n_txt
        i_say = f"Read this section, recapitulate the content of this section with less than {NUM_OF_WORD} words in Chinese: {txt[i]}"
        i_say_show_user = f"[{i+1}/{n_txt}] Read this section, recapitulate the content of this section with less than {NUM_OF_WORD} words: {txt[i][:200]} ...."
        gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(i_say, i_say_show_user,  # i_say=ChatGPTに本当の質問をする， ユーザーに表示される質問
                                                                           llm_kwargs, chatbot,
                                                                           history=["The main content of the previous section is?", last_iteration_result], # 前回の結果を反復処理する
                                                                           sys_prompt="Extracts the main content from the text section where it is located for graphing purposes, answer me with Chinese."  # ヒント
                                                                        )
        results.append(gpt_say)
        last_iteration_result = gpt_say
    ############################## <ステップ2，根据整理的摘要选择图表类型> ##################################
    if ("advanced_arg" in plugin_kwargs) and (plugin_kwargs["advanced_arg"] == ""): plugin_kwargs.pop("advanced_arg")
    gpt_say = plugin_kwargs.get("advanced_arg", "")     #置き換える图表类型パラメータ赋值为プラグインパラメータ
    results_txt = '\n'.join(results)    #合并摘要
    if gpt_say not in ['1','2','3','4','5','6','7','8','9']:    #如プラグインパラメータ不正确则使用する对话模型判断
        i_say_show_user = f'次に置き換える判断适合的图表类型,如连续3次判断失敗しました置き換える会使用する流程图进行绘制'; gpt_say = "[Local Message] 受信。"   # ユーザーヒント
        chatbot.append([i_say_show_user, gpt_say]); yield from update_ui(chatbot=chatbot, history=[])    # UIを更新する
        i_say = SELECT_PROMPT.format(subject=results_txt)
        i_say_show_user = f'请判断适合使用する的流程图类型,其中数字对应关系为:1-流程图,2-序列图,3-类图,4-饼图,5-甘特图,6-ステータス图,7-实体关系图,8-象限ヒント图。由于不管提供文本是什么,模型大概率认为"思维导图"最合适,因此思维导图仅能通过パラメータ调用。'
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
    i_say_show_user = f'请根据判断结果绘制相应的图表。如需绘制思维导图请使用するパラメータ调用,同時过大的图表可能需要复制到在线编辑器中进行渲染。'
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
        "根据当前チャット履歴或指定的路径文件(文件内容優先)绘制多种mermaid图表，置き換える会由对话模型首先判断适合的图表类型，随后绘制图表。\
        \n您也可以使用するプラグインパラメータ指定绘制的图表类型,関数プラグインの貢献者: Menghuan1918"])
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
                b = f"找到了.doc文件，但是该文件フォーマット不被支持，まず.docx形式に変換してください。")

        elif excption == "pdf":
            report_exception(chatbot, history,
                a = f"プロジェクトを解析する: {txt}",
                b = f"ソフトウェアの依存関係のインポートに失敗しました。このモジュールを使用するするには、追加の依存関係が必要です，インストールテキストの翻訳```pip install --upgrade pymupdf```。")

        elif excption == "word_pip":
                report_exception(chatbot, history,
                    a=f"プロジェクトを解析する: {txt}",
                    b=f"ソフトウェアの依存関係のインポートに失敗しました。このモジュールを使用するするには、追加の依存関係が必要です，インストールテキストの翻訳```pip install --upgrade python-docx pywin32```。")

        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する

    else:
        if not file_exist:
            history.append(txt)     #如入力エリア不是文件则置き換える入力エリア内容加入History记录
            i_say_show_user = f'首先你从History记录中要約を抽出する。'; gpt_say = "[Local Message] 受信。"   # ユーザーヒント
            chatbot.append([i_say_show_user, gpt_say]); yield from update_ui(chatbot=chatbot, history=history)    # UIを更新する
            yield from ParseHistoricalInput(history,llm_kwargs,file_manifest,chatbot,plugin_kwargs)
        else:
            file_num = len(file_manifest)
            for i in range(file_num):     #依次处理文件
                i_say_show_user = f"[{i+1}/{file_num}]处理文件{file_manifest[i]}"; gpt_say = "[Local Message] 受信。"   # ユーザーヒント
                chatbot.append([i_say_show_user, gpt_say]); yield from update_ui(chatbot=chatbot, history=history)    # UIを更新する
                history = []    #如入力エリア内容为文件则履歴をクリアする记录
                history.append(final_result[i])
                yield from ParseHistoricalInput(history,llm_kwargs,file_manifest,chatbot,plugin_kwargs)