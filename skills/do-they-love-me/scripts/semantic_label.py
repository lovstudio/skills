#!/usr/bin/env python3
"""Label each message with one topic: work / love / life / other.

Default backend is a local Ollama model, so private chat text never leaves the
machine. A remote OpenAI-compatible backend exists for users who explicitly
opt in; it is never selected implicitly.

Always run `--eval` against a hand-labelled sample before believing the shares:
the accuracy of the model is part of the result, not a footnote.
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

TAXONOMY = """你是中文聊天消息的话题分类器。给每条消息选一个话题，四选一：
work = 工作、学业、项目、活动事务（筹备、执行、报名、场地、物料、嘉宾、时间地点对接）、职业与行业、技术与产品
love = 情感与关系：对聊天对象本人的喜欢、想念、在意、夸赞、撒娇、求陪伴、约定见面、关系状态的讨论
life = 生活与日常：吃喝睡玩、出行、身体、天气、购物、朋友、心情、兴趣与个人看法
other = 没有实际话题内容的消息

判定顺序（自上而下，命中即停）：
1. other：这条消息有没有实际话题？纯图片/语音/表情/链接/文件、系统通知与预订提醒、招呼与自我介绍，算 other；
   只有应答或附和口气、说完就没了（okk、嗯呐、好滴、哈哈、笑死、还行、可以），即使带情绪也算 other；
   只报地点、时间、序号、数字，或没有上下文的英文碎片，也算 other。
2. work：谈的是具体活动、项目、课程、招聘、物料、场地、嘉宾、进度、上线、行业与职业、技术与产品。
   只要在谈具体事务就算 work，即使是在约时间、即使只有一句话。
   约时间、接机、报名、对进度这类具体事务，一律算 work。
3. love：这句话是不是在说「对聊天对象本人」的喜欢、想念、在意、夸赞、撒娇、求陪伴、约见面或关系状态？是则 love。
   夸对方本人（夸声音、夸性格、夸对方做的事）算 love。
   说自己喜欢某个城市、某款产品、某位明星、某支乐队，属于 life，不算 love。
4. life：剩下的个人话题：吃睡玩、出行、身体、天气、购物、朋友、心情、兴趣、个人观点。短也可以算 life。

关键补充：`work` 不看这句话像不像上班，而看它是不是在推进一件具体的事
（约时间、接人、取件、报名、物料、场地、进度、上线、招聘与面试、器材与设备）。
一句很短、单看像生活的话，只要上文在谈具体事务，就按 `work` 判。

示例：全部是合成句子，不含任何真实聊天内容；示例也不许出现在校准集里，否则准确率是假的：
明天的物料清单我发群里了 -> work
场地那边说下午三点才能进场 -> work
这版海报今晚能定稿吗 -> work
印好的展板先放我办公室 -> work
报名链接还差两个人没填 -> work
周五的机场接人你去吗 -> work
补光灯到了吗 我先架起来 -> work
面试安排在明天下午三点 -> work
等会儿部署完我把链接发你 -> work
印刷厂说明天上午出货 -> work
我顺路把样册取回来 -> work
直播推流参数我调好了 -> work
今天一直想找你说话 -> love
你笑起来特别好看 -> love
忙完记得回我 别让我等 -> love
你讲这件事的时候特别有耐心 -> love
这周末一起去看展好不好 -> love
你今天穿这件真好看 -> love
昨晚两点才睡着 -> life
我最近在学做饭 -> life
我很喜欢那支乐队的现场 -> life
今天下雨就不出门了 -> life
楼下新开了家咖啡店 -> life
我周末一般在家躺着 -> life
好滴！ -> other
收到 -> other
王老师早！ -> other
对方撤回了一条消息 -> other
嗯呐 -> other

