from toolbox import HotReload  # HotReloadの意味はホット更新です，関数プラグインを変更した後，プログラムを再起動する必要はありません，コードが直接有効になる
from toolbox import trimmed_format_exc


def get_crazy_functions():
    from crazy_functions.ReadArticleWriteSummary import ReadArticleWriteSummary
    from crazy_functions.GenerateFunctionComments import BatchGenerateFunctionComments
    from crazy_functions.ParseProjectSourceCode import ParseProjectItself
    from crazy_functions.ParseProjectSourceCode import ParsePythonProject
    from crazy_functions.ParseProjectSourceCode import AnalyzeAMatlabProject
    from crazy_functions.ParseProjectSourceCode import ParseCProjectHeaderFiles
    from crazy_functions.ParseProjectSourceCode import ParseCProject
    from crazy_functions.ParseProjectSourceCode import ParseGolangProject
    from crazy_functions.ParseProjectSourceCode import ParseRustProject
    from crazy_functions.ParseProjectSourceCode import ParseJavaProject
    from crazy_functions.ParseProjectSourceCode import ParseFrontendProject
    from crazy_functions.AdvancedFunctionTemplate import HighOrderFunctionTemplateFunctions
    from crazy_functions.FullTextProofreadingForLatex import EnglishProofreadingForLatex
    from crazy_functions.InquiryMultipleLargeLanguageModels import SimultaneousInquiry
    from crazy_functions.ParseProjectSourceCode import ParsingLuaProject
    from crazy_functions.ParseProjectSourceCode import ParsingCSharpProject
    from crazy_functions.SummarizingWordDocuments import SummarizingWordDocuments
    from crazy_functions.ParsingJupyterNotebook import ParsingIpynbFiles
    from crazy_functions.ConversationHistoryArchive import ConversationHistoryArchive
    from crazy_functions.ConversationHistoryArchive import LoadConversationHistoryArchive
    from crazy_functions.ConversationHistoryArchive import DeleteAllLocalConversationHistoryRecords
    from crazy_functions.Accessibility import ClearCache
    from crazy_functions.BatchTranslateMarkdown import TranslateMarkdownFromEnglishToChinese
    from crazy_functions.BatchSummarizePDFDocuments import BatchSummarizePDFDocuments
    from crazy_functions.BatchTranslatePDFDocuments_MultiThreaded import BatchTranslatePDFDocuments
    from crazy_functions.GoogleSearchAssistant import GoogleSearchAssistant
    from crazy_functions.UnderstandPdfDocumentContent import UnderstandPdfDocumentContentStandardFileInput
    from crazy_functions.FullTextProofreadingForLatex import LatexChineseProofreading
    from crazy_functions.FullTextProofreadingForLatex import LatexEnglishCorrection
    from crazy_functions.BatchTranslateMarkdown import MarkdownChineseToEnglish
    from crazy_functions.VoidTerminal import VoidTerminal
    from crazy_functions.GenerateMultipleMermaidCharts import GenerateMultipleMermaidCharts

    function_plugins = {
        "VoidTerminal": {
            "Group": "对话|编程|学术|智能体",
            "Color": "stop",
            "AsButton": True,
            "Function": HotReload(VoidTerminal),
        },
        "テキストの翻訳": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": True,
            "Info": "ParsePythonProject的所有源文件(.py) | 入力パラメータ为路径",
            "Function": HotReload(ParsePythonProject),
        },
        "LoadConversationHistoryArchive（アーカイブをアップロードするか、パスを入力してください）": {
            "Group": "对话",
            "Color": "stop",
            "AsButton": False,
            "Info": "LoadConversationHistoryArchive | 入力パラメータ为路径",
            "Function": HotReload(LoadConversationHistoryArchive),
        },
        "DeleteAllLocalConversationHistoryRecords（谨慎操作）": {
            "Group": "对话",
            "AsButton": False,
            "Info": "DeleteAllLocalConversationHistoryRecords，谨慎操作 | 不需要入力パラメータ",
            "Function": HotReload(DeleteAllLocalConversationHistoryRecords),
        },
        "クリア所有缓存文件（谨慎操作）": {
            "Group": "对话",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "クリア所有缓存文件，谨慎操作 | 不需要入力パラメータ",
            "Function": HotReload(ClearCache),
        },
        "GenerateMultipleMermaidCharts(从当前对话或路径(.pdf/.md/.docx)中生产图表）": {
            "Group": "对话",
            "Color": "stop",
            "AsButton": False,
            "Info" : "基于当前对话或文件GenerateMultipleMermaidCharts,图表类型由模型判断",
            "Function": HotReload(GenerateMultipleMermaidCharts),
            "AdvancedArgs": True,
            "ArgsReminder": "请入力图类型对应的数字,不入力则为模型自行判断:1-流程图,2-序列图,3-类图,4-饼图,5-甘特图,6-ステータス图,7-实体关系图,8-象限ヒント图,9-思维导图",
        },
        "Word文書を一括で要約する": {
            "Group": "学术",
            "Color": "stop",
            "AsButton": True,
            "Info": "バッチ量SummarizingWordDocuments | 入力パラメータ为路径",
            "Function": HotReload(SummarizingWordDocuments),
        },
        "解析整piecesMatlab项目": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": False,
            "Info": "AnalyzeAMatlabProject的所有源文件(.m) | 入力パラメータ为路径",
            "Function": HotReload(AnalyzeAMatlabProject),
        },
        "C++プロジェクトのヘッダーファイル全体を解析する": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "解析一piecesC++项目的所有头文件(.h/.hpp) | 入力パラメータ为路径",
            "Function": HotReload(ParseCProjectHeaderFiles),
        },
        "C++プロジェクト全体を解析する（.cpp/.hpp/.c/.h）": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "解析一piecesC++项目的所有源文件（.cpp/.hpp/.c/.h）| 入力パラメータ为路径",
            "Function": HotReload(ParseCProject),
        },
        "Goプロジェクト全体を解析する": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "解析一piecesGo项目的所有源文件 | 入力パラメータ为路径",
            "Function": HotReload(ParseGolangProject),
        },
        "Rustプロジェクト全体を解析する": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "ParseRustProject的所有源文件 | 入力パラメータ为路径",
            "Function": HotReload(ParseRustProject),
        },
        "Javaプロジェクト全体を解析する": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "ParseJavaProject的所有源文件 | 入力パラメータ为路径",
            "Function": HotReload(ParseJavaProject),
        },
        "フロントエンドプロジェクト全体を解析する（js,ts,CSSなど）": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "ParseFrontendProject的所有源文件（js,ts,CSSなど） | 入力パラメータ为路径",
            "Function": HotReload(ParseFrontendProject),
        },
        "Luaプロジェクト全体を解析する": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "ParsingLuaProject的所有源文件 | 入力パラメータ为路径",
            "Function": HotReload(ParsingLuaProject),
        },
        "CSharpプロジェクト全体を解析する": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "ParsingCSharpProject的所有源文件 | 入力パラメータ为路径",
            "Function": HotReload(ParsingCSharpProject),
        },
        "Jupyter Notebookファイルの解析": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": False,
            "Info": "Jupyter Notebookファイルの解析 | 入力パラメータ为路径",
            "Function": HotReload(ParsingIpynbFiles),
            "AdvancedArgs": True,  # 呼び出し時，高度なパラメータ入力エリアを呼び出す（デフォルトはFalse）
            "ArgsReminder": "0を入力する場合，したがって、ノートブックのMarkdownブロックを解析しない",  # 高度なパラメータ入力エリアの表示ヒント
        },
        "Tex論文を読んで要約を書く": {
            "Group": "学术",
            "Color": "stop",
            "AsButton": False,
            "Info": "读取Tex論文并写摘要 | 入力パラメータ为路径",
            "Function": HotReload(ReadArticleWriteSummary),
        },
        "翻訳README或MD": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": True,
            "Info": "置き換えるMarkdownの翻訳为中文 | 入力パラメータ为路径或URL",
            "Function": HotReload(TranslateMarkdownFromEnglishToChinese),
        },
        "翻訳Markdown或README（支持Github链接）": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": False,
            "Info": "置き換えるMarkdown或README日本語に翻訳する | 入力パラメータ为路径或URL",
            "Function": HotReload(TranslateMarkdownFromEnglishToChinese),
        },
        "BatchGenerateFunctionComments": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "バッチ量生成函数的注释 | 入力パラメータ为路径",
            "Function": HotReload(BatchGenerateFunctionComments),
        },
        "現在の対話を保存する": {
            "Group": "对话",
            "AsButton": True,
            "Info": "現在の対話を保存する | 不需要入力パラメータ",
            "Function": HotReload(ConversationHistoryArchive),
        },
        "[マルチスレッドデモ]このプロジェクト自体を解析する（ソースコードの自動翻訳解析）": {
            "Group": "对话|编程",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "マルチスレッド解析并翻訳此项目的源码 | 不需要入力パラメータ",
            "Function": HotReload(ParseProjectItself),
        },
        "Today in history": {
            "Group": "对话",
            "AsButton": True,
            "Info": "查看Today in history事件 (这是一pieces面向开发者的プラグインDemo) | 不需要入力パラメータ",
            "Function": HotReload(HighOrderFunctionTemplateFunctions),
        },
        "精准翻訳PDF論文": {
            "Group": "学术",
            "Color": "stop",
            "AsButton": True,
            "Info": "精准翻訳PDF論文为中文 | 入力パラメータ为路径",
            "Function": HotReload(BatchTranslatePDFDocuments),
        },
        "複数のGPTモデルについて問い合わせる": {
            "Group": "对话",
            "Color": "stop",
            "AsButton": True,
            "Function": HotReload(SimultaneousInquiry),
        },
        "BatchSummarizePDFDocuments": {
            "Group": "学术",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "BatchSummarizePDFDocuments的内容 | 入力パラメータ为路径",
            "Function": HotReload(BatchSummarizePDFDocuments),
        },
        "Google学術検索アシスタント（Google Scholar検索ページのURLを入力してください）": {
            "Group": "学术",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "使用するGoogle学術検索アシスタント搜索指定URL的结果 | 入力パラメータ为谷歌学术搜索页的URL",
            "Function": HotReload(GoogleSearchAssistant),
        },
        "UnderstandPdfDocumentContent （ChatPDFを模倣する）": {
            "Group": "学术",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "理解PDF文档的内容并进行回答 | 入力パラメータ为路径",
            "Function": HotReload(UnderstandPdfDocumentContentStandardFileInput),
        },
        "英語のLatexプロジェクト全体を校正する（パスを入力するか、圧縮ファイルをアップロードする）": {
            "Group": "学术",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "对英文Latex项目全文进行校正中处理 | 入力パラメータ为路径或上传テキストの翻訳",
            "Function": HotReload(EnglishProofreadingForLatex),
        },

        "中国語のLatexプロジェクトの全文を校正する（パスを入力するか、圧縮ファイルをアップロードする）": {
            "Group": "学术",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "对中文Latex项目全文进行校正中处理 | 入力パラメータ为路径或上传テキストの翻訳",
            "Function": HotReload(LatexChineseProofreading),
        },
        # 已经被新プラグイン取代
        # "英文Latex项目全文纠错（パスを入力するか、圧縮ファイルをアップロードする）": {
        #     "Group": "学术",
        #     "Color": "stop",
        #     "AsButton": False,  # ドロップダウンメニューに追加する
        #     "Info": "对英文Latex项目全文进行纠错处理 | 入力パラメータ为路径或上传テキストの翻訳",
        #     "Function": HotReload(LatexEnglishCorrection),
        # },
        # 已经被新プラグイン取代
        # "LaTeXプロジェクト全文の中国語から英語への翻訳（パスを入力するか、圧縮ファイルをアップロードする）": {
        #     "Group": "学术",
        #     "Color": "stop",
        #     "AsButton": False,  # ドロップダウンメニューに追加する
        #     "Info": "对Latex项目全文进行中国語から英語への翻訳处理 | 入力パラメータ为路径或上传テキストの翻訳",
        #     "Function": HotReload(LatexChineseToEnglish)
        # },
        # 已经被新プラグイン取代
        # "Full translation of Latex project from English to Chinese（パスを入力するか、圧縮ファイルをアップロードする）": {
        #     "Group": "学术",
        #     "Color": "stop",
        #     "AsButton": False,  # ドロップダウンメニューに追加する
        #     "Info": "对Latex项目全文进行英語から中国語への翻訳处理 | 入力パラメータ为路径或上传テキストの翻訳",
        #     "Function": HotReload(LatexEnglishToChinese)
        # },
        "バッチ量MarkdownChineseToEnglish（パスを入力するか、圧縮ファイルをアップロードする）": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "バッチ量置き換えるMarkdown文件中文翻訳为英文 | 入力パラメータ为路径或上传テキストの翻訳",
            "Function": HotReload(MarkdownChineseToEnglish),
        },
    }

    # -=--=- 尚未充分测试的实验性プラグイン & 需要额外依赖的プラグイン -=--=-
    try:
        from crazy_functions.DownloadArxivPaperTranslateAbstract import DownloadArxivPaperAndTranslateAbstract

        function_plugins.update(
            {
                "一键DownloadArxivPaperAndTranslateAbstract（まずinputに番号を入力してください，例えば1812.10695のように）": {
                    "Group": "学术",
                    "Color": "stop",
                    "AsButton": False,  # ドロップダウンメニューに追加する
                    # "Info": "DownloadArxivPaperAndTranslateAbstract | 入力パラメータ为arxiv编号例えば1812.10695のように",
                    "Function": HotReload(DownloadArxivPaperAndTranslateAbstract),
                }
            }
        )
    except:
        print(trimmed_format_exc())
        print("Load function plugin failed")

    try:
        from crazy_functions.ChatGPTConnectedToNetwork import ConnectToNetworkToAnswerQuestions

        function_plugins.update(
            {
                "ConnectToNetworkToAnswerQuestions（質問を入力した後、このプラグインをクリックします，Googleにアクセスする必要があります）": {
                    "Group": "对话",
                    "Color": "stop",
                    "AsButton": False,  # ドロップダウンメニューに追加する
                    # "Info": "ConnectToNetworkToAnswerQuestions（Googleにアクセスする必要があります）| 入力パラメータ是一pieces問題",
                    "Function": HotReload(ConnectToNetworkToAnswerQuestions),
                }
            }
        )
        from crazy_functions.OnlineChatGPT_BingEdition import ConnectBingSearchAnswerQuestion

        function_plugins.update(
            {
                "ConnectToNetworkToAnswerQuestions（中国語Bing版，質問を入力した後、このプラグインをクリックします）": {
                    "Group": "对话",
                    "Color": "stop",
                    "AsButton": False,  # ドロップダウンメニューに追加する
                    "Info": "ConnectToNetworkToAnswerQuestions（需要访问中文Bing）| 入力パラメータ是一pieces問題",
                    "Function": HotReload(ConnectBingSearchAnswerQuestion),
                }
            }
        )
    except:
        print(trimmed_format_exc())
        print("Load function plugin failed")

    try:
        from crazy_functions.ParseProjectSourceCode import ParseAnyCodeProject

        function_plugins.update(
            {
                "ParseProjectSourceCode（ソースコードファイルタイプを手動で指定およびフィルタリングする）": {
                    "Group": "编程",
                    "Color": "stop",
                    "AsButton": False,
                    "AdvancedArgs": True,  # 呼び出し時，高度なパラメータ入力エリアを呼び出す（デフォルトはFalse）
                    "ArgsReminder": '入力時にカンマで区切ってください, * represents a wildcard, ^を追加すると、一致しないことを意味します; No input means all matches。例えば: "*.c, ^*.cpp, config.toml, ^*.toml"',  # 高度なパラメータ入力エリアの表示ヒント
                    "Function": HotReload(ParseAnyCodeProject),
                },
            }
        )
    except:
        print(trimmed_format_exc())
        print("Load function plugin failed")

    try:
        from crazy_functions.InquiryMultipleLargeLanguageModels import InquireSimultaneously_SpecifiedModel

        function_plugins.update(
            {
                "複数のGPTモデルについて問い合わせる（手動でどのモデルを問い合わせるか指定する）": {
                    "Group": "对话",
                    "Color": "stop",
                    "AsButton": False,
                    "AdvancedArgs": True,  # 呼び出し時，高度なパラメータ入力エリアを呼び出す（デフォルトはFalse）
                    "ArgsReminder": "Support any number of llm interfaces，&記号で分割する。例えばchatglm&gpt-3.5-turbo&gpt-4",  # 高度なパラメータ入力エリアの表示ヒント
                    "Function": HotReload(InquireSimultaneously_SpecifiedModel),
                },
            }
        )
    except:
        print(trimmed_format_exc())
        print("Load function plugin failed")

    try:
        from crazy_functions.ImageGeneration import ImageGeneration_DALLE2, ImageGeneration_DALLE3, ImageModification_DALLE2

        function_plugins.update(
            {
                "ImageGeneration_DALLE2 （先切换模型到gpt-*）": {
                    "Group": "对话",
                    "Color": "stop",
                    "AsButton": False,
                    "AdvancedArgs": True,  # 呼び出し時，高度なパラメータ入力エリアを呼び出す（デフォルトはFalse）
                    "ArgsReminder": "解像度をここに入力してください, 1024x1024のように（#），支持 256x256, 512x512, 1024x1024",  # 高度なパラメータ入力エリアの表示ヒント
                    "Info": "使用するDALLE2生成图片 | 入力パラメータ文字列，提供图像的内容",
                    "Function": HotReload(ImageGeneration_DALLE2),
                },
            }
        )
        function_plugins.update(
            {
                "ImageGeneration_DALLE3 （先切换模型到gpt-*）": {
                    "Group": "对话",
                    "Color": "stop",
                    "AsButton": False,
                    "AdvancedArgs": True,  # 呼び出し時，高度なパラメータ入力エリアを呼び出す（デフォルトはFalse）
                    "ArgsReminder": "在这里入力自定义パラメータ「分辨率-质量(オプション)-风格(オプション)」, パラメータ示例「1024x1024-hd-vivid」 || 分辨率支持 「1024x1024」(#) /「1792x1024」/「1024x1792」 || 质量支持 「-standard」(#) /「-hd」 || 风格支持 「-vivid」(#) /「-natural」",  # 高度なパラメータ入力エリアの表示ヒント
                    "Info": "使用するDALLE3生成图片 | 入力パラメータ文字列，提供图像的内容",
                    "Function": HotReload(ImageGeneration_DALLE3),
                },
            }
        )
        function_plugins.update(
            {
                "ImageModification_DALLE2 （先切换模型到gpt-*）": {
                    "Group": "对话",
                    "Color": "stop",
                    "AsButton": False,
                    "AdvancedArgs": False,  # 呼び出し時，高度なパラメータ入力エリアを呼び出す（デフォルトはFalse）
                    # "Info": "使用するDALLE2修改图片 | 入力パラメータ文字列，提供图像的内容",
                    "Function": HotReload(ImageModification_DALLE2),
                },
            }
        )
    except:
        print(trimmed_format_exc())
        print("Load function plugin failed")

    try:
        from crazy_functions.SummaryAudioVideo import SummaryAudioVideo

        function_plugins.update(
            {
                "バッチ量SummaryAudioVideo（パスを入力するか、圧縮ファイルをアップロードする）": {
                    "Group": "对话",
                    "Color": "stop",
                    "AsButton": False,
                    "AdvancedArgs": True,
                    "ArgsReminder": "テキストの翻訳, 現在サポートされている形式:mp4, m4a, wav, mpga, mpeg, mp3。此处可以入力解析ヒント，例えば：テキストの翻訳（#）。",
                    "Info": "バッチ量音声をまとめる或视频 | 入力パラメータ为路径",
                    "Function": HotReload(SummaryAudioVideo),
                }
            }
        )
    except:
        print(trimmed_format_exc())
        print("Load function plugin failed")

    try:
        from crazy_functions.MathematicalAnimationGenerationManim import AnimationGeneration

        function_plugins.update(
            {
                "数学AnimationGeneration（Manim）": {
                    "Group": "对话",
                    "Color": "stop",
                    "AsButton": False,
                    "Info": "按照自然语言描述生成一pieces动画 | 入力パラメータ是一段话",
                    "Function": HotReload(AnimationGeneration),
                }
            }
        )
    except:
        print(trimmed_format_exc())
        print("Load function plugin failed")

    try:
        from crazy_functions.BatchTranslateMarkdown import TranslateMarkdownToSpecifiedLanguage

        function_plugins.update(
            {
                "Markdownの翻訳（指定翻訳成何种语言）": {
                    "Group": "编程",
                    "Color": "stop",
                    "AsButton": False,
                    "AdvancedArgs": True,
                    "ArgsReminder": "日本語，デフォルトはChineseです。",
                    "Function": HotReload(TranslateMarkdownToSpecifiedLanguage),
                }
            }
        )
    except:
        print(trimmed_format_exc())
        print("Load function plugin failed")

    try:
        from crazy_functions.UpdateKnowledgeArchive import InjectKnowledgeBaseFiles

        function_plugins.update(
            {
                "テキストの翻訳（先上传文件素材,再运行此プラグイン）": {
                    "Group": "对话",
                    "Color": "stop",
                    "AsButton": False,
                    "AdvancedArgs": True,
                    "ArgsReminder": "此处待注入的知识库名称id, デフォルトはdefaultです。文件进入知识库后可长期保存。可以通过再次调用本プラグイン的方式，向知识库追加更多文档。",
                    "Function": HotReload(InjectKnowledgeBaseFiles),
                }
            }
        )
    except:
        print(trimmed_format_exc())
        print("Load function plugin failed")

    try:
        from crazy_functions.UpdateKnowledgeArchive import ReadKnowledgeArchiveAnswerQuestions

        function_plugins.update(
            {
                "InjectKnowledgeBaseFiles（テキストの翻訳后,再运行此プラグイン）": {
                    "Group": "对话",
                    "Color": "stop",
                    "AsButton": False,
                    "AdvancedArgs": True,
                    "ArgsReminder": "原始文本, デフォルトはdefaultです, 您需要テキストの翻訳后再运行此プラグイン。",
                    "Function": HotReload(ReadKnowledgeArchiveAnswerQuestions),
                }
            }
        )
    except:
        print(trimmed_format_exc())
        print("Load function plugin failed")

    try:
        from crazy_functions.InteractiveFunctionFunctionTemplate import InteractiveFunctionTemplateFunction

        function_plugins.update(
            {
                "交互功能模板Demo函数（查找wallhaven.cc的壁纸）": {
                    "Group": "对话",
                    "Color": "stop",
                    "AsButton": False,
                    "Function": HotReload(InteractiveFunctionTemplateFunction),
                }
            }
        )
    except:
        print(trimmed_format_exc())
        print("Load function plugin failed")

    try:
        from crazy_functions.OutputPDFFromLatex import CorrectEnglishInLatexWithPDFComparison
        from crazy_functions.OutputPDFFromLatex import TranslateChineseToEnglishInLatexAndRecompilePDF
        from crazy_functions.OutputPDFFromLatex import TranslatePDFToChineseAndRecompilePDF

        function_plugins.update(
            {
                "LatexEnglishCorrection+高亮修正位置 [LaTeXが必要です]": {
                    "Group": "学术",
                    "Color": "stop",
                    "AsButton": False,
                    "AdvancedArgs": True,
                    "ArgsReminder": "ある場合必要, ここにより詳細なエラー修正命令を追加してください（使用する英文）。",
                    "Function": HotReload(CorrectEnglishInLatexWithPDFComparison),
                },
                "Arxiv論文精细翻訳（arxivIDを入力する）[LaTeXが必要です]": {
                    "Group": "学术",
                    "Color": "stop",
                    "AsButton": False,
                    "AdvancedArgs": True,
                    "ArgsReminder": r"ある場合必要, カスタム翻訳コマンドをここに入力してください, 一部の用語の翻訳の不正確さを解決する。 "
                                    r"例えば当单词'agent'翻訳不准确時, テキストの翻訳: "
                                    r'If the term "agent" is used in this section, it should be translated to "智能体". ',
                    "Info": "Arixv論文の詳細な翻訳 | 入力パラメータarxiv論文的ID，比例えば1812.10695のように",
                    "Function": HotReload(TranslateChineseToEnglishInLatexAndRecompilePDF),
                },
                "ローカルのLaTeX論文の詳細な翻訳（Latexプロジェクトをアップロードする）[LaTeXが必要です]": {
                    "Group": "学术",
                    "Color": "stop",
                    "AsButton": False,
                    "AdvancedArgs": True,
                    "ArgsReminder": r"ある場合必要, カスタム翻訳コマンドをここに入力してください, 一部の用語の翻訳の不正確さを解決する。 "
                                    r"例えば当单词'agent'翻訳不准确時, テキストの翻訳: "
                                    r'If the term "agent" is used in this section, it should be translated to "智能体". ',
                    "Info": "ローカルのLaTeX論文の詳細な翻訳 | 入力パラメータ是路径",
                    "Function": HotReload(TranslateChineseToEnglishInLatexAndRecompilePDF),
                },
                "TranslatePDFToChineseAndRecompilePDF（上传PDF）[LaTeXが必要です]": {
                    "Group": "学术",
                    "Color": "stop",
                    "AsButton": False,
                    "AdvancedArgs": True,
                    "ArgsReminder": r"ある場合必要, カスタム翻訳コマンドをここに入力してください, 一部の用語の翻訳の不正確さを解決する。 "
                                    r"例えば当单词'agent'翻訳不准确時, テキストの翻訳: "
                                    r'If the term "agent" is used in this section, it should be translated to "智能体". ',
                    "Info": "PDF翻訳中文，并重新编译PDF | 入力パラメータ为路径",
                    "Function": HotReload(TranslatePDFToChineseAndRecompilePDF)
                }
            }
        )
    except:
        print(trimmed_format_exc())
        print("Load function plugin failed")

    try:
        from toolbox import get_conf

        ENABLE_AUDIO = get_conf("ENABLE_AUDIO")
        if ENABLE_AUDIO:
            from crazy_functions.VoiceAssistant import VoiceAssistant

            function_plugins.update(
                {
                    "实時语音对话": {
                        "Group": "对话",
                        "Color": "stop",
                        "AsButton": True,
                        "Info": "这是一pieces時刻聆听着的语音对话助手 | 没有入力パラメータ",
                        "Function": HotReload(VoiceAssistant),
                    }
                }
            )
    except:
        print(trimmed_format_exc())
        print("Load function plugin failed")

    try:
        from crazy_functions.BatchTranslatePDFDocuments_NOUGAT import BatchTranslatePDFDocuments

        function_plugins.update(
            {
                "精准翻訳PDF文档（NOUGAT）": {
                    "Group": "学术",
                    "Color": "stop",
                    "AsButton": False,
                    "Function": HotReload(BatchTranslatePDFDocuments),
                }
            }
        )
    except:
        print(trimmed_format_exc())
        print("Load function plugin failed")

    try:
        from crazy_functions.DynamicFunctionGeneration import DynamicFunctionGeneration

        function_plugins.update(
            {
                "动态代码解释器（CodeInterpreter）": {
                    "Group": "智能体",
                    "Color": "stop",
                    "AsButton": False,
                    "Function": HotReload(DynamicFunctionGeneration),
                }
            }
        )
    except:
        print(trimmed_format_exc())
        print("Load function plugin failed")

    try:
        from crazy_functions.MultiAgent import MultiAgentTerminal

        function_plugins.update(
            {
                "AutoGenMultiAgentTerminal（仅供测试）": {
                    "Group": "智能体",
                    "Color": "stop",
                    "AsButton": False,
                    "Function": HotReload(MultiAgentTerminal),
                }
            }
        )
    except:
        print(trimmed_format_exc())
        print("Load function plugin failed")

    try:
        from crazy_functions.InteractiveMiniGame import RandomMiniGame

        function_plugins.update(
            {
                "随机InteractiveMiniGame（仅供测试）": {
                    "Group": "智能体",
                    "Color": "stop",
                    "AsButton": False,
                    "Function": HotReload(RandomMiniGame),
                }
            }
        )
    except:
        print(trimmed_format_exc())
        print("Load function plugin failed")

    # try:
    #     from crazy_functions.AdvancedFunctionTemplate import 测试图表渲染
    #     function_plugins.update({
    #         "绘制逻辑关系（测试图表渲染）": {
    #             "Group": "智能体",
    #             "Color": "stop",
    #             "AsButton": True,
    #             "Function": HotReload(测试图表渲染)
    #         }
    #     })
    # except:
    #     print(trimmed_format_exc())
    #     print('Load function plugin failed')

    # try:
    #     from crazy_functions.ChatGLMFineTuningTool import FineTuneDatasetGeneration
    #     function_plugins.update({
    #         "黑盒模型学习: FineTuneDatasetGeneration (まずデータセットをアップロードしてください)": {
    #             "Color": "stop",
    #             "AsButton": False,
    #             "AdvancedArgs": True,
    #             "ArgsReminder": "针对数据集入力（例えば、緑の帽子*濃い青のシャツ*黒のスポーツパンツ）指示を与える，たとえば、以下のコマンドを下にコピーできます: --llm_to_learn=azure-gpt-3.5 --prompt_prefix='根据下面的服装类型ヒント，着用者を想像してください，この人の外見、環境、内面世界、過去の経験について描写する。要求：100文字以内，第二人称を使用するする。' --system_prompt=''",
    #             "Function": HotReload(FineTuneDatasetGeneration)
    #         }
    #     })
    # except:
    #     print('Load function plugin failed')

    """
    设置デフォルト値:
    - # Group = 对话
    - # AsButton = True
    - # AdvancedArgs = False
    - # Color = secondary
    """
    for name, function_meta in function_plugins.items():
        if "Group" not in function_meta:
            function_plugins[name]["Group"] = "对话"
        if "AsButton" not in function_meta:
            function_plugins[name]["AsButton"] = True
        if "AdvancedArgs" not in function_meta:
            function_plugins[name]["AdvancedArgs"] = False
        if "Color" not in function_meta:
            function_plugins[name]["Color"] = "secondary"

    return function_plugins
