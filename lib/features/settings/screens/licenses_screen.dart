import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import '../../../core/constants/app_colors.dart';

class CustomLicensesScreen extends StatefulWidget {
  const CustomLicensesScreen({super.key});

  @override
  State<CustomLicensesScreen> createState() => _CustomLicensesScreenState();
}

class _CustomLicensesScreenState extends State<CustomLicensesScreen> {
  final TextEditingController _searchController = TextEditingController();
  final Map<String, List<LicenseEntry>> _packageLicenses = {};
  bool _loading = true;
  String _searchQuery = '';

  @override
  void initState() {
    super.initState();
    _loadLicenses();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadLicenses() async {
    final Map<String, List<LicenseEntry>> map = {};
    await for (final LicenseEntry license in LicenseRegistry.licenses) {
      for (final String package in license.packages) {
        map.putIfAbsent(package, () => []).add(license);
      }
    }

    if (mounted) {
      setState(() {
        _packageLicenses.addAll(map);
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final sortedPackages = _packageLicenses.keys.toList()..sort();
    final filteredPackages = sortedPackages.where((p) {
      return p.toLowerCase().contains(_searchQuery.toLowerCase());
    }).toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Open Source Licenses'),
        elevation: 0,
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                // Header Banner
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
                  color: theme.cardColor,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: AppColors.primary.withValues(alpha: 0.12),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: const Icon(
                              Icons.code_rounded,
                              color: AppColors.primary,
                              size: 20,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'MedNarrate',
                                style: TextStyle(
                                  color: theme.colorScheme.onSurface,
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              Text(
                                '${_packageLicenses.length} Third-Party Libraries',
                                style: TextStyle(
                                  color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                                  fontSize: 13,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                      const SizedBox(height: 14),

                      // Search Bar
                      TextField(
                        controller: _searchController,
                        onChanged: (val) => setState(() => _searchQuery = val),
                        decoration: InputDecoration(
                          hintText: 'Search packages...',
                          prefixIcon: const Icon(Icons.search_rounded, size: 20),
                          suffixIcon: _searchQuery.isNotEmpty
                              ? IconButton(
                                  icon: const Icon(Icons.clear_rounded, size: 18),
                                  onPressed: () {
                                    _searchController.clear();
                                    setState(() => _searchQuery = '');
                                  },
                                )
                              : null,
                          contentPadding: const EdgeInsets.symmetric(vertical: 10, horizontal: 16),
                          filled: true,
                          fillColor: theme.colorScheme.surface,
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(14),
                            borderSide: BorderSide.none,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                const Divider(height: 1),

                // Package List
                Expanded(
                  child: filteredPackages.isEmpty
                      ? Center(
                          child: Text(
                            'No licenses match "$_searchQuery"',
                            style: TextStyle(
                              color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                            ),
                          ),
                        )
                      : ListView.separated(
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          itemCount: filteredPackages.length,
                          separatorBuilder: (_, __) => const Divider(height: 1, indent: 20),
                          itemBuilder: (context, index) {
                            final package = filteredPackages[index];
                            final count = _packageLicenses[package]!.length;

                            return ListTile(
                              title: Text(
                                package,
                                style: TextStyle(
                                  color: theme.colorScheme.onSurface,
                                  fontWeight: FontWeight.w600,
                                  fontSize: 15,
                                ),
                              ),
                              subtitle: Text(
                                '$count ${count == 1 ? 'license' : 'licenses'}',
                                style: TextStyle(
                                  color: theme.colorScheme.onSurface.withValues(alpha: 0.6),
                                  fontSize: 13,
                                ),
                              ),
                              trailing: Icon(
                                Icons.arrow_forward_ios_rounded,
                                size: 14,
                                color: theme.colorScheme.onSurface.withValues(alpha: 0.4),
                              ),
                              onTap: () {
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) => _PackageLicenseDetailScreen(
                                      package: package,
                                      entries: _packageLicenses[package]!,
                                    ),
                                  ),
                                );
                              },
                            );
                          },
                        ),
                ),
              ],
            ),
    );
  }
}

class _PackageLicenseDetailScreen extends StatelessWidget {
  final String package;
  final List<LicenseEntry> entries;

  const _PackageLicenseDetailScreen({
    required this.package,
    required this.entries,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(package),
        elevation: 0,
      ),
      body: ListView.separated(
        padding: const EdgeInsets.all(20),
        itemCount: entries.length,
        separatorBuilder: (_, __) => const SizedBox(height: 24),
        itemBuilder: (context, index) {
          final entry = entries[index];
          final text = entry.paragraphs.map((p) => p.text).join('\n\n');

          return Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: theme.cardColor,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: theme.colorScheme.outlineVariant.withValues(alpha: 0.2),
              ),
            ),
            child: SelectionArea(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'License ${index + 1} of ${entries.length}',
                    style: const TextStyle(
                      color: AppColors.primary,
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    text,
                    style: TextStyle(
                      fontFamily: 'monospace',
                      fontSize: 12.5,
                      height: 1.5,
                      color: theme.colorScheme.onSurface.withValues(alpha: 0.85),
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
