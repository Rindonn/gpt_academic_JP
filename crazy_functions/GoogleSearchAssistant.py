from .crazy_utils import request_gpt_model_in_new_thread_with_ui_alive
from toolbox import CatchException, report_exception, promote_file_to_downloadzone
from toolbox import update_ui, update_ui_lastest_msg, disable_auto_promotion, write_history_to_file
import logging
import requests
import time
import random

ENABLE_ALL_VERSION_SEARCH = True

def get_meta_information(url, chatbot, history):
    import arxiv
    import difflib
    import re
    from bs4 import BeautifulSoup
    from toolbox import get_conf
    from urllib.parse import urlparse
    session = requests.session()

    proxies = get_conf('proxies')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
        'Cache-Control':'max-age=0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Connection': 'keep-alive'
    }
    try:
        session.proxies.update(proxies)
    except:
        report_exception(chatbot, history,
                    a=f"获取代理失敗しました It is very likely that you cannot access the OpenAI family of models without a proxy及谷歌学术 提案する：USE_PROXYオプションが変更されているかどうかを確認してください。",
                    b=f"Try直接连接")
        yield from update_ui(chatbot=chatbot, history=history)  # 画面を更新する
    session.headers.update(headers)

    response = session.get(url)
    # ウェブページの内容を解析する
    soup = BeautifulSoup(response.text, "html.parser")

    def string_similar(s1, s2):
        return difflib.SequenceMatcher(None, s1, s2).quick_ratio()

    if ENABLE_ALL_VERSION_SEARCH:
        def search_all_version(url):
            time.sleep(random.randint(1,5)) # 睡一会防止触发google反爬虫
            response = session.get(url)
            soup = BeautifulSoup(response.text, "html.parser")

            for result in soup.select(".gs_ri"):
                try:
                    url = result.select_one(".gs_rt").a['href']
                except:
                    continue
                arxiv_id = extract_arxiv_id(url)
                if not arxiv_id:
                    continue
                search = arxiv.Search(
                    id_list=[arxiv_id],
                    max_results=1,
                    sort_by=arxiv.SortCriterion.Relevance,
                )
                try: paper = next(search.results())
                except: paper = None
                return paper

            return None

        def extract_arxiv_id(url):
            # 戻る给定的url解析出的arxiv_id，如url未成功匹配戻るNone
            pattern = r'arxiv.org/abs/([^/]+)'
            match = re.search(pattern, url)
            if match:
                return match.group(1)
            else:
                return None

    profile = []
    # すべての記事のタイトルと著者を取得する
    for result in soup.select(".gs_ri"):
        title = result.a.text.replace('\n', ' ').replace('  ', ' ')
        author = result.select_one(".gs_a").text
        try:
            citation = result.select_one(".gs_fl > a[href*='cites']").text  # The reference count is the text in the link，直接取り出す
        except:
            citation = 'cited by 0'
        abstract = result.select_one(".gs_rs").text.strip()  # .gs_rs中の要約テキスト，先頭と末尾の空白を削除する必要があります

        # 首先在arxiv上搜索，获取文章摘要
        search = arxiv.Search(
            query = title,
            max_results = 1,
            sort_by = arxiv.SortCriterion.Relevance,
        )
        try: paper = next(search.results())
        except: paper = None

        is_match = paper is not None and string_similar(title, paper.title) > 0.90

        # 如果在Arxiv上匹配失敗しました，检索文章的History版本的题目
        if not is_match and ENABLE_ALL_VERSION_SEARCH:
            other_versions_page_url = [tag['href'] for tag in result.select_one('.gs_flb').select('.gs_nph') if 'cluster' in tag['href']]
            if len(other_versions_page_url) > 0:
                other_versions_page_url = other_versions_page_url[0]
                paper = search_all_version('http://' + urlparse(url).netloc + other_versions_page_url)
                is_match = paper is not None and string_similar(title, paper.title) > 0.90

        if is_match:
            # same paper
            abstract = paper.summary.replace('\n', ' ')
            is_paper_in_arxiv = True
        else:
            # different paper
            abstract = abstract
            is_paper_in_arxiv = False

        logging.info('[title]:' + title)
        logging.info('[author]:' + author)
        logging.info('[citation]:' + citation)

        profile.append({
            'title': title,
            'author': author,
            'citation': citation,
            'abstract': abstract,
            'is_paper_in_arxiv': is_paper_in_arxiv,
        })

        chatbot[-1] = [chatbot[-1][0], title + f'\n\narxivにあるかどうか（arxivにないと完全な要約を取得できません）:{is_paper_in_arxiv}\n\n' + abstract]
        yield from update_ui(chatbot=chatbot, history=[]) # 画面を更新する
    return profile

@CatchException
def GoogleSearchAssistant(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    disable_auto_promotion(chatbot=chatbot)
    # 基本情報：機能、貢献者
    chatbot.append([
        "関数プラグイン機能？",
        "ユーザーが提供したGoogle Scholarの分析（google scholar）ページ内を検索する，表示されるすべての記事: binary-husky，プラグインの初期化中..."])
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する

    # 依存関係のインポートを試みる，依存関係が不足している場合，インストールの提案を行います
    try:
        import arxiv
        import math
        from bs4 import BeautifulSoup
    except:
        report_exception(chatbot, history,
            a = f"プロジェクトを解析する: {txt}",
            b = f"ソフトウェアの依存関係のインポートに失敗しました。このモジュールを使用するするには、追加の依存関係が必要です，インストールテキストの翻訳```pip install --upgrade beautifulsoup4 arxiv```。")
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return

    # 履歴をクリアする，オーバーフローを防ぐために
    history = []
    meta_paper_info_list = yield from get_meta_information(txt, chatbot, history)
    if len(meta_paper_info_list) == 0:
        yield from update_ui_lastest_msg(lastmsg='获取文献失敗しました，可能触发了google反爬虫机制。',chatbot=chatbot, history=history, delay=0)
        return
    batchsize = 5
    for batch in range(math.ceil(len(meta_paper_info_list)/batchsize)):
        if len(meta_paper_info_list[:batchsize]) > 0:
            i_say = "Below are some data on academic literature，以下の内容を抽出する：" + \
            "1.英語のタイトル；2.中国語のタイトルの翻訳；3.著者；4.arxiv公開（is_paper_in_arxiv）；4、引用数量（cite）；5、中国語要約翻訳。" + \
            f"以下は情報源です：{str(meta_paper_info_list[:batchsize])}"

            inputs_show_user = f"このページに表示されるすべての記事を分析してください：{txt}，これは第{batch+1}バッチ"
            gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(
                inputs=i_say, inputs_show_user=inputs_show_user,
                llm_kwargs=llm_kwargs, chatbot=chatbot, history=[],
                sys_prompt="あなたは学術翻訳者です，データから情報を抽出してください。Markdownテーブルを使用するする必要があります。文献を1つずつ処理する必要があります。"
            )

            history.extend([ f"第{batch+1}バッチ", gpt_say ])
            meta_paper_info_list = meta_paper_info_list[batchsize:]

    chatbot.append(["ステータス？",
        "すべて完了しました，AIにRelated Worksを書かせてみることができます，例えば您可以继续入力Write a \"Related Works\" section about \"你搜索的研究领域\" for me."])
    msg = '正常'
    yield from update_ui(chatbot=chatbot, history=history, msg=msg) # 画面を更新する
    path = write_history_to_file(history)
    promote_file_to_downloadzone(path, chatbot=chatbot)
    chatbot.append(("完了しましたか？", path));
    yield from update_ui(chatbot=chatbot, history=history, msg=msg) # 画面を更新する
