import 'package:flutter/material.dart';
import 'package:mednarrate/l10n/app_localizations.dart';

class ReportSearchBar extends StatelessWidget {
  final ValueChanged<String> onChanged;

  const ReportSearchBar({
    super.key,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return TextField(
      onChanged: onChanged,
      decoration: InputDecoration(
        hintText: AppLocalizations.of(context)!.searchReportsHint,
        prefixIcon: Icon(Icons.search),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        filled: true,
      ),
    );
  }
}