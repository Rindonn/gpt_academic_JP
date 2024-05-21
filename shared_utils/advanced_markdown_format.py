import markdown
import re
import os
import math
from textwrap import dedent
from functools import lru_cache
from pymdownx.superfences import fence_code_format
from latex2mathml.converter import convert as tex2mathml
from shared_utils.config_loader import get_conf as get_conf
from shared_utils.text_mask import apply_gpt_academic_string_mask

markdown_extension_configs = {
    "mdx_math": {
        "enable_dollar_delimiter": True,
        "use_gitlab_delimiters": False,
    },
}

code_highlight_configs = {
    "pymdownx.superfences": {
        "css_class": "codehilite",
        "custom_fences": [
            {"name": "mermaid", "class": "mermaid", "format": fence_code_format}
        ],
    },
    "pymdownx.highlight": {
        "css_class": "codehilite",
        "guess_lang": True,
        # 'auto_title': True,
        # 'linenums': True
    },
}

code_highlight_configs_block_mermaid = {
    "pymdownx.superfences": {
        "css_class": "codehilite",
        # "custom_fences": [
        #     {"name": "mermaid", "class": "mermaid", "format": fence_code_format}
        # ],
    },
    "pymdownx.highlight": {
        "css_class": "codehilite",
        "guess_lang": True,
        # 'auto_title': True,
        # 'linenums': True
    },
}

def tex2mathml_catch_exception(content, *args, **kwargs):
    try:
        content = tex2mathml(content, *args, **kwargs)
    except:
        content = content
    return content


def replace_math_no_render(match):
    content = match.group(1)
    if "mode=display" in match.group(0):
        content = content.replace("\n", "</br>")
        return f'<font color="#00FF00">$$</font><font color="#FF00FF">{content}</font><font color="#00FF00">$$</font>'
    else:
        return f'<font color="#00FF00">$</font><font color="#FF00FF">{content}</font><font color="#00FF00">$</font>'


def replace_math_render(match):
    content = match.group(1)
    if "mode=display" in match.group(0):
        if "\\begin{aligned}" in content:
            content = content.replace("\\begin{aligned}", "\\begin{array}")
            content = content.replace("\\end{aligned}", "\\end{array}")
            content = content.replace("&", " ")
        content = tex2mathml_catch_exception(content, display="block")
        return content
    else:
        return tex2mathml_catch_exception(content)


def markdown_bug_hunt(content):
    """
    mdx_mathのバグを解決する（beginコマンドを単一の$で囲むと余分になります<script>）
    """
    content = content.replace(
        '<script type="math/tex">\n<script type="math/tex; mode=display">',
        '<script type="math/tex; mode=display">',
    )
    content = content.replace("</script>\n</script>", "</script>")
    return content


def is_equation(txt):
    """
    判定是否为公式 | 测试1 写出洛伦兹定律，使TeX形式で公式 测试2 给出柯西不等式，使用するするlatexフォーマット 测试3 写出麦克斯韦方程组
    """
    if "```" in txt and "```reference" not in txt:
        return False
    if "$" not in txt and "\\[" not in txt:
        return False
    mathpatterns = {
        r"(?<!\\|\$)(\$)([^\$]+)(\$)": {"allow_multi_lines": False},  #  $...$
        r"(?<!\\)(\$\$)([^\$]+)(\$\$)": {"allow_multi_lines": True},  # $$...$$
        r"(?<!\\)(\\\[)(.+?)(\\\])": {"allow_multi_lines": False},  # \[...\]
        # r'(?<!\\)(\\\()(.+?)(\\\))': {'allow_multi_lines': False},                       # \(...\)
        # r'(?<!\\)(\\begin{([a-z]+?\*?)})(.+?)(\\end{\2})': {'allow_multi_lines': True},  # \begin...\end
        # r'(?<!\\)(\$`)([^`]+)(`\$)': {'allow_multi_lines': False},                       # $`...`$
    }
    matches = []
    for pattern, property in mathpatterns.items():
        flags = re.ASCII | re.DOTALL if property["allow_multi_lines"] else re.ASCII
        matches.extend(re.findall(pattern, txt, flags))
    if len(matches) == 0:
        return False
    contain_any_eq = False
    illegal_pattern = re.compile(r"[^\x00-\x7F]|echo")
    for match in matches:
        if len(match) != 3:
            return False
        eq_canidate = match[1]
        if illegal_pattern.search(eq_canidate):
            return False
        else:
            contain_any_eq = True
    return contain_any_eq


