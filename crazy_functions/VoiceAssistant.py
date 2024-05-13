from toolbox import update_ui
from toolbox import CatchException, get_conf, markdown_convertion
from crazy_functions.crazy_utils import input_clipping
from crazy_functions.agent_fns.watchdog import WatchDog
from request_llms.bridge_all import predict_no_ui_long_connection
import threading, time
import numpy as np
from .live_audio.aliyunASR import AliyunASR
import json
import re


def chatbot2history(chatbot):
    history = []
    for c in chatbot:
        for q in c:
            if q in ["[ 请讲话 ]", "[ テキストの翻訳 ]", "[ 質問が完了するのをお待ちしています ]"]:
                continue
            elif q.startswith("[ 質問が完了するのをお待ちしています ]"):
                continue
            else:
                history.append(q.strip('<div class="markdown-body">').strip('</div>').strip('<p>').strip('</p>'))
    return history

def visualize_audio(chatbot, audio_shape):
    if len(chatbot) == 0: chatbot.append(["[ 请讲话 ]", "[ 質問が完了するのをお待ちしています ]"])
    chatbot[-1] = list(chatbot[-1])
    p1 = '「'
    p2 = '」'
    chatbot[-1][-1] = re.sub(p1+r'(.*)'+p2, '', chatbot[-1][-1])
    chatbot[-1][-1] += (p1+f"`{audio_shape}`"+p2)

class AsyncGptTask():
    def __init__(self) -> None:
        self.observe_future = []
        self.observe_future_chatbot_index = []

    def gpt_thread_worker(self, i_say, llm_kwargs, history, sys_prompt, observe_window, index):
        try:
            MAX_TOKEN_ALLO = 2560
            i_say, history = input_clipping(i_say, history, max_token_limit=MAX_TOKEN_ALLO)
            gpt_say_partial = predict_no_ui_long_connection(inputs=i_say, llm_kwargs=llm_kwargs, history=history, sys_prompt=sys_prompt,
                                                            observe_window=observe_window[index], console_slience=True)
        except ConnectionAbortedError as token_exceed_err:
            print('少なくとも1つのスレッドタスクトークンがオーバーフローして失敗します', e)
        except Exception as e:
            print('少なくとも1つのスレッドタスクが予期しない失敗をした', e)

    def add_async_gpt_task(self, i_say, chatbot_index, llm_kwargs, history, system_prompt):
        self.observe_future.append([""])
        self.observe_future_chatbot_index.append(chatbot_index)
        cur_index = len(self.observe_future)-1
        th_new = threading.Thread(target=self.gpt_thread_worker, args=(i_say, llm_kwargs, history, system_prompt, self.observe_future, cur_index))
        th_new.daemon = True
        th_new.start()

    def update_chatbot(self, chatbot):
        for of, ofci in zip(self.observe_future, self.observe_future_chatbot_index):
            try:
                chatbot[ofci] = list(chatbot[ofci])
                chatbot[ofci][1] = markdown_convertion(of[0])
            except:
                self.observe_future = []
                self.observe_future_chatbot_index = []
        return chatbot

