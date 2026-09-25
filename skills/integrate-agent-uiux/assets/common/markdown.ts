export type AgentMarkdownBlock =
  | { kind: "heading"; level: number; text: string }
  | { kind: "paragraph"; text: string }
  | { kind: "quote"; text: string }
  | { kind: "list"; ordered: boolean; items: string[] }
  | { kind: "table"; headers: string[]; rows: string[][] }
  | { kind: "code"; language?: string; text: string };

export type AgentInlineToken =
  | { kind: "text"; text: string }
  | { kind: "bold"; text: string }
  | { kind: "code"; text: string }
  | { kind: "link"; text: string; url: string };

function splitTableRow(value: string): string[] {
  const cells: string[] = [];
  let cell = "";
  let inCode = false;
  for (let index = 0; index < value.length; index += 1) {
    const character = value[index] ?? "";
    const next = value[index + 1];
    if (character === "\\" && next === "|") {
      cell += "|";
      index += 1;
      continue;
    }
    if (character === "`") inCode = !inCode;
    if (character === "|" && !inCode) {
      cells.push(cell.trim());
      cell = "";
      continue;
    }
    cell += character;
  }
  cells.push(cell.trim());
  if (cells[0] === "") cells.shift();
  if (cells.at(-1) === "") cells.pop();
  return cells;
}

function isTableDivider(value: string): boolean {
  const cells = splitTableRow(value);
  return cells.length > 0 && cells.every((cell) => /^:?-{3,}:?$/.test(cell));
}

function normalizeRow(cells: string[], count: number): string[] {
  if (cells.length > count) {
    return [...cells.slice(0, count - 1), cells.slice(count - 1).join(" | ")];
  }
  return [...cells, ...Array.from({ length: count - cells.length }, () => "")];
}

export function parseAgentMarkdown(value: string): AgentMarkdownBlock[] {
  const lines = value.replace(/\r/g, "").split("\n");
  const blocks: AgentMarkdownBlock[] = [];
  let paragraph: string[] = [];
  let index = 0;
  const flush = () => {
    const text = paragraph.join("\n").trim();
    if (text) blocks.push({ kind: "paragraph", text });
    paragraph = [];
  };

  while (index < lines.length) {
    const line = lines[index] ?? "";
    const trimmed = line.trim();
    if (!trimmed) {
      flush();
      index += 1;
      continue;
    }
    const fence = trimmed.match(/^```([A-Za-z0-9_-]+)?\s*$/);
    if (fence) {
      flush();
      const code: string[] = [];
      index += 1;
      while (
        index < lines.length &&
        !(lines[index] ?? "").trim().startsWith("```")
      ) {
        code.push(lines[index] ?? "");
        index += 1;
      }
      if (index < lines.length) index += 1;
      blocks.push({
        kind: "code",
        language: fence[1],
        text: code.join("\n").trimEnd(),
      });
      continue;
    }
    const heading = trimmed.match(/^(#{1,3})\s+(.+)$/);
    if (heading) {
      flush();
      blocks.push({
        kind: "heading",
        level: heading[1].length,
        text: heading[2].trim(),
      });
      index += 1;
      continue;
    }
    if (/^>\s?/.test(trimmed)) {
      flush();
      const quote: string[] = [];
      while (
        index < lines.length &&
        /^>\s?/.test((lines[index] ?? "").trim())
      ) {
        quote.push((lines[index] ?? "").trim().replace(/^>\s?/, ""));
        index += 1;
      }
      blocks.push({ kind: "quote", text: quote.join("\n").trim() });
      continue;
    }
    const nextLine = (lines[index + 1] ?? "").trim();
    if (trimmed.includes("|") && isTableDivider(nextLine)) {
      const headers = splitTableRow(trimmed);
      if (
        headers.length > 0 &&
        headers.length === splitTableRow(nextLine).length
      ) {
        flush();
        const rows: string[][] = [];
        index += 2;
        while (index < lines.length) {
          const row = (lines[index] ?? "").trim();
          if (!row || !row.includes("|")) break;
          rows.push(normalizeRow(splitTableRow(row), headers.length));
          index += 1;
        }
        blocks.push({ kind: "table", headers, rows });
        continue;
      }
    }
    const list = trimmed.match(/^((?:[-*+])|\d+[.)])\s+(.+)$/);
    if (list) {
      flush();
      const ordered = /\d+[.)]/.test(list[1]);
      const items: string[] = [];
      while (index < lines.length) {
        const item = (lines[index] ?? "")
          .trim()
          .match(/^((?:[-*+])|\d+[.)])\s+(.+)$/);
        if (!item || /\d+[.)]/.test(item[1]) !== ordered) break;
        items.push(item[2].trim());
        index += 1;
      }
      blocks.push({ kind: "list", ordered, items });
      continue;
    }
    paragraph.push(line);
    index += 1;
  }
  flush();
  return blocks;
}

export function tokenizeAgentInline(value: string): AgentInlineToken[] {
  const tokens: AgentInlineToken[] = [];
  const pattern = /(\*\*[^*]+\*\*|__[^_]+__|`[^`]+`|\[[^\]]+\]\([^)]+\))/g;
  let cursor = 0;
  let match: RegExpExecArray | null;
  while ((match = pattern.exec(value)) !== null) {
    if (match.index > cursor)
      tokens.push({ kind: "text", text: value.slice(cursor, match.index) });
    const raw = match[0];
    if (raw.startsWith("**") || raw.startsWith("__")) {
      tokens.push({ kind: "bold", text: raw.slice(2, -2) });
    } else if (raw.startsWith("`")) {
      tokens.push({ kind: "code", text: raw.slice(1, -1) });
    } else {
      const link = raw.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
      tokens.push(
        link
          ? { kind: "link", text: link[1], url: link[2] }
          : { kind: "text", text: raw },
      );
    }
    cursor = match.index + raw.length;
  }
  if (cursor < value.length)
    tokens.push({ kind: "text", text: value.slice(cursor) });
  return tokens.length > 0 ? tokens : [{ kind: "text", text: value }];
}
