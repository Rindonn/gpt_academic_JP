import logging
import os
import gradio as gr
from toolbox import get_conf, ProxyNetworkActivate

CODE_HIGHLIGHT, ADD_WAIFU, LAYOUT = get_conf("CODE_HIGHLIGHT", "ADD_WAIFU", "LAYOUT")
theme_dir = os.path.dirname(__file__)


def dynamic_set_theme(THEME):
    set_theme = gr.themes.ThemeClass()
    with ProxyNetworkActivate("Download_Gradio_Theme"):
        logging.info("正在下载Gradio主题，お待ちください。")
        if THEME.startswith("Huggingface-"):
            THEME = THEME.lstrip("Huggingface-")
        if THEME.startswith("huggingface-"):
            THEME = THEME.lstrip("huggingface-")
        set_theme = set_theme.from_hub(THEME.lower())
    return set_theme


def adjust_theme():
    try:
        set_theme = gr.themes.ThemeClass()
        with ProxyNetworkActivate("Download_Gradio_Theme"):
            logging.info("正在下载Gradio主题，お待ちください。")
            THEME = get_conf("THEME")
            if THEME.startswith("Huggingface-"):
                THEME = THEME.lstrip("Huggingface-")
            if THEME.startswith("huggingface-"):
                THEME = THEME.lstrip("huggingface-")
            set_theme = set_theme.from_hub(THEME.lower())

        from themes.common import get_common_html_javascript_code
        js = get_common_html_javascript_code()
        
        if not hasattr(gr, "RawTemplateResponse"):
            gr.RawTemplateResponse = gr.routes.templates.TemplateResponse
        gradio_original_template_fn = gr.RawTemplateResponse

        def gradio_new_template_fn(*args, **kwargs):
            res = gradio_original_template_fn(*args, **kwargs)
            res.body = res.body.replace(b"</html>", f"{js}</html>".encode("utf8"))
            res.init_headers()
            return res

        gr.routes.templates.TemplateResponse = (
            gradio_new_template_fn  # override gradio template
        )
    except Exception:
        set_theme = None
        from toolbox import trimmed_format_exc

        logging.error("Gradioのバージョンが古いです, フォントと色をカスタマイズできません:", trimmed_format_exc())
    return set_theme


with open(os.path.join(theme_dir, "common.css"), "r", encoding="utf-8") as f:
    advanced_css = f.read()
