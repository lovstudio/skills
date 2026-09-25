import { useMemo, useState } from "react";

import { AgentMarkdown } from "./AgentMarkdown";
import {
  filterAgentMessages,
  formatToolContent,
  groupAdjacentTools,
  mergeAdjacentAssistantMessages,
  summarizeToolContent,
  toolGroupStatus,
  toolGroupTitle,
} from "./model";
import type {
  AgentInteractionAnswer,
  AgentMessage,
  AgentReplyDetail,
  AgentUiCopy,
  PendingInteraction,
} from "./types";

function ToolGroup({
  messages,
  copy,
}: {
  messages: AgentMessage[];
  copy: AgentUiCopy;
}) {
  const [expanded, setExpanded] = useState(false);
  const status = toolGroupStatus(messages);
  const title = toolGroupTitle(messages, copy.toolLabel);
  const label =
    status === "running"
      ? copy.runningLabel
      : status === "failed"
        ? copy.failedLabel
        : copy.completedLabel;
  return (
    <section className={`agent-ui-card agent-ui-tool agent-ui-tool--${status}`}>
      <button
        aria-expanded={expanded}
        className="agent-ui-tool-header"
        type="button"
        onClick={() => setExpanded((current) => !current)}
      >
        <span>
          <i aria-hidden="true" className="agent-ui-status-dot" /> {title}
        </span>
        <span>
          {label} {expanded ? "−" : "+"}
        </span>
      </button>
      {!expanded ? (
        <p className="agent-ui-muted agent-ui-ellipsis">
          {summarizeToolContent(messages.at(-1)?.content ?? "")}
        </p>
      ) : null}
      {expanded ? (
        <div className="agent-ui-tool-list">
          {messages.map((message) => (
            <div key={message.id}>
              {messages.length > 1 ? (
                <strong className="agent-ui-tool-item-title">
                  {message.title ?? copy.toolLabel}
                </strong>
              ) : null}
              <pre>
                <code>
                  {formatToolContent(message.content) || "No details"}
                </code>
              </pre>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function MessageCard({
  message,
  copy,
}: {
  message: AgentMessage;
  copy: AgentUiCopy;
}) {
  const title =
    message.title ??
    (message.role === "user"
      ? copy.userLabel
      : message.role === "status"
        ? copy.statusLabel
        : copy.assistantLabel);
  return (
    <article
      className={`agent-ui-card agent-ui-message agent-ui-message--${message.role}`}
    >
      <header>
        <strong>{title}</strong>
        {message.timestamp ? (
          <time dateTime={message.timestamp}>
            {new Date(message.timestamp).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </time>
        ) : null}
      </header>
      {message.format === "markdown" ? (
        <AgentMarkdown value={message.content} />
      ) : message.format === "code" ? (
        <pre>
          <code>{message.content}</code>
        </pre>
      ) : (
        <p className="agent-ui-plain">{message.content}</p>
      )}
    </article>
  );
}

function InteractionCard({
  interaction,
  answers,
  copy,
  onAnswersChange,
  onSubmit,
}: {
  interaction: PendingInteraction;
  answers: AgentInteractionAnswer;
  copy: AgentUiCopy;
  onAnswersChange: (answers: AgentInteractionAnswer) => void;
  onSubmit: (answers: AgentInteractionAnswer) => void;
}) {
  return (
    <form
      className="agent-ui-card agent-ui-interaction"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit(answers);
      }}
    >
      <h3>{interaction.title}</h3>
      {interaction.description ? (
        <p className="agent-ui-muted">{interaction.description}</p>
      ) : null}
      {interaction.questions.map((question) => (
        <fieldset key={question.id}>
          <legend>{question.header ?? question.prompt}</legend>
          {interaction.kind === "text" ? (
            <textarea
              aria-label={question.prompt}
              value={answers[question.id]?.[0] ?? ""}
              onChange={(event) =>
                onAnswersChange({
                  ...answers,
                  [question.id]: [event.target.value],
                })
              }
            />
          ) : (
            question.options.map((option) => {
              const selected =
                answers[question.id]?.includes(option.value) ?? false;
              return (
                <label key={option.id} className="agent-ui-option">
                  <input
                    checked={selected}
                    name={question.id}
                    type={question.multiSelect ? "checkbox" : "radio"}
                    onChange={() => {
                      const current = answers[question.id] ?? [];
                      const next = question.multiSelect
                        ? selected
                          ? current.filter((value) => value !== option.value)
                          : [...current, option.value]
                        : [option.value];
                      onAnswersChange({ ...answers, [question.id]: next });
                    }}
                  />
                  <span>
                    <strong>{option.label}</strong>
                    {option.description ? (
                      <small>{option.description}</small>
                    ) : null}
                  </span>
                </label>
              );
            })
          )}
        </fieldset>
      ))}
      <button className="agent-ui-primary" type="submit">
        {copy.answerLabel}
      </button>
    </form>
  );
}

export function AgentTranscript({
  messages,
  detail,
  pendingInteraction,
  interactionAnswers,
  copy,
  onInteractionAnswersChange,
  onSubmitInteraction,
}: {
  messages: readonly AgentMessage[];
  detail: AgentReplyDetail;
  pendingInteraction?: PendingInteraction | null;
  interactionAnswers: AgentInteractionAnswer;
  copy: AgentUiCopy;
  onInteractionAnswersChange: (answers: AgentInteractionAnswer) => void;
  onSubmitInteraction: (answers: AgentInteractionAnswer) => void;
}) {
  const items = useMemo(
    () =>
      groupAdjacentTools(
        mergeAdjacentAssistantMessages(filterAgentMessages(messages, detail)),
      ),
    [messages, detail],
  );
  return (
    <div className="agent-ui-transcript">
      {items.length === 0 ? (
        <p className="agent-ui-empty">{copy.emptyLabel}</p>
      ) : null}
      {items.map((item) =>
        item.kind === "tool-group" ? (
          <ToolGroup key={item.id} messages={item.messages} copy={copy} />
        ) : (
          <MessageCard key={item.id} message={item.message} copy={copy} />
        ),
      )}
      {pendingInteraction ? (
        <InteractionCard
          interaction={pendingInteraction}
          answers={interactionAnswers}
          copy={copy}
          onAnswersChange={onInteractionAnswersChange}
          onSubmit={onSubmitInteraction}
        />
      ) : null}
    </div>
  );
}
