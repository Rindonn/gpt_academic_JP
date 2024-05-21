#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@ Author: Rindon
@ Date: 2024-05-13 09:42:46
@ LastEditors: Rindon
@ LastEditTime: 2024-05-21 10:07:41
@ Description: prompt、インターフェースを日本語に変更
'''
from toolbox import update_ui, get_log_folder
from toolbox import write_history_to_file, promote_file_to_downloadzone
from toolbox import CatchException, report_exception, get_conf
import re, requests, unicodedata, os
from .crazy_utils import request_gpt_model_in_new_thread_with_ui_alive
def download_arxiv_(url_pdf):
    if 'arxiv.org' not in url_pdf:
        if ('.' in url_pdf) and ('/' not in url_pdf):
            new_url = 'https://arxiv.org/abs/'+url_pdf
            print('ダウンロード番号：', url_pdf, '位置：', new_url)
            # download_arxiv_(new_url)
            return download_arxiv_(new_url)
        else:
            print('URL認識できない！')
            return None
    if 'abs' in url_pdf:
        url_pdf = url_pdf.replace('abs', 'pdf')
        url_pdf = url_pdf + '.pdf'

    url_abs = url_pdf.replace('.pdf', '').replace('pdf', 'abs')
    title, other_info = get_name(_url_=url_abs)

    paper_id = title.split()[0]  # '[1712.00559]'
    if '2' in other_info['year']:
        title = other_info['year'] + ' ' + title

    known_conf = ['NeurIPS', 'NIPS', 'Nature', 'Science', 'ICLR', 'AAAI']
    for k in known_conf:
        if k in other_info['comment']:
            title = k + ' ' + title

    download_dir = get_log_folder(plugin_name='arxiv')
    os.makedirs(download_dir, exist_ok=True)

    title_str = title.replace('?', '？')\
        .replace(':', '：')\
        .replace('\"', '“')\
        .replace('\n', '')\
        .replace('  ', ' ')\
        .replace('  ', ' ')

    requests_pdf_url = url_pdf
    file_path = download_dir+title_str

    print('ダウンロード中')
    proxies = get_conf('proxies')
    r = requests.get(requests_pdf_url, proxies=proxies)
    with open(file_path, 'wb+') as f:
        f.write(r.content)
    print('ダウンロードが完了した')

    # print('出力下载命令：','aria2c -o \"%s\" %s'%(title_str,url_pdf))
    # subprocess.call('aria2c --all-proxy=\"172.18.116.150:11084\" -o \"%s\" %s'%(download_dir+title_str,url_pdf), shell=True)

    x = "%s  %s %s.bib" % (paper_id, other_info['year'], other_info['authors'])
    x = x.replace('?', '？')\
        .replace(':', '：')\
        .replace('\"', '“')\
        .replace('\n', '')\
        .replace('  ', ' ')\
        .replace('  ', ' ')
    return file_path, other_info


def get_name(_url_):
    import os
    from bs4 import BeautifulSoup
    print('文献名を取得している')
    print(_url_)

    # arxiv_recall = {}
    # if os.path.exists('./arxiv_recall.pkl'):
    #     with open('./arxiv_recall.pkl', 'rb') as f:
    #         arxiv_recall = pickle.load(f)

    # if _url_ in arxiv_recall:
    #     print('在缓存中')
    #     return arxiv_recall[_url_]

    proxies = get_conf('proxies')
    res = requests.get(_url_, proxies=proxies)

    bs = BeautifulSoup(res.text, 'html.parser')
    other_details = {}

    # get year
    try:
        year = bs.find_all(class_='dateline')[0].text
        year = re.search(r'(\d{4})', year, re.M | re.I).group(1)
        other_details['year'] = year
        abstract = bs.find_all(class_='abstract mathjax')[0].text
        other_details['abstract'] = abstract
    except:
        other_details['year'] = ''
        print('年を取得できなかった')

    # get author
    try:
        authors = bs.find_all(class_='authors')[0].text
        authors = authors.split('Authors:')[1]
        other_details['authors'] = authors
    except:
        other_details['authors'] = ''
        print('著者の取得に失敗した')

    # get comment
    try:
        comment = bs.find_all(class_='metatable')[0].text
        real_comment = None
        for item in comment.replace('\n', ' ').split('   '):
            if 'Comments' in item:
                real_comment = item
        if real_comment is not None:
            other_details['comment'] = real_comment
        else:
            other_details['comment'] = ''
    except:
        other_details['comment'] = ''
        print('年を取得できなかった')

    title_str = BeautifulSoup(
        res.text, 'html.parser').find('title').contents[0]
    print('取得した：', title_str)
    # arxiv_recall[_url_] = (title_str+'.pdf', other_details)
    # with open('./arxiv_recall.pkl', 'wb') as f:
    #     pickle.dump(arxiv_recall, f)

    return title_str+'.pdf', other_details



@CatchException
def DownloadArxivPaperAndTranslateAbstract(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):

    CRAZY_FUNCTION_INFO = "DownloadArxivPaperAndTranslateAbstract，関数プラグインの著者[binary-husky]。要約を抽出し、PDFドキュメントをダウンロードしている..."
    import glob
    import os

    # 基本情報：機能、貢献者
    chatbot.append(["関数プラグイン機能？", CRAZY_FUNCTION_INFO])
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する

    # 依存関係のインポートを試みる，依存関係が不足している場合，インストールの提案を行います
    try:
        import bs4
    except:
        report_exception(chatbot, history,
            a = f"プロジェクトを解析する: {txt}",
            b = f"ソフトウェアの依存関係のインポートに失敗しました。このモジュールを使用するするには、追加の依存関係が必要です，インストールテキストの翻訳```pip install --upgrade beautifulsoup4```。")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return

    # 履歴をクリアする，オーバーフローを防ぐために
    history = []

    # 要約を抽出する，PDF文書をダウンロードする
    try:
        pdf_path, info = download_arxiv_(txt)
    except:
        report_exception(chatbot, history,
            a = f"プロジェクトを解析する: {txt}",
            b = f"PDFファイルのダウンロードに失敗した")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return

    # 要約などを翻訳する
    i_say =            f"以下の学術論文に関連する資料を読んでください，要約を抽出して，日本語に翻訳する。資料：{str(info)}"
    i_say_show_user =  f'以下の学術論文に関連する資料を読んでください，要約を抽出して，日本語に翻訳する。論文：{pdf_path}'
    chatbot.append((i_say_show_user, "[Local Message] waiting gpt response."))
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
    msg = '正常'
    # ** gpt request **
    # Single line，記事のメタ情報を取得する
    gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(
        inputs=i_say,
        inputs_show_user=i_say_show_user,
        llm_kwargs=llm_kwargs,
        chatbot=chatbot, history=[],
        sys_prompt="Your job is to collect information from materials and translate to Japanese.",
    )

    chatbot[-1] = (i_say_show_user, gpt_say)
    history.append(i_say_show_user); history.append(gpt_say)
    yield from update_ui(chatbot=chatbot, history=history, msg=msg) # 画面を更新する
    res = write_history_to_file(history)
    promote_file_to_downloadzone(res, chatbot=chatbot)
    promote_file_to_downloadzone(pdf_path, chatbot=chatbot)

    chatbot.append(("完了したか？", res + "\n\nPDFファイルもダウンロードされた"))
    yield from update_ui(chatbot=chatbot, history=history, msg=msg) # 画面を更新する