class InterviewAssistant(AliyunASR):
    def __init__(self):
        self.capture_interval = 0.5 # second
        self.stop = False
        self.parsed_text = ""   # 下pieces句子中已经言う完的部分, 由 test_on_result_chg() 写入
        self.parsed_sentence = ""   # 某段话的整pieces句子, 由 test_on_sentence_end() 写入
        self.buffered_sentence = ""    #
        self.audio_shape = ""   # 音频的可视化表现, 由 audio_convertion_thread() 写入
        self.event_on_result_chg = threading.Event()
        self.event_on_entence_end = threading.Event()
        self.event_on_commit_question = threading.Event()

    def __del__(self):
        self.stop = True
        self.stop_msg = ""
        self.commit_wd.kill_dog = True
        self.plugin_wd.kill_dog = True

    def init(self, chatbot):
        # オーディオキャプチャスレッドを初期化します
        self.captured_audio = np.array([])
        self.keep_latest_n_second = 10
        self.commit_after_pause_n_second = 2.0
        self.ready_audio_flagment = None
        self.stop = False
        self.plugin_wd = WatchDog(timeout=5, bark_fn=self.__del__, msg="プログラムの終了")
        self.aut = threading.Thread(target=self.audio_convertion_thread, args=(chatbot._cookies['uuid'],))
        self.aut.daemon = True
        self.aut.start()
        # th2 = threading.Thread(target=self.audio2txt_thread, args=(chatbot._cookies['uuid'],))
        # th2.daemon = True
        # th2.start()

    def no_audio_for_a_while(self):
        if len(self.buffered_sentence) < 7: # 1つの文が7文字未満の場合，一時的に提出しない
            self.commit_wd.begin_watch()
        else:
            self.event_on_commit_question.set()

    def begin(self, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt):
        # main plugin function
        self.init(chatbot)
        chatbot.append(["[ 请讲话 ]", "[ 質問が完了するのをお待ちしています ]"])
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        self.plugin_wd.begin_watch()
        self.agt = AsyncGptTask()
        self.commit_wd = WatchDog(timeout=self.commit_after_pause_n_second, bark_fn=self.no_audio_for_a_while, interval=0.2)
        self.commit_wd.begin_watch()

        while not self.stop:
            self.event_on_result_chg.wait(timeout=0.25)  # run once every 0.25 second
            chatbot = self.agt.update_chatbot(chatbot)   # 置き換える子スレッド的gpt结果写入chatbot
            history = chatbot2history(chatbot)
            yield from update_ui(chatbot=chatbot, history=history)      # 画面を更新する
            self.plugin_wd.feed()

            if self.event_on_result_chg.is_set():
                # called when some words have finished
                self.event_on_result_chg.clear()
                chatbot[-1] = list(chatbot[-1])
                chatbot[-1][0] = self.buffered_sentence + self.parsed_text
                history = chatbot2history(chatbot)
                yield from update_ui(chatbot=chatbot, history=history)  # 画面を更新する
                self.commit_wd.feed()

            if self.event_on_entence_end.is_set():
                # called when a sentence has ended
                self.event_on_entence_end.clear()
                self.parsed_text = self.parsed_sentence
                self.buffered_sentence += self.parsed_text
                chatbot[-1] = list(chatbot[-1])
                chatbot[-1][0] = self.buffered_sentence
                history = chatbot2history(chatbot)
                yield from update_ui(chatbot=chatbot, history=history)  # 画面を更新する

            if self.event_on_commit_question.is_set():
                # called when a question should be commited
                self.event_on_commit_question.clear()
                if len(self.buffered_sentence) == 0: raise RuntimeError

                self.commit_wd.begin_watch()
                chatbot[-1] = list(chatbot[-1])
                chatbot[-1] = [self.buffered_sentence, "[ テキストの翻訳 ]"]
                yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
                # add gpt task 创建子スレッド请求gpt，スレッドのブロックを回避する
                history = chatbot2history(chatbot)
                self.agt.add_async_gpt_task(self.buffered_sentence, len(chatbot)-1, llm_kwargs, history, system_prompt)

                self.buffered_sentence = ""
                chatbot.append(["[ 请讲话 ]", "[ 質問が完了するのをお待ちしています ]"])
                yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する

            if not self.event_on_result_chg.is_set() and not self.event_on_entence_end.is_set() and not self.event_on_commit_question.is_set():
                visualize_audio(chatbot, self.audio_shape)
                yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する

        if len(self.stop_msg) != 0:
            raise RuntimeError(self.stop_msg)



@CatchException
def VoiceAssistant(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    # pip install -U openai-whisper
    chatbot.append(["対話アシスタント関数プラグイン：使用する時，両手をマウスとキーボードから離してください", "オーディオアシスタント, お話をお聞きしています（「停止」ボタンをクリックしてプログラムを終了できます）..."])
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する

    # 依存関係のインポートを試みる，依存関係が不足している場合，インストールの提案を行います
    try:
        import nls
        from scipy import io
    except:
        chatbot.append(["テキストの翻訳", "このモジュールを使用するするには、追加の依存関係が必要です, インストールテキストの翻訳:```pip install --upgrade aliyun-python-sdk-core==2.13.3 pyOpenSSL webrtcvad scipy git+https://github.com/aliyun/alibabacloud-nls-python-sdk.git```"])
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return

    APPKEY = get_conf('ALIYUN_APPKEY')
    if APPKEY == "":
        chatbot.append(["テキストの翻訳", "阿里雲の音声認識のAPPKEYとTOKENがありません, 详情见https://help.aliyun.com/document_detail/450255.html"])
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
        return

    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する
    ia = InterviewAssistant()
    yield from ia.begin(llm_kwargs, plugin_kwargs, chatbot, history, system_prompt)

