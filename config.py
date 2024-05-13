"""
    以下のすべての設定は環境変数を使用するして上書きすることもサポートしています，原始文本。
    優先度を読み取る：環境変数 > config_private.py > config.py
    --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
    All the following configurations also support using environment variables to override,
    and the environment variable configuration format can be seen in docker-compose.yml.
    Configuration reading priority: environment variable > config_private.py > config.py
"""

# [step 1]>> API_KEY = "sk-123456789xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx123456789"。テキストの翻訳，組織を入力する必要があります（org-123456789abcdefghijklmnoの形式），下にスクロールしてください，API_ORGの設定項目を検索します
API_KEY = ""    # Multiple API-KEYs can be filled in at the same time，英語のコンマで区切る，例えばAPI_KEY = "sk-openaikey1,sk-openaikey2,fkxxxx-api2dkey3,azure-apikey4"


# [step 2]>> Trueに変更してプロキシを適用する，If deployed directly on overseas servers，Do not modify here；如果使用する本地或なし地域限制的大模型時，此处也No modification needed
USE_PROXY = False
if USE_PROXY:
    """
    プロキシネットワークのアドレス，打开你的代理软件查看代理プロトコル(socks5h / http)、アドレス(localhost)およびポート(11284)
    入力フォーマットは [プロトコル]://  [Address] :[ポート]，記入する前に、USE_PROXYをTrueに変更することを忘れないでください，If deployed directly on overseas servers，Do not modify here
            <設定チュートリアル＆ビデオチュートリアル> https://github.com/binary-husky/gpt_academic/issues/1>
    [プロトコル] 一般的なプロトコルはsocks5h/http以外ありません; たとえば、v2 ** yとss *のデフォルトのローカルプロトコルはsocks5hです; cl ** hのデフォルトのローカルプロトコルはhttpです
    [Address] 填localhostまたは127.0.0.1（localhostは、プロキシソフトウェアがローカルマシンにインストールされていることを意味します）
    [ポート] プロキシソフトウェアの設定で検索する。異なるプロキシソフトウェアのインターフェースは異なりますが，しかし、ポート番号は常に目立つ場所にある必要があります
    """
    proxies = {
        #          [プロトコル]://  [Address]  :[ポート]
        "http":  "socks5h://localhost:11284",  # 再例えば  "http":  "http://127.0.0.1:7890",
        "https": "socks5h://localhost:11284",  # 再例えば  "https": "http://127.0.0.1:7890",
    }
else:
    proxies = None

# [step 3]>> モデルの選択は (注意: LLM_MODELはデフォルトで選択されたモデルです, それはAVAIL_LLM_MODELSリストに含まれている必要があります )
LLM_MODEL = "gpt-3.5-turbo-16k" # 選択可能 ↓↓↓
AVAIL_LLM_MODELS = ["gpt-4-1106-preview", "gpt-4-turbo-preview", "gpt-4-vision-preview",
                    "gpt-3.5-turbo-1106", "gpt-3.5-turbo-16k", "gpt-3.5-turbo", "azure-gpt-3.5",
                    "gpt-4", "gpt-4-32k", "azure-gpt-4", "glm-4", "glm-3-turbo",
                    "gemini-pro", "chatglm3"
                    ]
# --- --- --- ---
# P.S. 其他可用的模型还含む
# AVAIL_LLM_MODELS = [
#   "qianfan", "deepseekcoder",
#   "spark", "sparkv2", "sparkv3", "sparkv3.5",
#   "qwen-turbo", "qwen-plus", "qwen-max", "qwen-local",
#   "moonshot-v1-128k", "moonshot-v1-32k", "moonshot-v1-8k",
#   "gpt-3.5-turbo-0613", "gpt-3.5-turbo-16k-0613", "gpt-3.5-turbo-0125"
#   "claude-3-sonnet-20240229","claude-3-opus-20240229", "claude-2.1", "claude-instant-1.2",
#   "moss", "llama2", "chatglm_onnx", "internlm", "jittorllms_pangualpha", "jittorllms_llama",
#   "yi-34b-chat-0205", "yi-34b-chat-200k"
# ]
# --- --- --- ---
# さらに，为了更灵活地接入one-api多模型管理界面，您还可以在接入one-api時，
# 使用する"one-api-*"テキストの翻訳直接使用する非标准方式接入的模型，例えば
# AVAIL_LLM_MODELS = ["one-api-claude-3-sonnet-20240229(max_token=100000)"]
# --- --- --- ---


# --------------- 以下の設定で体験を最適化できます ---------------

