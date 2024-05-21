from .bridge_newbingfree import preprocess_newbing_out, preprocess_newbing_out_simple
from multiprocessing import Process, Pipe
from toolbox import update_ui, get_conf, trimmed_format_exc
import threading
import importlib
import logging
import time
from toolbox import get_conf
import asyncio

load_message = "Claudeコンポーネントを読み込んでいます，お待ちください..."

try:
    """
    =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    第1部分：Slack API Client
    https://github.com/yokonsan/claude-in-slack-api
    =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
    """

    from slack_sdk.errors import SlackApiError
    from slack_sdk.web.async_client import AsyncWebClient

    class SlackClient(AsyncWebClient):
        """SlackClientクラスはSlack APIとのインタラクションに使用するするされます，メッセージの送受信などの機能を実現する。

        原始文本：
        - CHANNEL_ID：strタイプ，チャネルIDを表示する。

        テキストの翻訳：
        - open_channel()：非同期メソッド。テキストの翻訳，テキストの翻訳。
        - chat(text: str)：非同期メソッド。既に開いているチャンネルにテキストメッセージを送信する。
        - get_slack_messages()：非同期メソッド。テキストの翻訳，現在、過去のメッセージのクエリはサポートされていません。
        - get_reply()：非同期メソッド。テキストの翻訳，如果受信"Typing…_"结尾的消息言う明Claude还在继续出力，それ以外の場合はループを終了する。

        """

        CHANNEL_ID = None

        async def open_channel(self):
            response = await self.conversations_open(
                users=get_conf("SLACK_CLAUDE_BOT_ID")
            )
            self.CHANNEL_ID = response["channel"]["id"]

        async def chat(self, text):
            if not self.CHANNEL_ID:
                raise Exception("Channel not found.")

            resp = await self.chat_postMessage(channel=self.CHANNEL_ID, text=text)
            self.LAST_TS = resp["ts"]

        async def get_slack_messages(self):
            try:
                # TODO：一時的に歴史メッセージはサポートされていません，同じチャンネルで複数の人が使用するするする場合、過去のメッセージが漏洩する問題があります
                resp = await self.conversations_history(
                    channel=self.CHANNEL_ID, oldest=self.LAST_TS, limit=1
                )
                msg = [
                    msg
                    for msg in resp["messages"]
                    if msg.get("user") == get_conf("SLACK_CLAUDE_BOT_ID")
                ]
                return msg
            except (SlackApiError, KeyError) as e:
                raise RuntimeError(f"Slackメッセージの取得に失敗しました。")

        async def get_reply(self):
            while True:
                slack_msgs = await self.get_slack_messages()
                if len(slack_msgs) == 0:
                    await asyncio.sleep(0.5)
                    continue

                msg = slack_msgs[-1]
                if msg["text"].endswith("Typing…_"):
                    yield False, msg["text"]
                else:
                    yield True, msg["text"]
                    break

except:
    pass

"""
=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
第2部分：サブプロセスWorker（Call subject）
=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
"""


class ClaudeHandle(Process):
    def __init__(self):
        super().__init__(daemon=True)
        self.parent, self.child = Pipe()
        self.claude_model = None
        self.info = ""
        self.success = True
        self.local_history = []
        self.check_dependency()
        if self.success:
            self.start()
            self.threadLock = threading.Lock()

    def check_dependency(self):
        try:
            self.success = False
            import slack_sdk

            self.info = "Dependency check passed，原始文本。現在、複数の人が同時にClaudeインターフェースを呼び出すことはできません（スレッドロックあり），さもないと、各人のClaudeの問い合わせ履歴が相互に侵入します。テキストの翻訳，事前に設定されたプロキシを自動的に使用するするします。"
            self.success = True
        except:
            self.info = "不足している依存関係，Claudeを使用するするする場合は，基本的なpip依存関係以外，実OKする必要があります`pip install -r request_llms/requirements_slackclaude.txt`テキストの翻訳，それからプログラムを再起動してください。"
            self.success = False

    def ready(self):
        return self.claude_model is not None

    async def async_run(self):
        await self.claude_model.open_channel()
        while True:
            # 待つ
            kwargs = self.child.recv()
            question = kwargs["query"]
            history = kwargs["history"]

            # 質問を始める
            prompt = ""

            # 問題
            prompt += question
            print("question:", prompt)

            # 提出
            await self.claude_model.chat(prompt)

            # 応答内容を取得
            async for final, response in self.claude_model.get_reply():
                if not final:
                    print(response)
                    self.child.send(str(response))
                else:
                    # テキストの翻訳
                    slack_msgs = await self.claude_model.get_slack_messages()
                    last_msg = (
                        slack_msgs[-1]["text"]
                        if slack_msgs and len(slack_msgs) > 0
                        else ""
                    )
                    if last_msg:
                        self.child.send(last_msg)
                    print("-------- receive final ---------")
                    self.child.send("[Finish]")

    def run(self):
        """
        この関数はサブプロセスで実OKされます
        """
        # 最初の実OK，パラメータをロードする
        self.success = False
        self.local_history = []
        if (self.claude_model is None) or (not self.success):
            # プロキシ設定
            proxies = get_conf("proxies")
            if proxies is None:
                self.proxies_https = None
            else:
                self.proxies_https = proxies["https"]

            try:
                SLACK_CLAUDE_USER_TOKEN = get_conf("SLACK_CLAUDE_USER_TOKEN")
                self.claude_model = SlackClient(
                    token=SLACK_CLAUDE_USER_TOKEN, proxy=self.proxies_https
                )
                print("原始文本。")
            except:
                self.success = False
                tb_str = "\n```\n" + trimmed_format_exc() + "\n```\n"
                self.child.send(f"[Local Message] Claudeコンポーネントをロードできない。{tb_str}")
                self.child.send("[Fail]")
                self.child.send("[Finish]")
                raise RuntimeError(f"Claudeコンポーネントをロードできない。")

        self.success = True
        try:
            # タスク待機状態に入る
            asyncio.run(self.async_run())
        except Exception:
            tb_str = "\n```\n" + trimmed_format_exc() + "\n```\n"
            self.child.send(f"[Local Message] テキストの翻訳 {tb_str}.")
            self.child.send("[Fail]")
            self.child.send("[Finish]")

    def stream_chat(self, **kwargs):
        """
        この関数はメインプロセスで実OKされます
        """
        self.threadLock.acquire()
        self.parent.send(kwargs)  # 子プロセスにリクエストを送信する
        while True:
            res = self.parent.recv()  # Claudeの返信を待っているフラグメント
            if res == "[Finish]":
                break  # 終了する
            elif res == "[Fail]":
                self.success = False
                break
            else:
                yield res  # Claudeの返信の一部
        self.threadLock.release()


