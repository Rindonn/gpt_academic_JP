from toolbox import update_ui, update_ui_lastest_msg, get_log_folder
from toolbox import get_conf, objdump, objload, promote_file_to_downloadzone
from .latex_toolbox import PRESERVE, TRANSFORM
from .latex_toolbox import set_forbidden_text, set_forbidden_text_begin_end, set_forbidden_text_careful_brace
from .latex_toolbox import reverse_forbidden_text_careful_brace, reverse_forbidden_text, convert_to_linklist, post_process
from .latex_toolbox import fix_content, find_main_tex_file, merge_tex_files, compile_latex_with_timeout
from .latex_toolbox import find_title_and_abs

import os, shutil
import re
import numpy as np

pj = os.path.join


def split_subprocess(txt, project_folder, return_dict, opts):
    """
    break down latex file to a linked list,
    each node use a preserve flag to indicate whether it should
    be proccessed by GPT.
    """
    text = txt
    mask = np.zeros(len(txt), dtype=np.uint8) + TRANSFORM

    # タイトルと著者以上の部分を吸収する
    text, mask = set_forbidden_text(text, mask, r"^(.*?)\\maketitle", re.DOTALL)
    text, mask = set_forbidden_text(text, mask, r"^(.*?)\\begin{document}", re.DOTALL)
    # iffalseコメントを吸収する
    text, mask = set_forbidden_text(text, mask, r"\\iffalse(.*?)\\fi", re.DOTALL)
    # 42行以内のbegin-endの組み合わせを取り込む
    text, mask = set_forbidden_text_begin_end(text, mask, r"\\begin\{([a-z\*]*)\}(.*?)\\end\{\1\}", re.DOTALL, limit_n_lines=42)
    # テキストの翻訳
    text, mask = set_forbidden_text(text, mask, [ r"\$\$([^$]+)\$\$",  r"\\\[.*?\\\]" ], re.DOTALL)
    # 他の雑項を吸収する
    text, mask = set_forbidden_text(text, mask, [ r"\\section\{(.*?)\}", r"\\section\*\{(.*?)\}", r"\\subsection\{(.*?)\}", r"\\subsubsection\{(.*?)\}" ])
    text, mask = set_forbidden_text(text, mask, [ r"\\bibliography\{(.*?)\}", r"\\bibliographystyle\{(.*?)\}" ])
    text, mask = set_forbidden_text(text, mask, r"\\begin\{thebibliography\}.*?\\end\{thebibliography\}", re.DOTALL)
    text, mask = set_forbidden_text(text, mask, r"\\begin\{lstlisting\}(.*?)\\end\{lstlisting\}", re.DOTALL)
    text, mask = set_forbidden_text(text, mask, r"\\begin\{wraptable\}(.*?)\\end\{wraptable\}", re.DOTALL)
    text, mask = set_forbidden_text(text, mask, r"\\begin\{algorithm\}(.*?)\\end\{algorithm\}", re.DOTALL)
    text, mask = set_forbidden_text(text, mask, [r"\\begin\{wrapfigure\}(.*?)\\end\{wrapfigure\}", r"\\begin\{wrapfigure\*\}(.*?)\\end\{wrapfigure\*\}"], re.DOTALL)
    text, mask = set_forbidden_text(text, mask, [r"\\begin\{figure\}(.*?)\\end\{figure\}", r"\\begin\{figure\*\}(.*?)\\end\{figure\*\}"], re.DOTALL)
    text, mask = set_forbidden_text(text, mask, [r"\\begin\{multline\}(.*?)\\end\{multline\}", r"\\begin\{multline\*\}(.*?)\\end\{multline\*\}"], re.DOTALL)
    text, mask = set_forbidden_text(text, mask, [r"\\begin\{table\}(.*?)\\end\{table\}", r"\\begin\{table\*\}(.*?)\\end\{table\*\}"], re.DOTALL)
    text, mask = set_forbidden_text(text, mask, [r"\\begin\{minipage\}(.*?)\\end\{minipage\}", r"\\begin\{minipage\*\}(.*?)\\end\{minipage\*\}"], re.DOTALL)
    text, mask = set_forbidden_text(text, mask, [r"\\begin\{align\*\}(.*?)\\end\{align\*\}", r"\\begin\{align\}(.*?)\\end\{align\}"], re.DOTALL)
    text, mask = set_forbidden_text(text, mask, [r"\\begin\{equation\}(.*?)\\end\{equation\}", r"\\begin\{equation\*\}(.*?)\\end\{equation\*\}"], re.DOTALL)
    text, mask = set_forbidden_text(text, mask, [r"\\includepdf\[(.*?)\]\{(.*?)\}", r"\\clearpage", r"\\newpage", r"\\appendix", r"\\tableofcontents", r"\\include\{(.*?)\}"])
    text, mask = set_forbidden_text(text, mask, [r"\\vspace\{(.*?)\}", r"\\hspace\{(.*?)\}", r"\\label\{(.*?)\}", r"\\begin\{(.*?)\}", r"\\end\{(.*?)\}", r"\\item "])
    text, mask = set_forbidden_text_careful_brace(text, mask, r"\\hl\{(.*?)\}", re.DOTALL)
    # reverse操作は最後に配置する必要があります
    text, mask = reverse_forbidden_text_careful_brace(text, mask, r"\\caption\{(.*?)\}", re.DOTALL, forbid_wrapper=True)
    text, mask = reverse_forbidden_text_careful_brace(text, mask, r"\\abstract\{(.*?)\}", re.DOTALL, forbid_wrapper=True)
    text, mask = reverse_forbidden_text(text, mask, r"\\begin\{abstract\}(.*?)\\end\{abstract\}", re.DOTALL, forbid_wrapper=True)
    root = convert_to_linklist(text, mask)

    # 最後のステップの処理，信頼性を向上させる
    root = post_process(root)

    # HTMLデバッグファイルの出力，テキストの翻訳（PRESERVE），黒い注釈で変換エリアをマークする（TRANSFORM）
    with open(pj(project_folder, 'debug_log.html'), 'w', encoding='utf8') as f:
        segment_parts_for_gpt = []
        nodes = []
        node = root
        while True:
            nodes.append(node)
            show_html = node.string.replace('\n','<br/>')
            if not node.preserve:
                segment_parts_for_gpt.append(node.string)
                f.write(f'<p style="color:black;">#{node.range}{show_html}#</p>')
            else:
                f.write(f'<p style="color:red;">{show_html}</p>')
            node = node.next
            if node is None: break

    for n in nodes: n.next = None   # break
    return_dict['nodes'] = nodes
    return_dict['segment_parts_for_gpt'] = segment_parts_for_gpt
    return return_dict