# URLを再度リダイレクトする，Implement the function of changing API_URL（高リスクの設定！通常は変更しないでください！この設定を変更することで，You will completely expose your API-KEY and conversation privacy to the intermediary you set!）
# フォーマット: API_URL_REDIRECT = {"https://api.openai.com/v1/chat/completions": "在这里填写重定向的api.openai.com的URL"}
# 例を挙げる: API_URL_REDIRECT = {"https://api.openai.com/v1/chat/completions": "https://reverse-proxy-url/v1/chat/completions"}
API_URL_REDIRECT = {}


# マルチスレッド関数プラグインで，デフォルトでOpenAIに同時にアクセスできるスレッド数はいくつですか。無料トライアルユーザーの制限は、1分あたり3回です，Pay-as-you-goユーザーの制限は1分間に3500回です
# 一言で言えば：無料（5ドル）ユーザーが3を入力する，OpenAIにクレジットカードをバインドしているユーザーは、16以上を入力できます。制限を引き上げるには、クエリを確認してください：https://platform.openai.com/docs/guides/rate-limits/overview
DEFAULT_WORKER_NUM = 3


# 色彩主题, オプション ["Default", "Chuanhu-Small-and-Beautiful", "High-Contrast"]
# 更多主题, 请查阅Gradio主题商店: https://huggingface.co/spaces/gradio/theme-gallery オプション ["Gstaff/Xkcd", "NoCrypt/Miku", ...]
THEME = "Default"
AVAIL_THEMES = ["Default", "Chuanhu-Small-and-Beautiful", "High-Contrast", "Gstaff/Xkcd", "NoCrypt/Miku"]


# #的系统ヒント词（system prompt）
INIT_SYS_PROMPT = "Serve me as a writing and programming assistant."


# Height of the conversation window （仅在LAYOUT="TOP-DOWN"時生效）
CHATBOT_HEIGHT = 1115


# コードのハイライト
CODE_HIGHLIGHT = True


# ウィンドウレイアウト
LAYOUT = "LEFT-RIGHT"   # "LEFT-RIGHT"（左右レイアウト） # "TOP-DOWN"（上下布局）


# ダークモード/ライトモード
DARK_MODE = True


# OpenAIにリクエストを送信した後，タイムアウトとして判定するまでの待機時間
TIMEOUT_SECONDS = 30


# Webページのポート, -1 represents a random port
WEB_PORT = -1


# OpenAIが応答しない場合（ネットワークの遅延、プロキシの失敗、KEYの無効化），再試行回数の制限
MAX_RETRY = 2


# プラグイン分类#选项
DEFAULT_FN_GROUPS = ['对话', '编程', '学术', '智能体']


# 定义界面上“複数のGPTモデルについて問い合わせる”プラグイン应该使用する哪些模型，からお願いしますAVAIL_LLM_MODELS中选择，并在不同模型之间用`&`间隔，例えば"gpt-3.5-turbo&chatglm3&azure-gpt-4"
MULTI_QUERY_LLM_MODELS = "gpt-3.5-turbo&chatglm3"


# 选择本地模型变体（只有当AVAIL_LLM_MODELS包含了对应本地模型時，才会起作用）
# 如果你选择Qwen系列的模型，那么请在下面的QWEN_MODEL_SELECTION中指定具体的模型
# 也可以是具体的模型路径
QWEN_LOCAL_MODEL_SELECTION = "Qwen/Qwen-1_8B-Chat-Int8"


# 接入通义千问在线大模型 https://dashscope.console.aliyun.com/
DASHSCOPE_API_KEY = "" # 阿里灵积云API_KEY


# 百度千帆（LLM_MODEL="qianfan"）
BAIDU_CLOUD_API_KEY = ''
BAIDU_CLOUD_SECRET_KEY = ''
BAIDU_CLOUD_QIANFAN_MODEL = 'ERNIE-Bot'    # オプション "ERNIE-Bot-4"(文心大模型4.0), "ERNIE-Bot"(文心一言), "ERNIE-Bot-turbo", "BLOOMZ-7B", "Llama-2-70B-Chat", "Llama-2-13B-Chat", "Llama-2-7B-Chat"


# ChatGLM2ファインチューニングモデルを使用するする場合，请把 LLM_MODEL="chatglmft"，并在此处指定模型路径
CHATGLM_PTUNING_CHECKPOINT = "" # 例えば"/home/hmp/ChatGLM2-6B/ptuning/output/6b-pt-128-1e-2/checkpoint-100"


