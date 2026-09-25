import { useMemo, useRef, useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  type NativeScrollEvent,
  type NativeSyntheticEvent,
} from "react-native";

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

const BOTTOM_THRESHOLD = 96;

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
  const scrollRef = useRef<ScrollView>(null);
  const atBottomRef = useRef(true);
  const [atBottom, setAtBottom] = useState(true);
  const answers = interactionAnswers ?? {};
  const statusColor =
    session.status === "error"
      ? theme.danger
      : session.status === "working"
        ? theme.warning
        : session.status === "completed"
          ? theme.success
          : theme.textMuted;
  const updateBottom = (next: boolean) => {
    atBottomRef.current = next;
    setAtBottom((current) => (current === next ? current : next));
  };
  const handleScroll = (event: NativeSyntheticEvent<NativeScrollEvent>) => {
    const { contentOffset, contentSize, layoutMeasurement } = event.nativeEvent;
    updateBottom(
      contentSize.height - contentOffset.y - layoutMeasurement.height <=
        BOTTOM_THRESHOLD,
    );
  };
  const jumpToLatest = () => {
    updateBottom(true);
    scrollRef.current?.scrollToEnd({ animated: true });
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      style={[styles.root, { backgroundColor: theme.background }]}
    >
      <View
        style={[
          styles.header,
          { backgroundColor: theme.surface, borderBottomColor: theme.border },
        ]}
      >
        <View style={{ flex: 1, gap: 3 }}>
          <Text
            accessibilityRole="header"
            numberOfLines={1}
            style={{ color: theme.text, fontSize: 18, fontWeight: "700" }}
          >
            {title}
          </Text>
          {session.contextId ? (
            <Text
              selectable
              numberOfLines={1}
              style={{ color: theme.textMuted, fontSize: 11 }}
            >
              contextId={session.contextId}
            </Text>
          ) : null}
        </View>
        <View
          accessibilityLabel={session.statusLabel ?? session.status}
          style={styles.status}
        >
          <View style={[styles.statusDot, { backgroundColor: statusColor }]} />
          <Text style={{ color: statusColor, fontSize: 12, fontWeight: "700" }}>
            {session.statusLabel ?? session.status}
          </Text>
        </View>
      </View>
      <ScrollView
        ref={scrollRef}
        contentContainerStyle={styles.content}
        keyboardDismissMode="interactive"
        keyboardShouldPersistTaps="handled"
        scrollEventThrottle={80}
        onContentSizeChange={() => {
          if (atBottomRef.current)
            scrollRef.current?.scrollToEnd({ animated: true });
        }}
        onScroll={handleScroll}
      >
        <AgentTranscript
          messages={messages}
          detail={replyDetail}
          pendingInteraction={pendingInteraction}
          interactionAnswers={answers}
          onInteractionAnswersChange={
            onInteractionAnswersChange ?? (() => undefined)
          }
          onSubmitInteraction={onSubmitInteraction ?? (() => undefined)}
          theme={theme}
          copy={copy}
        />
      </ScrollView>
      {!atBottom ? (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={copy.jumpToLatestLabel}
          style={[
            styles.jump,
            { backgroundColor: theme.surface, borderColor: theme.border },
          ]}
          onPress={jumpToLatest}
        >
          <Text style={{ color: theme.accent, fontWeight: "700" }}>
            {copy.jumpToLatestLabel}
          </Text>
        </Pressable>
      ) : null}
      <AgentComposer
        value={draft}
        attachments={attachments}
        disabled={!session.canSend && !session.canResume}
        copy={copy}
        theme={theme}
        onChangeText={onDraftChange}
        onPickAttachment={onPickAttachment}
        onRemoveAttachment={onRemoveAttachment}
        onSend={onSend}
      />
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  header: {
    alignItems: "center",
    borderBottomWidth: StyleSheet.hairlineWidth,
    flexDirection: "row",
    gap: 12,
    minHeight: 58,
    paddingHorizontal: 16,
    paddingVertical: 9,
  },
  status: { alignItems: "center", flexDirection: "row", gap: 6 },
  statusDot: { borderRadius: 5, height: 10, width: 10 },
  content: { padding: 14, paddingBottom: 24 },
  jump: {
    alignSelf: "center",
    borderRadius: 22,
    borderWidth: StyleSheet.hairlineWidth,
    bottom: 84,
    minHeight: 44,
    paddingHorizontal: 16,
    position: "absolute",
    justifyContent: "center",
  },
});
