import { useMemo } from "react";

import { parseAgentMarkdown, tokenizeAgentInline } from "./markdown";
import { safeAgentLink } from "./model";

function Inline({ text }: { text: string }) {
  return (
    <>
      {tokenizeAgentInline(text).map((token, index) => {
        if (token.kind === "bold")
          return <strong key={index}>{token.text}</strong>;
        if (token.kind === "code")
          return (
            <code key={index} className="agent-ui-inline-code">
              {token.text}
            </code>
          );
        if (token.kind === "link") {
          const href = safeAgentLink(token.url);
          return href ? (
            <a key={index} href={href} rel="noreferrer" target="_blank">
              {token.text}
            </a>
          ) : (
            <span key={index}>{token.text}</span>
          );
        }
        return token.text;
      })}
    </>
  );
}

export function AgentMarkdown({ value }: { value: string }) {
  const blocks = useMemo(() => parseAgentMarkdown(value), [value]);
  return (
    <div className="agent-ui-markdown">
      {blocks.map((block, index) => {
        if (block.kind === "heading") {
          const Heading =
            block.level === 1 ? "h2" : block.level === 2 ? "h3" : "h4";
          return <Heading key={index}>{block.text}</Heading>;
        }
        if (block.kind === "code")
          return (
            <pre key={index}>
              <code data-language={block.language}>{block.text}</code>
            </pre>
          );
        if (block.kind === "quote")
          return (
            <blockquote key={index}>
              <Inline text={block.text} />
            </blockquote>
          );
        if (block.kind === "list") {
          const List = block.ordered ? "ol" : "ul";
          return (
            <List key={index}>
              {block.items.map((item, itemIndex) => (
                <li key={`${itemIndex}-${item}`}>
                  <Inline text={item} />
                </li>
              ))}
            </List>
          );
        }
        if (block.kind === "table") {
          return (
            <div
              key={index}
              aria-label={`Table with ${block.rows.length} rows`}
              className="agent-ui-table-cards"
              role="table"
            >
              {block.rows.map((row, rowIndex) => (
                <div
                  key={`${rowIndex}-${row.join("|")}`}
                  className="agent-ui-table-card"
                  role="row"
                >
                  {block.headers.map((header, columnIndex) => (
                    <div
                      key={`${header}-${columnIndex}`}
                      className="agent-ui-table-field"
                      role="cell"
                    >
                      <span>{header || `Column ${columnIndex + 1}`}</span>
                      <strong>
                        <Inline text={row[columnIndex] || "—"} />
                      </strong>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          );
        }
        return (
          <p key={index}>
            <Inline text={block.text} />
          </p>
        );
      })}
    </div>
  );
}
