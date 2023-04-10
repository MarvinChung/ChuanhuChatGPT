# -*- coding:utf-8 -*-
import os
import logging
import sys

import gradio as gr

from modules import config
from modules.config import *
from modules.utils import *
from modules.presets import *
from modules.overwrites import *
from modules.models import ModelManager

gr.Chatbot.postprocess = postprocess
PromptHelper.compact_text_chunks = compact_text_chunks

with open("assets/custom.css", "r", encoding="utf-8") as f:
    customCSS = f.read()

with gr.Blocks(css=customCSS, theme=small_and_beautiful_theme) as demo:
    user_name = gr.State("")
    promptTemplates = gr.State(load_template(get_template_names(plain=True)[0], mode=2))
    user_question = gr.State("")
    current_model = gr.State(ModelManager(model_name = MODELS[DEFAULT_MODEL], access_key = my_api_key))

    topic = gr.State("未命名對話歷史記錄")

    with gr.Row():
        gr.HTML(CHUANHU_TITLE, elem_id="app_title")
        status_display = gr.Markdown(get_geoip(), elem_id="status_display")
    with gr.Row(elem_id="float_display"):
        user_info = gr.Markdown(value="getting user info...", elem_id="user_info")

        # https://github.com/gradio-app/gradio/pull/3296
        def create_greeting(request: gr.Request):
            if hasattr(request, "username") and request.username: # is not None or is not ""
                logging.info(f"Get User Name: {request.username}")
                return gr.Markdown.update(value=f"User: {request.username}"), request.username
            else:
                return gr.Markdown.update(value=f"User: default", visible=False), ""
        demo.load(create_greeting, inputs=None, outputs=[user_info, user_name])

    with gr.Row().style(equal_height=True):
        with gr.Column(scale=5):
            with gr.Row():
                chatbot = gr.Chatbot(elem_id="chuanhu_chatbot").style(height="100%")
            with gr.Row():
                with gr.Column(min_width=225, scale=12):
                    user_input = gr.Textbox(
                        elem_id="user_input_tb",
                        show_label=False, placeholder="在這裡輸入"
                    ).style(container=False)
                with gr.Column(min_width=42, scale=1):
                    submitBtn = gr.Button(value="", variant="primary", elem_id="submit_btn")
                    cancelBtn = gr.Button(value="", variant="secondary", visible=False, elem_id="cancel_btn")
            with gr.Row():
                emptyBtn = gr.Button(
                    "🧹 新的對話",
                )
                retryBtn = gr.Button("🔄 重新生成")
                delFirstBtn = gr.Button("🗑️ 刪除最舊對話")
                delLastBtn = gr.Button("🗑️ 刪除最新內容")

        with gr.Column():
            with gr.Column(min_width=50, scale=1):
                with gr.Tab(label="模型"):
                    
                    model_select_dropdown = gr.Dropdown(
                        label="選擇模型", choices=MODELS, multiselect=False, value=MODELS[DEFAULT_MODEL], interactive=True
                    )
                    lora_select_dropdown = gr.Dropdown(
                        label="選擇LoRA模型", choices=[], multiselect=False, interactive=True, visible=False
                    )
                    use_streaming_checkbox = gr.Checkbox(
                        label="實時傳輸回答", value=True, visible=False#visible=ENABLE_STREAMING_OPTION
                    )
                    use_websearch_checkbox = gr.Checkbox(label="使用在線搜索", value=False, visible=False)
                    language_select_dropdown = gr.Dropdown(
                        label="選擇回覆語言 (針對搜索&索引功能) ",
                        choices=REPLY_LANGUAGES,
                        multiselect=False,
                        value=REPLY_LANGUAGES[0],
                    )
                    index_files = gr.Files(label="上傳索引文件", type="file", visible=False)
                    two_column = gr.Checkbox(label="雙欄pdf", value=advance_docs["pdf"].get("two_column", False), visible=False)
                    # TODO: 公式ocr
                    # formula_ocr = gr.Checkbox(label="识别公式", value=advance_docs["pdf"].get("formula_ocr", False))


                # with gr.Tab(label="Prompt"):
                    systemPromptTxt = gr.Textbox(
                        show_label=True,
                        placeholder=f"在這裡輸入System Prompt...",
                        label="System prompt",
                        value=INITIAL_SYSTEM_PROMPT,
                        lines=10,
                        visible=False
                    ).style(container=False)
                    with gr.Accordion(label="加載Prompt模板", open=True, visible=False):
                        with gr.Column():
                            with gr.Row():
                                with gr.Column(scale=6):
                                    templateFileSelectDropdown = gr.Dropdown(
                                        label="選擇Prompt模板集合文件",
                                        choices=get_template_names(plain=True),
                                        multiselect=False,
                                        value=get_template_names(plain=True)[0],
                                    ).style(container=False)
                                with gr.Column(scale=1):
                                    templateRefreshBtn = gr.Button("🔄 刷新")
                            with gr.Row():
                                with gr.Column():
                                    templateSelectDropdown = gr.Dropdown(
                                        label="從Prompt模板中加載",
                                        choices=load_template(
                                            get_template_names(plain=True)[0], mode=1
                                        ),
                                        multiselect=False,
                                    ).style(container=False)


                # with gr.Tab(label="保存/加載"):
                    with gr.Accordion(label="保存/加載對話歷史紀錄", open=True, visible=False):
                        with gr.Column():
                            with gr.Row():
                                with gr.Column(scale=6):
                                    historyFileSelectDropdown = gr.Dropdown(
                                        label="從列表中加載對話",
                                        choices=get_history_names(plain=True),
                                        multiselect=False,
                                        value=get_history_names(plain=True)[0],
                                    )
                                with gr.Column(scale=1):
                                    historyRefreshBtn = gr.Button("🔄 刷新")
                            with gr.Row():
                                with gr.Column(scale=6):
                                    saveFileName = gr.Textbox(
                                        show_label=True,
                                        placeholder=f"設置文件名: 默認為.json，可選為.md",
                                        label="設置保存文件名",
                                        value="對話歷史紀錄",
                                    ).style(container=True)
                                with gr.Column(scale=1):
                                    saveHistoryBtn = gr.Button("💾 保存對話")
                                    exportMarkdownBtn = gr.Button("📝 導出為Markdown")
                                    gr.Markdown("默認保存於history文件夾")
                            with gr.Row():
                                with gr.Column():
                                    downloadFile = gr.File(interactive=True)

                # with gr.Tab(label="高級"):
                    # gr.Markdown("# ⚠️ 務必謹慎更改 ⚠️\n\n如果無法使用請恢復默認設置")
                    # gr.HTML(APPEARANCE_SWITCHER, elem_classes="insert_block")
                    with gr.Accordion("Hyperparameters", open=True):
                        temperature_slider = gr.Slider(
                            minimum=-0,
                            maximum=2.0,
                            value=1.0,
                            step=0.1,
                            interactive=True,
                            label="temperature",
                        )
                        top_p_slider = gr.Slider(
                            minimum=-0,
                            maximum=1.0,
                            value=0.95,
                            step=0.05,
                            interactive=True,
                            label="top-p",
                        )
                        n_choices_slider = gr.Slider(
                            minimum=1,
                            maximum=3,
                            value=1,
                            step=1,
                            interactive=True,
                            label="n choices",
                        )
                        stop_sequence_txt = gr.Textbox(
                            show_label=True,
                            placeholder=f"在這裡輸入停止符號，用英文逗號隔開...",
                            label="stop",
                            value="",
                            lines=1,
                            visible=False
                        )
                        max_context_length_slider = gr.Slider(
                            minimum=1,
                            maximum=64,
                            value=16,
                            step=1,
                            interactive=True,
                            label="max token"
                        )
                        max_generation_slider = gr.Slider(
                            minimum=1,
                            maximum=32768,
                            value=1000,
                            step=1,
                            interactive=True,
                            label="max generations",
                            visible=False
                        )
                        presence_penalty_slider = gr.Slider(
                            minimum=-2.0,
                            maximum=2.0,
                            value=0.0,
                            step=0.01,
                            interactive=True,
                            label="presence penalty",
                            visible=False
                        )
                        frequency_penalty_slider = gr.Slider(
                            minimum=-2.0,
                            maximum=2.0,
                            value=0.0,
                            step=0.01,
                            interactive=True,
                            label="frequency penalty",
                        )
                        logit_bias_txt = gr.Textbox(
                            show_label=True,
                            placeholder=f"word:likelihood",
                            label="logit bias",
                            value="",
                            lines=1,
                            visible=False
                        )
                        user_identifier_txt = gr.Textbox(
                            show_label=True,
                            placeholder=f"用於定位濫用行為",
                            label="用戶名",
                            value=user_name.value,
                            lines=1,
                            visible=False
                        )

                        default_btn = gr.Button("🔙 恢復預設值")


                    with gr.Accordion("網路設置", open=False, visible=False):
                        # 优先展示自定义的api_host
                        apihostTxt = gr.Textbox(
                            show_label=True,
                            placeholder=f"在這裡輸入API-Host...",
                            label="API-Host",
                            value=config.api_host or shared.API_HOST,
                            lines=1,
                        )
                        changeAPIURLBtn = gr.Button("🔄 切換API地址")
                        proxyTxt = gr.Textbox(
                            show_label=True,
                            placeholder=f"在這裡輸入代理地址...",
                            label="代理地址 (範例: http://127.0.0.1:10809) ",
                            value="",
                            lines=2,
                        )
                        changeProxyBtn = gr.Button("🔄 設置代理地址")
                        # default_btn = gr.Button("🔙 恢復默認設置")
                
                with gr.Tab("API key"):
                    keyTxt = gr.Textbox(
                        show_label=True,
                        placeholder=f"Playground API-key...",
                        value=hide_middle_chars(my_api_key),
                        type="password",
                        visible=not HIDE_MY_KEY,
                        label="API-Key",
                    )
                    if multi_api_key:
                        usageTxt = gr.Markdown("多帳號模式已開啟，無需輸入key，可直接開始對話", elem_id="usage_display", elem_classes="insert_block", visible=False)
                    else:
                        usageTxt = gr.Markdown("**發送消息** 或 **提交key** 以顯示額度", elem_id="usage_display", elem_classes="insert_block", visible=False)
                        

    gr.Markdown(CHUANHU_DESCRIPTION)
    gr.HTML(FOOTER.format(versions=versions_html()), elem_id="footer")
    chatgpt_predict_args = dict(
        fn=current_model.value.predict,
        inputs=[
            user_question,
            chatbot,
            use_streaming_checkbox,
            use_websearch_checkbox,
            index_files,
            language_select_dropdown,
        ],
        outputs=[chatbot, status_display],
        show_progress=True,
    )

    start_outputing_args = dict(
        fn=start_outputing,
        inputs=[],
        outputs=[submitBtn, cancelBtn],
        show_progress=True,
    )

    end_outputing_args = dict(
        fn=end_outputing, inputs=[], outputs=[submitBtn, cancelBtn]
    )

    reset_textbox_args = dict(
        fn=reset_textbox, inputs=[], outputs=[user_input]
    )

    transfer_input_args = dict(
        fn=transfer_input, inputs=[user_input], outputs=[user_question, user_input, submitBtn, cancelBtn], show_progress=True
    )

    get_usage_args = dict(
        fn=current_model.value.billing_info, inputs=None, outputs=[usageTxt], show_progress=False
    )

    load_history_from_file_args = dict(
        fn=current_model.value.load_chat_history,
        inputs=[historyFileSelectDropdown, chatbot, user_name],
        outputs=[saveFileName, systemPromptTxt, chatbot]
    )


    # Chatbot
    cancelBtn.click(current_model.value.interrupt, [], [])

    user_input.submit(**transfer_input_args).then(**chatgpt_predict_args).then(**end_outputing_args)
    user_input.submit(**get_usage_args)

    submitBtn.click(**transfer_input_args).then(**chatgpt_predict_args).then(**end_outputing_args)
    submitBtn.click(**get_usage_args)

    emptyBtn.click(
        current_model.value.reset,
        outputs=[chatbot, status_display],
        show_progress=True,
    )
    emptyBtn.click(**reset_textbox_args)

    retryBtn.click(**start_outputing_args).then(
        current_model.value.retry,
        [
            chatbot,
            use_streaming_checkbox,
            use_websearch_checkbox,
            index_files,
            language_select_dropdown,
        ],
        [chatbot, status_display],
        show_progress=True,
    ).then(**end_outputing_args)
    retryBtn.click(**get_usage_args)

    delFirstBtn.click(
        current_model.value.delete_first_conversation,
        None,
        [status_display],
    )

    delLastBtn.click(
        current_model.value.delete_last_conversation,
        [chatbot],
        [chatbot, status_display],
        show_progress=False
    )

    two_column.change(update_doc_config, [two_column], None)

    # LLM Models
    keyTxt.change(current_model.value.set_key, keyTxt, [status_display]).then(**get_usage_args)
    keyTxt.submit(**get_usage_args)
    model_select_dropdown.change(current_model.value.get_model, [model_select_dropdown, lora_select_dropdown, keyTxt, temperature_slider, top_p_slider, systemPromptTxt], [status_display, lora_select_dropdown], show_progress=True)
    lora_select_dropdown.change(current_model.value.get_model, [model_select_dropdown, lora_select_dropdown, keyTxt, temperature_slider, top_p_slider, systemPromptTxt], [status_display], show_progress=True)

    # Template
    systemPromptTxt.change(current_model.value.set_system_prompt, [systemPromptTxt], None)
    templateRefreshBtn.click(get_template_names, None, [templateFileSelectDropdown])
    templateFileSelectDropdown.change(
        load_template,
        [templateFileSelectDropdown],
        [promptTemplates, templateSelectDropdown],
        show_progress=True,
    )
    templateSelectDropdown.change(
        get_template_content,
        [promptTemplates, templateSelectDropdown, systemPromptTxt],
        [systemPromptTxt],
        show_progress=True,
    )

    # S&L
    saveHistoryBtn.click(
        current_model.value.save_chat_history,
        [saveFileName, chatbot, user_name],
        downloadFile,
        show_progress=True,
    )
    saveHistoryBtn.click(get_history_names, [gr.State(False), user_name], [historyFileSelectDropdown])
    exportMarkdownBtn.click(
        current_model.value.export_markdown,
        [saveFileName, chatbot, user_name],
        downloadFile,
        show_progress=True,
    )
    historyRefreshBtn.click(get_history_names, [gr.State(False), user_name], [historyFileSelectDropdown])
    historyFileSelectDropdown.change(**load_history_from_file_args)
    downloadFile.change(**load_history_from_file_args)

    # Advanced
    max_context_length_slider.change(current_model.value.set_token_upper_limit, [max_context_length_slider], None)
    temperature_slider.change(current_model.value.set_temperature, [temperature_slider], None)
    top_p_slider.change(current_model.value.set_top_p, [top_p_slider], None)
    n_choices_slider.change(current_model.value.set_n_choices, [n_choices_slider], None)
    stop_sequence_txt.change(current_model.value.set_stop_sequence, [stop_sequence_txt], None)
    max_generation_slider.change(current_model.value.set_max_tokens, [max_generation_slider], None)
    presence_penalty_slider.change(current_model.value.set_presence_penalty, [presence_penalty_slider], None)
    frequency_penalty_slider.change(current_model.value.set_frequency_penalty, [frequency_penalty_slider], None)
    logit_bias_txt.change(current_model.value.set_logit_bias, [logit_bias_txt], None)
    user_identifier_txt.change(current_model.value.set_user_identifier, [user_identifier_txt], None)

    default_btn.click(
        reset_default, [], [apihostTxt, proxyTxt, status_display], show_progress=True
    )
    changeAPIURLBtn.click(
        change_api_host,
        [apihostTxt],
        [status_display],
        show_progress=True,
    )
    changeProxyBtn.click(
        change_proxy,
        [proxyTxt],
        [status_display],
        show_progress=True,
    )

