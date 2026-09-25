import { useMemo, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

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
  AgentUiTheme,
  PendingInteraction,
} from "./types";

function ToolGroup({
  messages,
  copy,
  theme,
}: {
  messages: AgentMessage[];
  copy: AgentUiCopy;
  theme: AgentUiTheme;
}) {
  const [expanded, setExpanded] = useState(false);
  const status = toolGroupStatus(messages);
  const title = toolGroupTitle(messages, copy.toolLabel);
  const statusLabel =
    status === "running"
      ? copy.runningLabel
      : status === "failed"
        ? copy.failedLabel
        : copy.completedLabel;
  const statusColor =
    status === "running"
      ? theme.warning
      : status === "failed"
        ? theme.danger
        : theme.success;
  return (
    <View
      style={[
        styles.card,
        {
          backgroundColor: theme.surfaceMuted,
          borderColor: theme.border,
          borderRadius: theme.radius,
        },
      ]}
    >
      <Pressable
        accessibilityRole="button"
        accessibilityState={{ expanded, busy: status === "running" }}
        accessibilityLabel={`${expanded ? copy.collapseLabel : copy.expandLabel} ${title}. ${statusLabel}`}
        hitSlop={8}
        style={styles.toolHeader}
        onPress={() => setExpanded((current) => !current)}
      >
        <View style={styles.toolTitle}>
          {status === "running" ? (
            <ActivityIndicator color={statusColor} size="small" />
          ) : (
            <View
              style={[styles.statusDot, { backgroundColor: statusColor }]}
            />
          )}
          <Text
            numberOfLines={1}
            style={{ color: theme.text, flex: 1, fontWeight: "700" }}
          >
            {title}
          </Text>
        </View>
        <Text style={{ color: statusColor, fontSize: 12, fontWeight: "700" }}>
          {statusLabel} {expanded ? "−" : "+"}
        </Text>
      </Pressable>
      {!expanded ? (
        <Text numberOfLines={1} style={{ color: theme.textMuted }}>
          {summarizeToolContent(messages.at(-1)?.content ?? "")}
        </Text>
      ) : null}
      {expanded ? (
        <View style={{ gap: 10 }}>
          {messages.map((message) => (
            <View key={message.id} style={{ gap: 5 }}>
              {messages.length > 1 ? (
                <Text
                  style={{
                    color: theme.textMuted,
                    fontSize: 12,
                    fontWeight: "700",
                  }}
                >
                  {message.title ?? copy.toolLabel}
                </Text>
              ) : null}
              <View
                style={[
                  styles.code,
                  {
                    backgroundColor: theme.codeBackground,
                    borderRadius: theme.radius / 2,
                  },
                ]}
              >
                <Text
                  selectable
                  style={{
                    color: theme.codeText,
                    fontFamily: "Menlo",
                    fontSize: 13,
                    lineHeight: 19,
                  }}
                >
                  {formatToolContent(message.content) || "No details"}
                </Text>
              </View>
            </View>
          ))}
        </View>
      ) : null}
    </View>
  );
}

