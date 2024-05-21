from toolbox import CatchException, update_ui
from .crazy_utils import request_gpt_model_in_new_thread_with_ui_alive, input_clipping
import requests
from bs4 import BeautifulSoup
from request_llms.bridge_all import model_info


def bing_search(query, proxies=None):
    query = query
    url = f"https://cn.bing.com/search?q={query}"
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36'}
    response = requests.get(url, headers=headers, proxies=proxies)
    soup = BeautifulSoup(response.content, 'html.parser')
    results = []
    for g in soup.find_all('li', class_='b_algo'):
        anchors = g.find_all('a')
        if anchors:
            link = anchors[0]['href']
            if not link.startswith('http'):
                continue
            title = g.find('h2').text
            item = {'title': title, 'link': link}
            results.append(item)

    for r in results:
        print(r['link'])
    return results


def scrape_text(url, proxies) -> str:
    """Scrape text from a webpage

    Args:
        url (str): The URL to scrape text from

    Returns:
        str: The scraped text
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36',
        'Content-Type': 'text/plain',
    }
    try:
        response = requests.get(url, headers=headers, proxies=proxies, timeout=8)
        if response.encoding == "ISO-8859-1": response.encoding = response.apparent_encoding
    except:
        return "このウェブページに接続できません"
    soup = BeautifulSoup(response.text, "html.parser")
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = "\n".join(chunk for chunk in chunks if chunk)
    return text

@CatchException
def ConnectBingSearchAnswerQuestion(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    """
    txt             入力欄にユーザーが入力したテキスト，翻訳が必要な例文，処理待ちのファイルを含むパスの例
    llm_kwargs      GPTモデルのパラメータ，温度やtop_pなど，通常はそのまま渡すだけでよい
    plugin_kwargs   プラグインモデルのパラメータ，現時点では使用するされていません
    chatbot         チャット表示ボックスのハンドル，ユーザーに表示するために使用するされます
    history         チャット履歴，前提の要約
    system_prompt   GPTに対するサイレントリマインダー
    user_request    当前用户的请求信息（IPAddress等）
    """
    history = []    # 履歴をクリアする，オーバーフローを防ぐために
    chatbot.append((f"以下の問題にインターネット情報を組み合わせて回答してください：{txt}",
                    "[Local Message] 注意してください，呼び出している[関数プラグイン]のテンプレート，このテンプレートは、ChatGPTネットワーク情報の総合を実現できます。この関数は、より多くの面白い機能を実装したい開発者を対象としています，It can serve as a template for creating new feature functions。If you want to share new functional modules，PRを遠慮なく提出してください！"))
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する # GPTのリクエストには時間がかかるため，まず、タイムリーに画面を更新します

    # ------------- < ステップ1：検索エンジンの結果をクロールする > -------------
    from toolbox import get_conf
    proxies = get_conf('proxies')
    urls = bing_search(txt, proxies)
    history = []
    if len(urls) == 0:
        chatbot.append((f"結論：{txt}",
                        "[Local Message] bingから制限されて，情報を取ることが出来ません！"))
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する # GPTのリクエストには時間がかかるため，まず、タイムリーに画面を更新します
        return
    # ------------- < ステップ2：ウェブページに順次アクセスする > -------------
    max_search_result = 8   # Maximum number of web page results to be included
    for index, url in enumerate(urls[:max_search_result]):
        res = scrape_text(url['link'], proxies)
        history.extend([f"第{index}検索結果：", res])
        chatbot.append([f"第{index}検索結果：", res[:500]+"......"])
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する # GPTのリクエストには時間がかかるため，まず、タイムリーに画面を更新します

    # ------------- < ステップ3：ChatGPT総合 > -------------
    i_say = f"上記の検索結果から情報を抽出する，Then answer the question：{txt}"
    i_say, history = input_clipping(    # 入力をトリミングする，最長のエントリからトリミングを開始する，トークンの爆発を防止する
        inputs=i_say,
        history=history,
        max_token_limit=model_info[llm_kwargs['llm_model']]['max_token']*3//4
    )
    gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(
        inputs=i_say, inputs_show_user=i_say,
        llm_kwargs=llm_kwargs, chatbot=chatbot, history=history,
        sys_prompt="指定された複数の検索結果から情報を抽出してください，最も関連性の高い2つの検索結果をまとめる，Then answer the question。"
    )
    chatbot[-1] = (i_say, gpt_say)
    history.append(i_say);history.append(gpt_say)
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する # インターフェースの更新

