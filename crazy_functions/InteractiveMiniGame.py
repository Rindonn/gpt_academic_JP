from toolbox import CatchException, update_ui, update_ui_lastest_msg
from crazy_functions.multi_stage.multi_stage_utils import GptAcademicGameBaseState
from crazy_functions.crazy_utils import request_gpt_model_in_new_thread_with_ui_alive
from request_llms.bridge_all import predict_no_ui_long_connection
from crazy_functions.game_fns.game_utils import get_code_block, is_same_thing

@CatchException
def RandomMiniGame(prompt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    from crazy_functions.game_fns.game_interactive_story import MiniGame_ResumeStory
    # 履歴をクリアする
    history = []
    # 选择游戏
    cls = MiniGame_ResumeStory
    # 如果之前已经初始化了游戏实例，则继续该实例；否则重新初始化
    state = cls.sync_state(chatbot,
                           llm_kwargs,
                           cls,
                           plugin_name='MiniGame_ResumeStory',
                           callback_fn='crazy_functions.InteractiveMiniGame->RandomMiniGame',
                           lock_plugin=True
                           )
    yield from state.continue_game(prompt, chatbot, history)


@CatchException
def RandomMiniGame1(prompt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    from crazy_functions.game_fns.game_ascii_art import MiniGame_ASCII_Art
    # 履歴をクリアする
    history = []
    # 选择游戏
    cls = MiniGame_ASCII_Art
    # 如果之前已经初始化了游戏实例，则继续该实例；否则重新初始化
    state = cls.sync_state(chatbot,
                           llm_kwargs,
                           cls,
                           plugin_name='MiniGame_ASCII_Art',
                           callback_fn='crazy_functions.InteractiveMiniGame->RandomMiniGame1',
                           lock_plugin=True
                           )
    yield from state.continue_game(prompt, chatbot, history)
