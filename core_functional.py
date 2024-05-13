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

        "学术语料校正中": {
            # [1*] テキストの翻訳文字列，あなたの入力の前に追加されます。例えば，要求を説明するために使用するされます，例えば翻訳、コードの説明、修正など。
            #      这里填一piecesヒント词文字列就行了，这里为了区分中英文情景搞复杂了一点
            "Prefix":   build_gpt_academic_masked_string_langbased(
                            text_show_english=
                                r"Below is a paragraph from an academic paper. Polish the writing to meet the academic style, "
                                r"improve the spelling, grammar, clarity, concision and overall readability. When necessary, rewrite the whole sentence. "
                                r"Firstly, you should provide the polished paragraph. "
                                r"Secondly, you should list all your modification and explain the reasons to do so in markdown table.",
                            text_show_chinese=
                                r"中国語学術論文の執筆改善アシスタントとして，Your task is to improve the spelling, grammar, clarity, conciseness, and overall readability of the provided text，"
                                r"同時に長い文を分解する，重複を減らす，And provide improvement suggestions。请先提供文本的更正版本，然后在markdown表格中列出修改的内容，并给出修改的理由:"
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


        "总结绘制脑图": {
            # テキストの翻訳，あなたの入力の前に追加されます。例えば，要求を説明するために使用するされます，例えば翻訳、コードの説明、修正など
            "Prefix":   '''"""\n\n''',
            # 后缀，あなたの入力の後に追加されます。例えば，接頭辞と組み合わせて、入力内容を引用符で囲むことができます
            "Suffix":
                # dedent() 函数用于去除多行文字列的缩进
                dedent("\n\n"+r'''
                    """

                    使用するmermaid flowchart对以上文本进行总结，概括上述段落的内容以及内在逻辑关系，例えば：

                    以下是对以上文本的总结，以mermaid flowchart的形式展示：
                    ```mermaid
                    flowchart LR
                        A["节点名1"] --> B("节点名2")
                        B --> C{"节点名3"}
                        C --> D["节点名4"]
                        C --> |"箭头名1"| E["节点名5"]
                        C --> |"箭头名2"| F["节点名6"]
                    ```

                    注意：
                    （1）使用する中文
                    （2）节点名字使用する引号包裹，如["Laptop"]
                    （3）`|` and `"`之间不要存在空格
                    （4）根据情况选择flowchart LR（从左到右）またはflowchart TD（从上到下）
                '''),
        },


        "構文エラーを検索する": {
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


        "中国語から英語への翻訳": {
            "Prefix":   r"Please translate following sentence to English:" + "\n\n",
            "Suffix":   r"",
        },


        "学术英中互译": {
            "Prefix":   build_gpt_academic_masked_string_langbased(
                            text_show_chinese=
                                r"I want you to act as a scientific English-Chinese translator, "
                                r"I will provide you with some paragraphs in one language "
                                r"and your task is to accurately and academically translate the paragraphs only into the other language. "
                                r"Do not repeat the original provided paragraphs after translation. "
                                r"You should use artificial intelligence tools, "
                                r"such as natural language processing, and rhetorical knowledge "
                                r"and experience about effective writing techniques to reply. "
                                r"I'll give you my paragraphs as follows, tell me what language it is written in, and then translate:",
                            text_show_english=
                                r"你是经验丰富的翻訳，请把以下学术文章段落翻訳成中文，"
                                r"并同時充分考虑中文的语法、清晰、简洁and整体可读性，"
                                r"必要に応じて，你可以修改整pieces句子的顺序以确保翻訳后的段落符合中文的语言习惯。"
                                r"你需要翻訳的文本如下："
                        ) + "\n\n",
            "Suffix":   r"",
        },


        "英語から中国語への翻訳": {
            "Prefix":   r"自然な中国語に翻訳する：" + "\n\n",
            "Suffix":   r"",
            "Visible":  False,
        },


        "画像を検索する": {
            "Prefix":   r"インターネット上の画像を探してください。Unsplash APIを使用するする(https://source.unsplash.com/960x640/?<英語のキーワード>)画像のURLを取得する，"
                        r"次に、Markdown形式でパッケージ化してください，そしてバックスラッシュを含めないでください，コードブロックを使用するしないでください。今，以下の説明に従って画像を送信してください：" + "\n\n",
            "Suffix":   r"",
            "Visible":  False,
        },


        "Explain the code": {
            "Prefix":   r"以下のコードを説明してください：" + "\n```\n",
            "Suffix":   "\n```\n",
        },


        "参考文献をBibに変換する": {
            "Prefix":   r"Here are some bibliography items, please transform them into bibtex style."
                        r"Note that, reference styles maybe more than one kind, you should transform each item correctly."
                        r"Items need to be transformed:" + "\n\n",
            "Visible":  False,
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