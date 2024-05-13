from crazy_functions.crazy_utils import read_and_clean_pdf_text, get_files_from_everything
import os
import re
def extract_text_from_files(txt, chatbot, history):
    """
    查找pdf/md/word并获取文本内容并戻るステータス以及文本

    入力パラメータArgs:
        chatbot: chatbot inputs and outputs （ユーザーインターフェースの対話ウィンドウハンドル，データフローの可視化に使用するされる）
        history (list): List of chat history （History，会話履歴リスト）

    Returnsを出力する:
        文件是否存在(bool)
        final_result(list):文本内容
        page_one(list):第一页内容/摘要
        file_manifest(list):文件路径
        excption(string):需要用户手动处理的信息,如没出错则保持为空
    """

    final_result = []
    page_one = []
    file_manifest = []
    excption = ""

    if txt == "":
        final_result.append(txt)
        return False, final_result, page_one, file_manifest, excption   #如入力エリア内容不是文件则直接戻る入力エリア内容

    #查找入力エリア内容中のファイル
    file_pdf,pdf_manifest,folder_pdf = get_files_from_everything(txt, '.pdf')
    file_md,md_manifest,folder_md = get_files_from_everything(txt, '.md')
    file_word,word_manifest,folder_word = get_files_from_everything(txt, '.docx')
    file_doc,doc_manifest,folder_doc = get_files_from_everything(txt, '.doc')

    if file_doc:
        excption = "word"
        return False, final_result, page_one, file_manifest, excption

    file_num = len(pdf_manifest) + len(md_manifest) + len(word_manifest)
    if file_num == 0:
        final_result.append(txt)
        return False, final_result, page_one, file_manifest, excption   #如入力エリア内容不是文件则直接戻る入力エリア内容

    if file_pdf:
        try:    # 依存関係のインポートを試みる，依存関係が不足している場合，インストールの提案を行います
            import fitz
        except:
            excption = "pdf"
            return False, final_result, page_one, file_manifest, excption
        for index, fp in enumerate(pdf_manifest):
            file_content, pdf_one = read_and_clean_pdf_text(fp) # （Try）章ごとにPDFを切り分ける
            file_content = file_content.encode('utf-8', 'ignore').decode()   # avoid reading non-utf8 chars
            pdf_one = str(pdf_one).encode('utf-8', 'ignore').decode()  # avoid reading non-utf8 chars
            final_result.append(file_content)
            page_one.append(pdf_one)
            file_manifest.append(os.path.relpath(fp, folder_pdf))

    if file_md:
        for index, fp in enumerate(md_manifest):
            with open(fp, 'r', encoding='utf-8', errors='replace') as f:
                file_content = f.read()
            file_content = file_content.encode('utf-8', 'ignore').decode()
            headers = re.findall(r'^#\s(.*)$', file_content, re.MULTILINE)  #次に提取md中的一级/二级标题作为摘要
            if len(headers) > 0:
                page_one.append("\n".join(headers)) #合并所有的标题,以换行符分割
            else:
                page_one.append("")
            final_result.append(file_content)
            file_manifest.append(os.path.relpath(fp, folder_md))

    if file_word:
        try:    # 依存関係のインポートを試みる，依存関係が不足している場合，インストールの提案を行います
            from docx import Document
        except:
            excption = "word_pip"
            return False, final_result, page_one, file_manifest, excption
        for index, fp in enumerate(word_manifest):
            doc = Document(fp)
            file_content = '\n'.join([p.text for p in doc.paragraphs])
            file_content = file_content.encode('utf-8', 'ignore').decode()
            page_one.append(file_content[:200])
            final_result.append(file_content)
            file_manifest.append(os.path.relpath(fp, folder_word))

    return True, final_result, page_one, file_manifest, excption