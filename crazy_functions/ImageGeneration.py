from toolbox import CatchException, update_ui, get_conf, select_api_key, get_log_folder
from crazy_functions.multi_stage.multi_stage_utils import GptAcademicState


def gen_image(llm_kwargs, prompt, resolution="1024x1024", model="dall-e-2", quality=None, style=None):
    import requests, json, time, os
    from request_llms.bridge_all import model_info

    proxies = get_conf('proxies')
    # Set up OpenAI API key and model
    api_key = select_api_key(llm_kwargs['api_key'], llm_kwargs['llm_model'])
    chat_endpoint = model_info[llm_kwargs['llm_model']]['endpoint']
    # 'https://api.openai.com/v1/chat/completions'
    img_endpoint = chat_endpoint.replace('chat/completions','images/generations')
    # # Generate the image
    url = img_endpoint
    headers = {
        'Authorization': f"Bearer {api_key}",
        'Content-Type': 'application/json'
    }
    data = {
        'prompt': prompt,
        'n': 1,
        'size': resolution,
        'model': model,
        'response_format': 'url'
    }
    if quality is not None:
        data['quality'] = quality
    if style is not None:
        data['style'] = style
    response = requests.post(url, headers=headers, json=data, proxies=proxies)
    print(response.content)
    try:
        image_url = json.loads(response.content.decode('utf8'))['data'][0]['url']
    except:
        raise RuntimeError(response.content.decode())
    # ローカルにファイルを保存する
    r = requests.get(image_url, proxies=proxies)
    file_path = f'{get_log_folder()}/image_gen/'
    os.makedirs(file_path, exist_ok=True)
    file_name = 'Image' + time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()) + '.png'
    with open(file_path+file_name, 'wb+') as f: f.write(r.content)


    return image_url, file_path+file_name


def edit_image(llm_kwargs, prompt, image_path, resolution="1024x1024", model="dall-e-2"):
    import requests, json, time, os
    from request_llms.bridge_all import model_info

    proxies = get_conf('proxies')
    api_key = select_api_key(llm_kwargs['api_key'], llm_kwargs['llm_model'])
    chat_endpoint = model_info[llm_kwargs['llm_model']]['endpoint']
    # 'https://api.openai.com/v1/chat/completions'
    img_endpoint = chat_endpoint.replace('chat/completions','images/edits')
    # # Generate the image
    url = img_endpoint
    n = 1
    headers = {
        'Authorization': f"Bearer {api_key}",
    }
    make_transparent(image_path, image_path+'.tsp.png')
    make_square_image(image_path+'.tsp.png', image_path+'.tspsq.png')
    resize_image(image_path+'.tspsq.png', image_path+'.ready.png', max_size=1024)
    image_path = image_path+'.ready.png'
    with open(image_path, 'rb') as f:
        file_content = f.read()
        files = {
            'image': (os.path.basename(image_path), file_content),
            # 'mask': ('mask.png', open('mask.png', 'rb'))
            'prompt':   (None, prompt),
            "n":        (None, str(n)),
            'size':     (None, resolution),
        }

    response = requests.post(url, headers=headers, files=files, proxies=proxies)
    print(response.content)
    try:
        image_url = json.loads(response.content.decode('utf8'))['data'][0]['url']
    except:
        raise RuntimeError(response.content.decode())
    # ローカルにファイルを保存する
    r = requests.get(image_url, proxies=proxies)
    file_path = f'{get_log_folder()}/image_gen/'
    os.makedirs(file_path, exist_ok=True)
    file_name = 'Image' + time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()) + '.png'
    with open(file_path+file_name, 'wb+') as f: f.write(r.content)


    return image_url, file_path+file_name


