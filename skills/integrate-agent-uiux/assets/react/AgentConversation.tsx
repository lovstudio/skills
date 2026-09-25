import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
} from "react";

import { AgentComposer } from "./AgentComposer";
import { AgentTranscript } from "./AgentTranscript";
import {
  DEFAULT_AGENT_UI_COPY,
  DEFAULT_AGENT_UI_THEME,
  type AgentAttachment,
  type AgentInteractionAnswer,
  type AgentMessage,
  type AgentReplyDetail,
  type AgentSendPayload,
  type AgentSessionState,
  type AgentUiCopy,
  type AgentUiTheme,
  type PendingInteraction,
} from "./types";

export function AgentConversation({
  title,
  messages,
  session,
  draft,
  attachments,
  replyDetail = "verbose",
  pendingInteraction,
  interactionAnswers,
  theme: themeOverride,
  copy: copyOverride,
  onDraftChange,
  onPickAttachment,
  onRemoveAttachment,
  onSend,
  onInteractionAnswersChange,
  onSubmitInteraction,
}: {
  title: string;
  messages: readonly AgentMessage[];
  session: AgentSessionState;
  draft: string;
  attachments: AgentAttachment[];
  replyDetail?: AgentReplyDetail;
  pendingInteraction?: PendingInteraction | null;
  interactionAnswers?: AgentInteractionAnswer;
  theme?: Partial<AgentUiTheme>;
  copy?: Partial<AgentUiCopy>;
  onDraftChange: (value: string) => void;
  onPickAttachment?: () => void;
  onRemoveAttachment?: (id: string) => void;
  onSend: (payload: AgentSendPayload) => Promise<void>;
  onInteractionAnswersChange?: (answers: AgentInteractionAnswer) => void;
  onSubmitInteraction?: (answers: AgentInteractionAnswer) => void;
}) {
  const theme = useMemo(
    () => ({ ...DEFAULT_AGENT_UI_THEME, ...themeOverride }),
    [themeOverride],
  );
  const copy = useMemo(
    () => ({ ...DEFAULT_AGENT_UI_COPY, ...copyOverride }),
    [copyOverride],
  );
  const scrollRef = useRef<HTMLDivElement>(null);
  const atBottomRef = useRef(true);
  const [atBottom, setAtBottom] = useState(true);
  useEffect(() => {
    if (atBottomRef.current)
      scrollRef.current?.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: "smooth",
      });
  }, [messages, pendingInteraction]);
  const style = {
    "--agent-bg": theme.background,
    "--agent-surface": theme.surface,
    "--agent-muted-surface": theme.surfaceMuted,
    "--agent-text": theme.text,
    "--agent-muted": theme.textMuted,
    "--agent-border": theme.border,
    "--agent-accent": theme.accent,
    "--agent-accent-text": theme.accentText,
    "--agent-user": theme.userSurface,
    "--agent-user-text": theme.userText,
    "--agent-success": theme.success,
    "--agent-warning": theme.warning,
    "--agent-danger": theme.danger,
    "--agent-code-bg": theme.codeBackground,
    "--agent-code-text": theme.codeText,
    "--agent-radius": `${theme.radius}px`,
    "--agent-gap": `${theme.gap}px`,
  } as CSSProperties;
  return (
    <section className="agent-ui" style={style}>
      <header className="agent-ui-header">
        <div>
          <h2>{title}</h2>
          {session.contextId ? (
            <code>contextId={session.contextId}</code>
          ) : null}
        </div>
        <span
          className={`agent-ui-session agent-ui-session--${session.status}`}
        >
          <i aria-hidden="true" />
          {session.statusLabel ?? session.status}
        </span>
      </header>
      <div
        ref={scrollRef}
        className="agent-ui-scroll"
        onScroll={(event) => {
          const target = event.currentTarget;
          const next =
            target.scrollHeight - target.scrollTop - target.clientHeight <= 96;
          atBottomRef.current = next;
          setAtBottom(next);
        }}
      >
        <AgentTranscript
          messages={messages}
          detail={replyDetail}
          pendingInteraction={pendingInteraction}
          interactionAnswers={interactionAnswers ?? {}}
          copy={copy}
          onInteractionAnswersChange={
            onInteractionAnswersChange ?? (() => undefined)
          }
          onSubmitInteraction={onSubmitInteraction ?? (() => undefined)}
        />
      </div>
      {!atBottom ? (
        <button
          className="agent-ui-jump"
          type="button"
          onClick={() => {
            const target = scrollRef.current;
            if (target)
              target.scrollTo({ top: target.scrollHeight, behavior: "smooth" });
          }}
        >
          {copy.jumpToLatestLabel}
        </button>
      ) : null}
      <AgentComposer
        value={draft}
        attachments={attachments}
        disabled={!session.canSend && !session.canResume}
        copy={copy}
        onChange={onDraftChange}
        onPickAttachment={onPickAttachment}
        onRemoveAttachment={onRemoveAttachment}
        onSend={onSend}
      />
    </section>
  );
}