class LatexPaperSplit():
    """
    break down latex file to a linked list,
    each node use a preserve flag to indicate whether it should
    be proccessed by GPT.
    """
    def __init__(self) -> None:
        self.nodes = None
        self.msg = "*{\\scriptsize\\textbf{Warning：このPDFはGPT-Academicオープンソースプロジェクトによって大規模言語モデル+Latex翻訳プラグインを使用するして一括生成されました，" + \
            "原始文本。テキストの翻訳，注意深く確認し、元のテキストを参照してください。" + \
            "项目GithubAddress \\url{https://github.com/binary-husky/gpt_academic/}。"
        # テキストの翻訳，テキストの翻訳（テキストの翻訳，欢迎加REAME中的QQ联系开发者）
        self.msg_declare = "大規模言語モデルの誤った結果が広がるのを防ぐために，禁止移除或修改此Warning。}}\\\\"
        self.title = "unknown"
        self.abstract = "unknown"

    def read_title_and_abstract(self, txt):
        try:
            title, abstract = find_title_and_abs(txt)
            if title is not None:
                self.title = title.replace('\n', ' ').replace('\\\\', ' ').replace('  ', '').replace('  ', '')
            if abstract is not None:
                self.abstract = abstract.replace('\n', ' ').replace('\\\\', ' ').replace('  ', '').replace('  ', '')
        except:
            pass

    def merge_result(self, arr, mode, msg, buggy_lines=[], buggy_line_surgery_n_lines=10):
        """
        Merge the result after the GPT process completed
        """
        result_string = ""
        node_cnt = 0
        line_cnt = 0

        for node in self.nodes:
            if node.preserve:
                line_cnt += node.string.count('\n')
                result_string += node.string
            else:
                translated_txt = fix_content(arr[node_cnt], node.string)
                begin_line = line_cnt
                end_line = line_cnt + translated_txt.count('\n')

                # reverse translation if any error
                if any([begin_line-buggy_line_surgery_n_lines <= b_line <= end_line+buggy_line_surgery_n_lines for b_line in buggy_lines]):
                    translated_txt = node.string

                result_string += translated_txt
                node_cnt += 1
                line_cnt += translated_txt.count('\n')

        if mode == 'translate_zh':
            pattern = re.compile(r'\\begin\{abstract\}.*\n')
            match = pattern.search(result_string)
            if not match:
                # match \abstract{xxxx}
                pattern_compile = re.compile(r"\\abstract\{(.*?)\}", flags=re.DOTALL)
                match = pattern_compile.search(result_string)
                position = match.regs[1][0]
            else:
                # match \begin{abstract}xxxx\end{abstract}
                position = match.end()
            result_string = result_string[:position] + self.msg + msg + self.msg_declare + result_string[position:]
        return result_string


    def split(self, txt, project_folder, opts):
        """
        break down latex file to a linked list,
        each node use a preserve flag to indicate whether it should
        be proccessed by GPT.
        P.S. use multiprocessing to avoid timeout error
        """
        import multiprocessing
        manager = multiprocessing.Manager()
        return_dict = manager.dict()
        p = multiprocessing.Process(
            target=split_subprocess,
            args=(txt, project_folder, return_dict, opts))
        p.start()
        p.join()
        p.close()
        self.nodes = return_dict['nodes']
        self.sp = return_dict['segment_parts_for_gpt']
        return self.sp