@CatchException
def ImageGeneration_DALLE2(prompt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    """
    txt             入力欄にユーザーが入力したテキスト,翻訳が必要な例文,処理待ちのファイルを含むパスの例
    llm_kwargs      GPTモデルのパラメータ,温度やtop_pなど,通常はそのまま渡すだけでよい
    plugin_kwargs   プラグインモデルのパラメータ,現時点では使用するされていません
    chatbot         チャット表示ボックスのハンドル,ユーザーに表示するために使用するされます
    history         チャット履歴,前提の要約
    system_prompt   GPTに対するサイレントリマインダー
    user_request    当前用户的请求信息（IPAddress等）
    """
    history = []    # 履歴をクリアする,オーバーフローを防ぐために
    if prompt.strip() == "":
        chatbot.append((prompt, "[Local Message] 图像生成ヒント为空白，请在“入力エリア”入力图像生成ヒント。"))
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する インターフェースの更新
        return
    chatbot.append(("您正在调用“图像生成”プラグイン。", "[Local Message] 画像を生成する, 请先把模型切换至gpt-*。如果中文Prompt效果不理想, 请Try英文Prompt。処理中 ....."))
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する GPTのリクエストには時間がかかるため,まず、タイムリーに画面を更新します
    if ("advanced_arg" in plugin_kwargs) and (plugin_kwargs["advanced_arg"] == ""): plugin_kwargs.pop("advanced_arg")
    resolution = plugin_kwargs.get("advanced_arg", '1024x1024')
    image_url, image_path = gen_image(llm_kwargs, prompt, resolution)
    chatbot.append([prompt,
        f'画像の中継ウェブサイト: <br/>`{image_url}`<br/>'+
        f'中継ウェブサイトのプレビュー: <br/><div align="center"><img src="{image_url}"></div>'
        f'ローカルファイルアドレス: <br/>`{image_path}`<br/>'+
        f'ローカルファイルのプレビュー: <br/><div align="center"><img src="file={image_path}"></div>'
    ])
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する インターフェースの更新


@CatchException
def ImageGeneration_DALLE3(prompt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    history = []    # 履歴をクリアする,オーバーフローを防ぐために
    if prompt.strip() == "":
        chatbot.append((prompt, "[Local Message] 图像生成ヒント为空白，请在“入力エリア”入力图像生成ヒント。"))
        yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する インターフェースの更新
        return
    chatbot.append(("您正在调用“图像生成”プラグイン。", "[Local Message] 画像を生成する, 请先把模型切换至gpt-*。如果中文Prompt效果不理想, 请Try英文Prompt。処理中 ....."))
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する GPTのリクエストには時間がかかるため,まず、タイムリーに画面を更新します
    if ("advanced_arg" in plugin_kwargs) and (plugin_kwargs["advanced_arg"] == ""): plugin_kwargs.pop("advanced_arg")
    resolution_arg = plugin_kwargs.get("advanced_arg", '1024x1024-standard-vivid').lower()
    parts = resolution_arg.split('-')
    resolution = parts[0] # 解析分辨率
    quality = 'standard' # 质量与风格デフォルト値
    style = 'vivid'
    # 遍历检查是否有额外パラメータ
    for part in parts[1:]:
        if part in ['hd', 'standard']:
            quality = part
        elif part in ['vivid', 'natural']:
            style = part
    image_url, image_path = gen_image(llm_kwargs, prompt, resolution, model="dall-e-3", quality=quality, style=style)
    chatbot.append([prompt,
        f'画像の中継ウェブサイト: <br/>`{image_url}`<br/>'+
        f'中継ウェブサイトのプレビュー: <br/><div align="center"><img src="{image_url}"></div>'
        f'ローカルファイルアドレス: <br/>`{image_path}`<br/>'+
        f'ローカルファイルのプレビュー: <br/><div align="center"><img src="file={image_path}"></div>'
    ])
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する インターフェースの更新


class ImageEditState(GptAcademicState):
    # 尚未完了
    def get_image_file(self, x):
        import os, glob
        if len(x) == 0:             return False, None
        if not os.path.exists(x):   return False, None
        if x.endswith('.png'):      return True, x
        file_manifest = [f for f in glob.glob(f'{x}/**/*.png', recursive=True)]
        confirm = (len(file_manifest) >= 1 and file_manifest[0].endswith('.png') and os.path.exists(file_manifest[0]))
        file = None if not confirm else file_manifest[0]
        return confirm, file

    def lock_plugin(self, chatbot):
        chatbot._cookies['lock_plugin'] = 'crazy_functions.ImageGeneration->ImageModification_DALLE2'
        self.dump_state(chatbot)

    def unlock_plugin(self, chatbot):
        self.reset()
        chatbot._cookies['lock_plugin'] = None
        self.dump_state(chatbot)

    def get_resolution(self, x):
        return (x in ['256x256', '512x512', '1024x1024']), x

    def get_prompt(self, x):
        confirm = (len(x)>=5) and (not self.get_resolution(x)[0]) and (not self.get_image_file(x)[0])
        return confirm, x

    def reset(self):
        self.req = [
            {'value':None, 'description': '请先上传图像（必须是.pngフォーマット）, 然后再次点击本プラグイン',                      'verify_fn': self.get_image_file},
            {'value':None, 'description': '请入力分辨率,オプション：256x256, 512x512 或 1024x1024, 然后再次点击本プラグイン',   'verify_fn': self.get_resolution},
            {'value':None, 'description': '请入力修改需求,提案する您使用する英文ヒント词, 然后再次点击本プラグイン',                 'verify_fn': self.get_prompt},
        ]
        self.info = ""

    def feed(self, prompt, chatbot):
        for r in self.req:
            if r['value'] is None:
                confirm, res = r['verify_fn'](prompt)
                if confirm:
                    r['value'] = res
                    self.dump_state(chatbot)
                    break
        return self

    def next_req(self):
        for r in self.req:
            if r['value'] is None:
                return r['description']
        return "已经收集到所有信息"

    def already_obtained_all_materials(self):
        return all([x['value'] is not None for x in self.req])

@CatchException
def ImageModification_DALLE2(prompt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    # 尚未完了
    history = []    # 履歴をクリアする
    state = ImageEditState.get_state(chatbot, ImageEditState)
    state = state.feed(prompt, chatbot)
    state.lock_plugin(chatbot)
    if not state.already_obtained_all_materials():
        chatbot.append(["图片修改\n\n1. 上传图片（图片中需要修改的位置用橡皮擦擦除为纯白色，即RGB=255,255,255）\n2. 入力分辨率 \n3. 入力修改需求", state.next_req()])
        yield from update_ui(chatbot=chatbot, history=history)
        return

    image_path = state.req[0]['value']
    resolution = state.req[1]['value']
    prompt = state.req[2]['value']
    chatbot.append(["图片修改, 実行中", f"图片:`{image_path}`<br/>分辨率:`{resolution}`<br/>修改需求:`{prompt}`"])
    yield from update_ui(chatbot=chatbot, history=history)
    image_url, image_path = edit_image(llm_kwargs, prompt, image_path, resolution)
    chatbot.append([prompt,
        f'画像の中継ウェブサイト: <br/>`{image_url}`<br/>'+
        f'中継ウェブサイトのプレビュー: <br/><div align="center"><img src="{image_url}"></div>'
        f'ローカルファイルアドレス: <br/>`{image_path}`<br/>'+
        f'ローカルファイルのプレビュー: <br/><div align="center"><img src="file={image_path}"></div>'
    ])
    yield from update_ui(chatbot=chatbot, history=history) # 画面を更新する インターフェースの更新
    state.unlock_plugin(chatbot)

def make_transparent(input_image_path, output_image_path):
    from PIL import Image
    image = Image.open(input_image_path)
    image = image.convert("RGBA")
    data = image.getdata()
    new_data = []
    for item in data:
        if item[0] == 255 and item[1] == 255 and item[2] == 255:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
    image.putdata(new_data)
    image.save(output_image_path, "PNG")

def resize_image(input_path, output_path, max_size=1024):
    from PIL import Image
    with Image.open(input_path) as img:
        width, height = img.size
        if width > max_size or height > max_size:
            if width >= height:
                new_width = max_size
                new_height = int((max_size / width) * height)
            else:
                new_height = max_size
                new_width = int((max_size / height) * width)

            resized_img = img.resize(size=(new_width, new_height))
            resized_img.save(output_path)
        else:
            img.save(output_path)

def make_square_image(input_path, output_path):
    from PIL import Image
    with Image.open(input_path) as img:
        width, height = img.size
        size = max(width, height)
        new_img = Image.new("RGBA", (size, size), color="black")
        new_img.paste(img, ((size - width) // 2, (size - height) // 2))
        new_img.save(output_path)
