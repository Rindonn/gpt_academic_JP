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
            "AsButton": False,
            "Function": HotReload(VoidTerminal),
        },
        "pythonプロジェクトを翻訳": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": False,
            "Info": "PythonProject全てのソースコード(.py) | 入力パラメータはパス",
            "Function": HotReload(ParsePythonProject),
        },
        "LoadConversationHistoryArchive（アーカイブをアップロードするか、パスを入力してください）": {
            "Group": "对话",
            "Color": "stop",
            "AsButton": False,
            "Info": "LoadConversationHistoryArchive | 入力パラメータはパス",
            "Function": HotReload(LoadConversationHistoryArchive),
        },
        "DeleteAllLocalConversationHistoryRecords（慎重にご利用）": {
            "Group": "对话",
            "AsButton": False,
            "Info": "DeleteAllLocalConversationHistoryRecords，慎重にご利用 | 入力パラメータなし",
            "Function": HotReload(DeleteAllLocalConversationHistoryRecords),
        },
        "キャッチクリア（慎重にご利用）": {
            "Group": "对话",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "キャッチ削除，慎重にご利用 | 入力パラメータなし",
            "Function": HotReload(ClearCache),
        },
        "GenerateMultipleMermaidCharts(今の対話とパスから(.pdf/.md/.docx)グラフを作る）": {
            "Group": "对话",
            "Color": "stop",
            "AsButton": False,
            "Info" : "今の対話とファイルからグラフを作る,モデルからグラフの種類を判断します",
            "Function": HotReload(GenerateMultipleMermaidCharts),
            "AdvancedArgs": True,
            "ArgsReminder": "選択肢に対応する数字を入力して下さい,入力しないとモデルから判断します:1-フローチャート,2-シーケンス図,3-クラス図,4-円グラフ,5-ガントチャート,6-ステータス图,7-実体関係図,8-象限ヒント图,9-マインドマップ",
        },
        "Word文書を一括で要約する": {
            "Group": "学术",
            "Color": "stop",
            "AsButton": False,
            "Info": "バッチ量SummarizingWordDocuments | 入力パラメータはパスです。",
            "Function": HotReload(SummarizingWordDocuments),
        },
        "Matlabプロジェクトを解析": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": False,
            "Info": "AnalyzeAMatlabProjectのソースファイル(.m) | 入力パラメータはパスです。",
            "Function": HotReload(AnalyzeAMatlabProject),
        },
        "C++プロジェクトのヘッダーファイルを解析する": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "C++プロジェクトのヘッダーファイルを解析(.h/.hpp) | 入力パラメータはパスです。",
            "Function": HotReload(ParseCProjectHeaderFiles),
        },
        "C++プロジェクト全体を解析する（.cpp/.hpp/.c/.h）": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "C++プロジェクトの全体を解析（.cpp/.hpp/.c/.h）| 入力パラメータはパスです。",
            "Function": HotReload(ParseCProject),
        },
        "Goプロジェクト全体を解析する": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "Goプロジェクト全体を解析する | 入力パラメータはパスです。",
            "Function": HotReload(ParseGolangProject),
        },
        "Rustプロジェクト全体を解析する": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "Rustプロジェクト全体を解析する | 入力パラメータはパスです。",
            "Function": HotReload(ParseRustProject),
        },
        "Javaプロジェクト全体を解析する": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "Javaプロジェクト全体を解析する | 入力パラメータはパスです。",
            "Function": HotReload(ParseJavaProject),
        },
        "フロントエンドプロジェクト全体を解析する（js,ts,CSSなど）": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "Frontendプロジェクト全体を解析する（js,ts,CSSなど） | 入力パラメータはパスです。",
            "Function": HotReload(ParseFrontendProject),
        },
        "Luaプロジェクト全体を解析する": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "LuaProjectプロジェクト全体を解析する | 入力パラメータはパスです。",
            "Function": HotReload(ParsingLuaProject),
        },
        "CSharpプロジェクト全体を解析する": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "CSharpプロジェクト全体を解析する | 入力パラメータはパスです。",
            "Function": HotReload(ParsingCSharpProject),
        },
        "Jupyter Notebookファイルの解析": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": False,
            "Info": "Jupyter Notebookファイルの解析 | 入力パラメータはパスです。",
            "Function": HotReload(ParsingIpynbFiles),
            "AdvancedArgs": True,  # 呼び出し時，高度なパラメータ入力エリアを呼び出す（デフォルトはFalse）
            "ArgsReminder": "0を入力する場合，したがって、ノートブックのMarkdownブロックを解析しない",  # 高度なパラメータ入力エリアの表示ヒント
        },
        "Tex論文を読んで要約を書く": {
            "Group": "学术",
            "Color": "stop",
            "AsButton": False,
            "Info": "Tex論文を読んで要約を書く | 入力パラメータはパスです。",
            "Function": HotReload(ReadArticleWriteSummary),
        },
        "READMEとMDを翻訳する": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": False,
            "Info": "Markdownのファイルを翻訳 | 入力パラメータはパスとURLです",
            "Function": HotReload(TranslateMarkdownFromEnglishToChinese),
        },
        "MarkdownとREADMEを翻訳（Githubリンク解析でき）": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": True,
            "Info": "MarkdownとREADMEを日本語に翻訳 | 入力パラメータはパスとURLです",
            "Function": HotReload(TranslateMarkdownFromEnglishToChinese),
        },
        "BatchGenerateFunctionComments": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "関数のコメント文を自動的に生成する | 入力パラメータはパスです。",
            "Function": HotReload(BatchGenerateFunctionComments),
        },
        "現在の対話を保存する": {
            "Group": "对话",
            "AsButton": False,
            "Info": "現在の対話を保存する | 入力パラメータなし",
            "Function": HotReload(ConversationHistoryArchive),
        },
        "[マルチスレッドデモ]このプロジェクト自体を解析する（ソースコードの自動翻訳解析）": {
            "Group": "对话|编程",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "マルチスレッドで解析と翻訳 | 入力パラメータなし",
            "Function": HotReload(ParseProjectItself),
        },
        "Today in history": {
            "Group": "对话",
            "AsButton": False,
            "Info": "Today in historyをチェック (開発者向けのプラグインDemo) | 入力パラメータなし",
            "Function": HotReload(HighOrderFunctionTemplateFunctions),
        },
        "精確にPDF論文を翻訳": {
            "Group": "学术",
            "Color": "stop",
            "AsButton": True,
            "Info": "精確にPDF論文を翻訳 | 入力パラメータはパスです。",
            "Function": HotReload(BatchTranslatePDFDocuments),
        },
        "複数のGPTモデルについて問い合わせる（まだ翻訳していない）": {
            "Group": "对话",
            "Color": "stop",
            "AsButton": False,
            "Function": HotReload(SimultaneousInquiry),
        },
        "BatchSummarizePDFDocuments": {
            "Group": "学术",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "BatchSummarizePDFDocumentsの内容 | 入力パラメータはパスです。",
            "Function": HotReload(BatchSummarizePDFDocuments),
        },
        "Google学術検索アシスタント（Google Scholar検索ページのURLを入力してください）": {
            "Group": "学术",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "Google学術検索アシスタントを使用した結果 | 入力パラメータはGoogle ScholarのURL",
            "Function": HotReload(GoogleSearchAssistant),
        },
        "UnderstandPdfDocumentContent （ChatPDFを模倣する）": {
            "Group": "学术",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "PDFの内容を理解し、問題を答える | 入力パラメータはパスです。",
            "Function": HotReload(UnderstandPdfDocumentContentStandardFileInput),
        },
        "英語のLatexプロジェクト全体を校正する（パスを入力するか、圧縮ファイルをアップロードする）": {
            "Group": "学术",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "英語のLatexプロジェクト全体を校正する | 入力パラメータはパスとアプロードした圧縮ファイル",
            "Function": HotReload(EnglishProofreadingForLatex),
        },

        "中国語のLatexプロジェクトの全文を校正する（パスを入力するか、圧縮ファイルをアップロードする）": {
            "Group": "学术",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "中国語のLatexプロジェクトの全文を校正する | 入力パラメータはパスとアプロードした圧縮ファイル",
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
        "MarkdownChineseToEnglish（パスを入力するか、圧縮ファイルをアップロードする）": {
            "Group": "编程",
            "Color": "stop",
            "AsButton": False,  # ドロップダウンメニューに追加する
            "Info": "Markdownを英語に翻訳 | 入力パラメータはパスとアプロードした圧縮ファイル",
            "Function": HotReload(MarkdownChineseToEnglish),
        },
    }

    # -=--=- 尚未充分测试的实验性プラグイン & 需要额外依赖的プラグイン -=--=-
    try:
        from crazy_functions.DownloadArxivPaperTranslateAbstract import DownloadArxivPaperAndTranslateAbstract

        function_plugins.update(
            {
                "Arxiv論文ダウンロードと要約": {
                    "Group": "学术",
                    "Color": "stop",
                    "AsButton": True,  # ドロップダウンメニューに追加する
                    "Info": "Arxiv論文ダウンロードと要約（まずinputに番号を入力してください，例えば1812.10695のように） | 入力パラメータ为arxiv编号例えば1812.10695のように",
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
                "ConnectToNetworkToAnswerQuestions（中国語Bing，質問を入力した後、このプラグインをクリックします）": {
                    "Group": "对话",
                    "Color": "stop",
                    "AsButton": False,  # ドロップダウンメニューに追加する
                    "Info": "ConnectToNetworkToAnswerQuestions（中国語Bingへアクセスが必要）| 入力パラメータは質問内容",
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
                "ImageGeneration_DALLE2 （翻訳していない）": {
                    "Group": "对话",
                    "Color": "stop",
                    "AsButton": False,
                    "AdvancedArgs": True,  # 呼び出し時，高度なパラメータ入力エリアを呼び出す（デフォルトはFalse）
                    "ArgsReminder": "解像度をここに入力してください, 1024x1024のように（#），例： 256x256, 512x512, 1024x1024",  # 高度なパラメータ入力エリアの表示ヒント
                    "Info": "DALLE2で写真を生成する | 入力パラメータは生成したい写真の内容",
                    "Function": HotReload(ImageGeneration_DALLE2),
                },
            }
        )
        function_plugins.update(
            {
                "ImageGeneration_DALLE3 （翻訳していない）": {
                    "Group": "对话",
                    "Color": "stop",
                    "AsButton": False,
                    "AdvancedArgs": True,  # 呼び出し時，高度なパラメータ入力エリアを呼び出す（デフォルトはFalse）
                    "ArgsReminder": "ここにパラメータを入力「解像度-質(オプション)-スタイル(オプション)」, パラメータ例「1024x1024-hd-vivid」 || 選択できる解像度 「1024x1024」(#) /「1792x1024」/「1024x1792」 || 質 「-standard」(#) /「-hd」 || スタイル 「-vivid」(#) /「-natural」",  # 高度なパラメータ入力エリアの表示ヒント
                    "Info": "DALLE3で写真を生成する | 入力パラメータは生成したい写真の内容",
                    "Function": HotReload(ImageGeneration_DALLE3),
                },
            }
        )
        function_plugins.update(
            {
                "ImageModification_DALLE2 （翻訳していない）": {
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
                "SummaryAudioVideo（パスを入力するか、圧縮ファイルをアップロードする）": {
                    "Group": "对话",
                    "Color": "stop",
                    "AsButton": False,
                    "AdvancedArgs": True,
                    "ArgsReminder": "サポートされている形式:mp4, m4a, wav, mpga, mpeg, mp3。",
                    "Info": "バッチ音声とビデオをまとめる | 入力パラメータはパス",
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
                "AnimationGeneration（Manim）": {
                    "Group": "对话",
                    "Color": "stop",
                    "AsButton": False,
                    "Info": "入力した内容からビデオを生成する | 入力パラメータはビデオの内容",
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
                "Markdownの翻訳（言語を指定して下さい）": {
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
                "LatexEnglishCorrection [LaTeXが必要です]": {
                    "Group": "学术",
                    "Color": "stop",
                    "AsButton": False,
                    "AdvancedArgs": True,
                    "ArgsReminder": "必要な場合, ここにより詳細なエラー修正命令を追加してください（英語で）。",
                    "Function": HotReload(CorrectEnglishInLatexWithPDFComparison),
                },
                "Arxiv論文精確に翻訳（arxivIDを入力する）[LaTeXが必要です]": {
                    "Group": "学术",
                    "Color": "stop",
                    "AsButton": True,
                    "AdvancedArgs": True,
                    "ArgsReminder": r"必要な場合, カスタム翻訳コマンドをここに入力してください, 一部の用語の翻訳の不正を解決することができる。 "
                                    r"例えば'agent'翻訳が間違えた時, テキストの翻訳: エージェント"
                                    r'If the term "agent" is used in this section, it should be translated to "エージェント". ',
                    "Info": "Arixv論文を精確に翻訳 | 入力はarxiv論文的ID，1812.10695のように",
                    "Function": HotReload(TranslateChineseToEnglishInLatexAndRecompilePDF),
                },
                "ローカルのLaTeX論文を精確に翻訳（Latexプロジェクトをアップロードする）[LaTeXが必要です]": {
                    "Group": "学术",
                    "Color": "stop",
                    "AsButton": True,
                    "AdvancedArgs": True,
                    "ArgsReminder": r"必要な場合, カスタム翻訳コマンドをここに入力してください, 一部の用語の翻訳の不正を解決することができる。 "
                                    r"例えば'agent'翻訳が間違えた時, テキストの翻訳: エージェント "
                                    r'If the term "agent" is used in this section, it should be translated to "エージェント". ',
                    "Info": "ローカルのLaTeX論文を精確に翻訳 | 入力パラメータはファイルのルート",
                    "Function": HotReload(TranslateChineseToEnglishInLatexAndRecompilePDF),
                },
                "PDF翻訳[LaTeXが必要です]": {
                    "Group": "学术",
                    "Color": "stop",
                    "AsButton": True,
                    "AdvancedArgs": True,
                    "ArgsReminder": r"必要な場合, カスタム翻訳コマンドをここに入力してください, 一部の用語の翻訳の不正を解決することができる。 "
                                    r"例えば'agent'翻訳が間違えた時, テキストの翻訳: エージェント "
                                    r'If the term "agent" is used in this section, it should be translated to "エージェント". ',
                    "Info": "PDF翻訳 | 入力パラメータはファイルのルート",
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
                    "ライブ音声対話": {
                        "Group": "对话",
                        "Color": "stop",
                        "AsButton": True,
                        "Info": "音声対話アシスタントです。 | 入力パラメータなし",
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
                "PDFドキュメントを翻訳する（NOUGAT）": {
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
                "ダイナミックコード説明機（CodeInterpreter）": {
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
                "AutoGenMultiAgentTerminal（テストだけ）": {
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
                "ランダムMiniGame（テストだけ）": {
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
