import { useRef, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { canSubmitAgentInput, createAgentRequestId } from "./model";
import type {
  AgentAttachment,
  AgentSendPayload,
  AgentUiCopy,
  AgentUiTheme,
} from "./types";

export function AgentComposer({
  value,
  attachments,
  disabled,
  copy,
  theme,
  onChangeText,
  onPickAttachment,
  onRemoveAttachment,
  onSend,
}: {
  value: string;
  attachments: AgentAttachment[];
  disabled?: boolean;
  copy: AgentUiCopy;
  theme: AgentUiTheme;
  onChangeText: (value: string) => void;
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

  const send = async () => {
    if (
      !canSubmitAgentInput(value, attachments.length, busy || Boolean(disabled))
    )
      return;
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
      onChangeText("");
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : String(cause);
      setIssue(`${message}\nrequestId=${requestId}`);
    } finally {
      setBusy(false);
    }
  };

  const canSend = canSubmitAgentInput(
    value,
    attachments.length,
    busy || Boolean(disabled),
  );
  return (
    <View
      style={[
        styles.shell,
        { backgroundColor: theme.surface, borderColor: theme.border },
      ]}
    >
      {attachments.length > 0 ? (
        <View style={styles.attachments}>
          {attachments.map((attachment) => (
            <View
              key={attachment.id}
              style={[
                styles.attachment,
                { backgroundColor: theme.surfaceMuted },
              ]}
            >
              <Text numberOfLines={1} style={{ color: theme.text, flex: 1 }}>
                {attachment.name}
              </Text>
              {onRemoveAttachment ? (
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel={`${copy.removeAttachmentLabel}: ${attachment.name}`}
                  hitSlop={8}
                  onPress={() => onRemoveAttachment(attachment.id)}
                >
                  <Text style={{ color: theme.danger, fontWeight: "700" }}>
                    ×
                  </Text>
                </Pressable>
              ) : null}
            </View>
          ))}
        </View>
      ) : null}
      {issue ? (
        <View
          accessibilityLiveRegion="polite"
          style={[
            styles.issue,
            { backgroundColor: theme.surfaceMuted, borderColor: theme.danger },
          ]}
        >
          <Text
            selectable
            style={{ color: theme.danger, fontSize: 12, lineHeight: 18 }}
          >
            {issue}
          </Text>
        </View>
      ) : null}
      <View style={styles.inputRow}>
        {onPickAttachment ? (
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={copy.addAttachmentLabel}
            disabled={busy || disabled}
            hitSlop={8}
            style={[styles.iconButton, { borderColor: theme.border }]}
            onPress={onPickAttachment}
          >
            <Text style={{ color: theme.text, fontSize: 22 }}>+</Text>
          </Pressable>
        ) : null}
        <TextInput
          accessibilityLabel={copy.placeholder}
          editable={!disabled}
          multiline
          placeholder={copy.placeholder}
          placeholderTextColor={theme.textMuted}
          style={[styles.input, { color: theme.text }]}
          value={value}
          onChangeText={(next) => {
            setIssue(null);
            onChangeText(next);
          }}
        />
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={issue ? copy.retryLabel : copy.sendLabel}
          accessibilityState={{ disabled: !canSend, busy }}
          disabled={!canSend}
          style={[
            styles.sendButton,
            { backgroundColor: canSend ? theme.accent : theme.surfaceMuted },
          ]}
          onPress={() => void send()}
        >
          {busy ? (
            <ActivityIndicator color={theme.accentText} />
          ) : (
            <Text
              style={{
                color: canSend ? theme.accentText : theme.textMuted,
                fontWeight: "700",
              }}
            >
              {issue ? copy.retryLabel : copy.sendLabel}
            </Text>
          )}
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  shell: { borderTopWidth: StyleSheet.hairlineWidth, gap: 8, padding: 12 },
  attachments: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  attachment: {
    alignItems: "center",
    borderRadius: 8,
    flexDirection: "row",
    gap: 8,
    maxWidth: 220,
    minHeight: 36,
    paddingHorizontal: 10,
  },
  issue: { borderLeftWidth: 3, borderRadius: 8, padding: 9 },
  inputRow: { alignItems: "flex-end", flexDirection: "row", gap: 8 },
  input: {
    flex: 1,
    fontSize: 16,
    lineHeight: 22,
    maxHeight: 150,
    minHeight: 44,
    paddingHorizontal: 4,
    paddingVertical: 10,
  },
  iconButton: {
    alignItems: "center",
    borderRadius: 12,
    borderWidth: StyleSheet.hairlineWidth,
    height: 44,
    justifyContent: "center",
    width: 44,
  },
  sendButton: {
    alignItems: "center",
    borderRadius: 12,
    justifyContent: "center",
    minHeight: 44,
    minWidth: 68,
    paddingHorizontal: 13,
  },
});
