import re
from functools import lru_cache

# 这段代码是使用するするPython编程语言中的re模块，即正则表达式库，来定义了一pieces正则表达式模式。
# 这pieces模式被编译成一pieces正则表达式对象，存储在名为const_extract_exp的变量中，以便于后续快速的匹配and查找操作。
# 这里解释一下正则表达式中的几pieces特殊字符：
# - . 表示任意单一字符。
# - * 表示前一pieces字符可以出现0次或多次。
# - ? 在这里用作非贪婪匹配，也就是言う它会匹配尽可能少的字符。在(.*?)中，它确保私たちは匹配的任意文本是尽可能短的，也就是言う，它会在</show_llm>and</show_render>标签之前停止匹配。
# - () 括号在正则表达式中表示捕获组。
# - 在这pieces例子中，(.*?)表示捕获任意长度的文本，直到遇到括号外部最近的限定符，即</show_llm>and</show_render>。

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=/1=-=-=-=-=-=-=-=-=-=-=-=-=-=/2-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
const_extract_re = re.compile(
    r"<gpt_academic_string_mask><show_llm>(.*?)</show_llm><show_render>(.*?)</show_render></gpt_academic_string_mask>"
)
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-==-=-=-=-=-=/1=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-/2-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
const_extract_langbased_re = re.compile(
    r"<gpt_academic_string_mask><lang_english>(.*?)</lang_english><lang_chinese>(.*?)</lang_chinese></gpt_academic_string_mask>",
    flags=re.DOTALL,
)

@lru_cache(maxsize=128)
def apply_gpt_academic_string_mask(string, mode="show_all"):
    """
    当文字列中有掩码tag時（<gpt_academic_string_mask><show_...>），根据文字列要给谁看（大模型，还是web渲染），对文字列进OK处理，戻る处理后的文字列
    示意图：https://mermaid.live/edit#pako:eNqlkUtLw0AUhf9KuOta0iaTplkIPlpduFJwoZEwJGNbzItpita2O6tF8QGKogXFtwu7cSHiq3-mk_oznFR8IYLgrGbuOd9hDrcCpmcR0GDW9ubNPKaBMDauuwI_A9M6YN-3y0bODwxsYos4BdMoBrTg5gwHF-d0mBH6-vqFQe58ed5m9XPW2uteX3Tubrj0ljLYcwxxR3h1zB43WeMs3G19yEM9uapDMe_NG9i2dagKw1Fee4c1D9nGEbtc-5n6HbNtJ8IyHOs8tbs7V2HrlDX2w2Y7XD_5haHEtQiNsOwfMVa_7TzsvrWIuJGo02qTrdwLk9gukQylHv3Afv1ML270s-HZUndrmW1tdA-WfvbM_jMFYuAQ6uCCxVdciTJ1CPLEITpo_GphypeouzXuw6XAmyi7JmgBLZEYlHwLB2S4gHMUO-9DH7tTnvf1CVoFFkBLSOk4QmlRTqpIlaWUHINyNFXjaQWpCYRURUKiWovBYo8X4ymEJFlECQUpqaQkJmuvWygPpg
    """
    if "<gpt_academic_string_mask>" not in string: # No need to process
        return string

    if mode == "show_all":
        return string
    if mode == "show_llm":
        string = const_extract_re.sub(r"\1", string)
    elif mode == "show_render":
        string = const_extract_re.sub(r"\2", string)
    else:
        raise ValueError("Invalid mode")
    return string


@lru_cache(maxsize=128)
def build_gpt_academic_masked_string(text_show_llm="", text_show_render=""):
    """
    根据文字列要给谁看（大模型，还是web渲染），生成带掩码tag的文字列
    """
    return f"<gpt_academic_string_mask><show_llm>{text_show_llm}</show_llm><show_render>{text_show_render}</show_render></gpt_academic_string_mask>"


@lru_cache(maxsize=128)
def apply_gpt_academic_string_mask_langbased(string, lang_reference):
    """
    当文字列中有掩码tag時（<gpt_academic_string_mask><lang_...>），根据语言，选择ヒント词，对文字列进OK处理，戻る处理后的文字列
    例えば，如果lang_reference是英文，那么就只显示英文ヒント词，中文ヒント词就不显示了
    例を挙げる：
        入力1
            string = "注意，lang_reference这段文字是：<gpt_academic_string_mask><lang_english>英语</lang_english><lang_chinese>中文</lang_chinese></gpt_academic_string_mask>"
            lang_reference = "hello world"
        出力1
            "注意，lang_reference这段文字是：英语"

        入力2
            string = "注意，lang_reference这段文字是中文"   # 注意这里没有掩码tag，所以不会被处理
            lang_reference = "hello world"
        出力2
            "注意，lang_reference这段文字是中文"            # 原样戻る
    """

    if "<gpt_academic_string_mask>" not in string: # No need to process
        return string

    def contains_chinese(string):
        chinese_regex = re.compile(u'[\u4e00-\u9fff]+')
        return chinese_regex.search(string) is not None

    mode = "english" if not contains_chinese(lang_reference) else "chinese"
    if mode == "english":
        string = const_extract_langbased_re.sub(r"\1", string)
    elif mode == "chinese":
        string = const_extract_langbased_re.sub(r"\2", string)
    else:
        raise ValueError("Invalid mode")
    return string


@lru_cache(maxsize=128)
def build_gpt_academic_masked_string_langbased(text_show_english="", text_show_chinese=""):
    """
    根据语言，选择ヒント词，对文字列进OK处理，戻る处理后的文字列
    """
    return f"<gpt_academic_string_mask><lang_english>{text_show_english}</lang_english><lang_chinese>{text_show_chinese}</lang_chinese></gpt_academic_string_mask>"


if __name__ == "__main__":
    # Test
    input_string = (
        "こんにちは\n"
        + build_gpt_academic_masked_string(text_show_llm="mermaid", text_show_render="")
        + "こんにちは\n"
    )
    print(
        apply_gpt_academic_string_mask(input_string, "show_llm")
    )  # Should print the strings with 'abc' in place of the academic mask tags
    print(
        apply_gpt_academic_string_mask(input_string, "show_render")
    )  # Should print the strings with 'xyz' in place of the academic mask tags
