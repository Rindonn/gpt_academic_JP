from toolbox import update_ui, promote_file_to_downloadzone
from toolbox import CatchException, report_exception, write_history_to_file
fast_debug = False

class PaperFileGroup():
    def __init__(self):
        self.file_paths = []
        self.file_contents = []
        self.sp_file_contents = []
        self.sp_file_index = []
        self.sp_file_tag = []

        # count_token
        from request_llms.bridge_all import model_info
        enc = model_info["gpt-3.5-turbo"]['tokenizer']
        def get_token_num(txt): return len(enc.encode(txt, disallowed_special=()))
        self.get_token_num = get_token_num

    def run_file_split(self, max_token_limit=1900):
        """
        長いテキストを分離する
        """
        for index, file_content in enumerate(self.file_contents):
            if self.get_token_num(file_content) < max_token_limit:
                self.sp_file_contents.append(file_content)
                self.sp_file_index.append(index)
                self.sp_file_tag.append(self.file_paths[index])
            else:
                from crazy_functions.pdf_fns.breakdown_txt import breakdown_text_to_satisfy_token_limit
                segments = breakdown_text_to_satisfy_token_limit(file_content, max_token_limit)
                for j, segment in enumerate(segments):
                    self.sp_file_contents.append(segment)
                    self.sp_file_index.append(index)
                    self.sp_file_tag.append(self.file_paths[index] + f".part-{j}.tex")

        print('Segmentation: done')

def TranslateMultipleFiles(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, language='en'):
    import time, os, re
    from .crazy_utils import request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency

    #  <-------- Latexファイルを読み込む，すべてのコメントを削除する ---------->
    pfg = PaperFileGroup()

    for index, fp in enumerate(file_manifest):
        with open(fp, 'r', encoding='utf-8', errors='replace') as f:
            file_content = f.read()
            # コメントの正規表現を定義する
            comment_pattern = r'(?<!\\)%.*'
            # Use regular expressions to find comments，空の文字列に置き換える
            clean_tex_content = re.sub(comment_pattern, '', file_content)
            # コメントを削除したテキストを記録する
            pfg.file_paths.append(fp)
            pfg.file_contents.append(clean_tex_content)

    #  <-------- Split overly long latex files ---------->
    pfg.run_file_split(max_token_limit=1024)
    n_split = len(pfg.sp_file_contents)

    #  <-------- 要約を抽出する ---------->
    # if language == 'en':
    #     abs_extract_inputs = f"Please write an abstract for this paper"

    # # Single line，記事のメタ情報を取得する
    # paper_meta_info = yield from request_gpt_model_in_new_thread_with_ui_alive(
    #     inputs=abs_extract_inputs,
    #     inputs_show_user=f"正在要約を抽出する信息。",
    #     llm_kwargs=llm_kwargs,
    #     chatbot=chatbot, history=[],
    #     sys_prompt="Your job is to collect information from materials。",
    # )

    #  <-------- マルチスレッドの改善が開始されました ---------->
    if language == 'en->zh':
        inputs_array = ["Below is a section from an English academic paper, translate it into japanese, do not modify any latex command such as \section, \cite and equations:" +
                        f"\n\n{frag}" for frag in pfg.sp_file_contents]
        inputs_show_user_array = [f"翻訳 {f}" for f in pfg.sp_file_tag]
        sys_prompt_array = ["You are a professional academic paper translator." for _ in range(n_split)]
    elif language == 'zh->en':
        inputs_array = [f"Below is a section from a Chinese academic paper, translate it into English, do not modify any latex command such as \section, \cite and equations:" +
                        f"\n\n{frag}" for frag in pfg.sp_file_contents]
        inputs_show_user_array = [f"翻訳 {f}" for f in pfg.sp_file_tag]
        sys_prompt_array = ["You are a professional academic paper translator." for _ in range(n_split)]

    gpt_response_collection = yield from request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency(
        inputs_array=inputs_array,
        inputs_show_user_array=inputs_show_user_array,
        llm_kwargs=llm_kwargs,
        chatbot=chatbot,
        history_array=[[""] for _ in range(n_split)],
        sys_prompt_array=sys_prompt_array,
        # max_workers=5,  # OpenAIが許可する最大並列過負荷
        scroller_max_len = 80
    )

    #  <-------- Organized results，終了 ---------->
    create_report_file_name = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()) + f"-chatgpt.polish.md"
    res = write_history_to_file(gpt_response_collection, create_report_file_name)
    promote_file_to_downloadzone(res, chatbot=chatbot)
    history = gpt_response_collection
    chatbot.append((f"{fp}完了したか？", res))
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する





@CatchException
def LatexEnglishToChinese(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    # 基本情報：機能、貢献者
    chatbot.append([
        "関数プラグイン機能？",
        "Translate the entire Latex project。関数プラグインの貢献者: Binary-Husky"])
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する

    # 依存関係のインポートを試みる，依存関係が不足している場合，インストールの提案を行います
    try:
        import tiktoken
    except:
        report_exception(chatbot, history,
                         a=f"プロジェクトを解析する: {txt}",
                         b=f"ソフトウェアの依存関係のインポートに失敗しました。このモジュールを使用するするには、追加の依存関係が必要です，インストールテキストの翻訳```pip install --upgrade tiktoken```。")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    history = []    # 履歴をクリアする，オーバーフローを防ぐために
    import glob, os
    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空の入力欄'
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f"ローカルプロジェクトが見つからないか、アクセス権がありません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.tex', recursive=True)]
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f"テキストの翻訳: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    yield from TranslateMultipleFiles(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, language='en->zh')





@CatchException
def LatexChineseToEnglish(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    # 基本情報：機能、貢献者
    chatbot.append([
        "関数プラグイン機能？",
        "Translate the entire Latex project。関数プラグインの貢献者: Binary-Husky"])
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する

    # 依存関係のインポートを試みる，依存関係が不足している場合，インストールの提案を行います
    try:
        import tiktoken
    except:
        report_exception(chatbot, history,
                         a=f"プロジェクトを解析する: {txt}",
                         b=f"ソフトウェアの依存関係のインポートに失敗しました。このモジュールを使用するするには、追加の依存関係が必要です，インストールテキストの翻訳```pip install --upgrade tiktoken```。")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    history = []    # 履歴をクリアする，オーバーフローを防ぐために
    import glob, os
    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空の入力欄'
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f"ローカルプロジェクトが見つからないか、アクセス権がありません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.tex', recursive=True)]
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a = f"プロジェクトを解析する: {txt}", b = f"テキストの翻訳: {txt}")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return
    yield from TranslateMultipleFiles(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, language='zh->en')