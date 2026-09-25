export type AgentMessageRole = "user" | "assistant" | "tool" | "status";
export type AgentMessageFormat = "markdown" | "plain" | "code";
export type AgentPhase = "commentary" | "final";
export type AgentToolStatus = "running" | "completed" | "failed";
export type AgentReplyDetail = "hidden" | "concise" | "detailed" | "verbose";
export type AgentSessionStatus =
  | "idle"
  | "working"
  | "waiting"
  | "error"
  | "completed";

export type AgentMessage = {
  id: string;
  role: AgentMessageRole;
  content: string;
  format: AgentMessageFormat;
  timestamp: string | null;
  title?: string;
  agentPhase?: AgentPhase;
  toolCallId?: string;
  toolStatus?: AgentToolStatus;
};

export type AgentAttachment = {
  id: string;
  name: string;
  kind: "image" | "file";
  previewUri?: string;
};

export type AgentInteractionOption = {
  id: string;
  label: string;
  value: string;
  description?: string;
};

export type AgentInteractionQuestion = {
  id: string;
  prompt: string;
  header?: string;
  multiSelect: boolean;
  options: AgentInteractionOption[];
};

export type PendingInteraction = {
  id: string;
  kind: "choice" | "confirmation" | "text";
  title: string;
  description?: string;
  questions: AgentInteractionQuestion[];
};

export type AgentSessionState = {
  status: AgentSessionStatus;
  canSend: boolean;
  canResume?: boolean;
  statusLabel?: string;
  contextId?: string;
};

export type AgentSendPayload = {
  text: string;
  attachments: AgentAttachment[];
  clientRequestId: string;
};

export type AgentInteractionAnswer = Readonly<
  Record<string, readonly string[]>
>;

export type AgentUiCopy = {
  assistantLabel: string;
  userLabel: string;
  statusLabel: string;
  toolLabel: string;
  runningLabel: string;
  completedLabel: string;
  failedLabel: string;
  emptyLabel: string;
  placeholder: string;
  sendLabel: string;
  retryLabel: string;
  addAttachmentLabel: string;
  removeAttachmentLabel: string;
  jumpToLatestLabel: string;
  expandLabel: string;
  collapseLabel: string;
  answerLabel: string;
};

export const DEFAULT_AGENT_UI_COPY: AgentUiCopy = {
  assistantLabel: "Assistant",
  userLabel: "You",
  statusLabel: "Status",
  toolLabel: "Tool",
  runningLabel: "Running",
  completedLabel: "Done",
  failedLabel: "Failed",
  emptyLabel: "No conversation yet.",
  placeholder: "Ask or continue the task…",
  sendLabel: "Send",
  retryLabel: "Retry",
  addAttachmentLabel: "Add attachment",
  removeAttachmentLabel: "Remove attachment",
  jumpToLatestLabel: "Jump to latest",
  expandLabel: "Expand",
  collapseLabel: "Collapse",
  answerLabel: "Submit answer",
};

export type AgentUiTheme = {
  background: string;
  surface: string;
  surfaceMuted: string;
  text: string;
  textMuted: string;
  border: string;
  accent: string;
  accentText: string;
  userSurface: string;
  userText: string;
  success: string;
  warning: string;
  danger: string;
  codeBackground: string;
  codeText: string;
  radius: number;
  gap: number;
};

export const DEFAULT_AGENT_UI_THEME: AgentUiTheme = {
  background: "#f7f6f2",
  surface: "#ffffff",
  surfaceMuted: "#efeee8",
  text: "#1d1d1b",
  textMuted: "#6f6e68",
  border: "#d9d7cf",
  accent: "#285f56",
  accentText: "#ffffff",
  userSurface: "#285f56",
  userText: "#ffffff",
  success: "#2f7a4d",
  warning: "#9a6a14",
  danger: "#b4433b",
  codeBackground: "#202321",
  codeText: "#eef2ed",
  radius: 16,
  gap: 12,
};