function MessageCard({
  message,
  copy,
  theme,
}: {
  message: AgentMessage;
  copy: AgentUiCopy;
  theme: AgentUiTheme;
}) {
  const isUser = message.role === "user";
  const isStatus = message.role === "status";
  const title =
    message.title ??
    (isUser
      ? copy.userLabel
      : isStatus
        ? copy.statusLabel
        : copy.assistantLabel);
  const background = isUser
    ? theme.userSurface
    : isStatus
      ? theme.surfaceMuted
      : theme.surface;
  const foreground = isUser ? theme.userText : theme.text;
  return (
    <View
      style={[
        styles.card,
        isUser ? styles.userCard : null,
        {
          backgroundColor: background,
          borderColor: isUser ? theme.userSurface : theme.border,
          borderRadius: theme.radius,
        },
      ]}
    >
      <View style={styles.messageHeader}>
        <Text
          style={{
            color: isUser ? theme.userText : theme.textMuted,
            fontSize: 12,
            fontWeight: "700",
          }}
        >
          {title}
        </Text>
        {message.timestamp ? (
          <Text
            style={{
              color: isUser ? theme.userText : theme.textMuted,
              fontSize: 11,
            }}
          >
            {new Date(message.timestamp).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </Text>
        ) : null}
      </View>
      {message.format === "markdown" ? (
        <AgentMarkdown
          value={message.content}
          theme={
            isUser
              ? {
                  ...theme,
                  text: foreground,
                  accent: foreground,
                  surfaceMuted: "rgba(255,255,255,0.16)",
                  codeBackground: "rgba(0,0,0,0.28)",
                }
              : theme
          }
        />
      ) : (
        <Text
          selectable
          style={{
            color: foreground,
            fontFamily: message.format === "code" ? "Menlo" : undefined,
            fontSize: message.format === "code" ? 13 : 16,
            lineHeight: 23,
          }}
        >
          {message.content}
        </Text>
      )}
    </View>
  );
}

function InteractionCard({
  interaction,
  answers,
  onAnswersChange,
  onSubmit,
  theme,
  copy,
}: {
  interaction: PendingInteraction;
  answers: AgentInteractionAnswer;
  onAnswersChange: (answers: AgentInteractionAnswer) => void;
  onSubmit: (answers: AgentInteractionAnswer) => void;
  theme: AgentUiTheme;
  copy: AgentUiCopy;
}) {
  return (
    <View
      style={[
        styles.card,
        {
          backgroundColor: theme.surface,
          borderColor: theme.warning,
          borderRadius: theme.radius,
        },
      ]}
    >
      <Text
        accessibilityRole="header"
        style={{ color: theme.text, fontSize: 17, fontWeight: "700" }}
      >
        {interaction.title}
      </Text>
      {interaction.description ? (
        <Text style={{ color: theme.textMuted, lineHeight: 20 }}>
          {interaction.description}
        </Text>
      ) : null}
      {interaction.questions.map((question) => (
        <View key={question.id} style={{ gap: 8 }}>
          <Text style={{ color: theme.text, fontWeight: "600" }}>
            {question.header ?? question.prompt}
          </Text>
          {interaction.kind === "text" ? (
            <TextInput
              accessibilityLabel={question.prompt}
              multiline
              placeholder={question.prompt}
              placeholderTextColor={theme.textMuted}
              style={[
                styles.interactionInput,
                { borderColor: theme.border, color: theme.text },
              ]}
              value={answers[question.id]?.[0] ?? ""}
              onChangeText={(value) =>
                onAnswersChange({ ...answers, [question.id]: [value] })
              }
            />
          ) : (
            question.options.map((option) => {
              const selected =
                answers[question.id]?.includes(option.value) ?? false;
              return (
                <Pressable
                  key={option.id}
                  accessibilityRole={
                    question.multiSelect ? "checkbox" : "radio"
                  }
                  accessibilityState={{ checked: selected }}
                  style={[
                    styles.option,
                    {
                      borderColor: selected ? theme.accent : theme.border,
                      backgroundColor: selected
                        ? theme.surfaceMuted
                        : theme.surface,
                    },
                  ]}
                  onPress={() => {
                    const current = answers[question.id] ?? [];
                    const next = question.multiSelect
                      ? selected
                        ? current.filter((value) => value !== option.value)
                        : [...current, option.value]
                      : [option.value];
                    onAnswersChange({ ...answers, [question.id]: next });
                  }}
                >
                  <Text style={{ color: theme.text, fontWeight: "600" }}>
                    {option.label}
                  </Text>
                  {option.description ? (
                    <Text style={{ color: theme.textMuted, fontSize: 12 }}>
                      {option.description}
                    </Text>
                  ) : null}
                </Pressable>
              );
            })
          )}
        </View>
      ))}
      <Pressable
        accessibilityRole="button"
        style={[styles.answerButton, { backgroundColor: theme.accent }]}
        onPress={() => onSubmit(answers)}
      >
        <Text style={{ color: theme.accentText, fontWeight: "700" }}>
          {copy.answerLabel}
        </Text>
      </Pressable>
    </View>
  );
}

export function AgentTranscript({
  messages,
  detail,
  pendingInteraction,
  interactionAnswers,
  onInteractionAnswersChange,
  onSubmitInteraction,
  theme,
  copy,
}: {
  messages: readonly AgentMessage[];
  detail: AgentReplyDetail;
  pendingInteraction?: PendingInteraction | null;
  interactionAnswers: AgentInteractionAnswer;
  onInteractionAnswersChange: (answers: AgentInteractionAnswer) => void;
  onSubmitInteraction: (answers: AgentInteractionAnswer) => void;
  theme: AgentUiTheme;
  copy: AgentUiCopy;
}) {
  const items = useMemo(
    () =>
      groupAdjacentTools(
        mergeAdjacentAssistantMessages(filterAgentMessages(messages, detail)),
      ),
    [messages, detail],
  );
  return (
    <View style={{ gap: theme.gap }}>
      {items.length === 0 ? (
        <Text
          style={{
            color: theme.textMuted,
            paddingVertical: 24,
            textAlign: "center",
          }}
        >
          {copy.emptyLabel}
        </Text>
      ) : null}
      {items.map((item) =>
        item.kind === "tool-group" ? (
          <ToolGroup
            key={item.id}
            messages={item.messages}
            copy={copy}
            theme={theme}
          />
        ) : (
          <MessageCard
            key={item.id}
            message={item.message}
            copy={copy}
            theme={theme}
          />
        ),
      )}
      {pendingInteraction ? (
        <InteractionCard
          interaction={pendingInteraction}
          answers={interactionAnswers}
          onAnswersChange={onInteractionAnswersChange}
          onSubmit={onSubmitInteraction}
          theme={theme}
          copy={copy}
        />
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: { borderWidth: StyleSheet.hairlineWidth, gap: 10, padding: 14 },
  userCard: { alignSelf: "flex-end", maxWidth: "88%" },
  messageHeader: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  toolHeader: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    minHeight: 44,
  },
  toolTitle: { alignItems: "center", flex: 1, flexDirection: "row", gap: 8 },
  statusDot: { borderRadius: 5, height: 10, width: 10 },
  code: { padding: 11 },
  interactionInput: {
    borderRadius: 10,
    borderWidth: StyleSheet.hairlineWidth,
    fontSize: 16,
    minHeight: 72,
    padding: 10,
    textAlignVertical: "top",
  },
  option: {
    borderRadius: 10,
    borderWidth: 1,
    gap: 3,
    minHeight: 44,
    padding: 10,
  },
  answerButton: {
    alignItems: "center",
    borderRadius: 10,
    justifyContent: "center",
    minHeight: 44,
    paddingHorizontal: 16,
  },
});
