import 'package:flutter/material.dart';
import 'helpers.dart';

/// MarkdownFormatter — converts AI-generated Markdown text into structured
/// Flutter widgets. Handles: ### headings, ## headings, #, bullet lists (- * •),
/// bold **text**, numbered lists (1. 2. 3.), and plain paragraphs.
///
/// Never displays raw `#`, `**`, `*`, or `_` to the user.
/// Automatically pre-sanitizes INPUT_TEXT artifacts and entity labels.
class MarkdownFormatter {
  /// Converts [rawText] to a column of Flutter widgets with proper
  /// heading, bullet, and paragraph formatting.
  static Widget formatText(
    BuildContext context,
    String rawText, {
    TextStyle? baseStyle,
  }) {
    // Pre-sanitize display artifacts (INPUT_TEXT, entity labels, etc.)
    final sanitized = Helpers.sanitizeDisplayText(rawText);
    if (sanitized.trim().isEmpty) return const SizedBox.shrink();

    final theme = Theme.of(context);
    final defaultStyle = baseStyle ??
        TextStyle(
          fontSize: 14.5,
          height: 1.55,
          color: theme.colorScheme.onSurface,
        );
    final lines = sanitized.split('\n');

    final children = <Widget>[];
    bool prevWasEmpty = true;

    for (var line in lines) {
      final trimmed = line.trim();

      if (trimmed.isEmpty) {
        if (!prevWasEmpty) children.add(const SizedBox(height: 8));
        prevWasEmpty = true;
        continue;
      }
      prevWasEmpty = false;

      // ── Markdown header: ### / ## / #
      if (trimmed.startsWith('#')) {
        int level = 0;
        while (level < trimmed.length && trimmed[level] == '#') { level++; }
        final title = trimmed.substring(level).trim();
        final fontSize = level == 1 ? 18.0 : (level == 2 ? 15.5 : 14.0);
        final color = level == 1
            ? theme.colorScheme.primary
            : theme.colorScheme.onSurface;

        children.add(
          Padding(
            padding: EdgeInsets.only(top: level == 1 ? 18 : 14, bottom: 5),
            child: Text(
              _stripInlineMarkdown(title),
              style: TextStyle(
                fontSize: fontSize,
                fontWeight: FontWeight.bold,
                color: color,
                height: 1.3,
              ),
            ),
          ),
        );
        continue;
      }

      // ── Numbered list: "1. Item" or "1) Item"
      final numberedMatch =
          RegExp(r'^(\d+)[.)\s]\s+(.+)$').firstMatch(trimmed);
      if (numberedMatch != null) {
        final num = numberedMatch.group(1)!;
        final content = numberedMatch.group(2)!;
        children.add(
          Padding(
            padding: const EdgeInsets.only(bottom: 6),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 22,
                  height: 22,
                  margin: const EdgeInsets.only(right: 10, top: 1),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.primary.withValues(alpha: 0.12),
                    shape: BoxShape.circle,
                  ),
                  child: Center(
                    child: Text(
                      num,
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                        color: theme.colorScheme.primary,
                      ),
                    ),
                  ),
                ),
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.only(top: 2),
                    child: RichText(
                      text: TextSpan(
                        children: _parseInlineSpans(context, content, defaultStyle),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
        continue;
      }

      // ── Bullet point: "- " or "* " or "• "
      if (trimmed.startsWith('- ') ||
          trimmed.startsWith('* ') ||
          trimmed.startsWith('• ')) {
        final bulletText = trimmed.substring(2).trim();
        children.add(
          Padding(
            padding: const EdgeInsets.only(left: 6, bottom: 5),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  margin: const EdgeInsets.only(top: 7, right: 10),
                  width: 5,
                  height: 5,
                  decoration: BoxDecoration(
                    color: theme.colorScheme.primary,
                    shape: BoxShape.circle,
                  ),
                ),
                Expanded(
                  child: RichText(
                    text: TextSpan(
                      children: _parseInlineSpans(context, bulletText, defaultStyle),
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
        continue;
      }

      // ── Plain paragraph
      children.add(
        Padding(
          padding: const EdgeInsets.only(bottom: 4),
          child: RichText(
            text: TextSpan(
              children: _parseInlineSpans(context, trimmed, defaultStyle),
            ),
          ),
        ),
      );
    }

    if (children.isEmpty) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: children,
    );
  }

  // ── Strip all inline markdown for heading text ─────────────────────────
  static String _stripInlineMarkdown(String text) =>
      text.replaceAll(RegExp(r'\*\*|\*|__|_|`'), '');

  // ── Parse inline bold/italic/code into TextSpans ───────────────────────
  static List<TextSpan> _parseInlineSpans(
    BuildContext context,
    String text,
    TextStyle baseStyle,
  ) {
    final spans = <TextSpan>[];
    // Matches **bold**, *italic*, `code`
    final exp = RegExp(r'\*\*(.*?)\*\*|\*(.*?)\*|`(.*?)`');
    int last = 0;

    for (final m in exp.allMatches(text)) {
      if (m.start > last) {
        spans.add(TextSpan(
          text: text.substring(last, m.start),
          style: baseStyle,
        ));
      }
      if (m.group(1) != null) {
        // Bold
        spans.add(TextSpan(
          text: m.group(1),
          style: baseStyle.copyWith(fontWeight: FontWeight.bold),
        ));
      } else if (m.group(2) != null) {
        // Italic
        spans.add(TextSpan(
          text: m.group(2),
          style: baseStyle.copyWith(fontStyle: FontStyle.italic),
        ));
      } else if (m.group(3) != null) {
        // Code
        spans.add(TextSpan(
          text: m.group(3),
          style: baseStyle.copyWith(
            backgroundColor:
                Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.08),
            fontFamily: 'monospace',
          ),
        ));
      }
      last = m.end;
    }

    if (last < text.length) {
      spans.add(TextSpan(text: text.substring(last), style: baseStyle));
    }

    return spans.isEmpty
        ? [TextSpan(text: text, style: baseStyle)]
        : spans;
  }
}
