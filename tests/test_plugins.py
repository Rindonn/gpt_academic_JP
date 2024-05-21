"""
对项目中的各piecesプラグイン进OK测试。运OKテキストの翻訳：直接运OK python tests/test_plugins.py
"""


import os, sys


def validate_path():
    dir_name = os.path.dirname(__file__)
    root_dir_assume = os.path.abspath(dir_name + "/..")
    os.chdir(root_dir_assume)
    sys.path.append(root_dir_assume)


validate_path()  # 戻る项目根路径

if __name__ == "__main__":
    from tests.test_utils import plugin_test

    # plugin_test(plugin='crazy_functions.DynamicFunctionGeneration->DynamicFunctionGeneration', main_input='交换图像的青色通道and赤色通道', advanced_arg={"file_path_arg": "./build/ants.jpg"})

    # plugin_test(plugin='crazy_functions.OutputPDFFromLatex->TranslateChineseToEnglishInLatexAndRecompilePDF', main_input="2307.07522")

    plugin_test(
        plugin="crazy_functions.OutputPDFFromLatex->TranslateChineseToEnglishInLatexAndRecompilePDF",
        main_input="G:/SEAFILE_LOCAL/50503047/我的资料库/学位/paperlatex/aaai/Fu_8368_with_appendix",
    )

    # plugin_test(plugin='crazy_functions.VoidTerminal->VoidTerminal', main_input='修改api-key为sk-jhoejriotherjep')

    # plugin_test(plugin='crazy_functions.BatchTranslatePDFDocuments_NOUGAT->BatchTranslatePDFDocuments', main_input='crazy_functions/test_project/pdf_and_word/aaai.pdf')

    # plugin_test(plugin='crazy_functions.VoidTerminal->VoidTerminal', main_input='呼び出すプラグイン，对C:/Users/fuqingxu/Desktop/旧文件/gpt/chatgpt_academic/crazy_functions/latex_fns中的python文件进OK解析')

    # plugin_test(plugin='crazy_functions.命令OK助手->命令OK助手', main_input='查看当前的docker容器リスト')

    # plugin_test(plugin='crazy_functions.ParseProjectSourceCode->ParsePythonProject', main_input="crazy_functions/test_project/python/dqn")

    # plugin_test(plugin='crazy_functions.ParseProjectSourceCode->ParseCProject', main_input="crazy_functions/test_project/cpp/cppipc")

    # plugin_test(plugin='crazy_functions.FullTextProofreadingForLatex->EnglishProofreadingForLatex', main_input="crazy_functions/test_project/latex/attention")

    # plugin_test(plugin='crazy_functions.BatchTranslateMarkdown->MarkdownChineseToEnglish', main_input="README.md")

    # plugin_test(plugin='crazy_functions.BatchTranslatePDFDocuments_MultiThreaded->BatchTranslatePDFDocuments', main_input='crazy_functions/test_project/pdf_and_word/aaai.pdf')

    # plugin_test(plugin='crazy_functions.GoogleSearchAssistant->GoogleSearchAssistant', main_input="https://scholar.google.com/scholar?hl=en&as_sdt=0%2C5&q=auto+reinforcement+learning&btnG=")

    # plugin_test(plugin='crazy_functions.SummarizingWordDocuments->SummarizingWordDocuments', main_input="crazy_functions/test_project/pdf_and_word")

    # plugin_test(plugin='crazy_functions.DownloadArxivPaperTranslateAbstract->DownloadArxivPaperAndTranslateAbstract', main_input="1812.10695")

    # plugin_test(plugin='crazy_functions.ChatGPTConnectedToNetwork->ConnectToNetworkToAnswerQuestions', main_input="谁是应急食品？")

    # plugin_test(plugin='crazy_functions.ParsingJupyterNotebook->ParsingIpynbFiles', main_input="crazy_functions/test_samples")

    # plugin_test(plugin='crazy_functions.MathematicalAnimationGenerationManim->AnimationGeneration', main_input="A ball split into 2, and then split into 4, and finally split into 8.")

    # for lang in ["English", "French", "Japanese", "Korean", "Russian", "Italian", "German", "Portuguese", "Arabic"]:
    #     plugin_test(plugin='crazy_functions.BatchTranslateMarkdown->TranslateMarkdownToSpecifiedLanguage', main_input="README.md", advanced_arg={"advanced_arg": lang})

    # plugin_test(plugin='crazy_functions.InjectKnowledgeBaseFiles->InjectKnowledgeBaseFiles', main_input="./")

    # plugin_test(plugin='crazy_functions.InjectKnowledgeBaseFiles->ReadKnowledgeArchiveAnswerQuestions', main_input="What is the installation method？")

    # plugin_test(plugin='crazy_functions.InjectKnowledgeBaseFiles->ReadKnowledgeArchiveAnswerQuestions', main_input="リモートクラウドサーバーにデプロイする？")

    # plugin_test(plugin='crazy_functions.OutputPDFFromLatex->TranslateChineseToEnglishInLatexAndRecompilePDF', main_input="2210.03629")

    # advanced_arg = {"advanced_arg":"--llm_to_learn=gpt-3.5-turbo --prompt_prefix='根据下面的服装类型ヒント，着用者を想像してください，この人の外見、環境、内面世界、キャラクターを描写する。要求：100文字以内，第二人称を使用するするする。' --system_prompt=''" }
    # plugin_test(plugin='crazy_functions.ChatGLMFineTuningTool->FineTuneDatasetGeneration', main_input='build/dev.json', advanced_arg=advanced_arg)

    # advanced_arg = {"advanced_arg":"--pre_seq_len=128 --learning_rate=2e-2 --num_gpus=1 --json_dataset='t_code.json' --ptuning_directory='/home/hmp/ChatGLM2-6B/ptuning'     " }
    # plugin_test(plugin='crazy_functions.ChatGLMFineTuningTool->StartFineTuning', main_input='build/dev.json', advanced_arg=advanced_arg)