# ローカルLLMモデルの実行テキストの翻訳、例えばChatGLM CPU/GPU
LOCAL_MODEL_DEVICE = "cpu" # オプション "cuda"
LOCAL_MODEL_QUANT = "FP16" # # "FP16" "INT4" 启用量化INT4版本 "INT8" 启用量化INT8版本


# Set the parallel thread number of gradio（No modification needed）
CONCURRENT_COUNT = 100


# テキストの翻訳
AUTO_CLEAR_TXT = False


# live2dの装飾を追加する
ADD_WAIFU = False


# ユーザー名とパスワードを設定する（No modification needed）（関連機能は不安定です，gradioバージョンとネットワークに関連しています，ローカルで使用するする場合はお勧めしません）
# [("username", "password"), ("username2", "password2"), ...]
AUTHENTICATION = []


# 2次パスで実行する必要がある場合（通常の場合，修正しないでください!!）（有効にするには、main.pyを変更する必要があります！）
CUSTOM_PATH = "/"


# HTTPS 秘钥and证书（No modification needed）
SSL_KEYFILE = ""
SSL_CERTFILE = ""


# テキストの翻訳，openaiの公式KEYは組織コードと一緒に必要です（形式はorg-xxxxxxxxxxxxxxxxxxxxxxxxのようです）使用する
API_ORG = ""


# テキストの翻訳，使用するテキストの翻訳の詳細については、request_llms/README.mdを参照してください
SLACK_CLAUDE_BOT_ID = ''
SLACK_CLAUDE_USER_TOKEN = ''


# 如果需要使用するAZURE（テキストの翻訳一：单piecesazure模型部署）详情请见额外文档 docs\use_azure.md
AZURE_ENDPOINT = "https://你亲手写的api名称.openai.azure.com/"
AZURE_API_KEY = "Azure OpenAI APIのキーを入力してください"    # API_KEYの場所に直接入力することをお勧めします，このオプションはまもなく廃止されます
AZURE_ENGINE = "あなたが手書きしたデプロイ名を入力してください"            # ドキュメントを読む


# 如果需要使用するAZURE（テキストの翻訳二：多piecesazure模型部署+动态切换）详情请见额外文档 docs\use_azure.md
AZURE_CFG_ARRAY = {}


# 阿里云实時语音识别 配置难度较高
# 参考 https://github.com/binary-husky/gpt_academic/blob/master/docs/use_audio.md
ENABLE_AUDIO = False
ALIYUN_TOKEN=""     # テキストの翻訳
ALIYUN_APPKEY=""    # 例えば RoPlZrM88DnAFkZK
ALIYUN_ACCESSKEY="" # （記入する必要はありません）
ALIYUN_SECRET=""    # （記入する必要はありません）


# 接入讯飞星火大模型 https://console.xfyun.cn/services/iat
XFYUN_APPID = "00000000"
XFYUN_API_SECRET = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
XFYUN_API_KEY = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


# 接入智谱大模型
ZHIPUAI_API_KEY = ""
ZHIPUAI_MODEL = "" # 此选项已废弃，不再需要填写


# Claude API KEY
ANTHROPIC_API_KEY = ""


# 月之暗面 API KEY
MOONSHOT_API_KEY = ""


# 零一万物(Yi Model) API KEY
YIMODEL_API_KEY = ""


# Mathpix 拥有执行PDF的OCR功能，但是需要注册账号
MATHPIX_APPID = ""
MATHPIX_APPKEY = ""


# テキストの翻訳
CUSTOM_API_KEY_PATTERN = ""


# Google Gemini API-Key
GEMINI_API_KEY = ''


# HUGGINGFACE的TOKEN，下载LLAMA時起作用 https://huggingface.co/docs/hub/security-tokens
HUGGINGFACE_ACCESS_TOKEN = "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"


# GROBID服务器Address（填写多pieces可以均衡负载），用于高质量地读取PDF文档
# 获取テキストの翻訳：复制以下空间https://huggingface.co/spaces/qingxu98/grobid，设为public，然后GROBID_URL = "https://(你的hf用户名如qingxu98)-(你的填写的空间名如grobid).hf.space"
GROBID_URLS = [
    "https://qingxu98-grobid.hf.space","https://qingxu98-grobid2.hf.space","https://qingxu98-grobid3.hf.space",
    "https://qingxu98-grobid4.hf.space","https://qingxu98-grobid5.hf.space", "https://qingxu98-grobid6.hf.space",
    "https://qingxu98-grobid7.hf.space", "https://qingxu98-grobid8.hf.space",
]


# 是否允许通过自然语言描述修改本页の設定，该功能具有一定的危险性，#关闭
ALLOW_RESET_CONFIG = False


