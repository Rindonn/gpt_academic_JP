from toolbox import update_ui
from toolbox import CatchException, report_exception
from .crazy_utils import request_gpt_model_in_new_thread_with_ui_alive
from toolbox import write_history_to_file, promote_file_to_downloadzone

fast_debug = False

def readPdf(pdfPath):
    """
    PDFファイルを読み込む，テキストコンテンツを返します
    """
    import pdfminer
    from pdfminer.pdfparser import PDFParser
    from pdfminer.pdfdocument import PDFDocument
    from pdfminer.pdfpage import PDFPage, PDFTextExtractionNotAllowed
    from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
    from pdfminer.pdfdevice import PDFDevice
    from pdfminer.layout import LAParams
    from pdfminer.converter import PDFPageAggregator

    fp = open(pdfPath, 'rb')

    # Create a PDF parser object associated with the file object
    parser = PDFParser(fp)

    # Create a PDF document object that stores the document structure.
    # Password for initialization as 2nd parameter
    document = PDFDocument(parser)
    # Check if the document allows text extraction. If not, abort.
    if not document.is_extractable:
        raise PDFTextExtractionNotAllowed

    # Create a PDF resource manager object that stores shared resources.
    rsrcmgr = PDFResourceManager()

    # Create a PDF device object.
    # device = PDFDevice(rsrcmgr)

    # BEGIN LAYOUT ANALYSIS.
    # Set parameters for analysis.
    laparams = LAParams(
        char_margin=10.0,
        line_margin=0.2,
        boxes_flow=0.2,
        all_texts=False,
    )
    # Create a PDF page aggregator object.
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    # Create a PDF interpreter object.
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    # loop over all pages in the document
    outTextList = []
    for page in PDFPage.create_pages(document):
        # read the page into a layout object
        interpreter.process_page(page)
        layout = device.get_result()
        for obj in layout._objs:
            if isinstance(obj, pdfminer.layout.LTTextBoxHorizontal):
                # print(obj.get_text())
                outTextList.append(obj.get_text())

    return outTextList


def ParsePaper(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt):
    import time, glob, os
    from bs4 import BeautifulSoup
    print('begin analysis on:', file_manifest)
    for index, fp in enumerate(file_manifest):
        if ".tex" in fp:
            with open(fp, 'r', encoding='utf-8', errors='replace') as f:
                file_content = f.read()
        if ".pdf" in fp.lower():
            file_content = readPdf(fp)
            file_content = BeautifulSoup(''.join(file_content), features="lxml").body.text.encode('gbk', 'ignore').decode('gbk')

        prefix = "次に、論文ファイルを1つずつ分析してください，内容を要約する" if index==0 else ""
        i_say = prefix + f'Please summarize the following article fragment in Chinese，ファイル名は{os.path.relpath(fp, project_folder)}，The content of the article is ```{file_content}```'
        i_say_show_user = prefix + f'[{index}/{len(file_manifest)}] Please summarize the following article fragment: {os.path.abspath(fp)}'
        chatbot.append((i_say_show_user, "[Local Message] waiting gpt response."))
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する

        if not fast_debug:
            msg = '正常'
            # ** gpt request **
            gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(
                inputs=i_say,
                inputs_show_user=i_say_show_user,
                llm_kwargs=llm_kwargs,
                chatbot=chatbot,
                history=[],
                sys_prompt="記事をまとめる。"
            )  # タイムアウトカウントダウン付き
            chatbot[-1] = (i_say_show_user, gpt_say)
            history.append(i_say_show_user); history.append(gpt_say)
            yield from update_ui(chatbot=chatbot, history=history, msg=msg) # 画面を更新する
            if not fast_debug: time.sleep(2)

    all_file = ', '.join([os.path.relpath(fp, project_folder) for index, fp in enumerate(file_manifest)])
    i_say = f'上記の分析に基づいて自分自身を分析する，全文を要約する，学術的な言葉で中国語の要約を書く，そして、もう一つの英文要約を書く（含む{all_file}）。'
    chatbot.append((i_say, "[Local Message] waiting gpt response."))
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する

    if not fast_debug:
        msg = '正常'
        # ** gpt request **
        gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(
            inputs=i_say,
            inputs_show_user=i_say,
            llm_kwargs=llm_kwargs,
            chatbot=chatbot,
            history=history,
            sys_prompt="記事をまとめる。"
        )  # タイムアウトカウントダウン付き
        chatbot[-1] = (i_say, gpt_say)
        history.append(i_say); history.append(gpt_say)
        yield from update_ui(chatbot=chatbot, history=history, msg=msg) # 画面を更新する
        res = write_history_to_file(history)
        promote_file_to_downloadzone(res, chatbot=chatbot)
        chatbot.append(("完了しましたか？", res))
        yield from update_ui(chatbot=chatbot, history=history, msg=msg) # 画面を更新する



@CatchException
def BatchSummarizePDFDocumentspdfminer(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    history = []    # 履歴をクリアする，オーバーフローを防ぐために
    import glob, os

    # 基本情報：機能、貢献者
    chatbot.append([
        "関数プラグイン機能？",
        "BatchSummarizePDFDocuments，このバージョンではpdfminerプラグインが使用するされています，トークン約束機能を備えた。関数プラグインの貢献者: Euclid-Jie。"])
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する

    # 依存関係のインポートを試みる，依存関係が不足している場合，インストールの提案を行います
    try:
        import pdfminer, bs4
    except:
        report_exception(chatbot, history,
            a = f"プロジェクトを解析する: {txt}",
            b = f"ソフトウェアの依存関係のインポートに失敗しました。このモジュールを使用するするには、追加の依存関係が必要です，インストールテキストの翻訳```pip install --upgrade pdfminer beautifulsoup4```。")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空の入力欄'
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f"ローカルプロジェクトが見つからないか、アクセス権がありません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.tex', recursive=True)] + \
                    [f for f in glob.glob(f'{project_folder}/**/*.pdf', recursive=True)] # + \
                    # [f for f in glob.glob(f'{project_folder}/**/*.cpp', recursive=True)] + \
                    # [f for f in glob.glob(f'{project_folder}/**/*.c', recursive=True)]
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f".texまたはpdfファイルが見つかりません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    yield from ParsePaper(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt)

