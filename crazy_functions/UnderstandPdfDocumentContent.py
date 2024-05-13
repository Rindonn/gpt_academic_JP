from toolbox import update_ui
from toolbox import CatchException, report_exception
from .crazy_utils import read_and_clean_pdf_text
from .crazy_utils import request_gpt_model_in_new_thread_with_ui_alive
fast_debug = False


def ParsePDF(file_name, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt):
    import tiktoken
    print('begin analysis on:', file_name)

    ############################## <ステップ0，PDFを切り分ける> ##################################
    # PDFファイルを再帰的に分割する，各ブロック（可能な限り完全なセクションであること，例えば、導入，実験など，必要に応じて再分割する）
    # 長さは2500トークン以下でなければなりません
    file_content, page_one = read_and_clean_pdf_text(file_name) # （Try）章ごとにPDFを切り分ける
    file_content = file_content.encode('utf-8', 'ignore').decode()   # avoid reading non-utf8 chars
    page_one = str(page_one).encode('utf-8', 'ignore').decode()  # avoid reading non-utf8 chars

    TOKEN_LIMIT_PER_FRAGMENT = 2500

    from crazy_functions.pdf_fns.breakdown_txt import breakdown_text_to_satisfy_token_limit
    paper_fragments = breakdown_text_to_satisfy_token_limit(txt=file_content, limit=TOKEN_LIMIT_PER_FRAGMENT, llm_model=llm_kwargs['llm_model'])
    page_one_fragments = breakdown_text_to_satisfy_token_limit(txt=str(page_one), limit=TOKEN_LIMIT_PER_FRAGMENT//4, llm_model=llm_kwargs['llm_model'])
    # より良い効果を得るために，Introductionを削除した後の部分（ある場合）
    paper_meta = page_one_fragments[0].split('introduction')[0].split('Introduction')[0].split('INTRODUCTION')[0]

    ############################## <ステップ1，Extract high-value information from the summary，履歴に保存する> ##################################
    final_results = []
    final_results.append(paper_meta)

    ############################## <ステップ2，記事全体を反復処理する，情報の抽出と精製> ##################################
    i_say_show_user = f'最初に、論文全体を英語で読みます。'; gpt_say = "[Local Message] 受信。"           # ユーザーヒント
    chatbot.append([i_say_show_user, gpt_say]); yield from update_ui(chatbot=chatbot, history=[])    # UIを更新する

    iteration_results = []
    last_iteration_result = paper_meta  # 初期値は要約です
    MAX_WORD_TOTAL = 4096
    n_fragment = len(paper_fragments)
    if n_fragment >= 20: print('記事が非常に長い，期待される効果が得られない')
    for i in range(n_fragment):
        NUM_OF_WORD = MAX_WORD_TOTAL // n_fragment
        i_say = f"Read this section, recapitulate the content of this section with less than {NUM_OF_WORD} words: {paper_fragments[i]}"
        i_say_show_user = f"[{i+1}/{n_fragment}] Read this section, recapitulate the content of this section with less than {NUM_OF_WORD} words: {paper_fragments[i][:200]} ...."
        gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(i_say, i_say_show_user,  # i_say=ChatGPTに本当の質問をする， ユーザーに表示される質問
                                                                           llm_kwargs, chatbot,
                                                                           history=["The main idea of the previous section is?", last_iteration_result], # 前回の結果を反復処理する
                                                                           sys_prompt="Extract the main idea of this section, answer me with japanese."  # ヒント
                                                                        )
        iteration_results.append(gpt_say)
        last_iteration_result = gpt_say

    ############################## <ステップ3，履歴の整理> ##################################
    final_results.extend(iteration_results)
    final_results.append(f'次に，あなたは専門の学術教授です，上記情報を利用する，日本語で私の質問に答えてください。')
    # 次の2つの文は、画面にのみ表示されます，Does not have any actual effect
    i_say_show_user = f'次に，あなたは専門の学術教授です，上記情報を利用する，日本語で私の質問に答えてください。'; gpt_say = "[Local Message] 受信。"
    chatbot.append([i_say_show_user, gpt_say])

    ############################## <4番目のステップ，トークンの上限を設定する，回答時のTokenオーバーフローを防止する> ##################################
    from .crazy_utils import input_clipping
    _, final_results = input_clipping("", final_results, max_token_limit=3200)
    yield from update_ui(chatbot=chatbot, history=final_results) # ここでの履歴は置き換えられました


@CatchException
def UnderstandPdfDocumentContentStandardFileInput(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    import glob, os

    # 基本情報：機能、貢献者
    chatbot.append([
        "関数プラグイン機能？",
        "Understand the content of the PDF paper，そして文脈内容を結合します，学術的な回答を行う。関数プラグインの貢献者: Hanzoe, binary-husky"])
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
        if txt == "":
            txt = '空の入力欄'
        report_exception(chatbot, history,
                         a=f"プロジェクトを解析する: {txt}", b=f"ローカルプロジェクトが見つからないか、アクセス権がありません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return

    # 処理する必要のあるファイルリストを検索する
    file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.pdf', recursive=True)]
    # ファイルが見つからなかった場合
    if len(file_manifest) == 0:
        report_exception(chatbot, history,
                         a=f"プロジェクトを解析する: {txt}", b=f".texまたは.pdfファイルが見つかりません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    txt = file_manifest[0]
    # タスクを正式に実行する
    yield from ParsePDF(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt)
