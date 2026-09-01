# 草稿 transport 选择

## LovStudio 统一网关（默认）

所有微信公众号 API 请求都由 `https://api.lovstudio.ai/wechat/official-account` 发出：

```text
本地 Markdown
-> 当前品牌 Profile 的永久 endcap + 生效活动
-> lov-wechat-branding-cover-composition 最终封面 + 收据
-> lov-image-decorator 为必要正文图片生成 Caption 派生图 + 收据
-> lovpen-cli --format wechat
-> lov-env-management 解析密钥
-> uni-api 固定出口
-> stable_token
-> media/uploadimg + material/add_material
-> draft/add + draft/get
-> freepublish/submit + freepublish/get（仅获授权公开发布时）
```

本地只访问 LovStudio 后端，不需要将当前家庭、办公或移动网络 IP 加入微信白名单。AppSecret 与网关 API Key 不作为 CLI 明文参数，也不写入文章、收据或日志。

`draft/add` 返回后必须先把 `media_id` 写入回执，再调用 `draft/get`。即使回读或保真校验失败，也要保留同一草稿的 `media_id`，不得通过再次 `draft/add` 重试。原生 `mp-common-videosnap` 回读时先核对 `data-id`、`data-nonceid`、`data-username` 等身份字段，再允许微信接管其 Shadow DOM、尺寸与签名资源；文章其他节点仍执行严格保真校验。

常规草稿创建必须由 `lovpen-cli` 直接生成 `--format wechat` 复制态 HTML。该产物来自 Lovpen 的 `wechat-browser-copy` / `extractWechatClipboardHTML` 链路，根节点是 `section.lovpen-renderer`，正文样式已内联；仅原生 `mp-common-videosnap` 的 Shadow DOM 可保留组件隔离 `<style>`，文章正文其他位置不得出现 `<style>`。发布脚本只替换本地图片 `src`，不通过 BeautifulSoup 或 Markdown 重建正文；替换前后核对 style、class、span、table 与 img 数量，并比较忽略图片 `src` 后的全文 SHA-256。`--format standalone` 是独立网页契约，必须拒绝，不能再压缩投影成微信正文。

Lovpen 渲染前先按 [Profile 驱动的出版组件](editorial-components.md) 验收永久品牌尾注、个人卡片与当前生效活动，再完成正文图片 Caption 判断。需要补充证据、归属或解释的图片通过 `lov-image-decorator` 生成派生文件；不需要 Caption 的图片保持原样。文章链只接受显式 Caption，不使用默认 fallback 代替编辑判断。详细契约见 [image-caption-preparation.md](image-caption-preparation.md)。

封面必须由 `lov-wechat-branding-cover-composition` 生成。发布脚本同时接收 `share-cover-wide-logo.jpg` 和 `cover-composition.json`，核对收据 schema、官方 Logo SHA-256、`publisherLogoPresent` 与上传件路径后才进入网关。

## OneShot 旧直连链路

用于持续创作、账号连接和本地素材管理。当前真实链路为：

```text
Markdown 草稿
-> 安全存储中的公众号凭据
-> stable_token
-> material/add_material 上传封面
-> draft/add
-> mediaId + syncedAt
```

当前边界：

- 支持公众号文章与贴图草稿。
- 文章正文由 Markdown 转为微信内联样式 HTML。
- 文章只上传封面；草稿中的其他图片不会自动进入文章正文。
- payload 尚未传作者、摘要和阅读原文 URL。
- `synced` 只表示远端草稿创建成功。
- 当前应用代码没有注册 `freepublish/submit` 或 `freepublish/get`。

该链路只作为显式诊断兼容项，不再作为默认 transport。不要把 OneShot 的默认 Logo 封面或品牌文字卡带入通用文章。

## 其他直连工具（兼容）

`baoyu-post-to-wechat` 等工具可用于兼容旧流程，但其 API 直连会重新引入本机 IP 白名单，不用于默认路径。

调用前完整读取该 Skill 的 `SKILL.md`，并注意：

- API 主链实际止于 `draft/add`；日志中的 “Published successfully” 仍按 `draft_created` 解释。
- 浏览器文章脚本的 `--submit` 在当前实现中仍以保存草稿为主；以公众号后台回读为准。
- 配置路径属于该 transport，不要复制或迁移 OneShot Keychain 内容。

## 已登录公众号后台

适合需要可见编辑器、人工检查排版或 API 字段不覆盖的场景：

1. 复用当前已登录的浏览器实例。
2. 打开公众号草稿编辑器，核对目标账号。
3. 上传封面和正文图片，填写标题、作者、摘要、正文及可选设置。品牌化文章上传的封面必须是已包含官方 `publication.logo` 的最终合成件。
4. `digest` 已由公开草稿 API 写入；原创声明则按 [编辑器补全契约](editor-enrichment.md) 调用同源登录态的 `operate_appmsg` 私有网页 API。未指定的设置保持平台默认。
5. 保存草稿后重载同一篇，回读标题、推荐语、原创状态、封面和非目标开关；不以单次 DOM 变化或“已保存”提示代替回读。
6. 用户明确要求公开发表时再执行发表动作，并从已发表列表重载回读。

SPA/富文本编辑器会重渲染。每次写入后重新取得元素引用；DOM 中出现内容不等于保存成功。

私有网页 API 必须满足以下约束：

- 只复用用户已授权的登录会话，不读取、复制或持久化 Cookie/token。
- 只在正文与封面均能从当前目标草稿读取时提交更新。
- `ret=0` 后重新拉取编辑页并观察原创字段；不可观测时保持 `draft_enriching`。
- 页面结构或端点漂移时失败关闭，不回退为公开 `draft/update` 的伪原创字段。
