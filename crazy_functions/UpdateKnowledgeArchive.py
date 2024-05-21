#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@ Author: Rindon
@ Date: 2024-05-13 09:42:46
@ LastEditors: Rindon
@ LastEditTime: 2024-05-21 15:14:19
@ Description: まだ翻訳していない
'''
from toolbox import CatchException, update_ui, ProxyNetworkActivate, update_ui_lastest_msg, get_log_folder, get_user
from .crazy_utils import request_gpt_model_in_new_thread_with_ui_alive, get_files_from_everything

install_msg ="""

1. python -m pip install torch --index-url https://download.pytorch.org/whl/cpu

2. python -m pip install transformers protobuf langchain sentence-transformers  faiss-cpu nltk beautifulsoup4 bitsandbytes tabulate icetk --upgrade

3. python -m pip install unstructured[all-docs] --upgrade

4. python -c 'import nltk; nltk.download("punkt")'
"""

@CatchException
def InjectKnowledgeBaseFiles(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    """
    txt             入力欄にユーザーが入力したテキスト，翻訳が必要な例文，処理待ちのファイルを含むパスの例
    llm_kwargs      GPTモデルのパラメータ, 温度やtop_pなど, 通常はそのまま渡すだけでよい
    plugin_kwargs   プラグインモデルのパラメータ，現時点では使用するされていません
    chatbot         チャット表示ボックスのハンドル，ユーザーに表示するために使用するされます
    history         チャット履歴，前提の要約
    system_prompt   GPTに対するサイレントリマインダー
    user_request    当前用户的请求信息（IPAddress等）
    """
    history = []    # 履歴をクリアする，オーバーフローを防ぐために

    # < --------------------パラメータの読み込み--------------- >
    if ("advanced_arg" in plugin_kwargs) and (plugin_kwargs["advanced_arg"] == ""): plugin_kwargs.pop("advanced_arg")
    kai_id = plugin_kwargs.get("advanced_arg", 'default')

    chatbot.append((f"向`{kai_id}`知识库中添加文件。", "[Local Message] 一連のファイルから(txt, md, tex)データを読み取って知識ベースを構築する, 然后进行问答。"))
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する

    # resolve deps
    try:
        # from zh_langchain import construct_vector_store
        # from langchain.embeddings.huggingface import HuggingFaceEmbeddings
        from crazy_functions.vector_fns.vector_database import knowledge_archive_interface
    except Exception as e:
        chatbot.append(["不足の依存関係", f"{str(e)}\n\nテキストの翻訳。请用以下命令テキストの翻訳" + install_msg])
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        # from .crazy_utils import try_install_deps
        # try_install_deps(['zh_langchain==0.2.1', 'pypinyin'], reload_m=['pypinyin', 'zh_langchain'])
        # yield from update_ui_lastest_msg("テキストの翻訳完了，您可以再次重试。", chatbot, history)
        return

    # < ------------------テキストの翻訳--------------- >
    file_manifest = []
    spl = ["txt", "doc", "docx", "email", "epub", "html", "json", "md", "msg", "pdf", "ppt", "pptx", "rtf"]
    for sp in spl:
        _, file_manifest_tmp, _ = get_files_from_everything(txt, type=f'.{sp}')
        file_manifest += file_manifest_tmp

    if len(file_manifest) == 0:
        chatbot.append(["読み込み可能なファイルが見つかりません", "現在サポートされている形式には: txt, md, docx, pptx, pdf, jsonなど"])
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return

    # < ------------------テキストの翻訳--------------- >
    chatbot.append(['<br/>'.join(file_manifest), "テキストベクトル化モジュールのプリヒート中, 初めて実行する場合, 中国語のベクトル化モデルをダウンロードするのに時間がかかります..."])
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
    print('Checking Text2vec ...')
    from langchain.embeddings.huggingface import HuggingFaceEmbeddings
    with ProxyNetworkActivate('Download_LLM'):    # 临時地激活代理网络
        HuggingFaceEmbeddings(model_name="GanymedeNil/text2vec-large-chinese")

    # < -------------------ナレッジベースの構築--------------- >
    chatbot.append(['<br/>'.join(file_manifest), "テキストの翻訳..."])
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
    print('Establishing knowledge archive ...')
    with ProxyNetworkActivate('Download_LLM'):    # 临時地激活代理网络
        kai = knowledge_archive_interface()
        vs_path = get_log_folder(user=get_user(chatbot), plugin_name='vec_store')
        kai.feed_archive(file_manifest=file_manifest, vs_path=vs_path, id=kai_id)
    kai_files = kai.get_loaded_file(vs_path=vs_path)
    kai_files = '<br/>'.join(kai_files)
    # chatbot.append(['知识库构建成功', "正在置き換える知识库存储至cookie中"])
    # yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
    # chatbot._cookies['langchain_plugin_embedding'] = kai.get_current_archive_id()
    # chatbot._cookies['lock_plugin'] = 'crazy_functions.InjectKnowledgeBaseFiles->ReadKnowledgeArchiveAnswerQuestions'
    # chatbot.append(['完了', "“根据知识库作答”関数プラグイン已经接管问答系统, 質問してください！ただし注意してください, 原始文本，刷新页面即可以終了UpdateKnowledgeArchive模式。"])
    chatbot.append(['ビルドが完了しました', f"現在のナレッジベース内の有効なファイル：\n\n---\n\n{kai_files}\n\n---\n\n请切换至“UpdateKnowledgeArchive”プラグイン进行知识库访问, または、このプラグインを使用するしてさらにファイルをアップロードします。"])
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する # GPTのリクエストには時間がかかるため，まず、タイムリーに画面を更新します

@CatchException
def ReadKnowledgeArchiveAnswerQuestions(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request=-1):
    # resolve deps
    try:
        # from zh_langchain import construct_vector_store
        # from langchain.embeddings.huggingface import HuggingFaceEmbeddings
        from crazy_functions.vector_fns.vector_database import knowledge_archive_interface
    except Exception as e:
        chatbot.append(["不足の依存関係", f"{str(e)}\n\nテキストの翻訳。请用以下命令テキストの翻訳" + install_msg])
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        # from .crazy_utils import try_install_deps
        # try_install_deps(['zh_langchain==0.2.1', 'pypinyin'], reload_m=['pypinyin', 'zh_langchain'])
        # yield from update_ui_lastest_msg("テキストの翻訳完了，您可以再次重试。", chatbot, history)
        return

    # < -------------------  --------------- >
    kai = knowledge_archive_interface()

    if ("advanced_arg" in plugin_kwargs) and (plugin_kwargs["advanced_arg"] == ""): plugin_kwargs.pop("advanced_arg")
    kai_id = plugin_kwargs.get("advanced_arg", 'default')
    vs_path = get_log_folder(user=get_user(chatbot), plugin_name='vec_store')
    resp, prompt = kai.answer_with_archive_by_id(txt, kai_id, vs_path)

    chatbot.append((txt, f'[知识库 {kai_id}] ' + prompt))
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する # GPTのリクエストには時間がかかるため，まず、タイムリーに画面を更新します
    gpt_say = yield from request_gpt_model_in_new_thread_with_ui_alive(
        inputs=prompt, inputs_show_user=txt,
        llm_kwargs=llm_kwargs, chatbot=chatbot, history=[],
        sys_prompt=system_prompt
    )
    history.extend((prompt, gpt_say))
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する # GPTのリクエストには時間がかかるため，まず、タイムリーに画面を更新します