def fix_markdown_indent(txt):
    # fix markdown indent
    if (" - " not in txt) or (". " not in txt):
        # do not need to fix, fast escape
        return txt
    # walk through the lines and fix non-standard indentation
    lines = txt.split("\n")
    pattern = re.compile(r"^\s+-")
    activated = False
    for i, line in enumerate(lines):
        if line.startswith("- ") or line.startswith("1. "):
            activated = True
        if activated and pattern.match(line):
            stripped_string = line.lstrip()
            num_spaces = len(line) - len(stripped_string)
            if (num_spaces % 4) == 3:
                num_spaces_should_be = math.ceil(num_spaces / 4) * 4
                lines[i] = " " * num_spaces_should_be + stripped_string
    return "\n".join(lines)


FENCED_BLOCK_RE = re.compile(
    dedent(
        r"""
        (?P<fence>^[ \t]*(?:~{3,}|`{3,}))[ ]*                      # opening fence
        ((\{(?P<attrs>[^\}\n]*)\})|                              # (optional {attrs} or
        (\.?(?P<lang>[\w#.+-]*)[ ]*)?                            # optional (.)lang
        (hl_lines=(?P<quot>"|')(?P<hl_lines>.*?)(?P=quot)[ ]*)?) # optional hl_lines)
        \n                                                       # newline (end of opening fence)
        (?P<code>.*?)(?<=\n)                                     # the code block
        (?P=fence)[ ]*$                                          # closing fence
    """
    ),
    re.MULTILINE | re.DOTALL | re.VERBOSE,
)


def get_line_range(re_match_obj, txt):
    start_pos, end_pos = re_match_obj.regs[0]
    num_newlines_before = txt[: start_pos + 1].count("\n")
    line_start = num_newlines_before
    line_end = num_newlines_before + txt[start_pos:end_pos].count("\n") + 1
    return line_start, line_end


def fix_code_segment_indent(txt):
    lines = []
    change_any = False
    txt_tmp = txt
    while True:
        re_match_obj = FENCED_BLOCK_RE.search(txt_tmp)
        if not re_match_obj:
            break
        if len(lines) == 0:
            lines = txt.split("\n")

        # 清空 txt_tmp 对应的位置方便下次搜索
        start_pos, end_pos = re_match_obj.regs[0]
        txt_tmp = txt_tmp[:start_pos] + " " * (end_pos - start_pos) + txt_tmp[end_pos:]
        line_start, line_end = get_line_range(re_match_obj, txt)

        # 获取公共缩进
        shared_indent_cnt = 1e5
        for i in range(line_start, line_end):
            stripped_string = lines[i].lstrip()
            num_spaces = len(lines[i]) - len(stripped_string)
            if num_spaces < shared_indent_cnt:
                shared_indent_cnt = num_spaces

        # 修复缩进
        if (shared_indent_cnt < 1e5) and (shared_indent_cnt % 4) == 3:
            num_spaces_should_be = math.ceil(shared_indent_cnt / 4) * 4
            for i in range(line_start, line_end):
                add_n = num_spaces_should_be - shared_indent_cnt
                lines[i] = " " * add_n + lines[i]
            if not change_any:  # 遇到第一pieces
                change_any = True

    if change_any:
        return "\n".join(lines)
    else:
        return txt


@lru_cache(maxsize=128)  # 変換速度を高速化するためにlruキャッシュを使用するするする
def markdown_convertion(txt):
    """
    Markdown形式のテキストをHTML形式に変換する。数式が含まれている場合，公式をHTML形式に変換してください。
    """
    pre = '<div class="markdown-body">'
    suf = "</div>"
    if txt.startswith(pre) and txt.endswith(suf):
        # print('Warning，変換済みの文字列が入力されました，二次转化可能出問題')
        return txt  # すでに変換されています，再変換する必要はありません

    find_equation_pattern = r'<script type="math/tex(?:.*?)>(.*?)</script>'

    txt = fix_markdown_indent(txt)
    # txt = fix_code_segment_indent(txt)
    if is_equation(txt):  # $記号を持つ数式記号，And there is no code segment```のマーク
        # convert everything to html format
        split = markdown.markdown(text="---")
        convert_stage_1 = markdown.markdown(
            text=txt,
            extensions=[
                "sane_lists",
                "tables",
                "mdx_math",
                "pymdownx.superfences",
                "pymdownx.highlight",
            ],
            extension_configs={**markdown_extension_configs, **code_highlight_configs},
        )
        convert_stage_1 = markdown_bug_hunt(convert_stage_1)
        # 1. convert to easy-to-copy tex (do not render math)
        convert_stage_2_1, n = re.subn(
            find_equation_pattern,
            replace_math_no_render,
            convert_stage_1,
            flags=re.DOTALL,
        )
        # 2. convert to rendered equation
        convert_stage_2_2, n = re.subn(
            find_equation_pattern, replace_math_render, convert_stage_1, flags=re.DOTALL
        )
        # cat them together
        return pre + convert_stage_2_1 + f"{split}" + convert_stage_2_2 + suf
    else:
        return (
            pre
            + markdown.markdown(
                txt,
                extensions=[
                    "sane_lists",
                    "tables",
                    "pymdownx.superfences",
                    "pymdownx.highlight",
                ],
                extension_configs=code_highlight_configs,
            )
            + suf
        )


