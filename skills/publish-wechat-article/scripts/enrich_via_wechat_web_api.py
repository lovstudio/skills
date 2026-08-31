#!/usr/bin/env python3
"""Set editor-only WeChat fields through the logged-in web backend.

This deliberately targets mp.weixin.qq.com's private ``operate_appmsg`` endpoint,
not the documented api.weixin.qq.com draft API.  It runs the request inside an
already authenticated WeChat editor tab, so cookies and the session token never
leave the browser context or enter logs/receipts.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import websockets


class EnrichmentError(RuntimeError):
    pass


@dataclass(frozen=True)
class ChromeTarget:
    url: str
    websocket_url: str


def _read_json(url: str) -> Any:
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.load(response)


def _redact_url(url: str) -> str:
    return re.sub(r"([?&]token=)[^&]+", r"\1[REDACTED]", url)


def _find_target(cdp_base: str, appmsg_id: str | None) -> ChromeTarget:
    targets = _read_json(cdp_base.rstrip("/") + "/json")
    if not isinstance(targets, list):
        raise EnrichmentError("Chrome CDP 未返回标签页列表。")
    candidates = []
    for target in targets:
        if not isinstance(target, dict) or target.get("type") != "page":
            continue
        url = str(target.get("url") or "")
        websocket_url = str(target.get("webSocketDebuggerUrl") or "")
        if "mp.weixin.qq.com/cgi-bin/appmsg" not in url or not websocket_url:
            continue
        if appmsg_id and f"appmsgid={appmsg_id}" not in url:
            continue
        candidates.append(ChromeTarget(url=url, websocket_url=websocket_url))
    if not candidates:
        suffix = f" appmsgid={appmsg_id}" if appmsg_id else ""
        raise EnrichmentError(f"没有找到已登录且已打开草稿的公众号编辑页：{suffix}")
    if len(candidates) > 1 and not appmsg_id:
        raise EnrichmentError("检测到多个公众号编辑页；请用 --appmsg-id 指定目标草稿。")
    return candidates[0]


def _build_expression(
    *,
    title: str,
    author: str,
    digest: str,
    source_url: str,
    category: str,
    reprint_permit_type: int,
) -> str:
    values = {
        "title": title,
        "author": author,
        "digest": digest,
        "sourceUrl": source_url,
        "category": category,
        "reprintPermitType": str(reprint_permit_type),
    }
    config = json.dumps(values, ensure_ascii=False)
    return f"""(async function() {{
  const cfg = {config};
  const href = location.href;
  const token = new URL(href).searchParams.get('token') || '';
  const appMsgId = new URL(href).searchParams.get('appmsgid') || '';
  const type = new URL(href).searchParams.get('type') || '10';
  if (!token || !appMsgId) throw new Error('当前编辑页缺少 token 或 appmsgid');

  const firstValue = (selectors) => {{
    for (const selector of selectors) {{
      const element = document.querySelector(selector);
      const value = element && ('value' in element ? element.value : element.getAttribute('data-value'));
      if (value != null && String(value).trim()) return String(value).trim();
    }}
    return '';
  }};
  const firstHtml = (selectors) => {{
    for (const selector of selectors) {{
      const element = document.querySelector(selector);
      if (element && element.innerHTML && element.innerHTML.trim()) return element.innerHTML.trim();
    }}
    for (const frame of document.querySelectorAll('iframe')) {{
      try {{
        const body = frame.contentDocument && frame.contentDocument.body;
        if (body && body.innerHTML && body.innerHTML.trim()) return body.innerHTML.trim();
      }} catch (_) {{}}
    }}
    return '';
  }};

  const content = firstHtml([
    '.ProseMirror[contenteditable="true"]',
    '[contenteditable="true"].ProseMirror',
    '#ueditor_0 body',
    '.edui-body-container'
  ]);
  const fileId = firstValue(['input.js_file_id', 'input[name="fileid0"]', 'input[name="fileid"]']);
  const cdnUrl = firstValue(['input.js_cdn_url', 'input[name="cdn_url0"]', 'input[name="cdn_url"]']);
  const dataSeq = firstValue(['input[name="data_seq"]']) || '0';
  if (!content) throw new Error('未能从当前编辑页读取正文；为避免清空草稿，已停止。');
  if (!fileId && !cdnUrl) throw new Error('未能读取当前封面标识；为避免丢失封面，已停止。');

  const form = new URLSearchParams();
  const set = (name, value) => form.set(name, value == null ? '' : String(value));
  for (const element of document.querySelectorAll('input[name], textarea[name], select[name]')) {{
    if (element.disabled || !element.name) continue;
    const kind = String(element.type || '').toLowerCase();
    if ((kind === 'checkbox' || kind === 'radio') && !element.checked) continue;
    if (element instanceof HTMLSelectElement && element.multiple) {{
      for (const option of element.selectedOptions) form.append(element.name, option.value);
      continue;
    }}
    form.append(element.name, element.value == null ? '' : String(element.value));
  }}
  set('token', token); set('lang', 'zh_CN'); set('f', 'json'); set('ajax', '1');
  set('random', String(Math.random())); set('AppMsgId', appMsgId); set('count', '1');
  set('data_seq', dataSeq); set('operate_from', 'Chrome'); set('isMark', '0');
  set('title0', cfg.title); set('content0', content); set('author0', cfg.author);
  set('digest0', cfg.digest); set('auto_gen_digest0', '0');
  set('fileid0', fileId); set('cdn_url0', cdnUrl);
  set('sourceurl0', cfg.sourceUrl); set('content_source_url0', cfg.sourceUrl);
  set('copyright_type0', '1');
  set('original_article_type0', cfg.category);
  set('reprint_permit_type0', cfg.reprintPermitType);
  set('allow_reprint0', cfg.reprintPermitType === '1' ? '1' : '0');
  if (!form.has('allow_reprint_modify0')) set('allow_reprint_modify0', '0');

  const endpoint = `/cgi-bin/operate_appmsg?t=ajax-response&sub=update&type=${{encodeURIComponent(type)}}&token=${{encodeURIComponent(token)}}&lang=zh_CN`;
  const response = await fetch(endpoint, {{
    method: 'POST',
    credentials: 'include',
    headers: {{
      'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
      'X-Requested-With': 'XMLHttpRequest'
    }},
    body: form
  }});
  const saved = await response.json();
  const ret = String(saved.ret ?? saved.base_resp?.ret ?? '');
  if (ret !== '0') throw new Error(`operate_appmsg ret=${{ret}} err=${{saved.err_msg || saved.base_resp?.err_msg || ''}}`);

  const editorUrl = `/cgi-bin/appmsg?t=media/appmsg_edit&action=edit&type=${{encodeURIComponent(type)}}&appmsgid=${{encodeURIComponent(appMsgId)}}&token=${{encodeURIComponent(token)}}&lang=zh_CN`;
  const editorHtml = await (await fetch(editorUrl, {{credentials: 'include'}})).text();
  const copyrightIndex = editorHtml.indexOf('copyright_type');
  const copyrightWindow = copyrightIndex >= 0 ? editorHtml.slice(copyrightIndex, copyrightIndex + 160) : '';
  const copyrightInReload = /[:=]\\s*[\"']?1(?:[\"',}}\\s]|$)/.test(copyrightWindow);
  const categoryIndex = editorHtml.indexOf('original_article_type');
  const categoryWindow = categoryIndex >= 0 ? editorHtml.slice(categoryIndex, categoryIndex + 256) : '';
  const categoryInReload = categoryWindow.includes(cfg.category);
  const responseItems = saved.filtered_content_html || saved.filter_content_html || [];
  const responseItem = Array.isArray(responseItems) && responseItems.length ? responseItems[0] : {{}};
  const observedCopyright = Number(responseItem.copyright_type ?? responseItem.copyrightType ?? 0);
  const observedCategory = String(responseItem.original_article_type ?? responseItem.originalArticleType ?? '');
  const originalVerified =
    (observedCopyright === 1 && observedCategory === cfg.category) ||
    (copyrightInReload && categoryInReload);

  return {{
    appMsgId,
    type,
    ret: 0,
    originalRequested: true,
    originalVerified,
    observedCopyrightType: observedCopyright || (copyrightInReload ? 1 : null),
    observedOriginalArticleType: observedCategory || (categoryInReload ? cfg.category : null),
    author: cfg.author,
    category: cfg.category,
    coverPreserved: Boolean(fileId || cdnUrl),
    existingNamedFieldCount: Array.from(document.querySelectorAll('input[name], textarea[name], select[name]')).length,
    verificationSource: originalVerified ? 'operate_appmsg response or editor reload' : 'not observed after save'
  }};
}})()"""


async def _evaluate(target: ChromeTarget, expression: str) -> dict[str, Any]:
    async with websockets.connect(target.websocket_url, max_size=8 * 1024 * 1024) as socket:
        await socket.send(
            json.dumps(
                {
                    "id": 1,
                    "method": "Runtime.evaluate",
                    "params": {
                        "expression": expression,
                        "awaitPromise": True,
                        "returnByValue": True,
                    },
                }
            )
        )
        while True:
            message = json.loads(await asyncio.wait_for(socket.recv(), timeout=90))
            if message.get("id") != 1:
                continue
            if message.get("error"):
                raise EnrichmentError(str(message["error"]))
            result = message.get("result", {}).get("result", {})
            if result.get("subtype") == "error":
                detail = result.get("description") or result.get("value") or "浏览器执行失败"
                raise EnrichmentError(str(detail))
            value = result.get("value")
            if not isinstance(value, dict):
                raise EnrichmentError("浏览器未返回结构化的原创声明结果。")
            return value


def _write_receipt(path: Path, result: dict[str, Any], target: ChromeTarget) -> None:
    receipt = {
        "schemaVersion": 1,
        "platform": "wechat_official_account",
        "action": "editor_enrichment",
        "state": "draft_ready" if result.get("originalVerified") else "draft_enriching",
        "verificationPending": not bool(result.get("originalVerified")),
        "editorFields": {
            "originalRequested": True,
            "originalCategoryRequested": result.get("category"),
            "copyrightTypeObserved": result.get("observedCopyrightType"),
            "originalVerified": bool(result.get("originalVerified")),
            "authorObserved": result.get("author"),
            "originalCategoryObserved": result.get("observedOriginalArticleType"),
            "saved": result.get("ret") == 0,
            "reloaded": True,
            "editorFieldsVerified": bool(result.get("originalVerified")),
        },
        "technicalDetail": {
            "transport": "wechat-web-private-api",
            "endpoint": "mp.weixin.qq.com/cgi-bin/operate_appmsg",
            "appMsgId": result.get("appMsgId"),
            "editorUrl": _redact_url(target.url),
            "coverPreserved": bool(result.get("coverPreserved")),
            "verificationSource": result.get("verificationSource"),
            "sessionSecretsPersisted": False,
        },
        "checkedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Use a logged-in WeChat editor tab to save and verify an original declaration."
    )
    parser.add_argument("--cdp-base", default="http://127.0.0.1:9222")
    parser.add_argument("--appmsg-id")
    parser.add_argument("--title", required=True)
    parser.add_argument("--author", required=True)
    parser.add_argument("--digest", default="")
    parser.add_argument("--source-url", default="")
    parser.add_argument("--original-category", required=True)
    parser.add_argument("--reprint-permit-type", type=int, choices=(0, 1, 2), default=1)
    parser.add_argument("--confirm-original-rights", action="store_true")
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if len(args.author) > 16:
        raise EnrichmentError("作者超过 16 个字符。")
    if not args.confirm_original_rights and not args.dry_run:
        raise EnrichmentError("声明原创前必须显式传入 --confirm-original-rights。")
    target = _find_target(args.cdp_base, args.appmsg_id)
    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "prepared",
                    "target": _redact_url(target.url),
                    "author": args.author,
                    "originalCategory": args.original_category,
                    "rightsConfirmed": bool(args.confirm_original_rights),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    expression = _build_expression(
        title=args.title,
        author=args.author,
        digest=args.digest,
        source_url=args.source_url,
        category=args.original_category,
        reprint_permit_type=args.reprint_permit_type,
    )
    result = asyncio.run(_evaluate(target, expression))
    if args.receipt:
        _write_receipt(args.receipt.expanduser().resolve(), result, target)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result.get("originalVerified"):
        raise EnrichmentError("接口返回成功，但重载后未观察到原创状态；草稿仍为 draft_enriching。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except EnrichmentError as error:
        print(json.dumps({"status": "failed", "message": str(error)}, ensure_ascii=False))
        raise SystemExit(1)
