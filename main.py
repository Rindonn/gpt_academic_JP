import os; os.environ['no_proxy'] = '*' # プロキシネットワークによる予期しない汚染を回避する

help_menu_description = \
"""GitHubでソースコードが公開されました→(https://github.com/binary-husky/gpt_academic),
開発者たちに心より感謝しています(https://github.com/binary-husky/gpt_academic/graphs/contributors).
</br></br>よく聞いた問題をチェック[プロジェクトのWiki](https://github.com/binary-husky/gpt_academic/wiki),
もしバグが見つかった場合[Bugリクエスト]へお願いいたします。(https://github.com/binary-husky/gpt_academic/issues).
</br></br>対話モードの説明: 1. 問題を入力; 2. 提出をクリック
</br></br>基本機能エリアの説明: 1. テキストを入力; 2. 基本機能エリアでのボタンをクリック
</br></br>関数プラグインエリアの説明: 1. パス／問題を入力, またファイルをアプロード; 2. 関数プラグインエリアでのボタンをクリック
</br></br>VoidTerminalの説明: VoidTerminalをクリック, ヒントによってコマンドを入力した後もう一回VoidTerminalをクリック
</br></br>対話内容を保存したい場合: 保存するボタンをクリック
</br></br>対話内容を音声に変換したい場合: Wikiへアクセスしてください
</br></br>一度API_KEYを変更したい場合: 入力エリアでAPI_KEYを入力し、提出します（リフレッシュした後削除）
"""

