from toolbox import CatchException, report_exception, get_log_folder, gen_time_str, check_packages
from toolbox import update_ui, promote_file_to_downloadzone, update_ui_lastest_msg, disable_auto_promotion
from toolbox import write_history_to_file, promote_file_to_downloadzone
from .crazy_utils import request_gpt_model_in_new_thread_with_ui_alive
from .crazy_utils import request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency
from .crazy_utils import read_and_clean_pdf_text
from .pdf_fns.parse_pdf import parse_pdf, get_avail_grobid_url, translate_pdf
from colorful import *
import os


@CatchException
def BatchTranslatePDFDocuments(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):

    disable_auto_promotion(chatbot)
    # 基本情報：機能、貢献者
    chatbot.append([
        "関数プラグイン機能？",
        "BatchTranslatePDFDocuments。関数プラグインの貢献者: Binary-Husky"])
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する

    # 依存関係のインポートを試みる，依存関係が不足している場合，インストールの提案を行います
    try:
        check_packages(["fitz", "tiktoken", "scipdf"])
    except:
        report_exception(chatbot, history,
                         a=f"プロジェクトを解析する: {txt}",
                         b=f"ソフトウェアの依存関係のインポートに失敗しました。このモジュールを使用するするには、追加の依存関係が必要です，インストールテキストの翻訳```pip install --upgrade pymupdf tiktoken scipdf_parser```。")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return

    # 履歴をクリアする，オーバーフローを防ぐために
    history = []

    from .crazy_utils import get_files_from_everything
    success, file_manifest, project_folder = get_files_from_everything(txt, type='.pdf')
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
    grobid_url = get_avail_grobid_url()
    if grobid_url is not None:
        yield from ParsePDF_BasedOnGROBID(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, grobid_url)
    else:
        yield from update_ui_lastest_msg("GROBID利用出来ない，configのGROBID_URLをチェックして下さい。代わりに，ちょっと効が悪いコードを実行します。", chatbot, history, delay=3)
        yield from ParsePDF(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt)


def ParsePDF_BasedOnGROBID(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, grobid_url):
    import copy, json
    TOKEN_LIMIT_PER_FRAGMENT = 1024
    generated_conclusion_files = []
    generated_html_files = []
    DST_LANG = "中文"
    from crazy_functions.pdf_fns.report_gen_html import construct_html
    for index, fp in enumerate(file_manifest):
        chatbot.append(["当前进度：", f"正在连接GROBID服务，お待ちください: {grobid_url}\n如果待つ時间过长，请修改config中的GROBID_URL，可修改成本地GROBID服务。"]); yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        article_dict = parse_pdf(fp, grobid_url)
        grobid_json_res = os.path.join(get_log_folder(), gen_time_str() + "grobid.json")
        with open(grobid_json_res, 'w+', encoding='utf8') as f:
            f.write(json.dumps(article_dict, indent=4, ensure_ascii=False))
        promote_file_to_downloadzone(grobid_json_res, chatbot=chatbot)

        if article_dict is None: raise RuntimeError("ParsePDF失敗しました，请检查PDF是否损坏。")
        yield from translate_pdf(article_dict, llm_kwargs, chatbot, fp, generated_conclusion_files, TOKEN_LIMIT_PER_FRAGMENT, DST_LANG)
    chatbot.append(("出力ファイルリストを提供する", str(generated_conclusion_files + generated_html_files)))
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する