class LatexPaperFileGroup():
    """
    use tokenizer to break down text according to max_token_limit
    """
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
        use tokenizer to break down text according to max_token_limit
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

    def merge_result(self):
        self.file_result = ["" for _ in range(len(self.file_paths))]
        for r, k in zip(self.sp_file_result, self.sp_file_index):
            self.file_result[k] += r

    def write_result(self):
        manifest = []
        for path, res in zip(self.file_paths, self.file_result):
            with open(path + '.polish.tex', 'w', encoding='utf8') as f:
                manifest.append(path + '.polish.tex')
                f.write(res)
        return manifest


def DecomposeAndConvertLatex(file_manifest, project_folder, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, mode='proofread', switch_prompt=None, opts=[]):
    import time, os, re
    from ..crazy_utils import request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency
    from .latex_actions import LatexPaperFileGroup, LatexPaperSplit

    #  <-------- メインのtexファイルを検索する ---------->
    maintex = find_main_tex_file(file_manifest, mode)
    chatbot.append((f"メインのLatexファイルを特定する", f'[Local Message] 結果を分析する：このプロジェクトのLaTeXメインファイルは{maintex}, もし解析エラーがある場合, プログラムを即座に終了してください, 曖昧なファイルを削除または修正する, その後、再試行してください。メインプログラムがすぐに開始されます, お待ちください。'))
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
    time.sleep(3)

    #  <-------- Latexファイルを読み込む, 複数のファイルのtexプロジェクトを1つの巨大なtexに統合する ---------->
    main_tex_basename = os.path.basename(maintex)
    assert main_tex_basename.endswith('.tex')
    main_tex_basename_bare = main_tex_basename[:-4]
    may_exist_bbl = pj(project_folder, f'{main_tex_basename_bare}.bbl')
    if os.path.exists(may_exist_bbl):
        shutil.copyfile(may_exist_bbl, pj(project_folder, f'merge.bbl'))
        shutil.copyfile(may_exist_bbl, pj(project_folder, f'merge_{mode}.bbl'))
        shutil.copyfile(may_exist_bbl, pj(project_folder, f'merge_diff.bbl'))

    with open(maintex, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
        merged_content = merge_tex_files(project_folder, content, mode)

    with open(project_folder + '/merge.tex', 'w', encoding='utf-8', errors='replace') as f:
        f.write(merged_content)

    #  <-------- LaTeXファイルを細かく分割する ---------->
    chatbot.append((f"Latexファイルの統合が完了しました", f'[Local Message] LaTeXファイルを細かく分割しています，これには時間がかかります，ドキュメントが長いほど時間がかかります，お待ちください。'))
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
    lps = LatexPaperSplit()
    lps.read_title_and_abstract(merged_content)
    res = lps.split(merged_content, project_folder, opts) # 消耗時间的函数
    #  <-------- 原始文本 ---------->
    pfg = LatexPaperFileGroup()
    for index, r in enumerate(res):
        pfg.file_paths.append('segment-' + str(index))
        pfg.file_contents.append(r)

    pfg.run_file_split(max_token_limit=1024)
    n_split = len(pfg.sp_file_contents)

    #  <-------- テキストの翻訳 ---------->
    inputs_array, sys_prompt_array = switch_prompt(pfg, mode)
    inputs_show_user_array = [f"{mode} {f}" for f in pfg.sp_file_tag]

    if os.path.exists(pj(project_folder,'temp.pkl')):

        #  <-------- 【デバッグのみ】デバッグキャッシュファイルが存在する場合，GPTリクエストのスキップ ---------->
        pfg = objload(file=pj(project_folder,'temp.pkl'))

    else:
        #  <-------- GPTマルチスレッドリクエスト ---------->
        history_array = [[""] for _ in range(n_split)]
        # LATEX_EXPERIMENTAL, = get_conf('LATEX_EXPERIMENTAL')
        # if LATEX_EXPERIMENTAL:
        #     paper_meta = f"The paper you processing is `{lps.title}`, a part of the abstraction is `{lps.abstract}`"
        #     paper_meta_max_len = 888
        #     history_array = [[ paper_meta[:paper_meta_max_len] + '...',  "Understand, what should I do?"] for _ in range(n_split)]

        gpt_response_collection = yield from request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency(
            inputs_array=inputs_array,
            inputs_show_user_array=inputs_show_user_array,
            llm_kwargs=llm_kwargs,
            chatbot=chatbot,
            history_array=history_array,
            sys_prompt_array=sys_prompt_array,
            # max_workers=5,  # Parallel task quantity limit, 同時に最大5つ実行できます, その他の待ち行列
            scroller_max_len = 40
        )

        #  <-------- 文本碎片原始文本为完整的texフラグメント ---------->
        pfg.sp_file_result = []
        for i_say, gpt_say, orig_content in zip(gpt_response_collection[0::2], gpt_response_collection[1::2], pfg.sp_file_contents):
            pfg.sp_file_result.append(gpt_say)
        pfg.merge_result()

        # <-------- デバッグ用の一時的なストレージ ---------->
        pfg.get_token_num = None
        objdump(pfg, file=pj(project_folder,'temp.pkl'))

    write_html(pfg.sp_file_contents, pfg.sp_file_result, chatbot=chatbot, project_folder=project_folder)

    #  <-------- ファイルに書き出す ---------->
    msg = f"テキストの翻訳: {llm_kwargs['llm_model']}，現在の言語モデルの温度設定: {llm_kwargs['temperature']}。"
    final_tex = lps.merge_result(pfg.file_result, mode, msg)
    objdump((lps, pfg.file_result, mode, msg), file=pj(project_folder,'merge_result.pkl'))

    with open(project_folder + f'/merge_{mode}.tex', 'w', encoding='utf-8', errors='replace') as f:
        if mode != 'translate_zh' or "binary" in final_tex: f.write(final_tex)


    #  <-------- Organized results, 終了 ---------->
    chatbot.append((f"完了しましたか？", 'GPTの結果が出力されました, PDFをコンパイルする予定です'))
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する

    #  <-------- 戻る ---------->
    return project_folder + f'/merge_{mode}.tex'


def remove_buggy_lines(file_path, log_path, tex_name, tex_name_pure, n_fix, work_folder_modified, fixed_line=[]):
    try:
        with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
            log = f.read()
        import re
        buggy_lines = re.findall(tex_name+':([0-9]{1,5}):', log)
        buggy_lines = [int(l) for l in buggy_lines]
        buggy_lines = sorted(buggy_lines)
        buggy_line = buggy_lines[0]-1
        print("reversing tex line that has errors", buggy_line)

        # 原始文本，エラーのあるパラグラフを逆転させます
        if buggy_line not in fixed_line:
            fixed_line.append(buggy_line)

        lps, file_result, mode, msg = objload(file=pj(work_folder_modified,'merge_result.pkl'))
        final_tex = lps.merge_result(file_result, mode, msg, buggy_lines=fixed_line, buggy_line_surgery_n_lines=5*n_fix)

        with open(pj(work_folder_modified, f"{tex_name_pure}_fix_{n_fix}.tex"), 'w', encoding='utf-8', errors='replace') as f:
            f.write(final_tex)

        return True, f"{tex_name_pure}_fix_{n_fix}", buggy_lines
    except:
        print("Fatal error occurred, but we cannot identify error, please download zip, read latex log, and compile manually.")
        return False, -1, [-1]


def CompileLatex(chatbot, history, main_file_original, main_file_modified, work_folder_original, work_folder_modified, work_folder, mode='default'):
    import os, time
    n_fix = 1
    fixed_line = []
    max_try = 32
    chatbot.append([f"原始文本", f'コンパイルが開始されました。現在の作業パスは{work_folder}，原始文本，直接そのパスに移動して翻訳結果を取得してください，または再起動後に再試行してください ...']); yield from update_ui(chatbot=chatbot, history=history)
    chatbot.append([f"原始文本", '...']); yield from update_ui(chatbot=chatbot, history=history); time.sleep(1); chatbot[-1] = list(chatbot[-1]) # 画面を更新する
    yield from update_ui_lastest_msg('コンパイルが開始されました...', chatbot, history)   # Gradioフロントエンドインターフェースをリフレッシュする

    while True:
        import os
        may_exist_bbl = pj(work_folder_modified, f'merge.bbl')
        target_bbl = pj(work_folder_modified, f'{main_file_modified}.bbl')
        if os.path.exists(may_exist_bbl) and not os.path.exists(target_bbl):
            shutil.copyfile(may_exist_bbl, target_bbl)

        # https://stackoverflow.com/questions/738755/dont-make-me-manually-abort-a-latex-compile-when-theres-an-error
        yield from update_ui_lastest_msg(f'第# {n_fix}/{max_try} 次编译, 元のPDFをコンパイルする ...', chatbot, history)   # Gradioフロントエンドインターフェースをリフレッシュする
        ok = compile_latex_with_timeout(f'pdflatex -interaction=batchmode -file-line-error {main_file_original}.tex', work_folder_original)

        yield from update_ui_lastest_msg(f'第# {n_fix}/{max_try} 次编译, 変換されたPDFをコンパイルする ...', chatbot, history)   # Gradioフロントエンドインターフェースをリフレッシュする
        ok = compile_latex_with_timeout(f'pdflatex -interaction=batchmode -file-line-error {main_file_modified}.tex', work_folder_modified)

        if ok and os.path.exists(pj(work_folder_modified, f'{main_file_modified}.pdf')):
            # テキストの翻訳，次の手順に進むために
            yield from update_ui_lastest_msg(f'第# {n_fix}/{max_try} 次编译, BibTexのコンパイル ...', chatbot, history)    # Gradioフロントエンドインターフェースをリフレッシュする
            if not os.path.exists(pj(work_folder_original, f'{main_file_original}.bbl')):
                ok = compile_latex_with_timeout(f'bibtex  {main_file_original}.aux', work_folder_original)
            if not os.path.exists(pj(work_folder_modified, f'{main_file_modified}.bbl')):
                ok = compile_latex_with_timeout(f'bibtex  {main_file_modified}.aux', work_folder_modified)

            yield from update_ui_lastest_msg(f'第# {n_fix}/{max_try} 次编译, 文献の相互参照をコンパイルする ...', chatbot, history)  # Gradioフロントエンドインターフェースをリフレッシュする
            ok = compile_latex_with_timeout(f'pdflatex -interaction=batchmode -file-line-error {main_file_original}.tex', work_folder_original)
            ok = compile_latex_with_timeout(f'pdflatex -interaction=batchmode -file-line-error {main_file_modified}.tex', work_folder_modified)
            ok = compile_latex_with_timeout(f'pdflatex -interaction=batchmode -file-line-error {main_file_original}.tex', work_folder_original)
            ok = compile_latex_with_timeout(f'pdflatex -interaction=batchmode -file-line-error {main_file_modified}.tex', work_folder_modified)

            if mode!='translate_zh':
                yield from update_ui_lastest_msg(f'第# {n_fix}/{max_try} 次编译, テキストの翻訳 ...', chatbot, history) # Gradioフロントエンドインターフェースをリフレッシュする
                print(    f'latexdiff --encoding=utf8 --append-safecmd=subfile {work_folder_original}/{main_file_original}.tex  {work_folder_modified}/{main_file_modified}.tex --flatten > {work_folder}/merge_diff.tex')
                ok = compile_latex_with_timeout(f'latexdiff --encoding=utf8 --append-safecmd=subfile {work_folder_original}/{main_file_original}.tex  {work_folder_modified}/{main_file_modified}.tex --flatten > {work_folder}/merge_diff.tex', os.getcwd())

                yield from update_ui_lastest_msg(f'第# {n_fix}/{max_try} 次编译, テキストの翻訳 ...', chatbot, history)   # Gradioフロントエンドインターフェースをリフレッシュする
                ok = compile_latex_with_timeout(f'pdflatex  -interaction=batchmode -file-line-error merge_diff.tex', work_folder)
                ok = compile_latex_with_timeout(f'bibtex    merge_diff.aux', work_folder)
                ok = compile_latex_with_timeout(f'pdflatex  -interaction=batchmode -file-line-error merge_diff.tex', work_folder)
                ok = compile_latex_with_timeout(f'pdflatex  -interaction=batchmode -file-line-error merge_diff.tex', work_folder)

        # <---------- 結果をチェックする ----------->
        results_ = ""
        original_pdf_success = os.path.exists(pj(work_folder_original, f'{main_file_original}.pdf'))
        modified_pdf_success = os.path.exists(pj(work_folder_modified, f'{main_file_modified}.pdf'))
        diff_pdf_success     = os.path.exists(pj(work_folder, f'merge_diff.pdf'))
        results_ += f"元のPDFのコンパイルは成功しましたか: {original_pdf_success};"
        results_ += f"PDFのコンパイルが成功したかどうかを変換する: {modified_pdf_success};"
        results_ += f"PDFのコンパイルが成功したかどうかを比較する: {diff_pdf_success};"
        yield from update_ui_lastest_msg(f'第{n_fix}コンパイル終了:<br/>{results_}...', chatbot, history) # Gradioフロントエンドインターフェースをリフレッシュする

        if diff_pdf_success:
            result_pdf = pj(work_folder_modified, f'merge_diff.pdf')    # get pdf path
            promote_file_to_downloadzone(result_pdf, rename_file=None, chatbot=chatbot)  # promote file to web UI
        if modified_pdf_success:
            yield from update_ui_lastest_msg(f'PDF変換コンパイルが成功しました, 正在Try生成对比PDF, お待ちください ...', chatbot, history)    # Gradioフロントエンドインターフェースをリフレッシュする
            result_pdf = pj(work_folder_modified, f'{main_file_modified}.pdf') # get pdf path
            origin_pdf = pj(work_folder_original, f'{main_file_original}.pdf') # get pdf path
            if os.path.exists(pj(work_folder, '..', 'translation')):
                shutil.copyfile(result_pdf, pj(work_folder, '..', 'translation', 'translate_zh.pdf'))
            promote_file_to_downloadzone(result_pdf, rename_file=None, chatbot=chatbot)  # promote file to web UI
            # 2つのPDFを結合する
            if original_pdf_success:
                try:
                    from .latex_toolbox import merge_pdfs
                    concat_pdf = pj(work_folder_modified, f'comparison.pdf')
                    merge_pdfs(origin_pdf, result_pdf, concat_pdf)
                    if os.path.exists(pj(work_folder, '..', 'translation')):
                        shutil.copyfile(concat_pdf, pj(work_folder, '..', 'translation', 'comparison.pdf'))
                    promote_file_to_downloadzone(concat_pdf, rename_file=None, chatbot=chatbot)  # promote file to web UI
                except Exception as e:
                    print(e)
                    pass
            return True # 成功啦
        else:
            if n_fix>=max_try: break
            n_fix += 1
            can_retry, main_file_modified, buggy_lines = remove_buggy_lines(
                file_path=pj(work_folder_modified, f'{main_file_modified}.tex'),
                log_path=pj(work_folder_modified, f'{main_file_modified}.log'),
                tex_name=f'{main_file_modified}.tex',
                tex_name_pure=f'{main_file_modified}',
                n_fix=n_fix,
                work_folder_modified=work_folder_modified,
                fixed_line=fixed_line
            )
            yield from update_ui_lastest_msg(f'最も重要なPDF変換コンパイルが失敗したため, 原始文本, 現在のエラーのあるLaTeXコードは第{buggy_lines}行 ...', chatbot, history)   # Gradioフロントエンドインターフェースをリフレッシュする
            if not can_retry: break

    return False # 失敗しました


def write_html(sp_file_contents, sp_file_result, chatbot, project_folder):
    # write html
    try:
        import shutil
        from crazy_functions.pdf_fns.report_gen_html import construct_html
        from toolbox import gen_time_str
        ch = construct_html()
        orig = ""
        trans = ""
        final = []
        for c,r in zip(sp_file_contents, sp_file_result):
            final.append(c)
            final.append(r)
        for i, k in enumerate(final):
            if i%2==0:
                orig = k
            if i%2==1:
                trans = k
                ch.add_row(a=orig, b=trans)
        create_report_file_name = f"{gen_time_str()}.trans.html"
        res = ch.save_file(create_report_file_name)
        shutil.copyfile(res, pj(project_folder, create_report_file_name))
        promote_file_to_downloadzone(file=res, chatbot=chatbot)
    except:
        from toolbox import trimmed_format_exc
        print('writing html result failed:', trimmed_format_exc())
