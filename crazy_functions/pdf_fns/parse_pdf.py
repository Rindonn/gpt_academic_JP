#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@ Author: Rindon
@ Date: 2024-05-13 09:42:46
@ LastEditors: Rindon
@ LastEditTime: 2024-05-21 16:01:08
@ Description: prompt、インターフェースを日本語に変更
'''
from functools import lru_cache
from toolbox import gen_time_str
from toolbox import promote_file_to_downloadzone
from toolbox import write_history_to_file, promote_file_to_downloadzone
from toolbox import get_conf
from toolbox import ProxyNetworkActivate
from colorful import *
import requests
import random
import copy
import os
import math

class GROBID_OFFLINE_EXCEPTION(Exception): pass

def get_avail_grobid_url():
    GROBID_URLS = get_conf('GROBID_URLS')
    if len(GROBID_URLS) == 0: return None
    try:
        _grobid_url = random.choice(GROBID_URLS) # ランダムな負荷分散
        if _grobid_url.endswith('/'): _grobid_url = _grobid_url.rstrip('/')
        with ProxyNetworkActivate('Connect_Grobid'):
            res = requests.get(_grobid_url+'/api/isalive')
        if res.text=='true': return _grobid_url
        else: return None
    except:
        return None

@lru_cache(maxsize=32)
def parse_pdf(pdf_path, grobid_url):
    import scipdf   # pip install scipdf_parser
    if grobid_url.endswith('/'): grobid_url = grobid_url.rstrip('/')
    try:
        with ProxyNetworkActivate('Connect_Grobid'):
            article_dict = scipdf.parse_pdf_to_dict(pdf_path, grobid_url=grobid_url)
    except GROBID_OFFLINE_EXCEPTION:
        raise GROBID_OFFLINE_EXCEPTION("GROBIDサービス利用できない。configのGROBID_URLを変更し，ローカルGROBIDサービスに変更することができる。")
    except:
        raise RuntimeError("ParsePDF失敗しました，PDFファイルをチェックして下さい。")
    return article_dict


def produce_report_markdown(gpt_response_collection, meta, paper_meta_info, chatbot, fp, generated_conclusion_files):
    # -=-=-=-=-=-=-=-= 写出第1pieces文件：翻訳前后混合 -=-=-=-=-=-=-=-=
    res_path = write_history_to_file(meta +  ["# Meta Translation" , paper_meta_info] + gpt_response_collection, file_basename=f"{gen_time_str()}translated_and_original.md", file_fullname=None)
    promote_file_to_downloadzone(res_path, rename_file=os.path.basename(res_path)+'.md', chatbot=chatbot)
    generated_conclusion_files.append(res_path)

    # -=-=-=-=-=-=-=-= 写出第2pieces文件：仅翻訳后的文本 -=-=-=-=-=-=-=-=
    translated_res_array = []
    # 记录当前的大章节标题：
    last_section_name = ""
    for index, value in enumerate(gpt_response_collection):
        # 先挑选偶数序列号：
        if index % 2 != 0:
            # 先提取当前英文标题：
            cur_section_name = gpt_response_collection[index-1].split('\n')[0].split(" Part")[0]
            # 如果index是1的话，则直接使用するfirst section name：
            if cur_section_name != last_section_name:
                cur_value = cur_section_name + '\n'
                last_section_name = copy.deepcopy(cur_section_name)
            else:
                cur_value = ""
            # 再做一pieces小修改：重新修改当前part的标题，#用英文的
            cur_value += value
            translated_res_array.append(cur_value)
    res_path = write_history_to_file(meta +  ["# Meta Translation" , paper_meta_info] + translated_res_array,
                                     file_basename = f"{gen_time_str()}-translated_only.md",
                                     file_fullname = None,
                                     auto_caption = False)
    promote_file_to_downloadzone(res_path, rename_file=os.path.basename(res_path)+'.md', chatbot=chatbot)
    generated_conclusion_files.append(res_path)
    return res_path

def translate_pdf(article_dict, llm_kwargs, chatbot, fp, generated_conclusion_files, TOKEN_LIMIT_PER_FRAGMENT, DST_LANG):
    from crazy_functions.pdf_fns.report_gen_html import construct_html
    from crazy_functions.pdf_fns.breakdown_txt import breakdown_text_to_satisfy_token_limit
    from crazy_functions.crazy_utils import request_gpt_model_in_new_thread_with_ui_alive
    from crazy_functions.crazy_utils import request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency

    prompt = "以下是一篇学术論文的基本情報:\n"
    # title
    title = article_dict.get('title', 'title を取得できません'); prompt += f'title:{title}\n\n'
    # authors
    authors = article_dict.get('authors', 'authors を取得できません')[:100]; prompt += f'authors:{authors}\n\n'
    # abstract
    abstract = article_dict.get('abstract', 'abstract を取得できません'); prompt += f'abstract:{abstract}\n\n'
    # command
    prompt += f"テーマと要旨を{DST_LANG}に翻訳して下さい。"
    meta = [f'# Title:\n\n', title, f'# Abstract:\n\n', abstract ]

    # Single line，記事のメタ情報を取得する
    paper_meta_info = yield from request_gpt_model_in_new_thread_with_ui_alive(
        inputs=prompt,
        inputs_show_user=prompt,
        llm_kwargs=llm_kwargs,
        chatbot=chatbot, history=[],
        sys_prompt="You are an academic paper reader。",
    )

    # Multi-threaded，翻訳
    inputs_array = []
    inputs_show_user_array = []

    # get_token_num
    from request_llms.bridge_all import model_info
    enc = model_info[llm_kwargs['llm_model']]['tokenizer']
    def get_token_num(txt): return len(enc.encode(txt, disallowed_special=()))

    def break_down(txt):
        raw_token_num = get_token_num(txt)
        if raw_token_num <= TOKEN_LIMIT_PER_FRAGMENT:
            return [txt]
        else:
            # raw_token_num > TOKEN_LIMIT_PER_FRAGMENT
            # find a smooth token limit to achieve even seperation
            count = int(math.ceil(raw_token_num / TOKEN_LIMIT_PER_FRAGMENT))
            token_limit_smooth = raw_token_num // count + count
            return breakdown_text_to_satisfy_token_limit(txt, limit=token_limit_smooth, llm_model=llm_kwargs['llm_model'])

    for section in article_dict.get('sections'):
        if len(section['text']) == 0: continue
        section_frags = break_down(section['text'])
        for i, fragment in enumerate(section_frags):
            heading = section['heading']
            if len(section_frags) > 1: heading += f' Part-{i+1}'
            inputs_array.append(
                f"{heading}を翻訳することが必要です。内容は以下のよう: \n\n{fragment}"
            )
            inputs_show_user_array.append(
                f"# {heading}\n\n{fragment}"
            )

    gpt_response_collection = yield from request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency(
        inputs_array=inputs_array,
        inputs_show_user_array=inputs_show_user_array,
        llm_kwargs=llm_kwargs,
        chatbot=chatbot,
        history_array=[meta for _ in inputs_array],
        sys_prompt_array=[
            "学術翻訳者として翻訳をお願いします，学術論文を正確に日本語に翻訳する必要があります。記事の各文ごとに翻訳する必要があります。" for _ in inputs_array],
    )
    # -=-=-=-=-=-=-=-= 写出Markdown文件 -=-=-=-=-=-=-=-=
    produce_report_markdown(gpt_response_collection, meta, paper_meta_info, chatbot, fp, generated_conclusion_files)

    # -=-=-=-=-=-=-=-= 写出HTML文件 -=-=-=-=-=-=-=-=
    ch = construct_html()
    orig = ""
    trans = ""
    gpt_response_collection_html = copy.deepcopy(gpt_response_collection)
    for i,k in enumerate(gpt_response_collection_html):
        if i%2==0:
            gpt_response_collection_html[i] = inputs_show_user_array[i//2]
        else:
            # 先提取当前英文标题：
            cur_section_name = gpt_response_collection[i-1].split('\n')[0].split(" Part")[0]
            cur_value = cur_section_name + "\n" + gpt_response_collection_html[i]
            gpt_response_collection_html[i] = cur_value

    final = ["", "", "1.論文の概要",  "", "Abstract", paper_meta_info,  "2.論文の翻訳",  ""]
    final.extend(gpt_response_collection_html)
    for i, k in enumerate(final):
        if i%2==0:
            orig = k
        if i%2==1:
            trans = k
            ch.add_row(a=orig, b=trans)
    create_report_file_name = f"{os.path.basename(fp)}.trans.html"
    html_file = ch.save_file(create_report_file_name)
    generated_conclusion_files.append(html_file)
    promote_file_to_downloadzone(html_file, rename_file=os.path.basename(html_file), chatbot=chatbot)