# 在使用するAutoGenプラグイン時，是否使用するDocker容器运行代码
AUTOGEN_USE_DOCKER = False


# 临時的上传文件夹位置，请勿修改
PATH_PRIVATE_UPLOAD = "private_upload"


# 日志文件夹的位置，请勿修改
PATH_LOGGING = "gpt_log"


# 除了连接OpenAI之外，还有哪些场合允许使用する代理，请勿修改
WHEN_TO_USE_PROXY = ["Download_LLM", "Download_Gradio_Theme", "Connect_Grobid",
                     "Warmup_Modules", "Nougat_Download", "AutoGen"]


# *实验性功能*: 自动检测并屏蔽失效的KEY，请勿使用する
BLOCK_INVALID_APIKEY = False


# 启用プラグイン热加载
PLUGIN_HOT_RELOAD = False


# 自定义按钮的最大数量限制
NUM_CUSTOM_BASIC_BTN = 4



"""
--------------- 配置关联关系言う明 ---------------

在线大模型配置关联关系示意图
│
├── "gpt-3.5-turbo" 等openai模型
│   ├── API_KEY
│   ├── CUSTOM_API_KEY_PATTERN（不常用）
│   ├── API_ORG（不常用）
│   └── API_URL_REDIRECT（不常用）
│
├── "azure-gpt-3.5" 等azure模型（单piecesazure模型，不需要动态切换）
│   ├── API_KEY
│   ├── AZURE_ENDPOINT
│   ├── AZURE_API_KEY
│   ├── AZURE_ENGINE
│   └── API_URL_REDIRECT
│
├── "azure-gpt-3.5" 等azure模型（多piecesazure模型，需要动态切换，高優先级）
│   └── AZURE_CFG_ARRAY
│
├── "spark" 星火认知大模型 spark & sparkv2
│   ├── XFYUN_APPID
│   ├── XFYUN_API_SECRET
│   └── XFYUN_API_KEY
│
├── "claude-3-opus-20240229" 等claude模型
│   └── ANTHROPIC_API_KEY
│
├── "stack-claude"
│   ├── SLACK_CLAUDE_BOT_ID
│   └── SLACK_CLAUDE_USER_TOKEN
│
├── "qianfan" 百度千帆大模型库
│   ├── BAIDU_CLOUD_QIANFAN_MODEL
│   ├── BAIDU_CLOUD_API_KEY
│   └── BAIDU_CLOUD_SECRET_KEY
│
├── "glm-4", "glm-3-turbo", "zhipuai" 智谱AI大模型
│   └── ZHIPUAI_API_KEY
│
├── "yi-34b-chat-0205", "yi-34b-chat-200k" 等零一万物(Yi Model)大模型
│   └── YIMODEL_API_KEY
│
├── "qwen-turbo" 等通义千问大模型
│   └──  DASHSCOPE_API_KEY
│
├── "Gemini"
│   └──  GEMINI_API_KEY
│
└── "one-api-...(max_token=...)" 用一种更方便的方式接入one-api多模型管理界面
    ├── AVAIL_LLM_MODELS
    ├── API_KEY
    └── API_URL_REDIRECT


本地大模型示意图
│
├── "chatglm3"
├── "chatglm"
├── "chatglm_onnx"
├── "chatglmft"
├── "internlm"
├── "moss"
├── "jittorllms_pangualpha"
├── "jittorllms_llama"
├── "deepseekcoder"
├── "qwen-local"
├──  RWKV的支持见Wiki
└── "llama2"


用户图形界面布局依赖关系示意图
│
├── CHATBOT_HEIGHT Height of the conversation window
├── CODE_HIGHLIGHT コードのハイライト
├── LAYOUT ウィンドウレイアウト
├── DARK_MODE ダークモード/ライトモード
├── DEFAULT_FN_GROUPS プラグイン分类#选项
├── THEME 色彩主题
├── AUTO_CLEAR_TXT テキストの翻訳
├── ADD_WAIFU live2dの装飾を追加する
└── ALLOW_RESET_CONFIG 是否允许通过自然语言描述修改本页の設定，该功能具有一定的危险性


プラグイン在线服务配置依赖关系示意图
│
├── 语音功能
│   ├── ENABLE_AUDIO
│   ├── ALIYUN_TOKEN
│   ├── ALIYUN_APPKEY
│   ├── ALIYUN_ACCESSKEY
│   └── ALIYUN_SECRET
│
└── PDF文档精准解析
    ├── GROBID_URLS
    ├── MATHPIX_APPID
    └── MATHPIX_APPKEY


"""