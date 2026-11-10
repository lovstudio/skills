(function () {
  'use strict';

  const TOKEN = (document.querySelector('meta[name="lov-token"]') || {}).content || '';
  const embedded = document.getElementById('lov-snapshot');
  const IS_STATIC = Boolean(embedded);
  const TABS = ['overview', 'prompt', 'skills', 'studio', 'tidy'];
  const SEVERITIES = ['error', 'warn', 'info'];
  const SEVERITY = { error: '错误', warn: '警告', info: '提示' };
  const AREA = { prompt: 'System Prompt', skills: 'Skills', studio: '工作室' };
  const AREA_LINK = { prompt: '去 System Prompt 查看', skills: '去 Skills 查看', studio: '去工作室查看' };
  const ORIGIN = {
    studio: '工作室源码',
    registry: '第三方安装',
    'shared-copy': '共享目录副本',
    'host-copy': '宿主副本',
    external: '外部项目',
  };
  const PROMPT_STATE = {
    linked: ['已链接', 'ok'],
    copy: ['实体副本', 'info'],
    embedded: ['嵌入副本', 'ok'],
    'embedded-stale': ['嵌入副本已过期', 'warn'],
    independent: ['独立文件', ''],
    broken: ['断链', 'error'],
    missing: ['未绑定', ''],
  };
  const FILE_GROUPS = [
    ['root', '根 Prompt'],
    ['reference', 'Reference'],
    ['changelog', '变更记录'],
    ['host', '宿主里的副本'],
  ];
  const STUDIO_FILTERS = [
    ['', '全部', () => true],
    ['issues', '有问题', (r) => r.findings.length > 0],
    ['dirty', '有未提交改动', (r) => Boolean(r.git && r.git.repo && r.git.dirty)],
    ['unpushed', '有未推送提交', (r) => Boolean(r.git && r.git.repo && r.git.ahead)],
    ['drift', '版本不一致', (r) => r.drift],
    ['ahead', '源码领先目录', (r) => Boolean(r.catalog && r.catalog.relation === 'source-ahead')],
    ['behind', '源码落后目录', (r) => Boolean(r.catalog && r.catalog.relation === 'source-behind')],
    ['unlisted', '未登记目录', (r) => Boolean(r.dir && r.skill_md && !r.catalog)],
    ['uninstalled', '未安装到本机', (r) => Boolean(r.dir && r.skill_md && !installedCount(r))],
    ['paid', '付费', (r) => Boolean(r.catalog && r.catalog.paid)],
    ['free', '免费', (r) => Boolean(r.catalog && !r.catalog.paid)],
    ['nosource', '本地无源码', (r) => Boolean(r.missing_source)],
  ];
  const PAGE = 120;

  const state = {
    snap: null,
    findings: new Map(),
    tab: 'overview',
    basket: new Map(),
    journal: [],
    raw: new Map(),
    promptFile: '',
    promptView: 'structure',
    allHosts: false,
    skills: { query: '', host: '', origin: '', issues: false, sort: 'name', limit: PAGE, open: new Set() },
    studio: { query: '', filter: '', sort: 'name', limit: PAGE, open: new Set() },
  };

  // ---- DOM helpers -------------------------------------------------------

  function append(node, child) {
    if (child === null || child === undefined || child === false) return;
    if (Array.isArray(child)) {
      child.forEach((item) => append(node, item));
    } else if (typeof child === 'string' || typeof child === 'number') {
      node.appendChild(document.createTextNode(String(child)));
    } else {
      node.appendChild(child);
    }
  }

  // Dynamic values only ever enter the page through textContent or attributes.
  function h(tag, attrs) {
    const node = document.createElement(tag);
    Object.keys(attrs || {}).forEach((key) => {
      const value = attrs[key];
      if (value === null || value === undefined || value === false) return;
      if (key === 'class') node.className = value;
      else if (key === 'text') node.textContent = value;
      else if (key === 'dataset') Object.assign(node.dataset, value);
      else node.setAttribute(key, value === true ? '' : String(value));
    });
    for (let index = 2; index < arguments.length; index += 1) append(node, arguments[index]);
    return node;
  }

  const $ = (id) => document.getElementById(id);
  const num = (value) => Number(value || 0).toLocaleString('zh-CN');
  const day = (iso) => (iso ? String(iso).slice(0, 10) : '');
  const installedCount = (record) => record.installed.shared.length + record.installed.hosts.length;
  const hostCount = (skill) => skill.hosts.filter((host) => host !== 'shared').length;

  function bytes(value) {
    return value < 1024 ? value + ' B' : (value / 1024).toFixed(1) + ' KB';
  }

  function when(iso) {
    const date = new Date(iso);
    return Number.isNaN(date.getTime()) ? String(iso || '') : date.toLocaleString('zh-CN', { hour12: false });
  }

  function badge(text, tone) {
    return h('span', { class: 'badge' + (tone ? ' badge-' + tone : ''), text: text });
  }

  function hostLabel(id) {
    const host = state.snap.skills.hosts.find((item) => item.id === id);
    return host && host.label !== id ? host.label : id;
  }

  // ---- Server access -----------------------------------------------------

  async function api(path, body) {
    const options = { headers: { 'X-Lov-Token': TOKEN } };
    if (body !== undefined) {
      options.method = 'POST';
      options.headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(body);
    }
    const reply = await fetch(path, options);
    let data = null;
    try {
      data = await reply.json();
    } catch (error) {
      data = null;
    }
    if (!reply.ok) throw new Error((data && data.error) || '请求失败（' + reply.status + '）');
    return data;
  }

  let toastTimer = 0;
  function toast(message, isError) {
    const node = $('toast');
    node.textContent = message;
    node.classList.toggle('is-error', Boolean(isError));
    node.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      node.hidden = true;
    }, isError ? 7000 : 3200);
  }

  function showNotice(message, isError) {
    const node = $('notice');
    node.textContent = message;
    node.classList.toggle('is-error', Boolean(isError));
    node.hidden = !message;
  }

  function openDialog(title, body, actions) {
    const dialog = $('dialog');
    $('dialog-title').textContent = title;
    $('dialog-body').replaceChildren();
    append($('dialog-body'), body);
    const bar = $('dialog-actions');
    bar.replaceChildren();
    actions.filter(Boolean).forEach((action) => {
      const button = h('button', {
        class: 'button' + (action.primary ? ' button-primary' : ''),
        type: 'button',
        text: action.label,
      });
      button.addEventListener('click', async () => {
        if (!action.run) {
          dialog.close();
          return;
        }
        button.disabled = true;
        try {
          if (!(await action.run())) dialog.close();
        } catch (error) {
          toast(error.message, true);
          button.disabled = false;
        }
      });
      bar.appendChild(button);
    });
    if (!dialog.open) dialog.showModal();
  }

  async function copyText(text) {
    try {
      await navigator.clipboard.writeText(text);
      toast('已复制');
    } catch (error) {
      const area = h('textarea', { class: 'copy-buffer', 'aria-hidden': 'true' });
      area.value = text;
      document.body.appendChild(area);
      area.select();
      const copied = document.execCommand('copy');
      area.remove();
      toast(copied ? '已复制' : '复制失败，请手动选择文本', !copied);
    }
  }

  // aria-disabled keeps the trigger focusable, so a dialog it opens can hand focus back.
  function whileBusy(button, run) {
    button.addEventListener('click', async () => {
      if (button.getAttribute('aria-disabled') === 'true') return;
      button.setAttribute('aria-disabled', 'true');
      try {
        await run();
      } catch (error) {
        toast(error.message, true);
      }
      button.removeAttribute('aria-disabled');
    });
    return button;
  }

  function actionButton(label, run) {
    if (IS_STATIC) return null;
    return whileBusy(h('button', { class: 'button button-small', type: 'button', text: label }), run);
  }

  const revealButton = (path) => actionButton('在文件夹中显示', () => api('/api/open', { path: path, reveal: true }));

  async function showFile(path, title) {
    const data = await api('/api/file?path=' + encodeURIComponent(path));
    openDialog(title, [h('p', { class: 'mono muted', text: path }), h('pre', { class: 'raw', tabindex: '0', text: data.text })], [
      { label: '关闭' },
    ]);
  }

  // ---- Tidy basket -------------------------------------------------------

  function opKey(op) {
    return op.op === 'fix' ? 'fix:' + op.id : op.op + ':' + op.entry + (op.host ? '@' + op.host : '');
  }

  function opLabel(op) {
    if (op.op === 'fix') {
      const item = state.findings.get(op.id);
      return item ? item.fix.label + ' · ' + item.path : op.id;
    }
    if (op.op === 'disable') return '停用 ' + op.entry;
    if (op.op === 'enable') return '启用 ' + op.entry;
    if (op.op === 'link') return '安装 ' + op.entry + ' 到 ' + hostLabel(op.host);
    return '从 ' + hostLabel(op.host) + ' 移除 ' + op.entry;
  }

  // A pressed toggle: the label stays, aria-pressed and the filled style carry the state.
  function basketButton(op, label) {
    if (IS_STATIC) return null;
    const key = opKey(op);
    const button = h('button', {
      class: 'button button-small',
      type: 'button',
      text: label,
      'aria-pressed': String(state.basket.has(key)),
      dataset: { basket: key },
    });
    button.addEventListener('click', () => {
      if (state.basket.has(key)) state.basket.delete(key);
      else state.basket.set(key, op);
      syncBasket();
    });
    return button;
  }

  function syncBasket() {
    document.querySelectorAll('[data-basket]').forEach((node) => {
      node.setAttribute('aria-pressed', String(state.basket.has(node.dataset.basket)));
    });
    $('tab-tidy').textContent = state.basket.size ? '整理（' + state.basket.size + '）' : '整理';
    renderBasket();
  }

  // ---- Findings ----------------------------------------------------------

  function findingItem(item) {
    let action = null;
    if (item.fix) action = IS_STATIC ? badge('可整理', 'accent') : basketButton({ op: 'fix', id: item.id }, '加入整理');
    return h(
      'li',
      { class: 'finding' },
      badge(SEVERITY[item.severity], item.severity),
      h('div', { class: 'finding-title' }, item.title, h('span', { class: 'finding-code', text: item.code })),
      action ? h('div', { class: 'finding-action' }, action) : null,
      h('div', { class: 'finding-meta' }, h('span', { class: 'mono', text: item.path }), item.detail ? ' · ' + item.detail : '')
    );
  }

  function findingList(items, limit) {
    const list = h('ul', { class: 'findings' });
    const first = limit && items.length > limit ? items.slice(0, limit) : items;
    first.forEach((item) => list.appendChild(findingItem(item)));
    if (first.length === items.length) return list;
    const more = h('button', { class: 'button button-small', type: 'button', text: '显示全部 ' + items.length + ' 项' });
    more.addEventListener('click', () => {
      items.slice(limit).forEach((item) => list.appendChild(findingItem(item)));
      more.remove();
      syncBasket();
    });
    return h('div', { class: 'stack-tight' }, list, h('div', null, more));
  }

  function issueBadges(ids) {
    const counts = { error: 0, warn: 0, info: 0 };
    ids.forEach((id) => {
      const item = state.findings.get(id);
      if (item) counts[item.severity] += 1;
    });
    const nodes = SEVERITIES.filter((key) => counts[key]).map((key) => badge(SEVERITY[key] + ' ' + counts[key], key));
    return nodes.length ? h('span', { class: 'cluster' }, nodes) : h('span', { class: 'muted', text: '无' });
  }

  const findingsOf = (ids) => ids.map((id) => state.findings.get(id)).filter(Boolean);

  // ---- Header and overview ----------------------------------------------

  function renderHeader() {
    const meta = state.snap.meta;
    $('brand-line').textContent = [meta.brand, '本机 Agent 的规则、Skill 与源码'].filter(Boolean).join(' · ');
    const mode = $('mode-badge');
    mode.textContent = IS_STATIC ? '静态快照' : meta.write_enabled ? '可整理' : '只读';
    mode.className = 'badge' + (!IS_STATIC && meta.write_enabled ? ' badge-accent' : '');
    $('scan-time').textContent = '扫描于 ' + when(meta.generated_at);
    $('rescan').hidden = IS_STATIC;
  }

  function chain(title, lead, nodes) {
    return h(
      'section',
      { class: 'stack-tight' },
      h('div', null, h('h2', { text: title }), h('p', { class: 'muted', text: lead })),
      h(
        'ol',
        { class: 'chain-nodes' },
        nodes.map((node) =>
          h(
            'li',
            { class: 'chain-node' + (node.tone ? ' tone-' + node.tone : '') },
            h(
              'a',
              { href: node.href },
              h('span', { class: 'chain-value', text: node.value }),
              h('span', { class: 'chain-label', text: node.label }),
              h('span', { class: 'chain-note', text: node.note })
            )
          )
        )
      )
    );
  }

  function hostRows() {
    const rows = new Map();
    state.snap.skills.hosts.forEach((host) => rows.set(host.id, { id: host.id, label: host.label, skills: host, prompts: [] }));
    state.snap.prompt.hosts.forEach((entry) => {
      const row = rows.get(entry.host) || { id: entry.host, label: entry.label, skills: null, prompts: [] };
      row.prompts.push(entry);
      rows.set(entry.host, row);
    });
    const weight = (row) => (row.id === 'shared' ? Infinity : row.skills ? row.skills.entries : -1);
    return Array.from(rows.values()).sort((a, b) => weight(b) - weight(a) || a.id.localeCompare(b.id));
  }

  function promptBadges(entries) {
    if (!entries.length) return h('span', { class: 'muted', text: '—' });
    return h(
      'span',
      { class: 'cluster' },
      entries.map((entry) => {
        const info = PROMPT_STATE[entry.state] || [entry.state, ''];
        return badge(info[0], info[1]);
      })
    );
  }

  function renderOverview() {
    const snap = state.snap;
    const sum = snap.summary;
    const prompt = snap.prompt;
    const references = prompt.files.filter((file) => file.kind === 'reference');
    const referenceRules = references.reduce((total, file) => total + (file.rules || []).length, 0);
    const stale = prompt.hosts.filter((host) => host.state === 'embedded-stale' || host.state === 'broken').length;

    const promptChain = chain('规则链路', '根 Prompt 经 reference 展开，再由各宿主的指令文件加载。', [
      {
        href: '#prompt',
        value: prompt.root ? (prompt.root.version ? 'v' + prompt.root.version : '已建立') : '未建立',
        label: '根 Prompt',
        note: prompt.root ? num(prompt.root.rules) + ' 条规则 · ' + prompt.root.path : snap.roots.agents_home + '/AGENTS.md',
      },
      { href: '#prompt', value: num(references.length), label: 'Reference', note: num(referenceRules) + ' 条按需加载的规则' },
      {
        href: '#prompt',
        value: sum.prompt.hosts_bound + ' / ' + sum.prompt.hosts_total,
        label: '宿主已绑定',
        note: stale ? stale + ' 个副本已过期或断开' : '已绑定的副本与根 Prompt 一致',
        tone: stale ? 'warn' : '',
      },
    ]);
    const skillChain = chain('Skill 链路', '真源经共享目录分发，各宿主再链接到共享目录。', [
      {
        href: '#studio',
        value: snap.studio.configured ? num(sum.studio.sources) : '未配置',
        label: '源码目录',
        note: snap.studio.configured ? snap.roots.source_root : '还没有指定 Skill 源码根目录',
      },
      {
        href: '#skills',
        value: num(sum.skills.shared_entries),
        label: '共享目录入口',
        note: snap.skills.shared || '没有共享目录',
      },
      {
        href: '#skills',
        value: num(sum.skills.hosts),
        label: '宿主目录',
        note: num(sum.skills.unique) + ' 个不同的 Skill · ' + num(sum.skills.disabled) + ' 个已停用',
      },
    ]);

    const matrix = h(
      'table',
      null,
      h('thead', null, h('tr', null, h('th', { text: '区域' }), SEVERITIES.map((key) => h('th', { class: 'num', text: SEVERITY[key] })))),
      h(
        'tbody',
        null,
        Object.keys(AREA).map((key) =>
          h(
            'tr',
            null,
            h('td', null, h('a', { href: '#' + key, text: AREA[key] })),
            SEVERITIES.map((severity) => h('td', { class: 'num', text: num(sum.areas[key][severity]) }))
          )
        )
      )
    );
    const pending = h(
      'section',
      { class: 'card stack-tight' },
      h('h2', { text: '待处理' }),
      matrix,
      h(
        'p',
        null,
        '其中 ' + num(sum.findings.fixable) + ' 项可以自动整理。',
        sum.findings.fixable ? h('a', { href: '#tidy', text: '去整理' }) : null
      )
    );
    // One line per kind of problem, so a single noisy kind cannot fill the list.
    const kinds = new Map();
    snap.findings.forEach((item) => {
      if (item.severity === 'info') return;
      if (!kinds.has(item.code)) kinds.set(item.code, { first: item, count: 0 });
      kinds.get(item.code).count += 1;
    });
    const urgent = Array.from(kinds.values()).slice(0, 8);
    const top = h(
      'section',
      { class: 'card' },
      h('h2', { text: '优先处理' }),
      urgent.length
        ? h(
            'ul',
            { class: 'findings' },
            urgent.map((kind) =>
              h(
                'li',
                { class: 'finding' },
                badge(SEVERITY[kind.first.severity], kind.first.severity),
                h('div', { class: 'finding-title' }, kind.first.title + ' × ' + kind.count, h('span', { class: 'finding-code', text: kind.first.code })),
                h('div', { class: 'finding-action' }, h('a', { href: '#' + kind.first.area, text: AREA_LINK[kind.first.area] })),
                h('div', { class: 'finding-meta' }, kind.count > 1 ? '例如 ' : '', h('span', { class: 'mono', text: kind.first.path }))
              )
            )
          )
        : h('p', { class: 'muted', text: '没有错误或警告。' })
    );

    const rows = hostRows();
    const visible = state.allHosts ? rows : rows.slice(0, 10);
    const toggle =
      rows.length > 10
        ? h('button', {
            class: 'button button-small',
            type: 'button',
            id: 'hosts-toggle',
            'aria-expanded': String(state.allHosts),
            text: state.allHosts ? '只看前 10 个' : '显示全部 ' + rows.length + ' 个',
          })
        : null;
    if (toggle) {
      toggle.addEventListener('click', () => {
        state.allHosts = !state.allHosts;
        renderOverview();
        $('hosts-toggle').focus();
      });
    }
    const hosts = h(
      'section',
      { class: 'card stack-tight' },
      h('div', { class: 'spread' }, h('h2', { text: '宿主' }), toggle),
      h(
        'div',
        { class: 'table-wrap' },
        h(
          'table',
          null,
          h(
            'thead',
            null,
            h(
              'tr',
              null,
              h('th', { text: '宿主' }),
              h('th', { text: '指令文件' }),
              h('th', { class: 'num', text: '入口' }),
              h('th', { class: 'num', text: 'Skill' }),
              h('th', { class: 'num', text: '描述字符' })
            )
          ),
          h(
            'tbody',
            null,
            visible.map((row) =>
              h(
                'tr',
                null,
                h('td', null, row.label, row.label !== row.id ? h('span', { class: 'row-sub mono', text: row.id }) : null),
                h('td', null, promptBadges(row.prompts)),
                h('td', { class: 'num', text: row.skills ? num(row.skills.entries) : '—' }),
                h('td', { class: 'num', text: row.skills ? num(row.skills.skills) : '—' }),
                h('td', { class: 'num', text: row.skills ? num(row.skills.desc_chars) : '—' })
              )
            )
          )
        )
      ),
      h('p', { class: 'muted', text: '描述字符是该宿主每次会话都要读入的 Skill 描述总量。' })
    );

    const notes = snap.meta.notes.map((note) => h('p', { class: 'notice', text: note }));
    $('panel-overview').replaceChildren(
      h('div', { class: 'stack' }, notes, promptChain, skillChain, h('div', { class: 'grid-2' }, pending, top), hosts)
    );
  }

  // ---- System prompt -----------------------------------------------------

  function fileSummary(file) {
    if (file.state === 'broken') return '断开的链接';
    if (file.kind === 'root') return (file.version ? 'v' + file.version + ' · ' : '') + (file.rules || []).length + ' 条规则';
    if (file.kind === 'reference') {
      return ((file.namespaces || []).join('、') || '无编号') + ' · ' + (file.rules || []).length + ' 条规则' + (file.routed ? '' : ' · 未路由');
    }
    if (file.kind === 'changelog') return file.version ? '最新条目 ' + file.version : '没有版本条目';
    return file.path;
  }

  async function rawView(path, box) {
    if (IS_STATIC) {
      box.replaceChildren(h('p', { class: 'muted', text: '静态快照不包含文件原文。' }));
      return;
    }
    if (!state.raw.has(path)) {
      box.replaceChildren(h('p', { class: 'muted', text: '读取中…' }));
      try {
        state.raw.set(path, (await api('/api/file?path=' + encodeURIComponent(path))).text);
      } catch (error) {
        box.replaceChildren(h('p', { class: 'muted', text: '读取失败：' + error.message }));
        return;
      }
    }
    if (state.promptFile === path) box.replaceChildren(h('pre', { class: 'raw', tabindex: '0', text: state.raw.get(path) }));
  }

  function ruleGroups(rules) {
    const box = h('div', null);
    let section = null;
    let list = null;
    rules.forEach((rule) => {
      if (rule.section !== section || !list) {
        section = rule.section;
        if (section) box.appendChild(h('h4', { class: 'rule-section', text: section }));
        list = h('ul', { class: 'rules' });
        box.appendChild(list);
      }
      list.appendChild(
        h('li', { class: 'rule' }, h('span', { class: 'rule-id', text: rule.id }), h('div', null, h('strong', { text: rule.title }), h('p', { text: rule.body })))
      );
    });
    return box;
  }

  function fileDetail() {
    const prompt = state.snap.prompt;
    const file = prompt.files.find((item) => item.path === state.promptFile);
    if (!file) return h('div', { class: 'card empty', text: '这里还没有可查看的指令文件。' });
    const facts = [
      file.bytes !== undefined ? bytes(file.bytes) : '',
      file.lines ? file.lines + ' 行' : '',
      file.sha ? 'sha256 ' + file.sha : '',
      file.link_target ? '链接到 ' + file.link_target : '',
    ].filter(Boolean);
    const hasRules = (file.rules || []).length > 0;
    const view = hasRules ? state.promptView : 'raw';
    const body = h('div', null);
    if (view === 'raw') {
      rawView(file.path, body);
    } else {
      append(body, ruleGroups(file.rules));
      if (file.kind === 'root' && prompt.refs.length) {
        append(body, [
          h('h4', { class: 'rule-section', text: '引用的本机路径' }),
          h(
            'div',
            { class: 'table-wrap' },
            h(
              'table',
              null,
              h('thead', null, h('tr', null, h('th', { text: '规则' }), h('th', { text: '路径' }), h('th', { text: '状态' }))),
              h(
                'tbody',
                null,
                prompt.refs.map((ref) =>
                  h(
                    'tr',
                    null,
                    h('td', { class: 'mono', text: ref.rule || '第 ' + ref.line + ' 行' }),
                    h('td', { class: 'mono', text: ref.target }),
                    h('td', null, ref.exists ? badge('存在', 'ok') : badge('不存在', 'error'))
                  )
                )
              )
            )
          ),
        ]);
      }
    }
    let switcher = null;
    if (hasRules) {
      switcher = h(
        'div',
        { class: 'subtabs', role: 'group', 'aria-label': '查看方式' },
        [
          ['structure', '结构'],
          ['raw', '原文'],
        ].map((item) => {
          const button = h('button', { type: 'button', text: item[1], 'aria-pressed': String(view === item[0]) });
          button.addEventListener('click', () => {
            state.promptView = item[0];
            $('prompt-detail').replaceChildren(fileDetail());
            const again = Array.from(document.querySelectorAll('#prompt-detail .subtabs button')).find((node) => node.textContent === item[1]);
            if (again) again.focus();
          });
          return button;
        })
      );
    }
    return h(
      'article',
      { class: 'card stack-tight' },
      h(
        'div',
        { class: 'spread' },
        h('div', null, h('h2', { text: file.name }), h('p', { class: 'mono muted', text: file.path })),
        h('div', { class: 'cluster' }, switcher, revealButton(file.path), actionButton('用默认应用打开', () => api('/api/open', { path: file.path })))
      ),
      facts.length ? h('p', { class: 'muted', text: facts.join(' · ') }) : null,
      body
    );
  }

  function renderPrompt() {
    const prompt = state.snap.prompt;
    const files = prompt.files;
    if (!files.some((file) => file.path === state.promptFile)) state.promptFile = files.length ? files[0].path : '';
    const issues = state.snap.findings.filter((item) => item.area === 'prompt');

    const nav = h('nav', { class: 'card', 'aria-label': '指令文件' });
    FILE_GROUPS.forEach((group) => {
      const members = files.filter((file) => file.kind === group[0]);
      if (!members.length) return;
      nav.appendChild(h('p', { class: 'file-group', text: group[1] }));
      const list = h('ul', { class: 'file-list' });
      members.forEach((file) => {
        const button = h(
          'button',
          {
            class: 'file-button',
            type: 'button',
            'aria-current': String(file.path === state.promptFile),
            dataset: { file: file.path },
          },
          h('span', { class: 'row-name', text: file.name }),
          h('span', { class: 'row-sub', text: fileSummary(file) })
        );
        button.addEventListener('click', () => {
          state.promptFile = file.path;
          state.promptView = 'structure';
          nav.querySelectorAll('.file-button').forEach((node) => {
            node.setAttribute('aria-current', String(node.dataset.file === file.path));
          });
          $('prompt-detail').replaceChildren(fileDetail());
        });
        list.appendChild(h('li', null, button));
      });
      nav.appendChild(list);
    });

    const bindings = h(
      'section',
      { class: 'card stack-tight' },
      h('h2', { text: '宿主绑定' }),
      prompt.hosts.length
        ? h(
            'div',
            { class: 'table-wrap' },
            h(
              'table',
              null,
              h('thead', null, h('tr', null, h('th', { text: '宿主' }), h('th', { text: '指令文件' }), h('th', { text: '状态' }), h('th', { text: '指向' }), h('th', { text: '整理' }))),
              h(
                'tbody',
                null,
                prompt.hosts.map((entry) => {
                  const info = PROMPT_STATE[entry.state] || [entry.state, ''];
                  const fixable = issues.find((item) => item.path === entry.path && item.fix);
                  return h(
                    'tr',
                    null,
                    h('td', { text: entry.label }),
                    h('td', { class: 'mono', text: entry.path }),
                    h('td', null, badge(info[0], info[1])),
                    h('td', { class: 'mono', text: entry.link_target || entry.detail || '—' }),
                    h('td', null, fixable && !IS_STATIC ? basketButton({ op: 'fix', id: fixable.id }, fixable.fix.label) : '—')
                  );
                })
              )
            )
          )
        : h('p', { class: 'muted', text: '没有发现宿主的指令文件。' })
    );

    $('panel-prompt').replaceChildren(
      h(
        'div',
        { class: 'stack' },
        issues.length
          ? h('section', { class: 'card' }, h('h2', { text: '规则集的问题（' + issues.length + '）' }), findingList(issues, 6))
          : null,
        h('div', { class: 'prompt-layout' }, nav, h('div', { id: 'prompt-detail' }, fileDetail())),
        bindings
      )
    );
  }

  // ---- Expandable rows shared by Skills and Studio ----------------------

  function expandableRow(key, open, columns, cells, buildDetail) {
    const item = h('li', { class: 'row' });
    const head = h('button', { class: 'row-head ' + columns, type: 'button', 'aria-expanded': String(open.has(key)) }, cells);
    head.addEventListener('click', () => {
      const expanded = !open.has(key);
      if (expanded) {
        open.add(key);
        item.appendChild(buildDetail());
      } else {
        open.delete(key);
        item.querySelector('.row-detail').remove();
      }
      head.setAttribute('aria-expanded', String(expanded));
      item.classList.toggle('is-open', expanded);
      syncBasket();
    });
    item.appendChild(head);
    if (open.has(key)) {
      item.classList.add('is-open');
      item.appendChild(buildDetail());
    }
    return item;
  }

  function moreButton(remaining, grow) {
    const button = h('button', { class: 'button', type: 'button', text: '再显示 ' + Math.min(remaining, PAGE) + ' 个（还有 ' + remaining + ' 个）' });
    button.addEventListener('click', grow);
    return h('div', { class: 'cluster' }, button);
  }

  function field(label, control) {
    return h('label', { class: 'field' }, label, control);
  }

  function select(options, value, onChange) {
    const node = h(
      'select',
      null,
      options.map((option) => h('option', { value: option[0], text: option[1], selected: option[0] === value }))
    );
    node.addEventListener('change', () => onChange(node.value));
    return node;
  }

  function searchBox(value, placeholder, onChange) {
    const node = h('input', { type: 'search', value: value, placeholder: placeholder });
    // During IME composition the field holds pinyin, not the query.
    const handler = (event) => {
      if (!event.isComposing) onChange(node.value);
    };
    node.addEventListener('input', handler);
    node.addEventListener('compositionend', handler);
    return node;
  }

  // ---- Skills ------------------------------------------------------------

  function filteredSkills() {
    const filter = state.skills;
    const query = filter.query.trim().toLowerCase();
    const result = state.snap.skills.skills.filter((skill) => {
      if (filter.host && !skill.hosts.includes(filter.host)) return false;
      if (filter.origin && skill.origin !== filter.origin) return false;
      if (filter.issues && !skill.findings.length) return false;
      if (!query) return true;
      const haystack = [skill.name, skill.key, skill.description, skill.entries.map((entry) => entry.entry).join(' ')].join(' ');
      return haystack.toLowerCase().includes(query);
    });
    const byName = (a, b) => (a.name || a.key).localeCompare(b.name || b.key);
    if (filter.sort === 'desc') result.sort((a, b) => b.desc_len - a.desc_len || byName(a, b));
    else if (filter.sort === 'issues') result.sort((a, b) => b.findings.length - a.findings.length || byName(a, b));
    else if (filter.sort === 'hosts') result.sort((a, b) => hostCount(b) - hostCount(a) || byName(a, b));
    else result.sort(byName);
    return result;
  }

  function skillDetail(skill) {
    const shared = skill.entries.filter((entry) => entry.host === 'shared');
    const entryRows = (entries) =>
      entries.map((entry) => {
        let action = null;
        if (entry.host === 'shared') action = basketButton({ op: 'disable', entry: entry.entry }, '停用');
        else if (entry.kind === 'link') action = basketButton({ op: 'unlink', entry: entry.entry, host: entry.host }, '移除链接');
        return h(
          'tr',
          null,
          h('td', { text: hostLabel(entry.host) }),
          h('td', { class: 'mono', text: entry.entry }),
          h('td', { class: 'mono', text: entry.kind === 'link' ? entry.link_target : '实体目录' }),
          h('td', null, action || '—')
        );
      });
    const body = h('tbody', null, entryRows(skill.entries.slice(0, 8)));
    let expand = null;
    if (skill.entries.length > 8) {
      expand = h('button', { class: 'button button-small', type: 'button', text: '显示全部 ' + skill.entries.length + ' 个入口' });
      expand.addEventListener('click', () => {
        append(body, entryRows(skill.entries.slice(8)));
        expand.remove();
        syncBasket();
      });
    }

    let install = null;
    const targets = state.snap.skills.hosts.filter((host) => host.id !== 'shared' && !skill.hosts.includes(host.id));
    if (!IS_STATIC && shared.length && targets.length) {
      const picker = h('select', { 'aria-label': '安装到哪个宿主' }, targets.map((host) => h('option', { value: host.id, text: host.label })));
      const add = h('button', { class: 'button button-small', type: 'button', text: '加入整理' });
      add.addEventListener('click', () => {
        const op = { op: 'link', entry: shared[0].entry, host: picker.value };
        state.basket.set(opKey(op), op);
        syncBasket();
        toast('已加入整理篮：' + opLabel(op));
      });
      install = h('div', { class: 'cluster' }, h('span', { text: '安装到' }), picker, add);
    }

    const issues = findingsOf(skill.findings);
    return h(
      'div',
      { class: 'row-detail' },
      skill.description ? h('p', { text: skill.description }) : h('p', { class: 'muted', text: '没有描述。' }),
      h(
        'dl',
        { class: 'kv' },
        h('dt', { text: '位置' }),
        h('dd', { class: 'mono', text: skill.key }),
        h('dt', { text: '来源' }),
        h('dd', { text: (ORIGIN[skill.origin] || skill.origin) + (skill.source ? '（' + skill.source + '）' : '') }),
        skill.error ? [h('dt', { text: '解析' }), h('dd', { text: skill.error })] : null
      ),
      h(
        'div',
        null,
        h('h4', { text: '入口' }),
        h(
          'div',
          { class: 'table-wrap' },
          h('table', null, h('thead', null, h('tr', null, h('th', { text: '宿主' }), h('th', { text: '入口名' }), h('th', { text: '指向' }), h('th', { text: '整理' }))), body)
        ),
        expand
      ),
      issues.length ? h('div', null, h('h4', { text: '问题' }), findingList(issues)) : null,
      h(
        'div',
        { class: 'cluster' },
        revealButton(skill.key),
        actionButton('查看 SKILL.md', () => showFile(skill.key + '/SKILL.md', skill.name || 'SKILL.md')),
        install
      )
    );
  }

  function renderSkillsList() {
    const filter = state.skills;
    const all = filteredSkills();
    const shown = all.slice(0, filter.limit);
    const total = state.snap.skills.skills.length;
    const chars = all.reduce((sum, skill) => sum + skill.desc_len, 0);
    $('skills-count').textContent =
      '显示 ' + num(all.length) + ' / ' + num(total) + ' 个 Skill，描述合计 ' + num(chars) + ' 字符' +
      (filter.host ? '（' + hostLabel(filter.host) + ' 每次会话都会读入）' : '');
    const list = h(
      'ul',
      { class: 'list' },
      h(
        'li',
        { class: 'list-head cols-skills', 'aria-hidden': 'true' },
        ['Skill', '来源', '版本', '宿主', '描述', '问题'].map((label) => h('span', { text: label }))
      ),
      shown.map((skill) =>
        expandableRow(
          skill.key,
          filter.open,
          'cols-skills',
          [
            h('span', { class: 'row-name' }, skill.name || '（未命名）', h('span', { class: 'row-sub mono', text: skill.key })),
            h('span', null, badge(ORIGIN[skill.origin] || skill.origin, skill.origin === 'studio' ? 'accent' : '')),
            h('span', { text: skill.version || '—' }),
            h('span', { text: hostCount(skill) + ' 个宿主' }),
            h('span', { text: num(skill.desc_len) + ' 字' }),
            issueBadges(skill.findings),
          ],
          () => skillDetail(skill)
        )
      )
    );
    const box = $('skills-list');
    box.replaceChildren(all.length ? list : h('div', { class: 'card empty', text: '没有符合条件的 Skill。' }));
    if (all.length > shown.length) {
      box.appendChild(
        moreButton(all.length - shown.length, () => {
          filter.limit += PAGE;
          renderSkillsList();
        })
      );
    }
    syncBasket();
  }

  function renderSkills() {
    const data = state.snap.skills;
    const filter = state.skills;
    const attached = new Set();
    data.skills.forEach((skill) => skill.findings.forEach((id) => attached.add(id)));
    const loose = state.snap.findings.filter((item) => item.area === 'skills' && !attached.has(item.id));
    const refresh = () => {
      filter.limit = PAGE;
      renderSkillsList();
    };
    const issuesOnly = h('input', { type: 'checkbox', checked: filter.issues });
    issuesOnly.addEventListener('change', () => {
      filter.issues = issuesOnly.checked;
      refresh();
    });
    const toolbar = h(
      'div',
      { class: 'toolbar' },
      field('搜索', searchBox(filter.query, '名称、路径或描述', (value) => {
        filter.query = value;
        refresh();
      })),
      field('宿主', select([['', '全部宿主']].concat(data.hosts.map((host) => [host.id, host.label + '（' + host.skills + '）'])), filter.host, (value) => {
        filter.host = value;
        refresh();
      })),
      field('来源', select([['', '全部来源']].concat(Object.keys(ORIGIN).map((key) => [key, ORIGIN[key]])), filter.origin, (value) => {
        filter.origin = value;
        refresh();
      })),
      field('排序', select([['name', '名称'], ['desc', '描述最长'], ['issues', '问题最多'], ['hosts', '宿主最多']], filter.sort, (value) => {
        filter.sort = value;
        refresh();
      })),
      h('label', { class: 'check' }, issuesOnly, '只看有问题的')
    );

    const disabled = data.disabled.length
      ? h(
          'section',
          { class: 'card stack-tight' },
          h('h2', { text: '已停用（' + data.disabled.length + '）' }),
          h(
            'ul',
            { class: 'findings' },
            data.disabled.map((item) =>
              h(
                'li',
                { class: 'finding' },
                badge('停用', ''),
                h('div', { class: 'finding-title', text: item.name || item.entry }),
                IS_STATIC ? null : h('div', { class: 'finding-action' }, basketButton({ op: 'enable', entry: item.entry }, '启用')),
                h('div', { class: 'finding-meta' }, h('span', { class: 'mono', text: item.path }), item.description ? ' · ' + item.description : '')
              )
            )
          )
        )
      : null;

    $('panel-skills').replaceChildren(
      h(
        'div',
        { class: 'stack' },
        loose.length
          ? h('details', { class: 'card', open: loose.length <= 12 }, h('summary', { text: '不属于任何 Skill 的条目（' + loose.length + '）' }), findingList(loose, 12))
          : null,
        h('section', { class: 'stack-tight' }, toolbar, h('p', { id: 'skills-count', class: 'muted', role: 'status' }), h('div', { id: 'skills-list', class: 'stack-tight' })),
        disabled
      )
    );
    renderSkillsList();
  }

  // ---- Studio ------------------------------------------------------------

  function studioTitle(record) {
    return (record.catalog && record.catalog.name_zh) || record.name || record.dir || (record.catalog && record.catalog.name) || '';
  }

  function filteredSources() {
    const filter = state.studio;
    const query = filter.query.trim().toLowerCase();
    const predicate = (STUDIO_FILTERS.find((item) => item[0] === filter.filter) || STUDIO_FILTERS[0])[2];
    const result = state.snap.studio.sources.filter((record) => {
      if (!predicate(record)) return false;
      if (!query) return true;
      const catalog = record.catalog || {};
      return [record.dir, record.name, record.path, catalog.name, catalog.name_zh, catalog.display_name, catalog.category]
        .join(' ')
        .toLowerCase()
        .includes(query);
    });
    const byName = (a, b) => (a.dir || a.name).localeCompare(b.dir || b.name);
    const commit = (record) => (record.git && record.git.last_commit) || '';
    if (filter.sort === 'recent') result.sort((a, b) => commit(b).localeCompare(commit(a)) || byName(a, b));
    else if (filter.sort === 'issues') result.sort((a, b) => b.findings.length - a.findings.length || byName(a, b));
    else result.sort(byName);
    return result;
  }

  function versionCell(record) {
    const parts = [h('span', { text: record.version ? '源码 ' + record.version : '源码 —' })];
    if (record.catalog) {
      const relation = record.catalog.relation;
      parts.push(h('span', { text: '目录 ' + (record.catalog.version || '—') }));
      if (relation === 'source-ahead') parts.push(badge('待发布', 'info'));
      if (relation === 'source-behind') parts.push(badge('本地落后', 'warn'));
    }
    if (record.drift) parts.push(badge('版本不一致', 'warn'));
    return h('span', { class: 'cluster' }, parts);
  }

  function gitCell(record) {
    const git = record.git;
    if (!git) return h('span', { class: 'muted', text: '—' });
    if (!git.repo) return h('span', null, badge('非独立仓库', 'warn'));
    const parts = [h('span', { class: 'mono', text: git.branch || '(detached)' })];
    if (git.dirty) parts.push(badge('未提交 ' + git.dirty, 'warn'));
    if (git.ahead) parts.push(badge('未推送 ' + git.ahead, 'warn'));
    if (git.behind) parts.push(badge('落后 ' + git.behind, 'info'));
    if (!git.remote) parts.push(badge('无远端', 'info'));
    if (!git.dirty && !git.ahead && !git.behind && git.remote) parts.push(badge('已同步', 'ok'));
    return h('span', { class: 'cluster' }, parts);
  }

  function catalogCell(record) {
    const catalog = record.catalog;
    if (!catalog) return h('span', null, badge(record.skill_md ? '未登记' : '无 SKILL.md', ''));
    const parts = [badge(catalog.paid ? '付费' : '免费', catalog.paid ? 'accent' : 'ok')];
    if (catalog.visibility === 'internal') parts.push(badge('内部', ''));
    if (record.missing_source) parts.push(badge('本地无源码', 'info'));
    if (catalog.category) parts.push(h('span', { class: 'muted', text: catalog.category }));
    return h('span', { class: 'cluster' }, parts);
  }

  function studioDetail(record) {
    const git = record.git;
    const catalog = record.catalog;
    const facts = [];
    const fact = (label, value, mono) => {
      if (value) facts.push(h('dt', { text: label }), h('dd', { class: mono ? 'mono' : null, text: value }));
    };
    fact('位置', record.path, true);
    fact('SKILL.md', record.skill_md && record.skill_md !== 'SKILL.md' ? record.skill_md : '', true);
    fact('调用名', record.name, true);
    if (catalog) {
      fact('目录条目', [catalog.name, catalog.display_name, catalog.category].filter(Boolean).join(' · '));
      fact('目录更新', catalog.updated_at ? when(catalog.updated_at) : '');
    }
    if (git && git.repo) {
      fact('分支', git.branch + (git.upstream ? ' → ' + git.upstream : '（未设置上游）'), true);
      fact('远端', git.remote || '', true);
      fact('最近提交', git.last_commit ? when(git.last_commit) : '');
    }
    fact('镜像', record.mirror ? (record.mirror.version ? '版本 ' + record.mirror.version : '缺失') : '');
    fact('已安装', installedCount(record) ? record.installed.shared.concat(record.installed.hosts.map(hostLabel)).join('、') : '');
    if (record.modules) fact('内嵌模块', record.modules + ' 个');

    const surfaces = Object.keys(record.surfaces);
    const bundle = Object.keys(record.bundle);
    const issues = findingsOf(record.findings);
    const copies = [];
    if (record.dir && record.skill_md) {
      copies.push(actionButton('复制优化指令', () => copyText('审计并优化这个 Skill 的源码：' + record.path)));
      copies.push(actionButton('复制发布指令', () => copyText('发布这个 Skill：' + record.path)));
      if (git && git.repo && (git.dirty || git.ahead)) {
        copies.push(actionButton('复制提交指令', () => copyText('检查 ' + record.path + ' 的未提交改动，确认后提交并推送')));
      }
    }
    return h(
      'div',
      { class: 'row-detail' },
      facts.length ? h('dl', { class: 'kv' }, facts) : h('p', { class: 'muted', text: '目录里登记了这个 Skill，但本机没有它的源码。' }),
      surfaces.length
        ? h(
            'div',
            null,
            h('h4', { text: '版本号' }),
            h(
              'div',
              { class: 'cluster' },
              surfaces.map((name) => badge(name + ' ' + record.surfaces[name], record.surfaces[name] === record.version ? '' : 'warn'))
            )
          )
        : null,
      bundle.length
        ? h(
            'div',
            null,
            h('h4', { text: '随源码交付的文件' }),
            h('div', { class: 'cluster' }, bundle.map((name) => badge((record.bundle[name] ? '有 ' : '缺 ') + name, record.bundle[name] ? 'ok' : '')))
          )
        : null,
      issues.length ? h('div', null, h('h4', { text: '问题' }), findingList(issues)) : null,
      record.path
        ? h(
            'div',
            { class: 'cluster' },
            revealButton(record.path),
            record.dir && record.skill_md
              ? actionButton('运行校验', async () => {
                  const result = await api('/api/validate', { path: record.path });
                  openDialog(result.ok ? '校验通过' : '校验未通过', [h('pre', { class: 'raw', tabindex: '0', text: result.output || '（没有输出）' })], [{ label: '关闭' }]);
                })
              : null,
            copies
          )
        : null
    );
  }

  function renderStudioList() {
    const filter = state.studio;
    const all = filteredSources();
    const shown = all.slice(0, filter.limit);
    $('studio-count').textContent = '显示 ' + num(all.length) + ' / ' + num(state.snap.studio.sources.length) + ' 项';
    const list = h(
      'ul',
      { class: 'list' },
      h('li', { class: 'list-head cols-studio', 'aria-hidden': 'true' }, ['Skill', '版本', 'Git', '目录', '问题'].map((label) => h('span', { text: label }))),
      shown.map((record) =>
        expandableRow(
          record.path || 'catalog:' + record.name,
          filter.open,
          'cols-studio',
          [
            h(
              'span',
              { class: 'row-name' },
              studioTitle(record),
              h('span', { class: 'row-sub mono', text: [record.name, record.dir].filter(Boolean).join(' · ') })
            ),
            versionCell(record),
            gitCell(record),
            catalogCell(record),
            issueBadges(record.findings),
          ],
          () => studioDetail(record)
        )
      )
    );
    const box = $('studio-list');
    box.replaceChildren(all.length ? list : h('div', { class: 'card empty', text: '没有符合条件的条目。' }));
    if (all.length > shown.length) {
      box.appendChild(
        moreButton(all.length - shown.length, () => {
          filter.limit += PAGE;
          renderStudioList();
        })
      );
    }
    syncBasket();
  }

  function renderStudio() {
    const studio = state.snap.studio;
    const sum = state.snap.summary.studio;
    const filter = state.studio;
    if (!studio.configured) {
      $('panel-studio').replaceChildren(
        h(
          'div',
          { class: 'card empty stack-tight' },
          h('p', { text: '还没有指定 Skill 源码根目录，所以这里没有内容。' }),
          h('p', { class: 'mono', text: '启动时加上 --source-root <目录>，或在共享 Profile 里设置 workspace.skill_repos_root' })
        )
      );
      return;
    }
    const refresh = () => {
      filter.limit = PAGE;
      renderStudioList();
    };
    const catalogLine = studio.catalog
      ? studio.catalog.error || studio.catalog.path + ' · ' + num(studio.catalog.total) + ' 条，其中 ' + num(studio.catalog.paid) + ' 条付费'
      : '没有找到目录文件；用 --catalog 指定 skills.yaml 后可以对照版本与登记状态';
    const header = h(
      'section',
      { class: 'card stack-tight' },
      h(
        'dl',
        { class: 'kv' },
        h('dt', { text: '源码根目录' }),
        h('dd', { class: 'mono', text: studio.source_root }),
        h('dt', { text: '目录' }),
        h('dd', { class: studio.catalog && !studio.catalog.error ? 'mono' : null, text: catalogLine })
      ),
      h(
        'div',
        { class: 'cluster' },
        badge(num(sum.sources) + ' 个源码目录', ''),
        badge(num(sum.listed) + ' 个已登记', ''),
        badge(num(sum.dirty) + ' 个有未提交改动', sum.dirty ? 'warn' : 'ok'),
        badge(num(sum.unpushed) + ' 个未推送', sum.unpushed ? 'warn' : 'ok'),
        badge(num(sum.drift) + ' 个版本不一致', sum.drift ? 'warn' : 'ok')
      ),
      state.snap.meta.git_checked ? null : h('p', { class: 'muted', text: '本次扫描跳过了 Git 状态。' }),
      studio.stray.length ? h('p', { class: 'muted', text: '根目录里还有 ' + studio.stray.length + ' 个散落文件：' + studio.stray.slice(0, 6).join('、') + (studio.stray.length > 6 ? ' 等' : '') }) : null
    );
    const toolbar = h(
      'div',
      { class: 'toolbar' },
      field('搜索', searchBox(filter.query, '名称、目录或分类', (value) => {
        filter.query = value;
        refresh();
      })),
      field('筛选', select(STUDIO_FILTERS.map((item) => [item[0], item[1]]), filter.filter, (value) => {
        filter.filter = value;
        refresh();
      })),
      field('排序', select([['name', '名称'], ['recent', '最近提交'], ['issues', '问题最多']], filter.sort, (value) => {
        filter.sort = value;
        refresh();
      }))
    );
    $('panel-studio').replaceChildren(
      h(
        'div',
        { class: 'stack' },
        header,
        h('section', { class: 'stack-tight' }, toolbar, h('p', { id: 'studio-count', class: 'muted', role: 'status' }), h('div', { id: 'studio-list', class: 'stack-tight' }))
      )
    );
    renderStudioList();
  }

  // ---- Tidy --------------------------------------------------------------

  function stepList(steps) {
    return h(
      'ol',
      { class: 'steps' },
      steps.map((step) => {
        let suffix = '';
        if (step.status === 'failed') suffix = '（失败：' + (step.error || '未知原因') + '）';
        if (step.status === 'skipped') suffix = '（已跳过）';
        return h('li', { class: step.status === 'failed' || step.status === 'skipped' ? 'step-' + step.status : null, text: step.text + suffix });
      })
    );
  }

  async function applyPlan(plan) {
    const journal = await api('/api/apply', { batch: plan.batch });
    state.basket.clear();
    await load(false);
    const failed = journal.steps.some((step) => step.status === 'failed');
    openDialog(
      failed ? '整理中断' : '整理完成',
      [
        h('p', {
          text: failed
            ? '有一步没有通过执行前的检查，之后的步骤已跳过。已完成的部分可以在整理记录里撤销。'
            : '全部步骤已完成，批次 ' + journal.batch + ' 已记入整理记录。',
        }),
        stepList(journal.steps),
      ],
      [{ label: '关闭' }]
    );
    return true;
  }

  async function previewPlan() {
    const plan = await api('/api/plan', { ops: Array.from(state.basket.values()) });
    const writable = state.snap.meta.write_enabled;
    openDialog(
      '整理计划 · ' + plan.steps.length + ' 步',
      [
        h('p', {
          text: writable
            ? '确认后按顺序执行。任何一步的前提发生变化都会停下，已完成的步骤可以在整理记录里撤销。'
            : '只读模式下仅供预览。用 --allow-write 重新启动后才能执行。',
        }),
        stepList(plan.steps),
      ],
      [{ label: writable ? '取消' : '关闭' }, writable ? { label: '确认执行', primary: true, run: () => applyPlan(plan) } : null]
    );
  }

  function confirmUndo(batch) {
    openDialog(
      '撤销这次整理？',
      [h('p', { text: '将按相反顺序恢复批次 ' + batch.batch + ' 完成的 ' + batch.done + ' 步。' }), stepList(batch.steps)],
      [
        { label: '取消' },
        {
          label: '撤销',
          primary: true,
          run: async () => {
            const result = await api('/api/undo', { batch: batch.batch });
            await load(false);
            toast(result.undone ? '已撤销' : '撤销没有全部完成，请查看整理记录', !result.undone);
          },
        },
      ]
    );
  }

  function renderBasket() {
    const box = $('basket');
    if (!box) return;
    const items = Array.from(state.basket.entries());
    const preview = whileBusy(
      h('button', { class: 'button button-primary', type: 'button', text: '预览计划', disabled: !items.length }),
      previewPlan
    );
    const clear = h('button', { class: 'button', type: 'button', text: '清空', disabled: !items.length });
    clear.addEventListener('click', () => {
      state.basket.clear();
      syncBasket();
    });
    box.replaceChildren(
      h('div', { class: 'spread' }, h('h2', { text: '整理篮（' + items.length + '）' }), h('div', { class: 'cluster' }, clear, preview)),
      items.length
        ? h(
            'ul',
            { class: 'basket' },
            items.map((item) => {
              const remove = h('button', { class: 'button button-small', type: 'button', text: '移除' });
              remove.addEventListener('click', () => {
                state.basket.delete(item[0]);
                syncBasket();
              });
              return h('li', null, h('span', { text: opLabel(item[1]) }), remove);
            })
          )
        : h('p', { class: 'muted', text: '在下面或其他页签里点「加入整理」，把要处理的项目放进来。' })
    );
  }

  function renderTidy() {
    const meta = state.snap.meta;
    const writable = !IS_STATIC && meta.write_enabled;
    const fixable = state.snap.findings.filter((item) => item.fix);
    let notice = '每次整理都先给出逐步计划，确认后才执行。只移动条目或增删符号链接，全部记入整理记录，可以撤销。';
    if (IS_STATIC) notice = '这是一份静态快照，不能在这里执行整理。请用 serve --allow-write 打开驾驶舱，或让 Agent 运行 tidy 命令。';
    else if (!writable) notice = '当前是只读模式：可以预览计划，但不会改动任何文件。用 --allow-write 重新启动后才能执行。';

    const groups = new Map();
    fixable.forEach((item) => {
      if (!groups.has(item.code)) groups.set(item.code, []);
      groups.get(item.code).push(item);
    });
    const groupNodes = Array.from(groups.entries()).map((entry) => {
      const items = entry[1];
      let addAll = null;
      if (!IS_STATIC) {
        addAll = h('button', { class: 'button button-small', type: 'button', text: '全部加入（' + items.length + '）' });
        addAll.addEventListener('click', () => {
          items.forEach((item) => state.basket.set('fix:' + item.id, { op: 'fix', id: item.id }));
          syncBasket();
        });
      }
      return h(
        'details',
        { class: 'card' },
        h('summary', null, items[0].title + '（' + items.length + '）', h('span', { class: 'finding-code', text: entry[0] })),
        h('div', { class: 'stack-tight' }, h('div', { class: 'spread' }, h('p', { class: 'muted', text: '整理方式：' + items[0].fix.label }), addAll), findingList(items, 8))
      );
    });

    let journal = null;
    if (!IS_STATIC) {
      journal = h(
        'section',
        { class: 'card stack-tight' },
        h('h2', { text: '整理记录' }),
        state.journal.length
          ? h(
              'ul',
              { class: 'findings' },
              state.journal.map((batch) => {
                const status = batch.undone_at ? badge('已撤销', '') : batch.failed ? badge('部分失败', 'warn') : badge('已执行', 'ok');
                let undo = null;
                if (writable && !batch.undone_at && batch.done) {
                  undo = h('button', { class: 'button button-small', type: 'button', text: '撤销' });
                  undo.addEventListener('click', () => confirmUndo(batch));
                }
                return h(
                  'li',
                  { class: 'finding' },
                  status,
                  h('div', { class: 'finding-title' }, when(batch.created_at), h('span', { class: 'finding-code', text: batch.batch })),
                  undo ? h('div', { class: 'finding-action' }, undo) : null,
                  h('div', { class: 'finding-meta' }, h('details', null, h('summary', { text: batch.done + ' 步完成' + (batch.failed ? '，' + batch.failed + ' 步失败' : '') }), stepList(batch.steps)))
                );
              })
            )
          : h('p', { class: 'muted', text: '还没有执行过整理。' })
      );
    }

    $('panel-tidy').replaceChildren(
      h(
        'div',
        { class: 'stack' },
        h('p', { class: 'notice', text: notice }),
        IS_STATIC ? null : h('section', { class: 'card stack-tight', id: 'basket' }),
        h('h2', { class: 'section-title', text: '可以自动整理的问题（' + fixable.length + '）' }),
        groupNodes.length ? groupNodes : h('div', { class: 'card empty', text: '没有可以自动整理的问题。' }),
        journal
      )
    );
  }

  // ---- Tabs and lifecycle ------------------------------------------------

  function selectTab(name, focus) {
    const target = TABS.includes(name) ? name : 'overview';
    state.tab = target;
    TABS.forEach((tab) => {
      const active = tab === target;
      const button = $('tab-' + tab);
      button.setAttribute('aria-selected', String(active));
      button.tabIndex = active ? 0 : -1;
      $('panel-' + tab).hidden = !active;
      if (active && focus) button.focus();
    });
    if (location.hash.slice(1) !== target) history.replaceState(null, '', '#' + target);
  }

  function renderAll() {
    renderHeader();
    renderOverview();
    renderPrompt();
    renderSkills();
    renderStudio();
    renderTidy();
    syncBasket();
  }

  async function load(refresh) {
    const button = $('rescan');
    button.disabled = true;
    button.textContent = '扫描中…';
    try {
      if (IS_STATIC) {
        state.snap = JSON.parse(embedded.textContent);
      } else {
        state.snap = await api('/api/snapshot' + (refresh ? '?refresh=1' : ''));
        state.journal = (await api('/api/journal')).batches;
      }
      state.findings = new Map(state.snap.findings.map((item) => [item.id, item]));
      state.raw.clear();
      Array.from(state.basket.keys()).forEach((key) => {
        if (key.startsWith('fix:') && !state.findings.has(key.slice(4))) state.basket.delete(key);
      });
      showNotice('');
      renderAll();
    } catch (error) {
      showNotice('无法读取 harness 状态：' + error.message, true);
    }
    button.disabled = false;
    button.textContent = '重新扫描';
  }

  const tablist = document.querySelector('.tabs');
  tablist.addEventListener('click', (event) => {
    const button = event.target.closest('[role="tab"]');
    if (button) selectTab(button.dataset.tab);
  });
  tablist.addEventListener('keydown', (event) => {
    const index = TABS.indexOf(state.tab);
    let next = -1;
    if (event.key === 'ArrowRight') next = (index + 1) % TABS.length;
    else if (event.key === 'ArrowLeft') next = (index + TABS.length - 1) % TABS.length;
    else if (event.key === 'Home') next = 0;
    else if (event.key === 'End') next = TABS.length - 1;
    if (next >= 0) {
      event.preventDefault();
      selectTab(TABS[next], true);
    }
  });
  window.addEventListener('hashchange', () => {
    selectTab(location.hash.slice(1));
    window.scrollTo(0, 0);
  });
  $('rescan').addEventListener('click', () => load(true));

  selectTab(location.hash.slice(1) || 'overview');
  load(false);
})();