logging.info(
    colorama.Back.GREEN
    + "\n溫馨提示：訪問 http://localhost:7860 查看介面"
    + colorama.Style.RESET_ALL
)
# 默认开启本地服务器，默认可以直接从IP访问，默认不创建公开分享链接
demo.title = "Playground"

if __name__ == "__main__":
    reload_javascript()
    # if running in Docker
    if dockerflag:
        if authflag:
            demo.queue(concurrency_count=CONCURRENT_COUNT).launch(
                server_name="0.0.0.0",
                server_port=7860,
                auth=auth_list,
                favicon_path="./assets/favicon.ico",
            )
        else:
            demo.queue(concurrency_count=CONCURRENT_COUNT).launch(
                server_name="0.0.0.0",
                server_port=7860,
                share=False,
                favicon_path="./assets/favicon.ico",
            )
    # if not running in Docker
    else:
        if authflag:
            demo.queue(concurrency_count=CONCURRENT_COUNT).launch(
                share=False,
                auth=auth_list,
                favicon_path="./assets/favicon.ico",
                inbrowser=True,
            )
        else:
            demo.queue(concurrency_count=CONCURRENT_COUNT).launch(
                share=False, favicon_path="./assets/favicon.ico", inbrowser=True
            )  # 改为 share=True 可以创建公开分享链接
        # demo.queue(concurrency_count=CONCURRENT_COUNT).launch(server_name="0.0.0.0", server_port=7860, share=False) # 可自定义端口
        # demo.queue(concurrency_count=CONCURRENT_COUNT).launch(server_name="0.0.0.0", server_port=7860,auth=("在这里填写用户名", "在这里填写密码")) # 可设置用户名与密码
        # demo.queue(concurrency_count=CONCURRENT_COUNT).launch(auth=("在这里填写用户名", "在这里填写密码")) # 适合Nginx反向代理