def main():
    import gradio as gr
    if gr.__version__ not in ['3.32.9']:
        raise ModuleNotFoundError("Gradioをインストールして一番よい体験をゲット!  `pip install -r requirements.txt` を実行してGradioなどライブラリーをインストールして下さい.")
    from request_llms.bridge_all import predict
    from toolbox import format_io, find_free_port, on_file_uploaded, on_report_generated, get_conf, ArgsGeneralWrapper, load_chat_cookies, DummyWith
    # config_private.pyをコピーして、自分の秘密を入れてください, Such as API and proxy URLs
    proxies, WEB_PORT, LLM_MODEL, CONCURRENT_COUNT, AUTHENTICATION = get_conf('proxies', 'WEB_PORT', 'LLM_MODEL', 'CONCURRENT_COUNT', 'AUTHENTICATION')
    CHATBOT_HEIGHT, LAYOUT, AVAIL_LLM_MODELS, AUTO_CLEAR_TXT = get_conf('CHATBOT_HEIGHT', 'LAYOUT', 'AVAIL_LLM_MODELS', 'AUTO_CLEAR_TXT')
    ENABLE_AUDIO, AUTO_CLEAR_TXT, PATH_LOGGING, AVAIL_THEMES, THEME, ADD_WAIFU = get_conf('ENABLE_AUDIO', 'AUTO_CLEAR_TXT', 'PATH_LOGGING', 'AVAIL_THEMES', 'THEME', 'ADD_WAIFU')
    NUM_CUSTOM_BASIC_BTN, SSL_KEYFILE, SSL_CERTFILE = get_conf('NUM_CUSTOM_BASIC_BTN', 'SSL_KEYFILE', 'SSL_CERTFILE')
    DARK_MODE, INIT_SYS_PROMPT, ADD_WAIFU = get_conf('DARK_MODE', 'INIT_SYS_PROMPT', 'ADD_WAIFU')

    # WEB_PORTが-1の場合, WEBポートをランダムに選択する
    PORT = find_free_port() if WEB_PORT <= 0 else WEB_PORT
    from check_proxy import get_current_version
    from themes.theme import adjust_theme, advanced_css, theme_declaration, js_code_clear, js_code_reset, js_code_show_or_hide, js_code_show_or_hide_group2
    from themes.theme import js_code_for_css_changing, js_code_for_toggle_darkmode, js_code_for_persistent_cookie_init
    from themes.theme import load_dynamic_theme, to_cookie_str, from_cookie_str, init_cookie
    title_html = f"<h1 align=\"center\">学術的GPT {get_current_version()}</h1>{theme_declaration}"

    # 对话记录, Pythonバージョン3.9+を推奨します（新しいほど良い）
    import logging, uuid
    os.makedirs(PATH_LOGGING, exist_ok=True)
    chat_secrets_log = os.path.join(PATH_LOGGING, "chat_secrets.log")
    try:logging.basicConfig(filename=chat_secrets_log, level=logging.INFO, encoding="utf-8", format="%(asctime)s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    except:logging.basicConfig(filename=chat_secrets_log, level=logging.INFO,  format="%(asctime)s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    # Disable logging output from the 'httpx' logger
    logging.getLogger("httpx").setLevel(logging.WARNING)
    print(f"全ての記録をローカルで保存している {chat_secrets_log}, プライバシー保護にご注意してください！")

    # いくつかの一般的な機能モジュール
    from core_functional import get_core_functions
    functional = get_core_functions()

    # 高度な関数プラグイン
    from crazy_functional import get_crazy_functions
    DEFAULT_FN_GROUPS = get_conf('DEFAULT_FN_GROUPS')
    plugins = get_crazy_functions()
    all_plugin_groups = list(set([g for _, plugin in plugins.items() for g in plugin['Group'].split('|')]))
    match_group = lambda tags, groups: any([g in groups for g in tags.split('|')])

    # Markdownテキストのフォーマット変換
    gr.Chatbot.postprocess = format_io

    # 外観の色調整を行う
    set_theme = adjust_theme()

    # プロキシと自動更新
    from check_proxy import check_proxy, auto_update, warm_up_modules
    proxy_info = check_proxy(proxies)

    gr_L1 = lambda: gr.Row().style()
    gr_L2 = lambda scale, elem_id: gr.Column(scale=scale, elem_id=elem_id, min_width=400)
    if LAYOUT == "TOP-DOWN":
        gr_L1 = lambda: DummyWith()
        gr_L2 = lambda scale, elem_id: gr.Row()
        CHATBOT_HEIGHT /= 2

    cancel_handles = []
    customize_btns = {}
    predefined_btns = {}
    with gr.Blocks(title="学術的GPT", theme=set_theme, analytics_enabled=False, css=advanced_css) as demo:
        gr.HTML(title_html)
        secret_css, py_pickle_cookie = gr.Textbox(visible=False), gr.Textbox(visible=False)
        cookies = gr.State(load_chat_cookies())
        with gr_L1():
            with gr_L2(scale=2, elem_id="gpt-chat"):
                chatbot = gr.Chatbot(label=f"Current model：{LLM_MODEL}", elem_id="gpt-chatbot")
                if LAYOUT == "TOP-DOWN":  chatbot.style(height=CHATBOT_HEIGHT)
                history = gr.State([])
            with gr_L2(scale=1, elem_id="gpt-panel"):
                with gr.Accordion("入力エリア", open=True, elem_id="input-panel") as area_input_primary:
                    with gr.Row():
                        txt = gr.Textbox(show_label=False, placeholder="Input question here.", elem_id='user_input_main').style(container=False)
                    with gr.Row():
                        submitBtn = gr.Button("提出", elem_id="elem_submit", variant="primary")
                    with gr.Row():
                        resetBtn = gr.Button("リセット", elem_id="elem_reset", variant="secondary"); resetBtn.style(size="sm")
                        stopBtn = gr.Button("停止", elem_id="elem_stop", variant="secondary"); stopBtn.style(size="sm")
                        clearBtn = gr.Button("クリア", elem_id="elem_clear", variant="secondary", visible=False); clearBtn.style(size="sm")
                    if ENABLE_AUDIO:
                        with gr.Row():
                            audio_mic = gr.Audio(source="microphone", type="numpy", elem_id="elem_audio", streaming=True, show_label=False).style(container=False)
                    with gr.Row():
                        status = gr.Markdown(f"Tip: Enterを押して提出, Shift + Enterで改行。Current model: {LLM_MODEL} \n {proxy_info}", elem_id="state-panel")

                with gr.Accordion("基本的の機能エリア", open=True, elem_id="basic-panel") as area_basic_fn:
                    with gr.Row():
                        for k in range(NUM_CUSTOM_BASIC_BTN):
                            customize_btn = gr.Button("自定义按钮" + str(k+1), visible=False, variant="secondary", info_str=f'基本的の機能エリア: 自定义按钮')
                            customize_btn.style(size="sm")
                            customize_btns.update({"自定义按钮" + str(k+1): customize_btn})
                        for k in functional:
                            if ("Visible" in functional[k]) and (not functional[k]["Visible"]): continue
                            variant = functional[k]["Color"] if "Color" in functional[k] else "secondary"
                            functional[k]["Button"] = gr.Button(k, variant=variant, info_str=f'基本的の機能エリア: {k}')
                            functional[k]["Button"].style(size="sm")
                            predefined_btns.update({k: functional[k]["Button"]})
                with gr.Accordion("関数プラグインエリア", open=True, elem_id="plugin-panel") as area_crazy_fn:
                    with gr.Row():
                        gr.Markdown("プラグインから“入力エリア”のテキストとパスをパラメータとして利用出来ます")
                    with gr.Row(elem_id="input-plugin-group"):
                        plugin_group_sel = gr.Dropdown(choices=all_plugin_groups, label='', show_label=False, value=DEFAULT_FN_GROUPS,
                                                      multiselect=True, interactive=True, elem_classes='normal_mut_select').style(container=False)
                    with gr.Row():
                        for k, plugin in plugins.items():
                            if not plugin.get("AsButton", True): continue
                            visible = True if match_group(plugin['Group'], DEFAULT_FN_GROUPS) else False
                            variant = plugins[k]["Color"] if "Color" in plugin else "secondary"
                            info = plugins[k].get("Info", k)
                            plugin['Button'] = plugins[k]['Button'] = gr.Button(k, variant=variant,
                                visible=visible, info_str=f'関数プラグインエリア: {info}').style(size="sm")
                    with gr.Row():
                        with gr.Accordion("その他の関数プラグイン", open=True):
                            dropdown_fn_list = []
                            for k, plugin in plugins.items():
                                if not match_group(plugin['Group'], DEFAULT_FN_GROUPS): continue
                                if not plugin.get("AsButton", True): dropdown_fn_list.append(k)     # 排除已经是按钮的プラグイン
                                elif plugin.get('AdvancedArgs', False): dropdown_fn_list.append(k)  # 对于需要高级パラメータ的プラグイン，亦在下拉菜单中显示
                            with gr.Row():
                                dropdown = gr.Dropdown(dropdown_fn_list, value=r"プラグインリストを開く", label="", show_label=False).style(container=False)
                            with gr.Row():
                                plugin_advanced_arg = gr.Textbox(show_label=True, label="パラメータ入力エリア", visible=False,
                                                                 placeholder="ここは特殊関数プラグインの高度なパラメータ入力エリアです").style(container=False)
                            with gr.Row():
                                switchy_bt = gr.Button(r"まず、プラグインリストから選択してください", variant="secondary").style(size="sm")
                    with gr.Row():
                        with gr.Accordion("Click：“ファイルダウンロード”。", open=False) as area_file_up:
                            file_upload = gr.Files(label="任意のファイル, ジップファイルがおすすめ(zip, tar)", file_count="multiple", elem_id="elem_upload")

        with gr.Floating(init_x="0%", init_y="0%", visible=True, width=None, drag="forbidden", elem_id="tooltip"):
            with gr.Row():
                with gr.Tab("ファイルアップロード", elem_id="interact-panel"):
                    gr.Markdown("関数プラグインエリアのためローカルファイルをアップロード。注意してください: アプロードした後入力エリアが自動変更。")
                    file_upload_2 = gr.Files(label="任意のファイル, ジップファイルがおすすめ(zip, tar)", file_count="multiple", elem_id="elem_upload_float")

                with gr.Tab("モデル変更", elem_id="interact-panel"):
                    md_dropdown = gr.Dropdown(AVAIL_LLM_MODELS, value=LLM_MODEL, label="LLMモデル/リクエストソースの変更").style(container=False)
                    top_p = gr.Slider(minimum=-0, maximum=1.0, value=1.0, step=0.01,interactive=True, label="Top-p (nucleus sampling)",)
                    temperature = gr.Slider(minimum=-0, maximum=2.0, value=1.0, step=0.01, interactive=True, label="Temperature", elem_id="elem_temperature")
                    max_length_sl = gr.Slider(minimum=256, maximum=1024*32, value=4096, step=128, interactive=True, label="Local LLM MaxLength",)
                    system_prompt = gr.Textbox(show_label=True, lines=2, placeholder=f"System Prompt", label="System prompt", value=INIT_SYS_PROMPT, elem_id="elem_prompt")
                    temperature.change(None, inputs=[temperature], outputs=None,
                        _js="""(temperature)=>gpt_academic_gradio_saveload("save", "elem_prompt", "js_temperature_cookie", temperature)""")
                    system_prompt.change(None, inputs=[system_prompt], outputs=None,
                        _js="""(system_prompt)=>gpt_academic_gradio_saveload("save", "elem_prompt", "js_system_prompt_cookie", system_prompt)""")

                with gr.Tab("主題変更", elem_id="interact-panel"):
                    theme_dropdown = gr.Dropdown(AVAIL_THEMES, value=THEME, label="更换UI主题").style(container=False)
                    checkboxes = gr.CheckboxGroup(["基本機能エリア", "関数プラグインエリア", "浮动入力エリア", "入力クリアキー", "プラグインパラメータエリア"], value=["基本機能エリア", "関数プラグインエリア"], label="Show/hide the function area", elem_id='cbs').style(container=False)
                    opt = ["自定义菜单"]
                    value=[]
                    if ADD_WAIFU: opt += ["添加Live2D形象"]; value += ["添加Live2D形象"]
                    checkboxes_2 = gr.CheckboxGroup(opt, value=value, label="显示/隐藏自定义菜单", elem_id='cbsc').style(container=False)
                    dark_mode_btn = gr.Button("切换界面明暗 ☀", variant="secondary").style(size="sm")
                    dark_mode_btn.click(None, None, None, _js=js_code_for_toggle_darkmode)
                with gr.Tab("ヘルプ", elem_id="interact-panel"):
                    gr.Markdown(help_menu_description)

        with gr.Floating(init_x="20%", init_y="50%", visible=False, width="40%", drag="top") as area_input_secondary:
            with gr.Accordion("浮动入力エリア", open=True, elem_id="input-panel2"):
                with gr.Row() as row:
                    row.style(equal_height=True)
                    with gr.Column(scale=10):
                        txt2 = gr.Textbox(show_label=False, placeholder="Input question here.",
                                          elem_id='user_input_float', lines=8, label="Input area 2").style(container=False)
                    with gr.Column(scale=1, min_width=40):
                        submitBtn2 = gr.Button("提出", variant="primary"); submitBtn2.style(size="sm")
                        resetBtn2 = gr.Button("リセット", variant="secondary"); resetBtn2.style(size="sm")
                        stopBtn2 = gr.Button("停止", variant="secondary"); stopBtn2.style(size="sm")
                        clearBtn2 = gr.Button("クリア", elem_id="elem_clear2", variant="secondary", visible=False); clearBtn2.style(size="sm")


        with gr.Floating(init_x="20%", init_y="50%", visible=False, width="40%", drag="top") as area_customize:
            with gr.Accordion("自定义菜单", open=True, elem_id="edit-panel"):
                with gr.Row() as row:
                    with gr.Column(scale=10):
                        AVAIL_BTN = [btn for btn in customize_btns.keys()] + [k for k in functional]
                        basic_btn_dropdown = gr.Dropdown(AVAIL_BTN, value="自定义按钮1", label="选择一pieces需要自定义基本機能エリア按钮").style(container=False)
                        basic_fn_title = gr.Textbox(show_label=False, placeholder="入力新按钮名称", lines=1).style(container=False)
                        basic_fn_prefix = gr.Textbox(show_label=False, placeholder="入力新ヒントテキストの翻訳", lines=4).style(container=False)
                        basic_fn_suffix = gr.Textbox(show_label=False, placeholder="入力新ヒント后缀", lines=4).style(container=False)
                    with gr.Column(scale=1, min_width=70):
                        basic_fn_confirm = gr.Button("確認と保存", variant="primary"); basic_fn_confirm.style(size="sm")
                        basic_fn_clean   = gr.Button("リセット", variant="primary"); basic_fn_clean.style(size="sm")
                        def assign_btn(persistent_cookie_, cookies_, basic_btn_dropdown_, basic_fn_title, basic_fn_prefix, basic_fn_suffix, clean_up=False):
                            ret = {}
                            # 读取之前的自定义按钮
                            customize_fn_overwrite_ = cookies_['customize_fn_overwrite']
                            # 更新新的自定义按钮
                            customize_fn_overwrite_.update({
                                basic_btn_dropdown_:
                                    {
                                        "Title":basic_fn_title,
                                        "Prefix":basic_fn_prefix,
                                        "Suffix":basic_fn_suffix,
                                    }
                                }
                            )
                            if clean_up:
                                customize_fn_overwrite_ = {}
                            cookies_.update(customize_fn_overwrite_)    # 更新cookie
                            visible = (not clean_up) and (basic_fn_title != "")
                            if basic_btn_dropdown_ in customize_btns:
                                # 是自定义按钮，不是预定义按钮
                                ret.update({customize_btns[basic_btn_dropdown_]: gr.update(visible=visible, value=basic_fn_title)})
                            else:
                                # 是预定义按钮
                                ret.update({predefined_btns[basic_btn_dropdown_]: gr.update(visible=visible, value=basic_fn_title)})
                            ret.update({cookies: cookies_})
                            try: persistent_cookie_ = from_cookie_str(persistent_cookie_)   # persistent cookie to dict
                            except: persistent_cookie_ = {}
                            persistent_cookie_["custom_bnt"] = customize_fn_overwrite_      # dict update new value
                            persistent_cookie_ = to_cookie_str(persistent_cookie_)          # persistent cookie to dict
                            ret.update({py_pickle_cookie: persistent_cookie_})             # write persistent cookie
                            return ret

                        # update btn
                        h = basic_fn_confirm.click(assign_btn, [py_pickle_cookie, cookies, basic_btn_dropdown, basic_fn_title, basic_fn_prefix, basic_fn_suffix],
                                                   [py_pickle_cookie, cookies, *customize_btns.values(), *predefined_btns.values()])
                        h.then(None, [py_pickle_cookie], None, _js="""(py_pickle_cookie)=>{setCookie("py_pickle_cookie", py_pickle_cookie, 365);}""")
                        # clean up btn
                        h2 = basic_fn_clean.click(assign_btn, [py_pickle_cookie, cookies, basic_btn_dropdown, basic_fn_title, basic_fn_prefix, basic_fn_suffix, gr.State(True)],
                                                   [py_pickle_cookie, cookies, *customize_btns.values(), *predefined_btns.values()])
                        h2.then(None, [py_pickle_cookie], None, _js="""(py_pickle_cookie)=>{setCookie("py_pickle_cookie", py_pickle_cookie, 365);}""")

                        def persistent_cookie_reload(persistent_cookie_, cookies_):
                            ret = {}
                            for k in customize_btns:
                                ret.update({customize_btns[k]: gr.update(visible=False, value="")})

                            try: persistent_cookie_ = from_cookie_str(persistent_cookie_)    # persistent cookie to dict
                            except: return ret

                            customize_fn_overwrite_ = persistent_cookie_.get("custom_bnt", {})
                            cookies_['customize_fn_overwrite'] = customize_fn_overwrite_
                            ret.update({cookies: cookies_})

                            for k,v in persistent_cookie_["custom_bnt"].items():
                                if v['Title'] == "": continue
                                if k in customize_btns: ret.update({customize_btns[k]: gr.update(visible=True, value=v['Title'])})
                                else: ret.update({predefined_btns[k]: gr.update(visible=True, value=v['Title'])})
                            return ret

        # 機能エリアの表示スイッチと機能エリアの相互作用
        def fn_area_visibility(a):
            ret = {}
            ret.update({area_input_primary: gr.update(visible=("浮动入力エリア" not in a))})
            ret.update({area_input_secondary: gr.update(visible=("浮动入力エリア" in a))})
            ret.update({plugin_advanced_arg: gr.update(visible=("プラグインパラメータエリア" in a))})
            if "浮动入力エリア" in a: ret.update({txt: gr.update(value="")})
            return ret
        checkboxes.select(fn_area_visibility, [checkboxes], [area_basic_fn, area_crazy_fn, area_input_primary, area_input_secondary, txt, txt2, plugin_advanced_arg] )
        checkboxes.select(None, [checkboxes], None, _js=js_code_show_or_hide)

        # 機能エリアの表示スイッチと機能エリアの相互作用
        def fn_area_visibility_2(a):
            ret = {}
            ret.update({area_customize: gr.update(visible=("自定义菜单" in a))})
            return ret
        checkboxes_2.select(fn_area_visibility_2, [checkboxes_2], [area_customize] )
        checkboxes_2.select(None, [checkboxes_2], None, _js=js_code_show_or_hide_group2)

        # 繰り返し出現するコントロールハンドルの組み合わせを整理する
        input_combo = [cookies, max_length_sl, md_dropdown, txt, txt2, top_p, temperature, chatbot, history, system_prompt, plugin_advanced_arg]
        output_combo = [cookies, chatbot, history, status]
        predict_args = dict(fn=ArgsGeneralWrapper(predict), inputs=[*input_combo, gr.State(True)], outputs=output_combo)
        # 送信ボタン、リセットボタン
        cancel_handles.append(txt.submit(**predict_args))
        cancel_handles.append(txt2.submit(**predict_args))
        cancel_handles.append(submitBtn.click(**predict_args))
        cancel_handles.append(submitBtn2.click(**predict_args))
        resetBtn.click(None, None, [chatbot, history, status], _js=js_code_reset)   # 先在前端快速クリアchatbot&status
        resetBtn2.click(None, None, [chatbot, history, status], _js=js_code_reset)  # 先在前端快速クリアchatbot&status
        resetBtn.click(lambda: ([], [], "リセットされました"), None, [chatbot, history, status])    # 再在后端クリアhistory
        resetBtn2.click(lambda: ([], [], "リセットされました"), None, [chatbot, history, status])   # 再在后端クリアhistory
        clearBtn.click(None, None, [txt, txt2], _js=js_code_clear)
        clearBtn2.click(None, None, [txt, txt2], _js=js_code_clear)
        if AUTO_CLEAR_TXT:
            submitBtn.click(None, None, [txt, txt2], _js=js_code_clear)
            submitBtn2.click(None, None, [txt, txt2], _js=js_code_clear)
            txt.submit(None, None, [txt, txt2], _js=js_code_clear)
            txt2.submit(None, None, [txt, txt2], _js=js_code_clear)
        # 基本機能エリアのコールバック関数の登録
        for k in functional:
            if ("Visible" in functional[k]) and (not functional[k]["Visible"]): continue
            click_handle = functional[k]["Button"].click(fn=ArgsGeneralWrapper(predict), inputs=[*input_combo, gr.State(True), gr.State(k)], outputs=output_combo)
            cancel_handles.append(click_handle)
        for btn in customize_btns.values():
            click_handle = btn.click(fn=ArgsGeneralWrapper(predict), inputs=[*input_combo, gr.State(True), gr.State(btn.value)], outputs=output_combo)
            cancel_handles.append(click_handle)
        # ファイルアップロードエリア，ファイルを受信した後、chatbotとのインタラクション
        file_upload.upload(on_file_uploaded, [file_upload, chatbot, txt, txt2, checkboxes, cookies], [chatbot, txt, txt2, cookies]).then(None, None, None,   _js=r"()=>{toast_push('上传完毕 ...'); cancel_loading_status();}")
        file_upload_2.upload(on_file_uploaded, [file_upload_2, chatbot, txt, txt2, checkboxes, cookies], [chatbot, txt, txt2, cookies]).then(None, None, None, _js=r"()=>{toast_push('上传完毕 ...'); cancel_loading_status();}")
        # 関数プラグイン-固定ボタンエリア
        for k in plugins:
            if not plugins[k].get("AsButton", True): continue
            click_handle = plugins[k]["Button"].click(ArgsGeneralWrapper(plugins[k]["Function"]), [*input_combo], output_combo)
            click_handle.then(on_report_generated, [cookies, file_upload, chatbot], [cookies, file_upload, chatbot])
            cancel_handles.append(click_handle)
        # 関数プラグイン-ドロップダウンメニューと可変ボタンの相互作用
        def on_dropdown_changed(k):
            variant = plugins[k]["Color"] if "Color" in plugins[k] else "secondary"
            info = plugins[k].get("Info", k)
            ret = {switchy_bt: gr.update(value=k, variant=variant, info_str=f'関数プラグインエリア: {info}')}
            if plugins[k].get("AdvancedArgs", False): # Whether to call the advanced plugin parameter area
                ret.update({plugin_advanced_arg: gr.update(visible=True,  label=f"プラグイン[{k}]高度なパラメータの説明：" + plugins[k].get("ArgsReminder", [f"高度なパラメータ機能の説明が提供されていません"]))})
            else:
                ret.update({plugin_advanced_arg: gr.update(visible=False, label=f"プラグイン[{k}]No advanced parameters required。")})
            return ret
        dropdown.select(on_dropdown_changed, [dropdown], [switchy_bt, plugin_advanced_arg] )

        def on_md_dropdown_changed(k):
            return {chatbot: gr.update(label="Current model："+k)}
        md_dropdown.select(on_md_dropdown_changed, [md_dropdown], [chatbot] )

        def on_theme_dropdown_changed(theme, secret_css):
            adjust_theme, css_part1, _, adjust_dynamic_theme = load_dynamic_theme(theme)
            if adjust_dynamic_theme:
                css_part2 = adjust_dynamic_theme._get_theme_css()
            else:
                css_part2 = adjust_theme()._get_theme_css()
            return css_part2 + css_part1

        theme_handle = theme_dropdown.select(on_theme_dropdown_changed, [theme_dropdown, secret_css], [secret_css])
        theme_handle.then(
            None,
            [secret_css],
            None,
            _js=js_code_for_css_changing
        )
        # 可変ボタンのコールバック関数の登録
        def route(request: gr.Request, k, *args, **kwargs):
            if k in [r"プラグインリストを開く", r"まず、プラグインリストから選択してください"]: return
            yield from ArgsGeneralWrapper(plugins[k]["Function"])(request, *args, **kwargs)
        click_handle = switchy_bt.click(route,[switchy_bt, *input_combo], output_combo)
        click_handle.then(on_report_generated, [cookies, file_upload, chatbot], [cookies, file_upload, chatbot])
        cancel_handles.append(click_handle)
        # 停止ボタンのコールバック関数の登録
        stopBtn.click(fn=None, inputs=None, outputs=None, cancels=cancel_handles)
        stopBtn2.click(fn=None, inputs=None, outputs=None, cancels=cancel_handles)
        plugins_as_btn = {name:plugin for name, plugin in plugins.items() if plugin.get('Button', None)}
        def on_group_change(group_list):
            btn_list = []
            fns_list = []
            if not group_list: # 处理特殊情况：没有选择任何プラグイン组
                return [*[plugin['Button'].update(visible=False) for _, plugin in plugins_as_btn.items()], gr.Dropdown.update(choices=[])]
            for k, plugin in plugins.items():
                if plugin.get("AsButton", True):
                    btn_list.append(plugin['Button'].update(visible=match_group(plugin['Group'], group_list))) # 刷新按钮
                    if plugin.get('AdvancedArgs', False): dropdown_fn_list.append(k) # 对于需要高级パラメータ的プラグイン，亦在下拉菜单中显示
                elif match_group(plugin['Group'], group_list): fns_list.append(k) # 刷新下拉リスト
            return [*btn_list, gr.Dropdown.update(choices=fns_list)]
        plugin_group_sel.select(fn=on_group_change, inputs=[plugin_group_sel], outputs=[*[plugin['Button'] for name, plugin in plugins_as_btn.items()], dropdown])
        if ENABLE_AUDIO:
            from crazy_functions.live_audio.audio_io import RealtimeAudioDistribution
            rad = RealtimeAudioDistribution()
            def deal_audio(audio, cookies):
                rad.feed(cookies['uuid'].hex, audio)
            audio_mic.stream(deal_audio, inputs=[audio_mic, cookies])


        demo.load(init_cookie, inputs=[cookies], outputs=[cookies])
        demo.load(persistent_cookie_reload, inputs = [py_pickle_cookie, cookies],
            outputs = [py_pickle_cookie, cookies, *customize_btns.values(), *predefined_btns.values()], _js=js_code_for_persistent_cookie_init)
        demo.load(None, inputs=[], outputs=None, _js=f"""()=>init_frontend_with_cookies("{DARK_MODE}","{INIT_SYS_PROMPT}","{ADD_WAIFU}")""")    # 配置ダークテーマ或明るいテーマ
        demo.load(None, inputs=[gr.Textbox(LAYOUT, visible=False)], outputs=None, _js='(LAYOUT)=>{GptAcademicJavaScriptInit(LAYOUT);}')

    # Gradioのinbrowserトリガーはあまり安定していません，コードを元のブラウザ開く関数にロールバックする
    def run_delayed_tasks():
        import threading, webbrowser, time
        print(f"ブラウザが自動的に開かない場合，以下のURLをコピーして移動してください：")
        if DARK_MODE:   print(f"\t「ダークテーマオン」: http://localhost:{PORT}")
        else:           print(f"\t「明るいテーマオン」: http://localhost:{PORT}")

        def auto_updates(): time.sleep(0); auto_update()
        def open_browser(): time.sleep(2); webbrowser.open_new_tab(f"http://localhost:{PORT}")
        def warm_up_mods(): time.sleep(6); warm_up_modules()

        threading.Thread(target=auto_updates, name="self-upgrade", daemon=True).start() # 查看自动更新
        threading.Thread(target=open_browser, name="open-browser", daemon=True).start() # ブラウザを開く页面
        threading.Thread(target=warm_up_mods, name="warm-up", daemon=True).start()      # 预热tiktoken模块

    run_delayed_tasks()
    demo.queue(concurrency_count=CONCURRENT_COUNT).launch(
        quiet=True,
        server_name="0.0.0.0",
        ssl_keyfile=None if SSL_KEYFILE == "" else SSL_KEYFILE,
        ssl_certfile=None if SSL_CERTFILE == "" else SSL_CERTFILE,
        ssl_verify=False,
        server_port=PORT,
        favicon_path=os.path.join(os.path.dirname(__file__), "docs/logo.png"),
        auth=AUTHENTICATION if len(AUTHENTICATION) != 0 else None,
        blocked_paths=["config.py","__pycache__","config_private.py","docker-compose.yml","Dockerfile",f"{PATH_LOGGING}/admin", chat_secrets_log])

if __name__ == "__main__":
    main()