输入每行格式为「序号|上文: <同一会话的前一条消息，可能为空>|本句: <待分类消息>」。
先结合上文理解这条消息在说什么，再按上面的顺序判定。
输出：每行 序号|类别，不要解释、不要空行、不要 markdown。"""

LABELS = ("work", "love", "life", "other")


# Messages that carry no topic at all are decided by rule, not by the model:
# a small local model reliably mislabels them, and every one of them would
# otherwise inflate `life`. Anything the rules do not catch still goes to the model.
SYSTEM_HINTS = (
    "以上是打招呼的消息",
    "把你添加到通讯录",
    "你已添加了",
    "邀请你加入群聊",
    "撤回了一条消息",
    "我拍了拍",
    "拍了拍我的",
    "红包",
    "转账",
    "语音通话",
    "视频通话",
    "该消息类型",
    "消息已发出",
)
ACK_ONLY = {
    "ok", "ok啦", "okk", "okkk", "好", "好的", "好的呢", "好滴", "好滴！", "好呀", "好嘞",
    "嗯", "嗯呐", "嗯嗯", "嗯呢", "嗯嗯嗯", "对", "对的", "对呀", "是的", "是的呢", "行", "可以",
    "可以呀", "收到", "谢谢", "谢谢啦", "谢谢！", "辛苦了", "辛苦啦", "晚安", "晚安啦", "早",
    "早上好", "哈哈", "哈哈哈", "哈哈哈哈", "哈哈哈哈哈哈", "笑死", "笑死啦", "deal", "wow",
    "哈哈真的吗", "不", "不要", "🐒", "🤔",
}
ASCII_ONLY = re.compile(r"^[A-Za-z0-9\s\.,!?~～\-_'’\(\)\[\]&%\*\+:=/\\|]+$")
EMOJI_ONLY = re.compile(r"^[\s\u2000-\u3300\U0001F000-\U0001FAFF\u2190-\u2BFF]+$")
DIGITS_ONLY = re.compile(r"^[\s\d\.,:：\-—~～/年月日号点分秒个次天周第]+$")


def prerule(text):
    """Return "other" when a message provably has no topic, else None."""
    t = (text or "").strip()
    if not t:
        return "other"
    if any(h in t for h in SYSTEM_HINTS):
        return "other"
    if t in ACK_ONLY:
        return "other"
    if EMOJI_ONLY.match(t) or DIGITS_ONLY.match(t):
        return "other"
    cjk = any("\u4e00" <= ch <= "\u9fff" for ch in t)
    if not cjk and len(t) <= 24 and ASCII_ONLY.match(t):
        return "other"
    return None


def batch_lines(batch, ctx_chars):
    out = []
    for r in batch:
        ctx = (r.get("p") or "").replace("\n", " ").strip()
        if ctx_chars <= 0:
            out.append(f'{r["i"]}|{r["t"]}')
        else:
            out.append(f'{r["i"]}|上文: {ctx[-ctx_chars:]}|本句: {r["t"]}')
    return "\n".join(out)


def ollama_call(base_url, model, batch, timeout, ctx_chars):
    lines = batch_lines(batch, ctx_chars)
    body = {
        "model": model,
        "stream": False,
        "think": False,
        "options": {"temperature": 0, "num_predict": 400},
        "messages": [
            {"role": "system", "content": TAXONOMY},
            {"role": "user", "content": lines},
        ],
    }
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/chat",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())["message"]["content"]


def remote_call(base_url, model, batch, timeout, api_key, ctx_chars):
    lines = batch_lines(batch, ctx_chars)
    body = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": TAXONOMY},
            {"role": "user", "content": lines},
        ],
    }
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode())
    return data["choices"][0]["message"]["content"]


def parse(raw, batch):
    raw = re.sub(r"<think.*?/>", "", raw, flags=re.S)
    allowed = {r["i"] for r in batch}
    got = {}
    for line in raw.splitlines():
        m = re.match(r"\s*(\d+)\s*[|:：\t]\s*([a-z]+)", line.strip())
        # a small model sometimes invents indices; keep only the ones we asked about
        if m and int(m.group(1)) in allowed and m.group(2).lower() in LABELS:
            got[int(m.group(1))] = m.group(2).lower()
    return got, [r["i"] for r in batch if r["i"] not in got]


def label(rows, args):
    backend = args.backend
    fixed, pending = {}, []
    if not args.no_prerules:
        for r in rows:
            hit = prerule(r.get("t", ""))
            if hit:
                fixed[r["i"]] = hit
            else:
                pending.append(r)
        rows = pending
        print(
            f"[prerule] {len(fixed)} rows decided by rule, {len(rows)} sent to {backend}",
            file=sys.stderr,
            flush=True,
        )
    if backend == "remote" and not args.api_key_env:
        raise SystemExit("remote backend needs --api-key-env (never pass keys on the CLI)")
    key = os.environ.get(args.api_key_env, "") if args.api_key_env else ""
    if backend == "remote" and not key:
        raise SystemExit(f"environment variable {args.api_key_env} is not set")

    out, missing, t0 = {}, [], time.time()
    total = (len(rows) + args.batch - 1) // args.batch
    for start in range(0, len(rows), args.batch):
        batch = rows[start : start + args.batch]
        if not batch:
            continue
        if backend == "ollama":
            raw = ollama_call(args.base_url, args.model, batch, args.timeout, args.context)
        else:
            raw = remote_call(args.base_url, args.model, batch, args.timeout, key, args.context)
        got, miss = parse(raw, batch)
        out.update(got)
        missing += miss
        print(
            f"[{backend}] batch {start // args.batch + 1}/{total} +{len(got)} "
            f"(missing {len(miss)}) {time.time() - t0:.0f}s",
            file=sys.stderr,
            flush=True,
        )
    out.update(fixed)
    return out, missing


def evaluate(pred, gold):
    agree = sum(1 for i, label_ in gold.items() if pred.get(i) == label_)
    report = {"gold_n": len(gold), "agreement": round(agree / len(gold), 3), "per_class": {}}
    for label_ in LABELS:
        gold_pos = [i for i, g in gold.items() if g == label_]
        pred_pos = [i for i, p in pred.items() if p == label_]
        tp = sum(1 for i in gold_pos if pred.get(i) == label_)
        report["per_class"][label_] = {
            "gold": len(gold_pos),
            "predicted": len(pred_pos),
            "precision": round(tp / len(pred_pos), 3) if pred_pos else None,
            "recall": round(tp / len(gold_pos), 3) if gold_pos else None,
        }
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True, help="label_input.jsonl")
    ap.add_argument("--out", required=True, help="labels.jsonl")
    ap.add_argument("--backend", choices=["ollama", "remote"], default="ollama")
    ap.add_argument("--base-url", default="http://127.0.0.1:11434")
    ap.add_argument("--model", default="qwen3:8b")
    ap.add_argument("--api-key-env", default="", help="env var holding the key (remote only)")
    ap.add_argument("--batch", type=int, default=28)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument(
        "--context",
        type=int,
        default=40,
        help="how many trailing characters of the previous message to show the model (0 disables)",
    )
    ap.add_argument(
        "--no-prerules",
        action="store_true",
        help="send every message to the model instead of pre-classifying contentless ones",
    )
    ap.add_argument("--eval-gold", default="", help="gold JSON: index -> label")
    ap.add_argument("--report", default="", help="write the accuracy report here")
    args = ap.parse_args()

    rows = [
        json.loads(line)
        for line in Path(args.input).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    gold = {}
    if args.eval_gold:
        gold = {int(k): v for k, v in json.loads(Path(args.eval_gold).read_text()).items()}
        rows = [r for r in rows if r["i"] in gold]

    pred, missing = label(rows, args)
    with open(args.out, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(
                json.dumps({**row, "label": pred.get(row["i"], "other")}, ensure_ascii=False)
                + "\n"
            )
    summary = {
        "labelled": len(pred),
        "unparsed": len(missing),
        "model": args.model,
        "backend": args.backend,
        "distribution": dict(
            Counter((pred.get(r["i"]) or "other") for r in rows if r["i"] in gold or not gold)
        ),
    }
    if gold:
        summary["accuracy"] = evaluate(pred, gold)
    if args.report:
        Path(args.report).write_text(
            json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8"
        )
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
