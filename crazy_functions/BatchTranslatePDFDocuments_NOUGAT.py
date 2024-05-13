from toolbox import CatchException, report_exception, get_log_folder, gen_time_str
from toolbox import update_ui, promote_file_to_downloadzone, update_ui_lastest_msg, disable_auto_promotion
from toolbox import write_history_to_file, promote_file_to_downloadzone
from .crazy_utils import request_gpt_model_in_new_thread_with_ui_alive
from .crazy_utils import request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency
from .crazy_utils import read_and_clean_pdf_text
from .pdf_fns.parse_pdf import parse_pdf, get_avail_grobid_url, translate_pdf
from colorful import *
import copy
import os
import math
import logging

def markdown_to_dict(article_content):
    import markdown
    from bs4 import BeautifulSoup
    cur_t = ""
    cur_c = ""
    results = {}
    for line in article_content:
        if line.startswith('#'):
            if cur_t!="":
                if cur_t not in results:
                    results.update({cur_t:cur_c.lstrip('\n')})
                else:
                    # 处理重名的章节
                    results.update({cur_t + " " + gen_time_str():cur_c.lstrip('\n')})
            cur_t = line.rstrip('\n')
            cur_c = ""
        else:
            cur_c += line
    results_final = {}
    for k in list(results.keys()):
        if k.startswith('# '):
            results_final['title'] = k.split('# ')[-1]
            results_final['authors'] = results.pop(k).lstrip('\n')
        if k.startswith('###### Abstract'):
            results_final['abstract'] = results.pop(k).lstrip('\n')

    results_final_sections = []
    for k,v in results.items():
        results_final_sections.append({
            'heading':k.lstrip("# "),
            'text':v if len(v) > 0 else f"The beginning of {k.lstrip('# ')} section."
        })
    results_final['sections'] = results_final_sections
    return results_final


@CatchException
def BatchTranslatePDFDocuments(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):

    disable_auto_promotion(chatbot)
    # 基本情報：機能、貢献者
    chatbot.append([
        "関数プラグイン機能？",
        "BatchTranslatePDFDocuments。関数プラグインの貢献者: Binary-Husky"])
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する

    # 履歴をクリアする，オーバーフローを防ぐために
    history = []

    from .crazy_utils import get_files_from_everything
    success, file_manifest, project_folder = get_files_from_everything(txt, type='.pdf')
    if len(file_manifest) > 0:
        # 依存関係のインポートを試みる，依存関係が不足している場合，インストールの提案を行います
        try:
            import nougat
            import tiktoken
        except:
            report_exception(chatbot, history,
                             a=f"プロジェクトを解析する: {txt}",
                             b=f"ソフトウェアの依存関係のインポートに失敗しました。このモジュールを使用するするには、追加の依存関係が必要です，インストールテキストの翻訳```pip install --upgrade nougat-ocr tiktoken```。")
            yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
            return
    success_mmd, file_manifest_mmd, _ = get_files_from_everything(txt, type='.mmd')
    success = success or success_mmd
    file_manifest += file_manifest_mmd
    chatbot.append(["文件リスト：", ", ".join([e.split('/')[-1] for e in file_manifest])]);
    yield from update_ui(      chatbot=chatbot, history=history)
    # 入力パラメータを検出する，入力パラメータが指定されていない場合，直接終了する
    if not success:
        if txt == "": txt = '空の入力欄'

    # ファイルが見つからなかった場合
    if len(file_manifest) == 0:
        report_exception(chatbot, history,
                         a=f"プロジェクトを解析する: {txt}", b=f"見つかりません任何.pdf拓展名のファイル: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return

    # タスクを正式に実行する
    yield from ParsePDF_NOUGAT(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt)




def ParsePDF_NOUGAT(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt):
    import copy
    import tiktoken
    TOKEN_LIMIT_PER_FRAGMENT = 1024
    generated_conclusion_files = []
    generated_html_files = []
    DST_LANG = "中文"
    from crazy_functions.crazy_utils import nougat_interface
    from crazy_functions.pdf_fns.report_gen_html import construct_html
    nougat_handle = nougat_interface()
    for index, fp in enumerate(file_manifest):
        if fp.endswith('pdf'):
            chatbot.append(["当前进度：", f"正在解析論文，お待ちください。（最初の実行時，需要花费较长時间下载NOUGATパラメータ）"]); yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
            fpp = yield from nougat_handle.NOUGAT_parse_pdf(fp, chatbot, history)
            promote_file_to_downloadzone(fpp, rename_file=os.path.basename(fpp)+'.nougat.mmd', chatbot=chatbot)
        else:
            chatbot.append(["当前論文なし需解析：", fp]); yield from update_ui(      chatbot=chatbot, history=history)
            fpp = fp
        with open(fpp, 'r', encoding='utf8') as f:
            article_content = f.readlines()
        article_dict = markdown_to_dict(article_content)
        logging.info(article_dict)
        yield from translate_pdf(article_dict, llm_kwargs, chatbot, fp, generated_conclusion_files, TOKEN_LIMIT_PER_FRAGMENT, DST_LANG)

    chatbot.append(("出力ファイルリストを提供する", str(generated_conclusion_files + generated_html_files)))
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する


