from crazy_functions.ipc_fns.mp import run_in_subprocess_with_timeout

def force_breakdown(txt, limit, get_token_fn):
    """ 句読点や空行で区切ることができない場合，最も暴力的なテキストの翻訳で切り分けます
    """
    for i in reversed(range(len(txt))):
        if get_token_fn(txt[:i]) < limit:
            return txt[:i], txt[i:]
    return "Tiktokenの不明のエラー", "Tiktokenの不明のエラー"


def maintain_storage(remain_txt_to_cut, remain_txt_to_cut_storage):
    """ 为了加速计算，私たちは采样一pieces特殊的手段。当 remain_txt_to_cut > `_max` 時， 私たちは把 _max 后的文字转存至 remain_txt_to_cut_storage
    当 remain_txt_to_cut < `_min` 時，私たちは再把 remain_txt_to_cut_storage 中的部分文字取出
    """
    _min = int(5e4)
    _max = int(1e5)
    # print(len(remain_txt_to_cut), len(remain_txt_to_cut_storage))
    if len(remain_txt_to_cut) < _min and len(remain_txt_to_cut_storage) > 0:
        remain_txt_to_cut = remain_txt_to_cut + remain_txt_to_cut_storage
        remain_txt_to_cut_storage = ""
    if len(remain_txt_to_cut) > _max:
        remain_txt_to_cut_storage = remain_txt_to_cut[_max:] + remain_txt_to_cut_storage
        remain_txt_to_cut = remain_txt_to_cut[:_max]
    return remain_txt_to_cut, remain_txt_to_cut_storage


def cut(limit, get_token_fn, txt_tocut, must_break_at_empty_line, break_anyway=False):
    """ 文本切分
    """
    res = []
    total_len = len(txt_tocut)
    fin_len = 0
    remain_txt_to_cut = txt_tocut
    remain_txt_to_cut_storage = ""
    # 为了加速计算，私たちは采样一pieces特殊的手段。当 remain_txt_to_cut > `_max` 時， 私たちは把 _max 后的文字转存至 remain_txt_to_cut_storage
    remain_txt_to_cut, remain_txt_to_cut_storage = maintain_storage(remain_txt_to_cut, remain_txt_to_cut_storage)

    while True:
        if get_token_fn(remain_txt_to_cut) <= limit:
            # 如果剩余文本的token数小于限制，那么就不用切了
            res.append(remain_txt_to_cut); fin_len+=len(remain_txt_to_cut)
            break
        else:
            # 如果剩余文本的token数大于限制，那么就切
            lines = remain_txt_to_cut.split('\n')

            # 估计一pieces切分点
            estimated_line_cut = limit / get_token_fn(remain_txt_to_cut) * len(lines)
            estimated_line_cut = int(estimated_line_cut)

            # 開始查找合适切分点的偏移（cnt）
            cnt = 0
            for cnt in reversed(range(estimated_line_cut)):
                if must_break_at_empty_line:
                    # 首先Try用双空行（\n\n）分割点として
                    if lines[cnt] != "":
                        continue
                prev = "\n".join(lines[:cnt])
                post = "\n".join(lines[cnt:])
                if get_token_fn(prev) < limit:
                    break

            if cnt == 0:
                # 如果没有找到合适的切分点
                if break_anyway:
                    # 是否允许暴力切分
                    prev, post = force_breakdown(remain_txt_to_cut, limit, get_token_fn)
                else:
                    # 不允许直接报错
                    raise RuntimeError(f"1行の非常に長いテキストが存在します！{remain_txt_to_cut}")

            # 追加リスト
            res.append(prev); fin_len+=len(prev)
            # 准备下一次迭代
            remain_txt_to_cut = post
            remain_txt_to_cut, remain_txt_to_cut_storage = maintain_storage(remain_txt_to_cut, remain_txt_to_cut_storage)
            process = fin_len/total_len
            print(f'正在文本切分 {int(process*100)}%')
            if len(remain_txt_to_cut.strip()) == 0:
                break
    return res


def breakdown_text_to_satisfy_token_limit_(txt, limit, llm_model="gpt-3.5-turbo"):
    """ 使用する多种方式Try切分文本，以满足 token 限制
    """
    from request_llms.bridge_all import model_info
    enc = model_info[llm_model]['tokenizer']
    def get_token_fn(txt): return len(enc.encode(txt, disallowed_special=()))
    try:
        # 1回目の試み，2つの空行を挿入する（\n\n）分割点として
        return cut(limit, get_token_fn, txt, must_break_at_empty_line=True)
    except RuntimeError:
        try:
            # 2回目の試み，Single blank line（\n）分割点として
            return cut(limit, get_token_fn, txt, must_break_at_empty_line=False)
        except RuntimeError:
            try:
                # 3回目の試み，英文句点を（.）分割点として
                res = cut(limit, get_token_fn, txt.replace('.', '。\n'), must_break_at_empty_line=False) # この中国語の句点は意図的です，識別子として存在する
                return [r.replace('。\n', '.') for r in res]
            except RuntimeError as e:
                try:
                    # 4回目の試み，Replace Chinese period（。）分割点として
                    res = cut(limit, get_token_fn, txt.replace('。', '。。\n'), must_break_at_empty_line=False)
                    return [r.replace('。。\n', '。') for r in res]
                except RuntimeError as e:
                    # 5回目の試み，どうしようもない，随便切一下吧
                    return cut(limit, get_token_fn, txt, must_break_at_empty_line=False, break_anyway=True)

breakdown_text_to_satisfy_token_limit = run_in_subprocess_with_timeout(breakdown_text_to_satisfy_token_limit_, timeout=60)

if __name__ == '__main__':
    from crazy_functions.crazy_utils import read_and_clean_pdf_text
    file_content, page_one = read_and_clean_pdf_text("build/assets/at.pdf")

    from request_llms.bridge_all import model_info
    for i in range(5):
        file_content += file_content

    print(len(file_content))
    TOKEN_LIMIT_PER_FRAGMENT = 2500
    res = breakdown_text_to_satisfy_token_limit(file_content, TOKEN_LIMIT_PER_FRAGMENT)

