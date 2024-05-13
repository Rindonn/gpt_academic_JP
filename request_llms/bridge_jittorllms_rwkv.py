
from transformers import AutoModel, AutoTokenizer
import time
import threading
import importlib
from toolbox import update_ui, get_conf
from multiprocessing import Process, Pipe

load_message = "jittorllms has not been loaded，読み込みには時間がかかります。注意，複数のjittorモデルを混在させないでください，それ以外の場合、グラフィックスメモリのオーバーフローが発生し、フリーズが発生する可能性があります，に依存する`config.py`の設定，jittorllmsは大量のメモリを消費します（CPU）またはグラフィックスメモリ（GPU），低スペックのコンピューターがクラッシュする可能性があります......"

#################################################################################
class GetGLMHandle(Process):
    def __init__(self):
        super().__init__(daemon=True)
        self.parent, self.child = Pipe()
        self.jittorllms_model = None
        self.info = ""
        self.local_history = []
        self.success = True
        self.check_dependency()
        self.start()
        self.threadLock = threading.Lock()

    def check_dependency(self):
        try:
            import pandas
            self.info = "Dependency check passed"
            self.success = True
        except:
            from toolbox import trimmed_format_exc
            self.info = r"jittorllmsの依存関係が不足しています，jittorllmsを使用するする場合，基本的なpip依存関係以外，実行する必要があります`pip install -r request_llms/requirements_jittorllms.txt -i https://pypi.jittor.org/simple -I`"+\
                        r"and`git clone https://gitlink.org.cn/jittor/JittorLLMs.git --depth 1 request_llms/jittorllms`jittorllmsの依存関係をインストールするための2つの命令（プロジェクトのルートディレクトリでこれら2つのコマンドを実行する）。" +\
                        r"Warning：jittorllmsの依存関係をインストールすると、既存のpytorch環境が完全に破壊されます，It is recommended to use a docker environment!" + trimmed_format_exc()
            self.success = False

    def ready(self):
        return self.jittorllms_model is not None

    def run(self):
        # Subprocess execution
        # 最初の実行，パラメータをロードする
        def validate_path():
            import os, sys
            dir_name = os.path.dirname(__file__)
            env = os.environ.get("PATH", "")
            os.environ["PATH"] = env.replace('/cuda/bin', '/x/bin')
            root_dir_assume = os.path.abspath(os.path.dirname(__file__) +  '/..')
            os.chdir(root_dir_assume + '/request_llms/jittorllms')
            sys.path.append(root_dir_assume + '/request_llms/jittorllms')
        validate_path() # validate path so you can run from base directory

        def load_model():
            import types
            try:
                if self.jittorllms_model is None:
                    device = get_conf('LOCAL_MODEL_DEVICE')
                    from .jittorllms.models import get_model
                    # availabel_models = ["chatglm", "pangualpha", "llama", "chatrwkv"]
                    args_dict = {'model': 'chatrwkv'}
                    print('self.jittorllms_model = get_model(types.SimpleNamespace(**args_dict))')
                    self.jittorllms_model = get_model(types.SimpleNamespace(**args_dict))
                    print('done get model')
            except:
                self.child.send('[Local Message] jittorllmsのパラメータを正常にロードできません。')
                raise RuntimeError("jittorllmsのパラメータを正常にロードできません！")
        print('load_model')
        load_model()

        # タスク待機状態に入る
        print('タスク待機状態に入る')
        while True:
            # タスク待機状態に入る
            kwargs = self.child.recv()
            query = kwargs['query']
            history = kwargs['history']
            # リセットしますか
            if len(self.local_history) > 0 and len(history)==0:
                print('リセットをトリガーする')
                self.jittorllms_model.reset()
            self.local_history.append(query)

            print('メッセージを受信しました，リクエストを開始する')
            try:
                for response in self.jittorllms_model.stream_chat(query, history):
                    print(response)
                    self.child.send(response)
            except:
                from toolbox import trimmed_format_exc
                print(trimmed_format_exc())
                self.child.send('[Local Message] Call jittorllms fail.')
            # リクエスト処理が終了しました，次のループを開始する
            self.child.send('[Finish]')

    def stream_chat(self, **kwargs):
        # Main process execution
        self.threadLock.acquire()
        self.parent.send(kwargs)
        while True:
            res = self.parent.recv()
            if res != '[Finish]':
                yield res
            else:
                break
        self.threadLock.release()

global rwkv_glm_handle
rwkv_glm_handle = None
#################################################################################
def predict_no_ui_long_connection(inputs, llm_kwargs, history=[], sys_prompt="", observe_window=[], console_slience=False):
    """
        Multi-threaded method
        関数の説明については、request_llms/bridge_all.pyを参照してください
    """
    global rwkv_glm_handle
    if rwkv_glm_handle is None:
        rwkv_glm_handle = GetGLMHandle()
        if len(observe_window) >= 1: observe_window[0] = load_message + "\n\n" + rwkv_glm_handle.info
        if not rwkv_glm_handle.success:
            error = rwkv_glm_handle.info
            rwkv_glm_handle = None
            raise RuntimeError(error)

    # jittorllmsにはsys_promptインターフェースがありません，したがって、履歴にpromptを追加します
    history_feedin = []
    for i in range(len(history)//2):
        history_feedin.append([history[2*i], history[2*i+1]] )

    watch_dog_patience = 5 # ウォッチドッグ (watchdog) の忍耐力, Set for 5 seconds
    response = ""
    for response in rwkv_glm_handle.stream_chat(query=inputs, history=history_feedin, system_prompt=sys_prompt, max_length=llm_kwargs['max_length'], top_p=llm_kwargs['top_p'], temperature=llm_kwargs['temperature']):
        print(response)
        if len(observe_window) >= 1:  observe_window[0] = response
        if len(observe_window) >= 2:
            if (time.time()-observe_window[1]) > watch_dog_patience:
                raise RuntimeError("プログラムの終了。")
    return response



def predict(inputs, llm_kwargs, plugin_kwargs, chatbot, history=[], system_prompt='', stream = True, additional_fn=None):
    """
        シングルスレッドメソッド
        関数の説明については、request_llms/bridge_all.pyを参照してください
    """
    chatbot.append((inputs, ""))

    global rwkv_glm_handle
    if rwkv_glm_handle is None:
        rwkv_glm_handle = GetGLMHandle()
        chatbot[-1] = (inputs, load_message + "\n\n" + rwkv_glm_handle.info)
        yield from update_ui(chatbot=chatbot, history=[])
        if not rwkv_glm_handle.success:
            rwkv_glm_handle = None
            return

    if additional_fn is not None:
        from core_functional import handle_core_functionality
        inputs, history = handle_core_functionality(additional_fn, inputs, history, chatbot)

    # 履歴情報の処理
    history_feedin = []
    for i in range(len(history)//2):
        history_feedin.append([history[2*i], history[2*i+1]] )

    # jittorllmsの返信を受け取り始める
    response = "[Local Message] jittorllmsの応答を待っています ..."
    for response in rwkv_glm_handle.stream_chat(query=inputs, history=history_feedin, system_prompt=system_prompt, max_length=llm_kwargs['max_length'], top_p=llm_kwargs['top_p'], temperature=llm_kwargs['temperature']):
        chatbot[-1] = (inputs, response)
        yield from update_ui(chatbot=chatbot, history=history)

    # 出力をまとめる
    if response == "[Local Message] jittorllmsの応答を待っています ...":
        response = "[Local Message] jittorllms応答異常 ..."
    history.extend([inputs, response])
    yield from update_ui(chatbot=chatbot, history=history)