def close_up_code_segment_during_stream(gpt_reply):
    """
    GPTがコードを出力する途中で（前のものを出力し、1つの文字列に結合します```，しかし、まだ後ろの出力が完了していません```），後ろに補完する```

    Args:
        gpt_reply (str): GPTモデルからの返信文字列。

    Returns:
        str: Return a new string，コードスニペットの後ろに出力する```補う。

    """
    if "```" not in gpt_reply:
        return gpt_reply
    if gpt_reply.endswith("```"):
        return gpt_reply

    # Excludes the above two cases，私たちは
    segments = gpt_reply.split("```")
    n_mark = len(segments) - 1
    if n_mark % 2 == 1:
        return gpt_reply + "\n```"  # 出力代码フラグメント中！
    else:
        return gpt_reply


def special_render_issues_for_mermaid(text):
    # 用不太优雅的方式处理一piecescore_functional.py中出现的mermaid渲染特例：
    # 我不希望"总结绘制脑图"prompt中的mermaid渲染出来
    @lru_cache(maxsize=1)
    def get_special_case():
        from core_functional import get_core_functions
        special_case = get_core_functions()["总结绘制脑图"]["Suffix"]
        return special_case
    if text.endswith(get_special_case()): text = text.replace("```mermaid", "```")
    return text


def compat_non_markdown_input(text):
    """
    改善非markdown入力的显示效果，例えば置き換える空格转换为&nbsp;，置き換える换OK符转换为</br>等。
    """
    if "```" in text:
        # careful input：markdown入力
        text = special_render_issues_for_mermaid(text)  # 处理特殊的渲染問題
        return text
    elif "</div>" in text:
        # careful input：html入力
        return text
    else:
        # whatever input：非markdown入力
        lines = text.split("\n")
        for i, line in enumerate(lines):
            lines[i] = lines[i].replace(" ", "&nbsp;")  # 空格转换为&nbsp;
        text = "</br>".join(lines)  # 换OK符转换为</br>
        return text


@lru_cache(maxsize=128)  # 使用するするlru缓存
def simple_markdown_convertion(text):
    pre = '<div class="markdown-body">'
    suf = "</div>"
    if text.startswith(pre) and text.endswith(suf):
        return text  # すでに変換されています，再変換する必要はありません
    text = compat_non_markdown_input(text)    # 兼容非markdown入力
    text = markdown.markdown(
        text,
        extensions=["pymdownx.superfences", "tables", "pymdownx.highlight"],
        extension_configs=code_highlight_configs,
    )
    return pre + text + suf


def format_io(self, y):
    """
    入力と出力をHTML形式で解析する。Paragraphize the input part of the last item in y，出力部分のMarkdownと数式をHTML形式に変換する。
    """
    if y is None or y == []:
        return []
    i_ask, gpt_reply = y[-1]
    i_ask = apply_gpt_academic_string_mask(i_ask, mode="show_render")
    gpt_reply = apply_gpt_academic_string_mask(gpt_reply, mode="show_render")
    # コードが半分出力されたとき，後のものを試してみてください```
    if gpt_reply is not None:
        gpt_reply = close_up_code_segment_during_stream(gpt_reply)
    # 处理提问与出力
    y[-1] = (
        # 入力部分
        None if i_ask is None else simple_markdown_convertion(i_ask),
        # 出力部分
        None if gpt_reply is None else markdown_convertion(gpt_reply),
    )
    return y
