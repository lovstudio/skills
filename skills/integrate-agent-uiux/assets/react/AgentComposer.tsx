import { useRef, useState } from "react";

import { canSubmitAgentInput, createAgentRequestId } from "./model";
import type { AgentAttachment, AgentSendPayload, AgentUiCopy } from "./types";

export function AgentComposer({
  value,
  attachments,
  disabled,
  copy,
  onChange,
  onPickAttachment,
  onRemoveAttachment,
  onSend,
}: {
  value: string;
  attachments: AgentAttachment[];
  disabled?: boolean;
  copy: AgentUiCopy;
  onChange: (value: string) => void;
  onPickAttachment?: () => void;
  onRemoveAttachment?: (id: string) => void;
  onSend: (payload: AgentSendPayload) => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);
  const [issue, setIssue] = useState<string | null>(null);
  const pendingId = useRef<string | null>(null);
  const fingerprint = `${value.trim()}\u0000${attachments.map((item) => item.id).join(",")}`;
  const pendingFingerprint = useRef(fingerprint);
  if (pendingFingerprint.current !== fingerprint && !busy) {
    pendingFingerprint.current = fingerprint;
    pendingId.current = null;
  }
  const canSend = canSubmitAgentInput(
    value,
    attachments.length,
    busy || Boolean(disabled),
  );
  const send = async () => {
    if (!canSend) return;
    const requestId = pendingId.current ?? createAgentRequestId();
    pendingId.current = requestId;
    setBusy(true);
    setIssue(null);
    try {
      await onSend({
        text: value.trim(),
        attachments,
        clientRequestId: requestId,
      });
      pendingId.current = null;
      onChange("");
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : String(cause);
      setIssue(`${message}\nrequestId=${requestId}`);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="agent-ui-composer">
      {attachments.length > 0 ? (
        <div className="agent-ui-attachments">
          {attachments.map((attachment) => (
            <span key={attachment.id} className="agent-ui-attachment">
              {attachment.name}
              {onRemoveAttachment ? (
                <button
                  aria-label={`${copy.removeAttachmentLabel}: ${attachment.name}`}
                  type="button"
                  onClick={() => onRemoveAttachment(attachment.id)}
                >
                  ×
                </button>
              ) : null}
            </span>
          ))}
        </div>
      ) : null}
      {issue ? (
        <pre aria-live="polite" className="agent-ui-issue">
          {issue}
        </pre>
      ) : null}
      <div className="agent-ui-composer-row">
        {onPickAttachment ? (
          <button
            aria-label={copy.addAttachmentLabel}
            className="agent-ui-icon-button"
            disabled={busy || disabled}
            type="button"
            onClick={onPickAttachment}
          >
            +
          </button>
        ) : null}
        <textarea
          aria-label={copy.placeholder}
          disabled={disabled}
          placeholder={copy.placeholder}
          rows={1}
          value={value}
          onChange={(event) => {
            setIssue(null);
            onChange(event.target.value);
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              void send();
            }
          }}
        />
        <button
          aria-busy={busy}
          className="agent-ui-primary"
          disabled={!canSend}
          type="button"
          onClick={() => void send()}
        >
          {busy ? "…" : issue ? copy.retryLabel : copy.sendLabel}
        </button>
      </div>
    </div>
  );
}
