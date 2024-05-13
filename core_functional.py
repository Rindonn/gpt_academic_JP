# 'primary' 颜色对应 theme.py 中的 primary_hue
# 'secondary' 颜色对应 theme.py 中的 neutral_hue
# 'stop' 颜色对应 theme.py 中的 color_er
import importlib
from toolbox import clear_line_break
from toolbox import apply_gpt_academic_string_mask_langbased
from toolbox import build_gpt_academic_masked_string_langbased
from textwrap import dedent

def get_core_functions():
    return {

        "論文テキストを改善": {
            # [1*] テキストの翻訳文字列，あなたの入力の前に追加されます。例えば，要求を説明するために使用するされます，例えば翻訳、コードの説明、修正など。
            #      这里填一piecesヒント词文字列就行了，这里为了区分中英文情景搞复杂了一点
            "Prefix":   build_gpt_academic_masked_string_langbased(
                            text_show_english=
                                r"Below is a paragraph from an academic paper. Polish the writing to meet the academic style, "
                                r"improve the spelling, grammar, clarity, concision and overall readability. When necessary, rewrite the whole sentence. "
                                r"Firstly, you should provide the polished paragraph. "
                                r"Secondly, you should list all your modification and explain the reasons to do so in markdown table.",
                            text_show_chinese=
                                r"日本語学術論文の執筆改善アシスタントとして，Your task is to improve the spelling, grammar, clarity, conciseness, and overall readability of the provided text，"
                                r"同時に長い文を分解する，重複を減らす，And provide improvement suggestions。まず修正したテキストを提供して，markdownテーブルで修正した内容を入力し，修正理由も書いて下さい:"
                        ) + "\n\n",
            # [2*] 后缀文字列，あなたの入力の後に追加されます。例えば，接頭辞と組み合わせて、入力内容を引用符で囲むことができます
            "Suffix":   r"",
            # [3] ボタンの色 (オプションパラメータ，デフォルトのセカンダリ)
            "Color":    r"secondary",
            # [4] ボタンが表示可能かどうか (オプションパラメータ，原始文本，テキストの翻訳)
            "Visible": True,
            # [5] 原始文本 (オプションパラメータ，デフォルトはFalseです，以前の対話履歴を処理しない)
            "AutoClearHistory": False,
            # [6] 文本前処理 （オプションパラメータ，# None，例を挙げる：写pieces函数移除所有的换行符）
            "PreProcess": None,
        },


        "マインドマップを作り": {
            # テキストの翻訳，あなたの入力の前に追加されます。例えば，要求を説明するために使用するされます，例えば翻訳、コードの説明、修正など
            "Prefix":   '''"""\n\n''',
            # 后缀，あなたの入力の後に追加されます。例えば，接頭辞と組み合わせて、入力内容を引用符で囲むことができます
            "Suffix":
                # dedent() 函数用于去除多行文字列的缩进
                dedent("\n\n"+r'''
                    """

                    mermaid flowchartを利用してテキストを要約し，テキストの内容とロジック関係などを抽出して下さい，例えば：

                    以下は要約した結果をmermaid flowchartの形式で示します：
                    ```mermaid
                    flowchart LR
                        A["ポイント名前1"] --> B("ポイント名前2")
                        B --> C{"ポイント名前3"}
                        C --> D["ポイント名前4"]
                        C --> |"矢印名前1"| E["ポイント名前5"]
                        C --> |"矢印名前2"| F["ポイント名前6"]
                    ```

                    ご注意：
                    （1）日本語を使ってください
                    （2）ポイント名前は英字のクオーテーションマークを使ってください，例えば["Laptop"]
                    （3）`|` と `"`の間にスペースなし
                    （4）状況によるflowchart LR（左から右まで）またはflowchart TD（上から下まで）を選んでください
                '''),
        },


        "文法チェック（英語）": {
            "Prefix":   r"Help me ensure that the grammar and the spelling is correct. "
                        r"Do not try to polish the text, if no mistake is found, tell me that this paragraph is good. "
                        r"If you find grammar or spelling mistakes, please list mistakes you find in a two-column markdown table, "
                        r"put the original text the first column, "
                        r"put the corrected text in the second column and highlight the key words you fixed. "
                        r"Finally, please provide the proofreaded text.""\n\n"
                        r"Example:""\n"
                        r"Paragraph: How is you? Do you knows what is it?""\n"
                        r"| Original sentence | Corrected sentence |""\n"
                        r"| :--- | :--- |""\n"
                        r"| How **is** you? | How **are** you? |""\n"
                        r"| Do you **knows** what **is** **it**? | Do you **know** what **it** **is** ? |""\n\n"
                        r"Below is a paragraph from an academic paper. "
                        r"You need to report all grammar and spelling mistakes as the example before."
                        + "\n\n",
            "Suffix":   r"",
            "PreProcess": clear_line_break,    # 前処理：改行をクリアする
        },


        "英語への翻訳": {
            "Prefix":   r"Please translate following sentence to English:" + "\n\n",
            "Suffix":   r"",
        },


        "学術的に英和翻訳": {
            "Prefix":   build_gpt_academic_masked_string_langbased(
                            text_show_chinese=
                                r"I want you to act as a scientific English-Japanese translator, "
                                r"I will provide you with some paragraphs in one language "
                                r"and your task is to accurately and academically translate the paragraphs only into the other language. "
                                r"Do not repeat the original provided paragraphs after translation. "
                                r"You should use artificial intelligence tools, "
                                r"such as natural language processing, and rhetorical knowledge "
                                r"and experience about effective writing techniques to reply. "
                                r"I'll give you my paragraphs as follows, tell me what language it is written in, and then translate:",
                            text_show_english=
                                r"あなたは経験豊富な翻訳者で，日本語の文法、わかりやすさ、簡潔さ、全体的な読みやすさを考えて，"
                                r"学術論文を日本語に翻訳してください，"
                                r"必要に応じて，文章の順番を変えて、翻訳された段落が日本語に沿ったものになるようにしてください。"
                                r"翻訳してもらう文章は以下の通り："
                        ) + "\n\n",
            "Suffix":   r"",
        },


        "英語から日本語へ翻訳": {
            "Prefix":   r"自然な日本語に翻訳する：" + "\n\n",
            "Suffix":   r"",
        },


        "画像検索": {
            "Prefix":   r"インターネット上の画像を探してください。Unsplash APIを使用するする(https://source.unsplash.com/960x640/?<英語のキーワード>)画像のURLを取得する，"
                        r"次に、Markdown形式でパッケージ化してください，そしてバックスラッシュを含めないでください，コードブロックを使用するしないでください。今，以下の説明に従って画像を送信してください：" + "\n\n",
            "Suffix":   r"",
            "Visible":  False,
        },


        "コード説明": {
            "Prefix":   r"以下のコードを説明してください：" + "\n```\n",
            "Suffix":   "\n```\n",
        },


        "参考文献をBibに変換する": {
            "Prefix":   r"Here are some bibliography items, please transform them into bibtex style."
                        r"Note that, reference styles maybe more than one kind, you should transform each item correctly."
                        r"Items need to be transformed:" + "\n\n",
            "Suffix":   r"",
        }
    }


def handle_core_functionality(additional_fn, inputs, history, chatbot):
    import core_functional
    importlib.reload(core_functional)    # プロンプトのホット更新
    core_functional = core_functional.get_core_functions()
    addition = chatbot._cookies['customize_fn_overwrite']
    if additional_fn in addition:
        # 自定义功能
        inputs = addition[additional_fn]["Prefix"] + inputs + addition[additional_fn]["Suffix"]
        return inputs, history
    else:
        # 预制功能
        if "PreProcess" in core_functional[additional_fn]:
            if core_functional[additional_fn]["PreProcess"] is not None:
                inputs = core_functional[additional_fn]["PreProcess"](inputs)  # 前処理関数を取得する（ある場合は）
        # 为文字列加上上面定义的テキストの翻訳and后缀。
        inputs = apply_gpt_academic_string_mask_langbased(
            string = core_functional[additional_fn]["Prefix"] + inputs + core_functional[additional_fn]["Suffix"],
            lang_reference = inputs,
        )
        if core_functional[additional_fn].get("AutoClearHistory", False):
            history = []
        return inputs, history

if __name__ == "__main__":
    t = get_core_functions()["总结绘制脑图"]
    print(t["Prefix"] + t["Suffix"])