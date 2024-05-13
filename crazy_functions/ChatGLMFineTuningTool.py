from toolbox import CatchException, update_ui, promote_file_to_downloadzone
from .crazy_utils import request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency
import datetime, json

def fetch_items(list_of_items, batch_size):
    for i in range(0, len(list_of_items), batch_size):
        yield list_of_items[i:i + batch_size]

def string_to_options(arguments):
    import argparse
    import shlex

    # Create an argparse.ArgumentParser instance
    parser = argparse.ArgumentParser()

    # Add command-line arguments
    parser.add_argument("--llm_to_learn", type=str, help="LLM model to learn", default="gpt-3.5-turbo")
    parser.add_argument("--prompt_prefix", type=str, help="Prompt prefix", default='')
    parser.add_argument("--system_prompt", type=str, help="System prompt", default='')
    parser.add_argument("--batch", type=int, help="System prompt", default=50)
    parser.add_argument("--pre_seq_len", type=int, help="pre_seq_len", default=50)
    parser.add_argument("--learning_rate", type=float, help="learning_rate", default=2e-2)
    parser.add_argument("--num_gpus", type=int, help="num_gpus", default=1)
    parser.add_argument("--json_dataset", type=str, help="json_dataset", default="")
    parser.add_argument("--ptuning_directory", type=str, help="ptuning_directory", default="")



    # Parse the arguments
    args = parser.parse_args(shlex.split(arguments))

    return args

@CatchException
def FineTuneDatasetGeneration(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    """
    txt             入力欄にユーザーが入力したテキスト，翻訳が必要な例文，処理待ちのファイルを含むパスの例
    llm_kwargs      GPTモデルのパラメータ，温度やtop_pなど，通常はそのまま渡すだけでよい
    plugin_kwargs   プラグインモデルのパラメータ
    chatbot         チャット表示ボックスのハンドル，ユーザーに表示するために使用するされます
    history         チャット履歴，前提の要約
    system_prompt   GPTに対するサイレントリマインダー
    user_request    当前用户的请求信息（IPAddress等）
    """
    history = []    # 履歴をクリアする，オーバーフローを防ぐために
    chatbot.append(("What is this function?？", "[Local Message] FineTuneDatasetGeneration"))
    if ("advanced_arg" in plugin_kwargs) and (plugin_kwargs["advanced_arg"] == ""): plugin_kwargs.pop("advanced_arg")
    args = plugin_kwargs.get("advanced_arg", None)
    if args is None:
        chatbot.append(("テキストの翻訳", "終了"))
        yield from update_ui(chatbot=chatbot, history=history); return
    else:
        arguments = string_to_options(arguments=args)

    dat = []
    with open(txt, 'r', encoding='utf8') as f:
        for line in f.readlines():
            json_dat = json.loads(line)
            dat.append(json_dat["content"])

    llm_kwargs['llm_model'] = arguments.llm_to_learn
    for batch in fetch_items(dat, arguments.batch):
        res = yield from request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency(
            inputs_array=[f"{arguments.prompt_prefix}\n\n{b}" for b in (batch)],
            inputs_show_user_array=[f"Show Nothing" for _ in (batch)],
            llm_kwargs=llm_kwargs,
            chatbot=chatbot,
            history_array=[[] for _ in (batch)],
            sys_prompt_array=[arguments.system_prompt for _ in (batch)],
            max_workers=10  # OpenAIが許可する最大並列過負荷
        )

        with open(txt+'.generated.json', 'a+', encoding='utf8') as f:
            for b, r in zip(batch, res[1::2]):
                f.write(json.dumps({"content":b, "summary":r}, ensure_ascii=False)+'\n')

    promote_file_to_downloadzone(txt+'.generated.json', rename_file='generated.json', chatbot=chatbot)
    return



@CatchException
def StartFineTuning(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    """
    txt             入力欄にユーザーが入力したテキスト，翻訳が必要な例文，処理待ちのファイルを含むパスの例
    llm_kwargs      GPTモデルのパラメータ，温度やtop_pなど，通常はそのまま渡すだけでよい
    plugin_kwargs   プラグインモデルのパラメータ
    chatbot         チャット表示ボックスのハンドル，ユーザーに表示するために使用するされます
    history         チャット履歴，前提の要約
    system_prompt   GPTに対するサイレントリマインダー
    user_request    当前用户的请求信息（IPAddress等）
    """
    import subprocess
    history = []    # 履歴をクリアする，オーバーフローを防ぐために
    chatbot.append(("What is this function?？", "[Local Message] FineTuneDatasetGeneration"))
    if ("advanced_arg" in plugin_kwargs) and (plugin_kwargs["advanced_arg"] == ""): plugin_kwargs.pop("advanced_arg")
    args = plugin_kwargs.get("advanced_arg", None)
    if args is None:
        chatbot.append(("テキストの翻訳", "終了"))
        yield from update_ui(chatbot=chatbot, history=history); return
    else:
        arguments = string_to_options(arguments=args)



    pre_seq_len = arguments.pre_seq_len             # 128
    learning_rate = arguments.learning_rate                               # 2e-2
    num_gpus = arguments.num_gpus                   # 1
    json_dataset = arguments.json_dataset                 # 't_code.json'
    ptuning_directory = arguments.ptuning_directory       # '/home/hmp/ChatGLM2-6B/ptuning'

    command = f"torchrun --standalone --nnodes=1 --nproc-per-node={num_gpus} main.py \
        --do_train \
        --train_file AdvertiseGen/{json_dataset} \
        --validation_file AdvertiseGen/{json_dataset} \
        --preprocessing_num_workers 20 \
        --prompt_column content \
        --response_column summary \
        --overwrite_cache \
        --model_name_or_path THUDM/chatglm2-6b \
        --output_dir output/clothgen-chatglm2-6b-pt-{pre_seq_len}-{learning_rate} \
        --overwrite_output_dir \
        --max_source_length 256 \
        --max_target_length 256 \
        --per_device_train_batch_size 1 \
        --per_device_eval_batch_size 1 \
        --gradient_accumulation_steps 16 \
        --predict_with_generate \
        --max_steps 100 \
        --logging_steps 10 \
        --save_steps 20 \
        --learning_rate {learning_rate} \
        --pre_seq_len {pre_seq_len} \
        --quantization_bit 4"

    process = subprocess.Popen(command, shell=True, cwd=ptuning_directory)
    try:
        process.communicate(timeout=3600*24)
    except subprocess.TimeoutExpired:
        process.kill()
    return
