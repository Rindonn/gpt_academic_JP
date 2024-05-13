"""
对项目中的各piecesプラグイン进行测试。运行テキストの翻訳：直接运行 python tests/test_plugins.py
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

    plugin_test(plugin="crazy_functions.UpdateKnowledgeArchive->InjectKnowledgeBaseFiles", main_input="./README.md")

    plugin_test(
        plugin="crazy_functions.UpdateKnowledgeArchive->ReadKnowledgeArchiveAnswerQuestions",
        main_input="What is the installation method？",
    )

    plugin_test(plugin="crazy_functions.UpdateKnowledgeArchive->ReadKnowledgeArchiveAnswerQuestions", main_input="リモートクラウドサーバーにデプロイする？")
