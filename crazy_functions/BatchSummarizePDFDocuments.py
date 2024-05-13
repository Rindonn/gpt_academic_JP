from toolbox import update_ui, promote_file_to_downloadzone, gen_time_str
from toolbox import CatchException, report_exception
from toolbox import write_history_to_file, promote_file_to_downloadzone
from .crazy_utils import request_gpt_model_in_new_thread_with_ui_alive
from .crazy_utils import read_and_clean_pdf_text
from .crazy_utils import input_clipping



def ParsePDF(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt):
    file_write_buffer = []
    for file_name in file_manifest:
        print('begin analysis on:', file_name)
        ############################## <ステップ0，PDFを切り分ける> ##################################
        # PDFファイルを再帰的に分割する，各ブロック（可能な限り完全なセクションであること，例えば、導入，実験など，必要に応じて再分割する）
        # 長さは2500トークン以下でなければなりません
        file_content, page_one = read_and_clean_pdf_text(file_name) # （Try）章ごとにPDFを切り分ける
        file_content = file_content.encode('utf-8', 'ignore').decode()   # avoid reading non-utf8 chars
        page_one = str(page_one).encode('utf-8', 'ignore').decode()  # avoid reading non-utf8 chars

        TOKEN_LIMIT_PER_FRAGMENT = 2500

        from crazy_functions.pdf_fns.breakdown_txt import breakdown_text_to_satisfy_token_limit
        paper_fragments = breakdown_text_to_satisfy_token_limit(txt=file_content,  limit=TOKEN_LIMIT_PER_FRAGMENT, llm_model=llm_kwargs['llm_model'])
        page_one_fragments = breakdown_text_to_satisfy_token_limit(txt=str(page_one), limit=TOKEN_LIMIT_PER_FRAGMENT//4, llm_model=llm_kwargs['llm_model'])
        # より良い効果を得るために，Introductionを削除した後の部分（ある場合）
        paper_meta = page_one_fragments[0].split('introduction')[0].split('Introduction')[0].split('INTRODUCTION')[0]

        ############################## <ステップ1，Extract high-value information from the summary，履歴に保存する> ##################################
        final_results = []
        final_results.append(paper_meta)

        ############################## <ステップ2，記事全体を反復処理する，情報の抽出と精製> ##################################
        i_say_show_user = f'まず、中国語の文脈で論文全体を読んでください。'; gpt_say = "[Local Message] 受信。"           # ユーザーヒント
        chatbot.append([i_say_show_user, gpt_say]); yield from update_ui(chatbot=chatbot, history=[])    # UIを更新する

        iteration_results = []
        last_iteration_result = paper_meta  # 初期値は要約です
        MAX_WORD_TOTAL = 4096 * 0.7
        n_fragment = len(paper_fragments)
        if n_fragment >= 20: print('記事が非常に長い，期待される効果が得られない')
        for i in range(n_fragment):
            NUM_OF_WORD = MAX_WORD_TOTAL // n_fragment
            i_say = f"Read this section, recapitulate the content of this section with less than {NUM_OF_WORD} Chinese characters: {paper_fragments[i]}"
            i_say_show_user = f"[{i+1}/{n_fragment}] Read this section, recapitulate the content of this section with less than {NUM_OF_WORD} Chinese characters: {paper_fragments[i][:200]}"
            gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(i_say, i_say_show_user,  # i_say=ChatGPTに本当の質問をする， ユーザーに表示される質問
                                                                                llm_kwargs, chatbot,
                                                                                history=["The main idea of the previous section is?", last_iteration_result], # 前回の結果を反復処理する
                                                                                sys_prompt="Extract the main idea of this section with Chinese."  # ヒント
                                                                                )
            iteration_results.append(gpt_say)
            last_iteration_result = gpt_say

        ############################## <ステップ3，履歴の整理，テキストの翻訳> ##################################
        final_results.extend(iteration_results)
        final_results.append(f'Please conclude this paper discussed above。')
        # This prompt is from https://github.com/kaixindelele/ChatPaper/blob/main/chat_paper.py
        NUM_OF_WORD = 1000
        i_say = """
1. Mark the title of the paper (with Chinese translation)
2. list all the authors' names (use English)
3. mark the first author's affiliation (output Chinese translation only)
4. mark the keywords of this article (use English)
5. link to the paper, Github code link (if available, fill in Github:None if not)
6. summarize according to the following four points.Be sure to use Chinese answers (proper nouns need to be marked in English)
    - (1):What is the research background of this article?
    - (2):What are the past methods? What are the problems with them? Is the approach well motivated?
    - (3):What is the research methodology proposed in this paper?
    - (4):On what task and what performance is achieved by the methods in this paper? Can the performance support their goals?
Follow the format of the output that follows:
1. Title: xxx\n\n
2. Authors: xxx\n\n
3. Affiliation: xxx\n\n
4. Keywords: xxx\n\n
5. Urls: xxx or xxx , xxx \n\n
6. Summary: \n\n
    - (1):xxx;\n
    - (2):xxx;\n
    - (3):xxx;\n
    - (4):xxx.\n\n
Be sure to use Chinese answers (proper nouns need to be marked in English), statements as concise and academic as possible,
do not have too much repetitive information, numerical values using the original numbers.
        """
        # This prompt is from https://github.com/kaixindelele/ChatPaper/blob/main/chat_paper.py
        file_write_buffer.extend(final_results)
        i_say, final_results = input_clipping(i_say, final_results, max_token_limit=2000)
        gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(
            inputs=i_say, inputs_show_user='開始最終的に总结',
            llm_kwargs=llm_kwargs, chatbot=chatbot, history=final_results,
            sys_prompt= f"Extract the main idea of this paper with less than {NUM_OF_WORD} Chinese characters"
        )
        final_results.append(gpt_say)
        file_write_buffer.extend([i_say, gpt_say])
        ############################## <4番目のステップ，トークンの上限を設定する> ##################################
        _, final_results = input_clipping("", final_results, max_token_limit=3200)
        yield from update_ui(chatbot=chatbot, history=final_results) # ここでの履歴は置き換えられました

    res = write_history_to_file(file_write_buffer)
    promote_file_to_downloadzone(res, chatbot=chatbot)
    yield from update_ui(chatbot=chatbot, history=final_results) # 画面を更新する


@CatchException
def BatchSummarizePDFDocuments(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    import glob, os

    # 基本情報：機能、貢献者
    chatbot.append([
        "関数プラグイン機能？",
        "BatchSummarizePDFDocuments。関数プラグインの貢献者: ValeriaWong，Eralien"])
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する

    # 依存関係のインポートを試みる，依存関係が不足している場合，インストールの提案を行います
    try:
        import fitz
    except:
        report_exception(chatbot, history,
            a = f"プロジェクトを解析する: {txt}",
            b = f"ソフトウェアの依存関係のインポートに失敗しました。このモジュールを使用するするには、追加の依存関係が必要です，インストールテキストの翻訳```pip install --upgrade pymupdf```。")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return

    # 履歴をクリアする，オーバーフローを防ぐために
    history = []

    # 入力パラメータを検出する，入力パラメータが指定されていない場合，直接終了する
    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空の入力欄'
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f"ローカルプロジェクトが見つからないか、アクセス権がありません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return

    # 処理する必要のあるファイルリストを検索する
    file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.pdf', recursive=True)]

    # ファイルが見つからなかった場合
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f".texまたは.pdfファイルが見つかりません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return

    # タスクを正式に実行する
    yield from ParsePDF(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt)
