import type { AgentMessage, AgentReplyDetail, AgentToolStatus } from "./types";

const INTERNAL_METADATA =
  /<oai-mem-citation\b[^>]*>[\s\S]*?<\/oai-mem-citation>/gi;
const TOOL_PREVIEW_LIMIT = 96;

export type AgentTranscriptItem =
  | { kind: "message"; id: string; message: AgentMessage }
  | { kind: "tool-group"; id: string; messages: AgentMessage[] };

export function stripInternalAgentMetadata(value: string): string {
  return value
    .replace(INTERNAL_METADATA, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

export function filterAgentMessages(
  messages: readonly AgentMessage[],
  detail: AgentReplyDetail,
): AgentMessage[] {
  const visible = messages.filter((message) => {
    if (detail === "hidden") return message.role === "user";
    if (detail === "concise") {
      return (
        message.role === "user" ||
        (message.role === "assistant" && message.agentPhase !== "commentary")
      );
    }
    if (detail === "detailed") return message.role !== "tool";
    return true;
  });

  return visible.flatMap((message) => {
    if (message.role !== "assistant") return [message];
    const content = stripInternalAgentMetadata(message.content);
    return content ? [{ ...message, content }] : [];
  });
}

export function mergeAdjacentAssistantMessages(
  messages: readonly AgentMessage[],
): AgentMessage[] {
  const merged: AgentMessage[] = [];
  for (const message of messages) {
    const previous = merged.at(-1);
    if (
      previous?.role === "assistant" &&
      message.role === "assistant" &&
      previous.agentPhase === message.agentPhase &&
      previous.format === message.format
    ) {
      previous.content = `${previous.content}\n\n${message.content}`.trim();
      previous.timestamp = message.timestamp ?? previous.timestamp;
      continue;
    }
    merged.push({ ...message });
  }
  return merged;
}

export function groupAdjacentTools(
  messages: readonly AgentMessage[],
): AgentTranscriptItem[] {
  const items: AgentTranscriptItem[] = [];
  for (const message of messages) {
    const previous = items.at(-1);
    if (message.role === "tool") {
      if (previous?.kind === "tool-group") previous.messages.push(message);
      else
        items.push({ kind: "tool-group", id: message.id, messages: [message] });
      continue;
    }
    items.push({ kind: "message", id: message.id, message });
  }
  return items;
}

export function formatToolContent(value: string): string {
  return value
    .replace(/\r\n?/g, "\n")
    .replace(/\\r\\n|\\n|\\r/g, "\n")
    .replace(/\\t/g, "  ")
    .trimEnd();
}

export function summarizeToolContent(value: string): string {
  const firstLine = formatToolContent(value)
    .split("\n")
    .map((line) => line.trim())
    .find(Boolean);
  if (!firstLine) return "No details";
  return firstLine.length > TOOL_PREVIEW_LIMIT
    ? `${firstLine.slice(0, TOOL_PREVIEW_LIMIT)}…`
    : firstLine;
}

export function toolGroupStatus(
  messages: readonly AgentMessage[],
): AgentToolStatus {
  if (messages.some((message) => message.toolStatus === "failed"))
    return "failed";
  if (messages.some((message) => message.toolStatus === "running"))
    return "running";
  return "completed";
}

export function toolGroupTitle(
  messages: readonly AgentMessage[],
  fallback = "Tool",
): string {
  const titles = [
    ...new Set(messages.map((message) => message.title ?? fallback)),
  ];
  if (messages.length === 1) return titles[0] ?? fallback;
  return titles.length === 1
    ? `${titles[0]} (${messages.length})`
    : `Tools (${messages.length})`;
}

export function safeAgentLink(value: string): string | null {
  try {
    const url = new URL(value.trim());
    return ["http:", "https:", "mailto:", "tel:"].includes(url.protocol)
      ? url.toString()
      : null;
  } catch {
    return null;
  }
}

export function canSubmitAgentInput(
  text: string,
  attachmentCount: number,
  busy: boolean,
): boolean {
  return !busy && (text.trim().length > 0 || attachmentCount > 0);
}

export function createAgentRequestId(
  now = Date.now(),
  random = Math.random(),
): string {
  return `agent-ui-${now.toString(36)}-${random.toString(36).slice(2, 12)}`;
}
