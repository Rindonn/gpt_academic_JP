#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@ Author: Rindon
@ Date: 2024-05-13 09:42:46
@ LastEditors: Rindon
@ LastEditTime: 2024-05-21 10:07:41
@ Description: prompt、インターフェースを日本語に変更
'''
from toolbox import update_ui, trimmed_format_exc, get_conf, get_log_folder, promote_file_to_downloadzone, check_repeat_upload, map_file_to_sha256
from toolbox import CatchException, report_exception, update_ui_lastest_msg, zip_result, gen_time_str
from functools import partial
import glob, os, requests, time, json, tarfile

pj = os.path.join
ARXIV_CACHE_DIR = os.path.expanduser(f"~/arxiv_cache/")


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- 工具函数 =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# ProfessionalTerminologyDeclaration  = 'If the term "agent" is used in this section, it should be translated to "智能体". '
def switch_prompt(pfg, mode, more_requirement):
    """
    Generate prompts and system prompts based on the mode for proofreading or translating.
    Args:
    - pfg: Proofreader or Translator instance.
    - mode: A string specifying the mode, either 'proofread' or 'translate_jp'.

    Returns:
    - inputs_array: A list of strings containing prompts for users to respond to.
    - sys_prompt_array: A list of strings containing prompts for system prompts.
    """
    n_split = len(pfg.sp_file_contents)
    if mode == 'proofread_en':
        inputs_array = [r"Below is a section from an academic paper, proofread this section." +
                        r"Do not modify any latex command such as \section, \cite, \begin, \item and equations. " + more_requirement +
                        r"Answer me only with the revised text:" +
                        f"\n\n{frag}" for frag in pfg.sp_file_contents]
        sys_prompt_array = ["You are a professional academic paper writer." for _ in range(n_split)]
    elif mode == 'translate_zh':
        inputs_array = [
            r"Below is a section from an English academic paper, translate it into Japanese. " + more_requirement +
            r"Do not modify any latex command such as \section, \cite, \begin, \item and equations. " +
            r"Answer me only with the translated text:" +
            f"\n\n{frag}" for frag in pfg.sp_file_contents]
        sys_prompt_array = ["You are a professional translator." for _ in range(n_split)]
    else:
        assert False, "不明なコマンド"
    return inputs_array, sys_prompt_array


def desend_to_extracted_folder_if_exist(project_folder):
    """
    Descend into the extracted folder if it exists, otherwise return the original folder.

    Args:
    - project_folder: A string specifying the folder path.

    Returns:
    - A string specifying the path to the extracted folder, or the original folder if there is no extracted folder.
    """
    maybe_dir = [f for f in glob.glob(f'{project_folder}/*') if os.path.isdir(f)]
    if len(maybe_dir) == 0: return project_folder
    if maybe_dir[0].endswith('.extract'): return maybe_dir[0]
    return project_folder


def move_project(project_folder, arxiv_id=None):
    """
    Create a new work folder and copy the project folder to it.

    Args:
    - project_folder: A string specifying the folder path of the project.

    Returns:
    - A string specifying the path to the new work folder.
    """
    import shutil, time
    time.sleep(2)  # avoid time string conflict
    if arxiv_id is not None:
        new_workfolder = pj(ARXIV_CACHE_DIR, arxiv_id, 'workfolder')
    else:
        new_workfolder = f'{get_log_folder()}/{gen_time_str()}'
    try:
        shutil.rmtree(new_workfolder)
    except:
        pass

    # align subfolder if there is a folder wrapper
    items = glob.glob(pj(project_folder, '*'))
    items = [item for item in items if os.path.basename(item) != '__MACOSX']
    if len(glob.glob(pj(project_folder, '*.tex'))) == 0 and len(items) == 1:
        if os.path.isdir(items[0]): project_folder = items[0]

    shutil.copytree(src=project_folder, dst=new_workfolder)
    return new_workfolder


def arxiv_download(chatbot, history, txt, allow_cache=True):
    def check_cached_translation_pdf(arxiv_id):
        translation_dir = pj(ARXIV_CACHE_DIR, arxiv_id, 'translation')
        if not os.path.exists(translation_dir):
            os.makedirs(translation_dir)
        target_file = pj(translation_dir, 'translate_jp.pdf')
        if os.path.exists(target_file):
            promote_file_to_downloadzone(target_file, rename_file=None, chatbot=chatbot)
            target_file_compare = pj(translation_dir, 'comparison.pdf')
            if os.path.exists(target_file_compare):
                promote_file_to_downloadzone(target_file_compare, rename_file=None, chatbot=chatbot)
            return target_file
        return False

    def is_float(s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    if ('.' in txt) and ('/' not in txt) and is_float(txt):  # is arxiv ID
        txt = 'https://arxiv.org/abs/' + txt.strip()
    if ('.' in txt) and ('/' not in txt) and is_float(txt[:10]):  # is arxiv ID
        txt = 'https://arxiv.org/abs/' + txt[:10]

    if not txt.startswith('https://arxiv.org'):
        return txt, None    # 是本地文件，跳过下载

    # <-------------- inspect format ------------->
    chatbot.append([f"axrivドキュメントを検出された", 'ダウンロードをしてみます ...'])
    yield from update_ui(chatbot=chatbot, history=history)
    time.sleep(1)  # 画面を更新する

    url_ = txt  # https://arxiv.org/abs/1707.06690
    if not txt.startswith('https://arxiv.org/abs/'):
        msg = f"arxivのURLの解析に失敗しました, 形式の例: https://arxiv.org/abs/1707.06690。実際にアクセスしたフォーマット: {url_}。"
        yield from update_ui_lastest_msg(msg, chatbot=chatbot, history=history)  # 画面を更新する
        return msg, None
    # <-------------- set format ------------->
    arxiv_id = url_.split('/abs/')[-1]
    if 'v' in arxiv_id: arxiv_id = arxiv_id[:10]
    cached_translation_pdf = check_cached_translation_pdf(arxiv_id)
    if cached_translation_pdf and allow_cache: return cached_translation_pdf, arxiv_id

    url_tar = url_.replace('/abs/', '/e-print/')
    translation_dir = pj(ARXIV_CACHE_DIR, arxiv_id, 'e-print')
    extract_dst = pj(ARXIV_CACHE_DIR, arxiv_id, 'extract')
    os.makedirs(translation_dir, exist_ok=True)

    # <-------------- download arxiv source file ------------->
    dst = pj(translation_dir, arxiv_id + '.tar')
    if os.path.exists(dst):
        yield from update_ui_lastest_msg("キャッシュを利用している", chatbot=chatbot, history=history)  # 画面を更新する
    else:
        yield from update_ui_lastest_msg("ダウンロード開始", chatbot=chatbot, history=history)  # 画面を更新する
        proxies = get_conf('proxies')
        r = requests.get(url_tar, proxies=proxies)
        with open(dst, 'wb+') as f:
            f.write(r.content)
    # <-------------- extract file ------------->
    yield from update_ui_lastest_msg("ダウンロードが完了した", chatbot=chatbot, history=history)  # 画面を更新する
    from toolbox import extract_archive
    extract_archive(file_path=dst, dest_dir=extract_dst)
    return extract_dst, arxiv_id


def pdf2tex_project(pdf_file_path):
    # Mathpix API credentials
    app_id, app_key = get_conf('MATHPIX_APPID', 'MATHPIX_APPKEY')
    headers = {"app_id": app_id, "app_key": app_key}

    # Step 1: Send PDF file for processing
    options = {
        "conversion_formats": {"tex.zip": True},
        "math_inline_delimiters": ["$", "$"],
        "rm_spaces": True
    }

    response = requests.post(url="https://api.mathpix.com/v3/pdf",
                             headers=headers,
                             data={"options_json": json.dumps(options)},
                             files={"file": open(pdf_file_path, "rb")})

    if response.ok:
        pdf_id = response.json()["pdf_id"]
        print(f"PDF processing initiated. PDF ID: {pdf_id}")

        # Step 2: Check processing status
        while True:
            conversion_response = requests.get(f"https://api.mathpix.com/v3/pdf/{pdf_id}", headers=headers)
            conversion_data = conversion_response.json()

            if conversion_data["status"] == "completed":
                print("PDF processing completed.")
                break
            elif conversion_data["status"] == "error":
                print("Error occurred during processing.")
            else:
                print(f"Processing status: {conversion_data['status']}")
                time.sleep(5)  # wait for a few seconds before checking again

        # Step 3: Save results to local files
        output_dir = os.path.join(os.path.dirname(pdf_file_path), 'mathpix_output')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        url = f"https://api.mathpix.com/v3/pdf/{pdf_id}.tex"
        response = requests.get(url, headers=headers)
        file_name_wo_dot = '_'.join(os.path.basename(pdf_file_path).split('.')[:-1])
        output_name = f"{file_name_wo_dot}.tex.zip"
        output_path = os.path.join(output_dir, output_name)
        with open(output_path, "wb") as output_file:
            output_file.write(response.content)
        print(f"tex.zip file saved at: {output_path}")

        import zipfile
        unzip_dir = os.path.join(output_dir, file_name_wo_dot)
        with zipfile.ZipFile(output_path, 'r') as zip_ref:
            zip_ref.extractall(unzip_dir)

        return unzip_dir

    else:
        print(f"Error sending PDF for processing. Status code: {response.status_code}")
        return None


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= プラグイン主程序1 =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=


@CatchException
def CorrectEnglishInLatexWithPDFComparison(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    # <-------------- information about this plugin ------------->
    chatbot.append(["関数プラグイン機能？",
                    "Latexプロジェクトを修正する, LaTeXでコンパイルしてPDFに修正をハイライトする。関数プラグインの貢献者: Binary-Husky。現在、GPT3.5/GPT4のみをサポートしています，他のモデルの変換効果は不明です。現在、機械学習の文献変換効果が最も良いです，他のタイプの文献の変換効果は不明です。Windowsシステムでのみテストされています，他のオペレーティングシステムの動作は不明です。"])
    yield from update_ui(chatbot=chatbot, history=history)  # 画面を更新する

    # <-------------- more requirements ------------->
    if ("advanced_arg" in plugin_kwargs) and (plugin_kwargs["advanced_arg"] == ""): plugin_kwargs.pop("advanced_arg")
    more_req = plugin_kwargs.get("advanced_arg", "")
    _switch_prompt_ = partial(switch_prompt, more_requirement=more_req)

    # <-------------- check deps ------------->
    try:
        import glob, os, time, subprocess
        subprocess.Popen(['pdflatex', '-version'])
        from .latex_fns.latex_actions import DecomposeAndConvertLatex, CompileLatex
    except Exception as e:
        chatbot.append([f"プロジェクトを解析する: {txt}",
                        f"LaTeXがインストールされていません, または環境変数PATHに記録していません。インストールには：https://tug.org/texlive/。エラーメッセージ\n\n```\n\n{trimmed_format_exc()}\n\n```\n\n"])
        yield from update_ui(chatbot=chatbot, history=history)  # 画面を更新する
        return

    # <-------------- clear history and read input ------------->
    history = []
    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空の入力欄'
        report_exception(chatbot, history, a=f"プロジェクトを解析する: {txt}", b=f"ローカルプロジェクトが見つからないか、アクセス権がありません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history)  # 画面を更新する
        return
    file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.tex', recursive=True)]
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a=f"プロジェクトを解析する: {txt}", b=f".texファイルが見つかりません： {txt}")
        yield from update_ui(chatbot=chatbot, history=history)  # 画面を更新する
        return

    # <-------------- if is a zip/tar file ------------->
    project_folder = desend_to_extracted_folder_if_exist(project_folder)

    # <-------------- move latex project away from temp folder ------------->
    project_folder = move_project(project_folder, arxiv_id=None)

    # <-------------- if merge_translate_zh is already generated, skip gpt req ------------->
    if not os.path.exists(project_folder + '/merge_proofread_en.tex'):
        yield from DecomposeAndConvertLatex(file_manifest, project_folder, llm_kwargs, plugin_kwargs,
                                       chatbot, history, system_prompt, mode='proofread_en',
                                       switch_prompt=_switch_prompt_)

    # <-------------- compile PDF ------------->
    success = yield from CompileLatex(chatbot, history, main_file_original='merge',
                                   main_file_modified='merge_proofread_en',
                                   work_folder_original=project_folder, work_folder_modified=project_folder,
                                   work_folder=project_folder)

    # <-------------- zip PDF ------------->
    zip_res = zip_result(project_folder)
    if success:
        chatbot.append((f"成功した", '結果を確認してください...'))
        yield from update_ui(chatbot=chatbot, history=history);
        time.sleep(1)  # 画面を更新する
        promote_file_to_downloadzone(file=zip_res, chatbot=chatbot)
    else:
        chatbot.append((f"失敗した",
                        'PDFの生成に失敗しました, 結果を確認してください, 翻訳済みのTexドキュメントが含まれています, 読み取りが可能です, GithubのIssueエリアに報告して下さい, ConversationHistoryArchiveを使用するしています ...'))
        yield from update_ui(chatbot=chatbot, history=history);
        time.sleep(1)  # 画面を更新する
        promote_file_to_downloadzone(file=zip_res, chatbot=chatbot)

    # <-------------- we are done ------------->
    return success


# =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-= プラグイン主程序2 =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

@CatchException
def TranslateChineseToEnglishInLatexAndRecompilePDF(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    # <-------------- information about this plugin ------------->
    chatbot.append([
        "関数プラグイン機能？",
        "Translate the entire Latex project, 日本語のPDFを生成する。関数プラグインの貢献者: Binary-Husky。このプラグインはWindowsに最適です，LinuxではDockerをインストール必要があります，詳細はプロジェクトのメインREADME.mdを参照してください。現在、GPT3.5/GPT4のみサポートしています，他のモデルの変換効果は不明です。現在、機械学習の文献変換効果が最も良いです，他のタイプの文献の変換効果は不明です。"])
    yield from update_ui(chatbot=chatbot, history=history)  # 画面を更新する

    # <-------------- more requirements ------------->
    if ("advanced_arg" in plugin_kwargs) and (plugin_kwargs["advanced_arg"] == ""): plugin_kwargs.pop("advanced_arg")
    more_req = plugin_kwargs.get("advanced_arg", "")
    no_cache = more_req.startswith("--no-cache")
    if no_cache: more_req.lstrip("--no-cache")
    allow_cache = not no_cache
    _switch_prompt_ = partial(switch_prompt, more_requirement=more_req)

    # <-------------- check deps ------------->
    try:
        import glob, os, time, subprocess
        subprocess.Popen(['pdflatex', '-version'])
        from .latex_fns.latex_actions import DecomposeAndConvertLatex, CompileLatex
    except Exception as e:
        chatbot.append([f"プロジェクトを解析する: {txt}",
                        f"LaTeXがインストールされていません,または環境変数PATHに記録していません。インストールには：https://tug.org/texlive/。エラーメッセージ\n\n```\n\n{trimmed_format_exc()}\n\n```\n\n"])
        yield from update_ui(chatbot=chatbot, history=history)  # 画面を更新する
        return

    # <-------------- clear history and read input ------------->
    history = []
    try:
        txt, arxiv_id = yield from arxiv_download(chatbot, history, txt, allow_cache)
    except tarfile.ReadError as e:
        yield from update_ui_lastest_msg(
            "Latexダウンロード出来ません，arxivへアクセスして、論文ダウンロードページを開いて，other Formatsをクリックして，download sourceクリックしてlatexをダウンロードして下さい。ローカルLatex翻訳プラグインを利用して下さい。",
            chatbot=chatbot, history=history)
        return

    if txt.endswith('.pdf'):
        report_exception(chatbot, history, a=f"プロジェクトを解析する: {txt}", b=f"翻訳済みのPDFドキュメントが既に存在している")
        yield from update_ui(chatbot=chatbot, history=history)  # 画面を更新する
        return

    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空の入力欄'
        report_exception(chatbot, history, a=f"プロジェクトを解析する: {txt}", b=f"見つかりません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history)  # 画面を更新する
        return

    file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.tex', recursive=True)]
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a=f"プロジェクトを解析する: {txt}", b=f".texファイルが見つかりません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history)  # 画面を更新する
        return

    # <-------------- if is a zip/tar file ------------->
    project_folder = desend_to_extracted_folder_if_exist(project_folder)

    # <-------------- move latex project away from temp folder ------------->
    project_folder = move_project(project_folder, arxiv_id)

    # <-------------- if merge_translate_zh is already generated, skip gpt req ------------->
    if not os.path.exists(project_folder + '/merge_translate_zh.tex'):
        yield from DecomposeAndConvertLatex(file_manifest, project_folder, llm_kwargs, plugin_kwargs,
                                       chatbot, history, system_prompt, mode='translate_zh',
                                       switch_prompt=_switch_prompt_)

    # <-------------- compile PDF ------------->
    success = yield from CompileLatex(chatbot, history, main_file_original='merge',
                                   main_file_modified='merge_translate_zh', mode='translate_zh',
                                   work_folder_original=project_folder, work_folder_modified=project_folder,
                                   work_folder=project_folder)

    # <-------------- zip PDF ------------->
    zip_res = zip_result(project_folder)
    if success:
        chatbot.append((f"成功した", '結果を確認してください...'))
        yield from update_ui(chatbot=chatbot, history=history);
        time.sleep(1)  # 画面を更新する
        promote_file_to_downloadzone(file=zip_res, chatbot=chatbot)
    else:
        chatbot.append((f"失敗した",
                        'PDFの生成に失敗しました, 結果を確認してください, 翻訳済みのTexドキュメントが含まれています, GithubのIssueエリアにアクセスし、報告して下さい...'))
        yield from update_ui(chatbot=chatbot, history=history);
        time.sleep(1)  # 画面を更新する
        promote_file_to_downloadzone(file=zip_res, chatbot=chatbot)

    # <-------------- we are done ------------->
    return success


#  =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- プラグイン主程序3  =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

@CatchException
def TranslatePDFToChineseAndRecompilePDF(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, web_port):
    # <-------------- information about this plugin ------------->
    chatbot.append([
        "関数プラグイン機能？",
        "PDFをLatexに変更し，日本語に翻訳した後PDFを作ります。関数プラグインの貢献者: Marroh。このプラグインはWindowsに最適です。現在、GPT3.5/GPT4のみをサポートしています，他のモデルの変換効果は不明です。現在、機械学習の文献変換効果が最も良いです，他のタイプの文献の変換効果は不明です。"])
    yield from update_ui(chatbot=chatbot, history=history)  # 画面を更新する

    # <-------------- more requirements ------------->
    if ("advanced_arg" in plugin_kwargs) and (plugin_kwargs["advanced_arg"] == ""): plugin_kwargs.pop("advanced_arg")
    more_req = plugin_kwargs.get("advanced_arg", "")
    no_cache = more_req.startswith("--no-cache")
    if no_cache: more_req.lstrip("--no-cache")
    allow_cache = not no_cache
    _switch_prompt_ = partial(switch_prompt, more_requirement=more_req)

    # <-------------- check deps ------------->
    try:
        import glob, os, time, subprocess
        subprocess.Popen(['pdflatex', '-version'])
        from .latex_fns.latex_actions import DecomposeAndConvertLatex, CompileLatex
    except Exception as e:
        chatbot.append([f"プロジェクトを解析する: {txt}",
                        f"LaTeXがインストールされていません, または環境変数PATHに存在しません。インストールには：https://tug.org/texlive/。エラーメッセージ\n\n```\n\n{trimmed_format_exc()}\n\n```\n\n"])
        yield from update_ui(chatbot=chatbot, history=history)  # 画面を更新する
        return

    # <-------------- clear history and read input ------------->
    if os.path.exists(txt):
        project_folder = txt
    else:
        if txt == "": txt = '空の入力欄'
        report_exception(chatbot, history, a=f"プロジェクトを解析する: {txt}", b=f"見つかりません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history)  # 画面を更新する
        return

    file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.pdf', recursive=True)]
    if len(file_manifest) == 0:
        report_exception(chatbot, history, a=f"プロジェクトを解析する: {txt}", b=f"PDFファイルが見つかりません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history)  # 画面を更新する
        return
    if len(file_manifest) != 1:
        report_exception(chatbot, history, a=f"プロジェクトを解析する: {txt}", b=f"同時に複数ファイルの処理が出来ません: {txt}")
        yield from update_ui(chatbot=chatbot, history=history)  # 画面を更新する
        return
    app_id, app_key = get_conf('MATHPIX_APPID', 'MATHPIX_APPKEY')
    if len(app_id) == 0 or len(app_key) == 0:
        report_exception(chatbot, history, a=" MATHPIX_APPID and MATHPIX_APPKEYなし。", b=f"MATHPIX_APPID and MATHPIX_APPKEYを設定して下さい")
        yield from update_ui(chatbot=chatbot, history=history)  # 画面を更新する
        return

    hash_tag = map_file_to_sha256(file_manifest[0])

    # <-------------- check repeated pdf ------------->
    chatbot.append([f"PDFあるかどうかをチェックしています", "チェックしています..."])
    yield from update_ui(chatbot=chatbot, history=history)
    repeat, project_folder = check_repeat_upload(file_manifest[0], hash_tag)

    except_flag = False

    if repeat:
        yield from update_ui_lastest_msg(f"ローカルでファイルが見つかりました，結果を確認してください...", chatbot=chatbot, history=history)

        try:
            trans_html_file = [f for f in glob.glob(f'{project_folder}/**/*.trans.html', recursive=True)][0]
            promote_file_to_downloadzone(trans_html_file, rename_file=None, chatbot=chatbot)

            translate_pdf = [f for f in glob.glob(f'{project_folder}/**/merge_translate_zh.pdf', recursive=True)][0]
            promote_file_to_downloadzone(translate_pdf, rename_file=None, chatbot=chatbot)

            comparison_pdf = [f for f in glob.glob(f'{project_folder}/**/comparison.pdf', recursive=True)][0]
            promote_file_to_downloadzone(comparison_pdf, rename_file=None, chatbot=chatbot)        

            zip_res = zip_result(project_folder)
            promote_file_to_downloadzone(file=zip_res, chatbot=chatbot)

            return True
        
        except:
            report_exception(chatbot, history, b=f"ローカルで履歴が見つかりました，ファイルが見つかりませんでした。")
            yield from update_ui(chatbot=chatbot, history=history)
            
            chatbot.append([f"ファイルが見つかりませんでした", '翻訳します...'])
            yield from update_ui(chatbot=chatbot, history=history)

            except_flag = True
            
    
    elif not repeat or except_flag:
        yield from update_ui_lastest_msg(f"履歴が見つかりませんでした", chatbot=chatbot, history=history)

        # <-------------- convert pdf into tex ------------->
        chatbot.append([f"プロジェクトを解析する: {txt}", "PDFをtexに変換しています，お待ちください..."])
        yield from update_ui(chatbot=chatbot, history=history)
        project_folder = pdf2tex_project(file_manifest[0])
        if project_folder is None:
            report_exception(chatbot, history, a=f"プロジェクトを解析する: {txt}", b=f"PDFをtexへの変換が失敗しました")
            yield from update_ui(chatbot=chatbot, history=history)
            return False

        # <-------------- translate latex file into Chinese ------------->
        yield from update_ui_lastest_msg("texファイルを日本語に翻訳しています...", chatbot=chatbot, history=history)
        file_manifest = [f for f in glob.glob(f'{project_folder}/**/*.tex', recursive=True)]
        if len(file_manifest) == 0:
            report_exception(chatbot, history, a=f"プロジェクトを解析する: {txt}", b=f".texファイルが見つかりません: {txt}")
            yield from update_ui(chatbot=chatbot, history=history)  # 画面を更新する
            return

        # <-------------- if is a zip/tar file ------------->
        project_folder = desend_to_extracted_folder_if_exist(project_folder)

        # <-------------- move latex project away from temp folder ------------->
        project_folder = move_project(project_folder)

        # <-------------- set a hash tag for repeat-checking ------------->
        with open(pj(project_folder, hash_tag + '.tag'), 'w') as f:
            f.write(hash_tag)
            f.close()


        # <-------------- if merge_translate_zh is already generated, skip gpt req ------------->
        if not os.path.exists(project_folder + '/merge_translate_zh.tex'):
            yield from DecomposeAndConvertLatex(file_manifest, project_folder, llm_kwargs, plugin_kwargs,
                                        chatbot, history, system_prompt, mode='translate_zh',
                                        switch_prompt=_switch_prompt_)

        # <-------------- compile PDF ------------->
        yield from update_ui_lastest_msg("翻訳したtexファイルをPDFに変換しています...", chatbot=chatbot, history=history)
        success = yield from CompileLatex(chatbot, history, main_file_original='merge',
                                    main_file_modified='merge_translate_zh', mode='translate_zh',
                                    work_folder_original=project_folder, work_folder_modified=project_folder,
                                    work_folder=project_folder)

        # <-------------- zip PDF ------------->
        zip_res = zip_result(project_folder)
        if success:
            chatbot.append((f"成功した", '結果を確認してください...'))
            yield from update_ui(chatbot=chatbot, history=history);
            time.sleep(1)  # 画面を更新する
            promote_file_to_downloadzone(file=zip_res, chatbot=chatbot)
        else:
            chatbot.append((f"失敗した",
                            'PDFの生成に失敗しました, 結果を確認してください, 翻訳済みのTexドキュメントが含まれています, GithubのIssueエリアにアクセスし、報告して下さい'))
            yield from update_ui(chatbot=chatbot, history=history);
            time.sleep(1)  # 画面を更新する
            promote_file_to_downloadzone(file=zip_res, chatbot=chatbot)

        # <-------------- we are done ------------->
        return success