def ParsePDF(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt):
    """
    此函数已经弃用
    """
    import copy
    TOKEN_LIMIT_PER_FRAGMENT = 1024
    generated_conclusion_files = []
    generated_html_files = []
    from crazy_functions.pdf_fns.report_gen_html import construct_html
    for index, fp in enumerate(file_manifest):
        # PDFファイルを読み込む
        file_content, page_one = read_and_clean_pdf_text(fp)
        file_content = file_content.encode('utf-8', 'ignore').decode()   # avoid reading non-utf8 chars
        page_one = str(page_one).encode('utf-8', 'ignore').decode()      # avoid reading non-utf8 chars

        # PDFファイルを再帰的に分割する
        from crazy_functions.pdf_fns.breakdown_txt import breakdown_text_to_satisfy_token_limit
        paper_fragments = breakdown_text_to_satisfy_token_limit(txt=file_content, limit=TOKEN_LIMIT_PER_FRAGMENT, llm_model=llm_kwargs['llm_model'])
        page_one_fragments = breakdown_text_to_satisfy_token_limit(txt=page_one, limit=TOKEN_LIMIT_PER_FRAGMENT//4, llm_model=llm_kwargs['llm_model'])

        # より良い効果を得るために，Introductionを削除した後の部分（ある場合）
        paper_meta = page_one_fragments[0].split('introduction')[0].split('Introduction')[0].split('INTRODUCTION')[0]

        # Single line，記事のメタ情報を取得する
        paper_meta_info = yield from request_gpt_model_in_new_thread_with_ui_alive(
            inputs=f"以下は学術論文の基本情報です，「タイトル」、「収録会議またはジャーナル」、「著者」、「要約」、「番号」、「著者の電子メール」の6つの部分を抽出してください。markdown形式で出力してください，Finally, translate the abstract section into Chinese。Please extract：{paper_meta}",
            inputs_show_user=f"からお願いします{fp}タイトル、収録会議またはジャーナルなどの基本情報を抽出する。",
            llm_kwargs=llm_kwargs,
            chatbot=chatbot, history=[],
            sys_prompt="Your job is to collect information from materials。",
        )

        # Multi-threaded，翻訳
        gpt_response_collection = yield from request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency(
            inputs_array=[
                f"以下の内容を翻訳する必要があります：\n{frag}" for frag in paper_fragments],
            inputs_show_user_array=[f"\n---\n 原文： \n\n {frag.replace('#', '')}  \n---\n翻訳：\n " for frag in paper_fragments],
            llm_kwargs=llm_kwargs,
            chatbot=chatbot,
            history_array=[[paper_meta] for _ in paper_fragments],
            sys_prompt_array=[
                "学術翻訳者としてお願いします，学術論文を正確に中国語に翻訳する責任があります。記事の各文は翻訳する必要があります。" for _ in paper_fragments],
            # max_workers=5  # OpenAIが許可する最大並列過負荷
        )
        gpt_response_collection_md = copy.deepcopy(gpt_response_collection)
        # レポートのフォーマットを整理する
        for i,k in enumerate(gpt_response_collection_md):
            if i%2==0:
                gpt_response_collection_md[i] = f"\n\n---\n\n ## 原文[{i//2}/{len(gpt_response_collection_md)//2}]： \n\n {paper_fragments[i//2].replace('#', '')}  \n\n---\n\n ## 翻訳[{i//2}/{len(gpt_response_collection_md)//2}]：\n "
            else:
                gpt_response_collection_md[i] = gpt_response_collection_md[i]
        final = ["1.論文概要\n\n---\n\n", paper_meta_info.replace('# ', '### ') + '\n\n---\n\n', "2.論文翻訳", ""]
        final.extend(gpt_response_collection_md)
        create_report_file_name = f"{os.path.basename(fp)}.trans.md"
        res = write_history_to_file(final, create_report_file_name)
        promote_file_to_downloadzone(res, chatbot=chatbot)

        # UIを更新する
        generated_conclusion_files.append(f'{get_log_folder()}/{create_report_file_name}')
        chatbot.append((f"{fp}完了しましたか？", res))
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する

        # write html
        try:
            ch = construct_html()
            orig = ""
            trans = ""
            gpt_response_collection_html = copy.deepcopy(gpt_response_collection)
            for i,k in enumerate(gpt_response_collection_html):
                if i%2==0:
                    gpt_response_collection_html[i] = paper_fragments[i//2].replace('#', '')
                else:
                    gpt_response_collection_html[i] = gpt_response_collection_html[i]
            final = ["論文の概要", paper_meta_info.replace('# ', '### '),  "2.論文翻訳",  ""]
            final.extend(gpt_response_collection_html)
            for i, k in enumerate(final):
                if i%2==0:
                    orig = k
                if i%2==1:
                    trans = k
                    ch.add_row(a=orig, b=trans)
            create_report_file_name = f"{os.path.basename(fp)}.trans.html"
            generated_html_files.append(ch.save_file(create_report_file_name))
        except:
            from toolbox import trimmed_format_exc
            print('writing html result failed:', trimmed_format_exc())

    # Preparing for file download
    for pdf_path in generated_conclusion_files:
        # ファイル名を変更する
        rename_file = f'翻訳-{os.path.basename(pdf_path)}'
        promote_file_to_downloadzone(pdf_path, rename_file=rename_file, chatbot=chatbot)
    for html_path in generated_html_files:
        # ファイル名を変更する
        rename_file = f'翻訳-{os.path.basename(html_path)}'
        promote_file_to_downloadzone(html_path, rename_file=rename_file, chatbot=chatbot)
    chatbot.append(("出力ファイルリストを提供する", str(generated_conclusion_files + generated_html_files)))
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する


