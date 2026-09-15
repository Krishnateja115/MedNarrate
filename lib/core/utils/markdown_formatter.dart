import 'package:flutter/material.dart';

/// MarkdownFormatter — parses raw Markdown text (headers, bold, bullet points)
/// into clean, structured Flutter Widgets without displaying literal `#`, `**`, or `-`.
class MarkdownFormatter {
  static Widget formatText(BuildContext context, String rawText, {TextStyle? baseStyle}) {
    if (rawText.trim().isEmpty) return const SizedBox.shrink();

    final theme = Theme.of(context);
    final defaultStyle = baseStyle ?? TextStyle(fontSize: 15, height: 1.5, color: theme.colorScheme.onSurface);
    final lines = rawText.split('\n');

    List<Widget> children = [];

    for (var line in lines) {
      final trimmed = line.trim();
      if (trimmed.isEmpty) {
        children.add(const SizedBox(height: 8));
        continue;
      }

      // Headers ### or ## or #
      if (trimmed.startsWith('#')) {
        int level = 0;
        while (level < trimmed.length && trimmed[level] == '#') {
          level++;
        }
        final title = trimmed.substring(level).trim();
        final fontSize = level == 1 ? 20.0 : (level == 2 ? 17.0 : 15.0);

        children.add(
          Padding(
            padding: const EdgeInsets.only(top: 14, bottom: 6),
            child: Text(
              _stripInlineMarkdown(title),
              style: TextStyle(
                fontSize: fontSize,
                fontWeight: FontWeight.bold,
                color: level == 1 ? theme.colorScheme.primary : theme.colorScheme.onSurface,
              ),
            ),
          ),
        );
      }
      // Bullet points (- or * or •)
      else if (trimmed.startsWith('- ') || trimmed.startsWith('* ') || trimmed.startsWith('• ')) {
        final bulletText = trimmed.substring(2).trim();
        children.add(
          Padding(
            padding: const EdgeInsets.only(left: 8, bottom: 6),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  margin: const EdgeInsets.only(top: 7, right: 10),
                  width: 6,
                  height: 6,
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
      }
      // Standard paragraph
      else {
        children.add(
          Padding(
            padding: const EdgeInsets.only(bottom: 6),
            child: RichText(
              text: TextSpan(
                children: _parseInlineSpans(context, trimmed, defaultStyle),
              ),
            ),
          ),
        );
      }
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: children,
    );
  }

  static String _stripInlineMarkdown(String text) {
    return text.replaceAll(RegExp(r'\*\*|\*|__|_|`'), '');
  }

  static List<TextSpan> _parseInlineSpans(BuildContext context, String text, TextStyle baseStyle) {
    final List<TextSpan> spans = [];
    final RegExp exp = RegExp(r'\*\*(.*?)\*\*|\*(.*?)\*|`(.*?)`');
    int lastMatchEnd = 0;

    for (final match in exp.allMatches(text)) {
      if (match.start > lastMatchEnd) {
        spans.add(TextSpan(
          text: text.substring(lastMatchEnd, match.start),
          style: baseStyle,
        ));
      }

      if (match.group(1) != null) {
        // Bold **text**
        spans.add(TextSpan(
          text: match.group(1),
          style: baseStyle.copyWith(fontWeight: FontWeight.bold),
        ));
      } else if (match.group(2) != null) {
        // Italic *text*
        spans.add(TextSpan(
          text: match.group(2),
          style: baseStyle.copyWith(fontStyle: FontStyle.italic),
        ));
      } else if (match.group(3) != null) {
        // Code `text`
        spans.add(TextSpan(
          text: match.group(3),
          style: baseStyle.copyWith(
            backgroundColor: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.08),
            fontFamily: 'monospace',
          ),
        ));
      }

      lastMatchEnd = match.end;
    }

    if (lastMatchEnd < text.length) {
      spans.add(TextSpan(
        text: text.substring(lastMatchEnd),
        style: baseStyle,
      ));
    }

    return spans;
  }
}
