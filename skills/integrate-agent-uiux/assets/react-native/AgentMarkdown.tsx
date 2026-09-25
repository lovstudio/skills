import { useMemo } from "react";
import {
  Linking,
  StyleSheet,
  Text,
  View,
  type StyleProp,
  type TextStyle,
} from "react-native";

import { parseAgentMarkdown, tokenizeAgentInline } from "./markdown";
import { safeAgentLink } from "./model";
import type { AgentUiTheme } from "./types";

function InlineText({
  text,
  theme,
  style,
}: {
  text: string;
  theme: AgentUiTheme;
  style?: StyleProp<TextStyle>;
}) {
  return (
    <Text
      selectable
      style={[{ color: theme.text, fontSize: 16, lineHeight: 24 }, style]}
    >
      {tokenizeAgentInline(text).map((token, index) => {
        if (token.kind === "bold")
          return (
            <Text key={index} style={styles.bold}>
              {token.text}
            </Text>
          );
        if (token.kind === "code") {
          return (
            <Text
              key={index}
              style={[
                styles.inlineCode,
                { backgroundColor: theme.surfaceMuted },
              ]}
            >
              {token.text}
            </Text>
          );
        }
        if (token.kind === "link") {
          return (
            <Text
              key={index}
              accessibilityRole="link"
              style={{ color: theme.accent, textDecorationLine: "underline" }}
              onPress={() => {
                const target = safeAgentLink(token.url);
                if (target) void Linking.openURL(target);
              }}
            >
              {token.text}
            </Text>
          );
        }
        return token.text;
      })}
    </Text>
  );
}

export function AgentMarkdown({
  value,
  theme,
}: {
  value: string;
  theme: AgentUiTheme;
}) {
  const blocks = useMemo(() => parseAgentMarkdown(value), [value]);
  return (
    <View style={{ gap: 10 }}>
      {blocks.map((block, index) => {
        if (block.kind === "heading") {
          return (
            <Text
              key={index}
              selectable
              accessibilityRole="header"
              style={{
                color: theme.text,
                fontSize: block.level === 1 ? 22 : 18,
                fontWeight: "700",
                lineHeight: 28,
              }}
            >
              {block.text}
            </Text>
          );
        }
        if (block.kind === "code") {
          return (
            <View
              key={index}
              style={[
                styles.code,
                {
                  backgroundColor: theme.codeBackground,
                  borderRadius: theme.radius / 2,
                },
              ]}
            >
              {block.language ? (
                <Text style={[styles.language, { color: theme.textMuted }]}>
                  {block.language}
                </Text>
              ) : null}
              <Text
                selectable
                style={[styles.codeText, { color: theme.codeText }]}
              >
                {block.text}
              </Text>
            </View>
          );
        }
        if (block.kind === "quote") {
          return (
            <View
              key={index}
              style={[styles.quote, { borderLeftColor: theme.accent }]}
            >
              <InlineText
                text={block.text}
                theme={theme}
                style={{ color: theme.textMuted }}
              />
            </View>
          );
        }
        if (block.kind === "list") {
          return (
            <View key={index} style={{ gap: 6 }}>
              {block.items.map((item, itemIndex) => (
                <View key={`${itemIndex}-${item}`} style={styles.listItem}>
                  <Text style={{ color: theme.textMuted, width: 22 }}>
                    {block.ordered ? `${itemIndex + 1}.` : "•"}
                  </Text>
                  <InlineText text={item} theme={theme} style={{ flex: 1 }} />
                </View>
              ))}
            </View>
          );
        }
        if (block.kind === "table") {
          return (
            <View
              key={index}
              accessibilityLabel={`Table with ${block.rows.length} rows`}
              style={{ gap: 8 }}
            >
              {block.rows.map((row, rowIndex) => (
                <View
                  key={`${rowIndex}-${row.join("|")}`}
                  style={[
                    styles.tableCard,
                    {
                      backgroundColor: theme.surfaceMuted,
                      borderColor: theme.border,
                      borderRadius: theme.radius / 2,
                    },
                  ]}
                >
                  {block.headers.map((header, columnIndex) => (
                    <View key={`${header}-${columnIndex}`} style={{ gap: 2 }}>
                      <Text
                        style={{
                          color: theme.textMuted,
                          fontSize: 12,
                          fontWeight: "600",
                        }}
                      >
                        {header || `Column ${columnIndex + 1}`}
                      </Text>
                      <InlineText
                        text={row[columnIndex] || "—"}
                        theme={theme}
                      />
                    </View>
                  ))}
                </View>
              ))}
            </View>
          );
        }
        return <InlineText key={index} text={block.text} theme={theme} />;
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  bold: { fontWeight: "700" },
  inlineCode: { fontFamily: "Menlo", fontSize: 14, paddingHorizontal: 4 },
  code: { gap: 6, padding: 12 },
  language: { fontSize: 11, fontWeight: "700", textTransform: "uppercase" },
  codeText: { fontFamily: "Menlo", fontSize: 13, lineHeight: 19 },
  quote: { borderLeftWidth: 3, paddingLeft: 12 },
  listItem: { alignItems: "flex-start", flexDirection: "row" },
  tableCard: { borderWidth: StyleSheet.hairlineWidth, gap: 10, padding: 12 },
});