"""
=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
第3部分：メインプロセスが関数インターフェースを統一的に呼び出します
=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
"""
global claude_handle
claude_handle = None


def predict_no_ui_long_connection(
    inputs,
    llm_kwargs,
    history=[],
    sys_prompt="",
    observe_window=None,
    console_slience=False,
):
    """
    Multi-threaded method
    関数の説明については、request_llms/bridge_all.pyを参照してください
    """
    global claude_handle
    if (claude_handle is None) or (not claude_handle.success):
        claude_handle = ClaudeHandle()
        observe_window[0] = load_message + "\n\n" + claude_handle.info
        if not claude_handle.success:
            error = claude_handle.info
            claude_handle = None
            raise RuntimeError(error)

    # sys_promptインターフェースがありません，したがって、履歴にpromptを追加します
    history_feedin = []
    for i in range(len(history) // 2):
        history_feedin.append([history[2 * i], history[2 * i + 1]])

    watch_dog_patience = 5  # ウォッチドッグ (watchdog) の忍耐力, Set for 5 seconds
    response = ""
    observe_window[0] = "[Local Message] Claudeの応答を待っています ..."
    for response in claude_handle.stream_chat(
        query=inputs,
        history=history_feedin,
        system_prompt=sys_prompt,
        max_length=llm_kwargs["max_length"],
        top_p=llm_kwargs["top_p"],
        temperature=llm_kwargs["temperature"],
    ):
        observe_window[0] = preprocess_newbing_out_simple(response)
        if len(observe_window) >= 2:
            if (time.time() - observe_window[1]) > watch_dog_patience:
                raise RuntimeError("プログラムの終了。")
    return preprocess_newbing_out_simple(response)


def predict(
    inputs,
    llm_kwargs,
    plugin_kwargs,
    chatbot,
    history=[],
    system_prompt="",
    stream=True,
    additional_fn=None,
):
    """
    シングルスレッドメソッド
    関数の説明については、request_llms/bridge_all.pyを参照してください
    """
    chatbot.append((inputs, "[Local Message] Claudeの応答を待っています ..."))

    global claude_handle
    if (claude_handle is None) or (not claude_handle.success):
        claude_handle = ClaudeHandle()
        chatbot[-1] = (inputs, load_message + "\n\n" + claude_handle.info)
        yield from update_ui(chatbot=chatbot, history=[])
        if not claude_handle.success:
            claude_handle = None
            return

    if additional_fn is not None:
        from core_functional import handle_core_functionality

        inputs, history = handle_core_functionality(
            additional_fn, inputs, history, chatbot
        )

    history_feedin = []
    for i in range(len(history) // 2):
        history_feedin.append([history[2 * i], history[2 * i + 1]])

    chatbot[-1] = (inputs, "[Local Message] Claudeの応答を待っています ...")
    response = "[Local Message] Claudeの応答を待っています ..."
    yield from update_ui(
        chatbot=chatbot, history=history, msg="Claudeの応答が遅い，すべての応答が完了していません，Please submit a new question after completing it patiently。"
    )
    for response in claude_handle.stream_chat(
        query=inputs, history=history_feedin, system_prompt=system_prompt
    ):
        chatbot[-1] = (inputs, preprocess_newbing_out(response))
        yield from update_ui(
            chatbot=chatbot, history=history, msg="Claudeの応答が遅い，すべての応答が完了していません，Please submit a new question after completing it patiently。"
        )
    if response == "[Local Message] Claudeの応答を待っています ...":
        response = "[Local Message] Claudeの応答が異常です，ページを更新して再試OKしてください ..."
    history.extend([inputs, response])
    logging.info(f"[raw_input] {inputs}")
    logging.info(f"[response] {response}")
    yield from update_ui(chatbot=chatbot, history=history, msg="すべての応答を完了する，新しい問題を提出してください。")
