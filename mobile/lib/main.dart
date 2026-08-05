import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const NexusApp());
}

String humanize(Object? value) {
  final text = (value ?? '').toString().replaceAll('_', ' ').trim();
  if (text.isEmpty) return '';
  return text[0].toUpperCase() + text.substring(1);
}

String compactMoney(num? value) {
  if (value == null) return '';
  final number = value.toDouble();
  if (number >= 10000000) return '₹${(number / 10000000).toStringAsFixed(2)} Cr';
  if (number >= 100000) return '₹${(number / 100000).toStringAsFixed(2)} L';
  return '₹${number.toStringAsFixed(0)}';
}

class NexusApi extends ChangeNotifier {
  NexusApi()
      : _baseUrl = const String.fromEnvironment(
          'NEXUS_API_URL',
          defaultValue: '',
        );

  String _baseUrl;
  String get baseUrl => _baseUrl;

  void setBaseUrl(String value) {
    _baseUrl = value.trim().replaceAll(RegExp(r'/$'), '');
    notifyListeners();
  }

  Uri uri(String path) {
    if (_baseUrl.isEmpty) {
      throw const NexusException('Backend address is not configured.');
    }
    return Uri.parse('$_baseUrl${path.startsWith('/') ? path : '/$path'}');
  }

  Future<dynamic> get(String path) async {
    final response = await http.get(uri(path)).timeout(const Duration(seconds: 20));
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw NexusException('Nexus returned ${response.statusCode}.');
    }
    return jsonDecode(response.body);
  }

  Future<Map<String, dynamic>> map(String path) async {
    final result = await get(path);
    if (result is Map<String, dynamic>) return result;
    throw const NexusException('Unexpected response received.');
  }

  Future<List<dynamic>> list(String path) async {
    final result = await get(path);
    if (result is List) return result;
    if (result is Map<String, dynamic> && result['items'] is List) {
      return result['items'] as List;
    }
    return const [];
  }


  Future<dynamic> send(
    String method,
    String path, {
    Map<String, dynamic>? body,
  }) async {
    final requestUri = uri(path);
    final headers = const {'Content-Type': 'application/json'};
    final encoded = body == null ? null : jsonEncode(body);

    final response = switch (method) {
      'POST' => await http
          .post(requestUri, headers: headers, body: encoded)
          .timeout(const Duration(seconds: 20)),
      'PUT' => await http
          .put(requestUri, headers: headers, body: encoded)
          .timeout(const Duration(seconds: 20)),
      'DELETE' => await http
          .delete(requestUri, headers: headers, body: encoded)
          .timeout(const Duration(seconds: 20)),
      _ => throw const NexusException('Unsupported request method.'),
    };

    if (response.statusCode < 200 || response.statusCode >= 300) {
      String message = 'Nexus returned ${response.statusCode}.';
      try {
        final decoded = jsonDecode(response.body);
        if (decoded is Map && decoded['detail'] != null) {
          message = decoded['detail'].toString();
        }
      } catch (_) {}
      throw NexusException(message);
    }

    if (response.body.trim().isEmpty) return const <String, dynamic>{};
    return jsonDecode(response.body);
  }
}

class NexusException implements Exception {
  const NexusException(this.message);
  final String message;
  @override
  String toString() => message;
}

class NexusScope extends InheritedNotifier<NexusApi> {
  const NexusScope({
    required NexusApi api,
    required super.child,
    super.key,
  }) : super(notifier: api);

  static NexusApi of(BuildContext context) {
    final scope = context.dependOnInheritedWidgetOfExactType<NexusScope>();
    assert(scope != null, 'NexusScope not found');
    return scope!.notifier!;
  }
}

class NexusApp extends StatefulWidget {
  const NexusApp({super.key});

  @override
  State<NexusApp> createState() => _NexusAppState();
}

class _NexusAppState extends State<NexusApp> {
  final api = NexusApi();

  @override
  Widget build(BuildContext context) {
    final scheme = ColorScheme.fromSeed(
      seedColor: const Color(0xFF3258D5),
      brightness: Brightness.light,
    );

    return NexusScope(
      api: api,
      child: MaterialApp(
        title: 'Nexus',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          useMaterial3: true,
          colorScheme: scheme,
          scaffoldBackgroundColor: const Color(0xFFF5F7FB),
          cardTheme: const CardThemeData(
            elevation: 0,
            margin: EdgeInsets.zero,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.all(Radius.circular(20)),
              side: BorderSide(color: Color(0xFFE3E8F1)),
            ),
          ),
          navigationBarTheme: const NavigationBarThemeData(
            height: 70,
            labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
          ),
        ),
        home: const AppShell(),
      ),
    );
  }
}

class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int index = 0;

  static const pages = <Widget>[
    HomeScreen(),
    WorldsScreen(),
    LoopsScreen(),
    EvidenceScreen(),
    SettingsScreen(),
  ];

  static const destinations = <NavigationDestination>[
    NavigationDestination(
      icon: Icon(Icons.home_outlined),
      selectedIcon: Icon(Icons.home),
      label: 'Home',
    ),
    NavigationDestination(
      icon: Icon(Icons.grid_view_outlined),
      selectedIcon: Icon(Icons.grid_view),
      label: 'Worlds',
    ),
    NavigationDestination(
      icon: Icon(Icons.track_changes_outlined),
      selectedIcon: Icon(Icons.track_changes),
      label: 'Loops',
    ),
    NavigationDestination(
      icon: Icon(Icons.article_outlined),
      selectedIcon: Icon(Icons.article),
      label: 'Evidence',
    ),
    NavigationDestination(
      icon: Icon(Icons.settings_outlined),
      selectedIcon: Icon(Icons.settings),
      label: 'Settings',
    ),
  ];

  @override
  Widget build(BuildContext context) {
    final api = NexusScope.of(context);

    if (api.baseUrl.isEmpty) {
      return const Scaffold(
        body: SafeArea(
          child: SettingsScreen(),
        ),
      );
    }

    return Scaffold(
      body: SafeArea(
        child: IndexedStack(
          index: index,
          children: pages,
        ),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        destinations: destinations,
        onDestinationSelected: (value) {
          setState(() => index = value);
        },
      ),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  Future<List<Map<String, dynamic>>>? future;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    future ??= _load();
  }

  Future<List<Map<String, dynamic>>> _load() async {
    final api = NexusScope.of(context);
    final results = await Future.wait([
      api.map('/api/dashboard'),
      api.map('/api/executive-brief?hours=72'),
      api.map('/api/banking-highlights?hours=168&limit=5'),
      api.map('/api/v1/executive/feed?hours=720&limit_per_section=8'),
    ]);
    return results;
  }

  Future<void> _refresh() async {
    setState(() => future = _load());
    await future;
  }

  @override
  Widget build(BuildContext context) {
    final api = NexusScope.of(context);

    if (api.baseUrl.isEmpty) {
      return const FirstConnectionView();
    }

    return RefreshIndicator(
      onRefresh: _refresh,
      child: FutureBuilder<List<Map<String, dynamic>>>(
        future: future,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const LoadingPage();
          }
          if (snapshot.hasError) {
            return ConnectionErrorPage(
              message: snapshot.error.toString(),
              onRetry: _refresh,
            );
          }

          final dashboard = snapshot.data![0];
          final brief = snapshot.data![1];
          final banking = snapshot.data![2];
          final feed = snapshot.data![3];

          final summary = Map<String, dynamic>.from(
            dashboard['summary'] as Map? ?? const {},
          );
          final morning = Map<String, dynamic>.from(
            brief['summary'] as Map? ?? const {},
          );

          return ListView(
            padding: const EdgeInsets.fromLTRB(14, 12, 14, 28),
            children: [
              CalmHero(
                reviewed: (morning['reviewed'] as num?)?.toInt() ??
                    (summary['reviewed'] as num?)?.toInt() ??
                    0,
                savedMinutes: (summary['saved_minutes'] as num?)?.toInt() ?? 0,
                headline: brief['headline']?.toString() ??
                    'Everything important is under control.',
              ),
              const SizedBox(height: 12),
              ExecutiveSection(
                title: 'Needs your notice',
                icon: Icons.warning_amber_rounded,
                color: Colors.red,
                emptyText: 'Nothing urgent right now.',
                items: List<dynamic>.from(feed['alerts'] as List? ?? const []),
              ),
              const SizedBox(height: 12),
              ExecutiveSection(
                title: 'Important updates',
                icon: Icons.notifications_active_outlined,
                color: Colors.amber.shade800,
                emptyText: 'No important updates right now.',
                items: List<dynamic>.from(feed['notices'] as List? ?? const []),
              ),
              const SizedBox(height: 12),
              BankingCard(data: banking),
              const SizedBox(height: 12),
              ExecutiveSection(
                title: 'Delegate',
                icon: Icons.group_outlined,
                color: Colors.indigo,
                emptyText: 'No delegation suggestions.',
                items: List<dynamic>.from(
                  feed['delegations'] as List? ?? const [],
                ),
              ),
              const SizedBox(height: 12),
              ExecutiveSection(
                title: 'Watching to closure',
                icon: Icons.visibility_outlined,
                color: Colors.green,
                emptyText: 'No open communication loops.',
                items: List<dynamic>.from(
                  feed['monitoring'] as List? ?? const [],
                ),
              ),
              const SizedBox(height: 12),
              HandledQuietlyCard(summary: summary, brief: brief),
            ],
          );
        },
      ),
    );
  }
}

class CalmHero extends StatelessWidget {
  const CalmHero({
    required this.reviewed,
    required this.savedMinutes,
    required this.headline,
    super.key,
  });

  final int reviewed;
  final int savedMinutes;
  final String headline;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFF3157D5), Color(0xFF6A75E8)],
        ),
        borderRadius: BorderRadius.circular(26),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 58,
                height: 58,
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.16),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.spa_outlined,
                  color: Colors.white,
                  size: 30,
                ),
              ),
              const SizedBox(width: 14),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Good afternoon, Niranjan',
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w900,
                        fontSize: 21,
                      ),
                    ),
                    SizedBox(height: 3),
                    Text(
                      'Your world, calmly understood.',
                      style: TextStyle(color: Colors.white70),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 18),
          Text(
            headline,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 15,
              height: 1.35,
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              HeroMetric(value: '$reviewed', label: 'messages reviewed'),
              const SizedBox(width: 9),
              HeroMetric(value: '$savedMinutes', label: 'minutes saved'),
            ],
          ),
        ],
      ),
    );
  }
}

class HeroMetric extends StatelessWidget {
  const HeroMetric({
    required this.value,
    required this.label,
    super.key,
  });

  final String value;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 11),
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.15),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              value,
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.w900,
                fontSize: 20,
              ),
            ),
            Text(
              label,
              style: const TextStyle(color: Colors.white70, fontSize: 11),
            ),
          ],
        ),
      ),
    );
  }
}

class ExecutiveSection extends StatelessWidget {
  const ExecutiveSection({
    required this.title,
    required this.icon,
    required this.color,
    required this.emptyText,
    required this.items,
    super.key,
  });

  final String title;
  final IconData icon;
  final Color color;
  final String emptyText;
  final List<dynamic> items;

  @override
  Widget build(BuildContext context) {
    return SectionCard(
      title: title,
      icon: icon,
      color: color,
      child: items.isEmpty
          ? Text(emptyText)
          : Column(
              children: items
                  .whereType<Map>()
                  .map(
                    (raw) => HumanEventTile(
                      item: Map<String, dynamic>.from(raw),
                      color: color,
                    ),
                  )
                  .toList(),
            ),
    );
  }
}

class HumanEventTile extends StatelessWidget {
  const HumanEventTile({
    required this.item,
    required this.color,
    super.key,
  });

  final Map<String, dynamic> item;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final summary = item['summary']?.toString() ??
        item['title']?.toString() ??
        'Business update';
    final details = <String>[
      if ((item['entity'] ?? item['entity_name']) != null)
        (item['entity'] ?? item['entity_name']).toString(),
      if (item['quantity'] is num)
        '${(item['quantity'] as num).toStringAsFixed(1)} ${item['unit'] ?? ''}'
            .trim(),
      if (item['value'] is num) compactMoney(item['value'] as num),
      if (item['reference'] != null) item['reference'].toString(),
    ];

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 6,
            height: 42,
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.circular(20),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(summary, style: const TextStyle(fontWeight: FontWeight.w800)),
                if (details.isNotEmpty) ...[
                  const SizedBox(height: 3),
                  Text(
                    details.join(' · '),
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
                if (item['confidence'] is num) ...[
                  const SizedBox(height: 7),
                  ConfidenceMeter(
                    confidence: (item['confidence'] as num).toDouble(),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}


class ConfidenceMeter extends StatelessWidget {
  const ConfidenceMeter({
    required this.confidence,
    super.key,
  });

  final double confidence;

  @override
  Widget build(BuildContext context) {
    final normalized = confidence > 1 ? confidence / 100 : confidence;
    final percent = (normalized.clamp(0.0, 1.0) * 100).round();
    final label = percent >= 85
        ? 'High'
        : percent >= 60
            ? 'Likely'
            : 'Review';
    final color = percent >= 85
        ? Colors.green
        : percent >= 60
            ? Colors.orange
            : Colors.red;

    return Row(
      children: [
        Expanded(
          child: ClipRRect(
            borderRadius: BorderRadius.circular(10),
            child: LinearProgressIndicator(
              value: normalized.clamp(0.0, 1.0),
              minHeight: 5,
              backgroundColor: color.withValues(alpha: 0.12),
              valueColor: AlwaysStoppedAnimation<Color>(color),
            ),
          ),
        ),
        const SizedBox(width: 8),
        Text(
          '$percent% · $label',
          style: TextStyle(
            color: color,
            fontSize: 11,
            fontWeight: FontWeight.w800,
          ),
        ),
      ],
    );
  }
}

class BankingCard extends StatelessWidget {
  const BankingCard({required this.data, super.key});

  final Map<String, dynamic> data;

  @override
  Widget build(BuildContext context) {
    final totals = Map<String, dynamic>.from(
      data['totals'] as Map? ?? const {},
    );
    final items = List<dynamic>.from(data['items'] as List? ?? const []);

    return SectionCard(
      title: 'Banking activity',
      icon: Icons.account_balance_outlined,
      color: const Color(0xFF0D7A66),
      child: Column(
        children: [
          Row(
            children: [
              MiniMetric(
                label: 'Credits',
                value: compactMoney(totals['credit'] as num?),
              ),
              const SizedBox(width: 8),
              MiniMetric(
                label: 'Debits',
                value: compactMoney(totals['debit'] as num?),
              ),
              const SizedBox(width: 8),
              MiniMetric(
                label: 'Bounces',
                value: '${totals['bounce_count'] ?? 0}',
                danger: (totals['bounce_count'] as num? ?? 0) > 0,
              ),
            ],
          ),
          if (items.isNotEmpty) ...[
            const SizedBox(height: 10),
            ...items.whereType<Map>().map((raw) {
              final item = Map<String, dynamic>.from(raw);
              final direction = item['direction']?.toString() ?? 'transaction';
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 7),
                child: Row(
                  children: [
                    Icon(
                      direction == 'credit'
                          ? Icons.add_circle_outline
                          : direction == 'debit'
                              ? Icons.remove_circle_outline
                              : Icons.error_outline,
                      color: direction == 'cheque_bounce'
                          ? Colors.red
                          : const Color(0xFF0D7A66),
                      size: 20,
                    ),
                    const SizedBox(width: 9),
                    Expanded(
                      child: Text(
                        '${humanize(direction)} · ${item['bank'] ?? 'Bank'}'
                        '${item['source'] != null ? ' · ${item['source']}' : ''}',
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    if (item['amount'] is num)
                      Text(
                        compactMoney(item['amount'] as num),
                        style: const TextStyle(fontWeight: FontWeight.w900),
                      ),
                  ],
                ),
              );
            }),
          ],
        ],
      ),
    );
  }
}

class MiniMetric extends StatelessWidget {
  const MiniMetric({
    required this.label,
    required this.value,
    this.danger = false,
    super.key,
  });

  final String label;
  final String value;
  final bool danger;

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
        decoration: BoxDecoration(
          color: danger
              ? Colors.red.withValues(alpha: 0.08)
              : const Color(0xFF0D7A66).withValues(alpha: 0.07),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Column(
          children: [
            Text(
              value.isEmpty ? '—' : value,
              style: TextStyle(
                fontWeight: FontWeight.w900,
                color: danger ? Colors.red : null,
              ),
            ),
            Text(label, style: const TextStyle(fontSize: 10)),
          ],
        ),
      ),
    );
  }
}

class HandledQuietlyCard extends StatelessWidget {
  const HandledQuietlyCard({
    required this.summary,
    required this.brief,
    super.key,
  });

  final Map<String, dynamic> summary;
  final Map<String, dynamic> brief;

  @override
  Widget build(BuildContext context) {
    final grouped = List<dynamic>.from(
      brief['grouped_recruitment'] as List? ?? const [],
    );
    final reviewed = (summary['reviewed'] as num?)?.toInt() ?? 0;
    final decisions = (summary['decision_count'] as num?)?.toInt() ?? 0;
    final quiet = (reviewed - decisions).clamp(0, reviewed);

    return SectionCard(
      title: 'Handled quietly',
      icon: Icons.auto_awesome_outlined,
      color: Colors.blueGrey,
      child: Text(
        '$quiet routine items reviewed'
        '${grouped.isNotEmpty ? ' · Recruitment grouped' : ''}'
        ' · Noise kept out of your way',
      ),
    );
  }
}


class WorldsScreen extends StatefulWidget {
  const WorldsScreen({super.key});

  @override
  State<WorldsScreen> createState() => _WorldsScreenState();
}

class _WorldsScreenState extends State<WorldsScreen> {
  Future<List<dynamic>>? future;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    future ??= _load();
  }

  Future<List<dynamic>> _load() {
    return NexusScope.of(context).list('/api/spaces');
  }

  Future<void> _refresh() async {
    setState(() => future = _load());
    await future;
  }

  Future<void> _showWorldDialog({
    Map<String, dynamic>? world,
  }) async {
    final api = NexusScope.of(context);
    final nameController = TextEditingController(
      text: world?['name']?.toString() ?? '',
    );
    final descriptionController = TextEditingController(
      text: world?['description']?.toString() ?? '',
    );

    String type = world?['world']?.toString() ?? 'business';
    bool crossWorld = world?['allow_cross_world'] == 1 ||
        world?['allow_cross_world'] == true;
    bool saving = false;

    final saved = await showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        return StatefulBuilder(
          builder: (context, setDialogState) {
            Future<void> save() async {
              if (nameController.text.trim().isEmpty) return;

              setDialogState(() => saving = true);
              try {
                final body = {
                  'name': nameController.text.trim(),
                  'world': type,
                  'description': descriptionController.text.trim().isEmpty
                      ? null
                      : descriptionController.text.trim(),
                  'allow_cross_world': crossWorld,
                };

                if (world == null) {
                  await api.send('POST', '/api/spaces', body: body);
                } else {
                  await api.send(
                    'PUT',
                    '/api/spaces/${world['id']}',
                    body: body,
                  );
                }

                if (dialogContext.mounted) {
                  Navigator.of(dialogContext).pop(true);
                }
              } catch (error) {
                setDialogState(() => saving = false);
                if (dialogContext.mounted) {
                  ScaffoldMessenger.of(dialogContext).showSnackBar(
                    SnackBar(content: Text(error.toString())),
                  );
                }
              }
            }

            return AlertDialog(
              title: Text(world == null ? 'Add World' : 'Edit World'),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    TextField(
                      controller: nameController,
                      decoration: const InputDecoration(
                        labelText: 'World name',
                        border: OutlineInputBorder(),
                      ),
                    ),
                    const SizedBox(height: 12),
                    DropdownButtonFormField<String>(
                      initialValue: type,
                      decoration: const InputDecoration(
                        labelText: 'Type',
                        border: OutlineInputBorder(),
                      ),
                      items: const [
                        DropdownMenuItem(
                          value: 'business',
                          child: Text('Business'),
                        ),
                        DropdownMenuItem(
                          value: 'family',
                          child: Text('Family'),
                        ),
                        DropdownMenuItem(
                          value: 'personal',
                          child: Text('Personal'),
                        ),
                        DropdownMenuItem(
                          value: 'digital',
                          child: Text('Digital'),
                        ),
                        DropdownMenuItem(
                          value: 'custom',
                          child: Text('Custom'),
                        ),
                      ],
                      onChanged: (value) {
                        if (value != null) {
                          setDialogState(() => type = value);
                        }
                      },
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      controller: descriptionController,
                      minLines: 2,
                      maxLines: 3,
                      decoration: const InputDecoration(
                        labelText: 'Description',
                        border: OutlineInputBorder(),
                      ),
                    ),
                    const SizedBox(height: 4),
                    SwitchListTile(
                      contentPadding: EdgeInsets.zero,
                      title: const Text('Allow cross-World intelligence'),
                      subtitle: const Text(
                        'Permit Nexus to connect this World with others.',
                      ),
                      value: crossWorld,
                      onChanged: (value) {
                        setDialogState(() => crossWorld = value);
                      },
                    ),
                  ],
                ),
              ),
              actions: [
                TextButton(
                  onPressed: saving
                      ? null
                      : () => Navigator.of(dialogContext).pop(false),
                  child: const Text('Cancel'),
                ),
                FilledButton(
                  onPressed: saving ? null : save,
                  child: saving
                      ? const SizedBox.square(
                          dimension: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : Text(world == null ? 'Add' : 'Save'),
                ),
              ],
            );
          },
        );
      },
    );

    if (saved == true) await _refresh();
  }

  Future<void> _deleteWorld(Map<String, dynamic> world) async {
    final mailboxCount = (world['mailbox_count'] as num?)?.toInt() ?? 0;
    final api = NexusScope.of(context);

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(
          mailboxCount > 0 ? 'Archive World?' : 'Delete World?',
        ),
        content: Text(
          mailboxCount > 0
              ? 'This World has $mailboxCount connected mailbox(es). It will be archived, not erased. Email evidence will remain safe.'
              : 'Delete ${world['name']}? This does not delete underlying email evidence.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: Text(mailboxCount > 0 ? 'Archive' : 'Delete'),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    try {
      await api.send(
        'DELETE',
        '/api/spaces/${world['id']}',
        body: const {},
      );
      await _refresh();
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.toString())),
      );
    }
  }

  Future<void> _makeDefault(Map<String, dynamic> world) async {
    try {
      await NexusScope.of(context).send(
        'POST',
        '/api/spaces/${world['id']}/default',
      );
      await _refresh();
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.toString())),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _refresh,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(14, 14, 14, 28),
        children: [
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Your worlds',
                      style:
                          Theme.of(context).textTheme.headlineSmall?.copyWith(
                                fontWeight: FontWeight.w900,
                              ),
                    ),
                    const SizedBox(height: 3),
                    const Text(
                      'Keep business, family, personal and digital life separate.',
                    ),
                  ],
                ),
              ),
              FilledButton.icon(
                onPressed: () => _showWorldDialog(),
                icon: const Icon(Icons.add),
                label: const Text('Add'),
              ),
            ],
          ),
          const SizedBox(height: 14),
          FutureBuilder<List<dynamic>>(
            future: future,
            builder: (context, snapshot) {
              if (snapshot.connectionState == ConnectionState.waiting) {
                return const Padding(
                  padding: EdgeInsets.only(top: 100),
                  child: Center(child: CircularProgressIndicator()),
                );
              }
              if (snapshot.hasError) return Text(snapshot.error.toString());

              final items = snapshot.data ?? const [];
              if (items.isEmpty) {
                return const EmptyMessage(
                  icon: Icons.grid_view_outlined,
                  title: 'No Worlds yet',
                  text: 'Add your first World to organize Nexus.',
                );
              }

              return Column(
                children: items.whereType<Map>().map((raw) {
                  final item = Map<String, dynamic>.from(raw);
                  final world = item['world']?.toString() ?? 'custom';
                  final color = switch (world) {
                    'business' => Colors.indigo,
                    'family' => Colors.pink,
                    'digital' => Colors.teal,
                    'personal' => Colors.deepPurple,
                    _ => Colors.blueGrey,
                  };
                  final icon = switch (world) {
                    'business' => Icons.business_center_outlined,
                    'family' => Icons.family_restroom,
                    'digital' => Icons.devices_outlined,
                    'personal' => Icons.person_outline,
                    _ => Icons.public_outlined,
                  };
                  final isDefault = item['is_default'] == 1 ||
                      item['is_default'] == true;
                  final crossWorld = item['allow_cross_world'] == 1 ||
                      item['allow_cross_world'] == true;

                  return Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: Card(
                      child: Padding(
                        padding: const EdgeInsets.fromLTRB(14, 14, 8, 14),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            CircleAvatar(
                              backgroundColor: color.withValues(alpha: 0.10),
                              child: Icon(icon, color: color),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      Flexible(
                                        child: Text(
                                          item['name']?.toString() ??
                                              humanize(world),
                                          style: const TextStyle(
                                            fontWeight: FontWeight.w900,
                                            fontSize: 16,
                                          ),
                                        ),
                                      ),
                                      if (isDefault) ...[
                                        const SizedBox(width: 7),
                                        const Chip(
                                          visualDensity: VisualDensity.compact,
                                          label: Text('Default'),
                                        ),
                                      ],
                                    ],
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    item['description']?.toString() ??
                                        '${humanize(world)} World',
                                  ),
                                  const SizedBox(height: 7),
                                  Wrap(
                                    spacing: 8,
                                    runSpacing: 5,
                                    children: [
                                      Text(
                                        '${item['mailbox_count'] ?? 0} mailbox(es)',
                                        style: Theme.of(context)
                                            .textTheme
                                            .bodySmall,
                                      ),
                                      if (crossWorld)
                                        Text(
                                          'Cross-World enabled',
                                          style: Theme.of(context)
                                              .textTheme
                                              .bodySmall,
                                        ),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                            PopupMenuButton<String>(
                              onSelected: (action) {
                                switch (action) {
                                  case 'edit':
                                    _showWorldDialog(world: item);
                                  case 'default':
                                    _makeDefault(item);
                                  case 'delete':
                                    _deleteWorld(item);
                                }
                              },
                              itemBuilder: (context) => [
                                const PopupMenuItem(
                                  value: 'edit',
                                  child: Text('Edit'),
                                ),
                                if (!isDefault)
                                  const PopupMenuItem(
                                    value: 'default',
                                    child: Text('Set as default'),
                                  ),
                                PopupMenuItem(
                                  value: 'delete',
                                  child: Text(
                                    ((item['mailbox_count'] as num?)
                                                    ?.toInt() ??
                                                0) >
                                            0
                                        ? 'Archive'
                                        : 'Delete',
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),
                  );
                }).toList(),
              );
            },
          ),
        ],
      ),
    );
  }
}

class LoopsScreen extends StatefulWidget {
  const LoopsScreen({super.key});

  @override
  State<LoopsScreen> createState() => _LoopsScreenState();
}

class _LoopsScreenState extends State<LoopsScreen> {
  Future<List<dynamic>>? future;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    future ??= NexusScope.of(context).list('/api/v1/conversations?status=open');
  }

  @override
  Widget build(BuildContext context) {
    return PageFrame(
      title: 'Open loops',
      subtitle: 'Important communication Nexus is following to closure.',
      child: FutureBuilder<List<dynamic>>(
        future: future,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) return Text(snapshot.error.toString());

          final items = snapshot.data ?? const [];
          if (items.isEmpty) {
            return const EmptyMessage(
              icon: Icons.check_circle_outline,
              title: 'No open loops',
              text: 'Everything currently tracked has reached closure.',
            );
          }

          return Column(
            children: items.whereType<Map>().map((raw) {
              final item = Map<String, dynamic>.from(raw);
              final stage = humanize(item['current_stage']);
              final next = humanize(item['expected_next_event']);
              final health = item['health']?.toString() ?? 'healthy';
              final color = health == 'critical'
                  ? Colors.red
                  : health == 'watch'
                      ? Colors.orange
                      : Colors.green;

              return Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(15),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        CircleAvatar(
                          backgroundColor: color.withValues(alpha: 0.10),
                          child: Icon(Icons.track_changes, color: color),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                item['subject']?.toString() ??
                                    humanize(item['intent']),
                                style: const TextStyle(
                                  fontWeight: FontWeight.w900,
                                  fontSize: 15,
                                ),
                              ),
                              const SizedBox(height: 5),
                              Text('Current: ${stage.isEmpty ? 'Observed' : stage}'),
                              if (next.isNotEmpty)
                                Text(
                                  'Waiting for: $next',
                                  style: Theme.of(context).textTheme.bodySmall,
                                ),
                              const SizedBox(height: 5),
                              Text(
                                '${item['event_count'] ?? 0} linked update(s)',
                                style: Theme.of(context).textTheme.bodySmall,
                              ),
                              if (item['confidence'] is num) ...[
                                const SizedBox(height: 8),
                                ConfidenceMeter(
                                  confidence:
                                      (item['confidence'] as num).toDouble(),
                                ),
                              ],
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              );
            }).toList(),
          );
        },
      ),
    );
  }
}

class EvidenceScreen extends StatefulWidget {
  const EvidenceScreen({super.key});

  @override
  State<EvidenceScreen> createState() => _EvidenceScreenState();
}

class _EvidenceScreenState extends State<EvidenceScreen> {
  Future<List<dynamic>>? future;
  String query = '';

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    future ??= NexusScope.of(context).list('/api/evidence?limit=250');
  }

  @override
  Widget build(BuildContext context) {
    return PageFrame(
      title: 'Evidence',
      subtitle: 'The source material behind Nexus intelligence.',
      top: SearchBar(
        hintText: 'Search evidence',
        leading: const Icon(Icons.search),
        onChanged: (value) => setState(() => query = value.toLowerCase()),
      ),
      child: FutureBuilder<List<dynamic>>(
        future: future,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) return Text(snapshot.error.toString());

          final all = (snapshot.data ?? const [])
              .whereType<Map>()
              .map((e) => Map<String, dynamic>.from(e))
              .where((item) {
            if (query.isEmpty) return true;
            return [
              item['title'],
              item['summary'],
              item['entity_name'],
              item['source'],
            ].any((value) => value?.toString().toLowerCase().contains(query) ?? false);
          }).toList();

          return Column(
            children: all.map((item) {
              return Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: Card(
                  child: ExpansionTile(
                    leading: const Icon(Icons.mail_outline),
                    title: Text(
                      item['title']?.toString() ?? 'Message',
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontWeight: FontWeight.w800),
                    ),
                    subtitle: Text(
                      [
                        if (item['entity_name'] != null)
                          item['entity_name'].toString(),
                        if (item['source'] != null) item['source'].toString(),
                        if (item['category'] != null)
                          humanize(item['category']),
                      ].join(' · '),
                    ),
                    childrenPadding:
                        const EdgeInsets.fromLTRB(16, 0, 16, 16),
                    children: [
                      Align(
                        alignment: Alignment.centerLeft,
                        child: Text(
                          item['summary']?.toString().trim().isNotEmpty == true
                              ? item['summary'].toString()
                              : 'No readable summary was extracted.',
                        ),
                      ),
                      if (item['confidence'] is num) ...[
                        const SizedBox(height: 10),
                        ConfidenceMeter(
                          confidence:
                              (item['confidence'] as num).toDouble(),
                        ),
                      ],
                    ],
                  ),
                ),
              );
            }).toList(),
          );
        },
      ),
    );
  }
}

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final controller = TextEditingController();
  String? status;
  bool testing = false;
  Future<List<dynamic>>? connectors;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final api = NexusScope.of(context);
    if (controller.text.isEmpty) controller.text = api.baseUrl;
    if (api.baseUrl.isNotEmpty) {
      connectors ??= api.list('/api/connections/mailboxes');
    }
  }

  Future<void> saveAndTest() async {
    final api = NexusScope.of(context);
    api.setBaseUrl(controller.text);
    setState(() {
      testing = true;
      status = null;
      connectors = null;
    });

    try {
      final health = await api.map('/api/v1/system/health');
      connectors = api.list('/api/connections/mailboxes');
      setState(() => status = 'Connected · Nexus ${health['version'] ?? ''}');
    } catch (error) {
      setState(() => status = error.toString());
    } finally {
      if (mounted) setState(() => testing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return PageFrame(
      title: 'Settings',
      subtitle: 'Connection, connectors and intelligence controls.',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SectionCard(
            title: 'Nexus server',
            icon: Icons.dns_outlined,
            color: Colors.indigo,
            child: Column(
              children: [
                TextField(
                  controller: controller,
                  keyboardType: TextInputType.url,
                  autocorrect: false,
                  decoration: const InputDecoration(
                    labelText: 'Backend address',
                    hintText: 'http://192.168.0.115:8010',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 10),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    onPressed: testing ? null : saveAndTest,
                    icon: testing
                        ? const SizedBox.square(
                            dimension: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.wifi_tethering),
                    label: const Text('Save and test'),
                  ),
                ),
                if (status != null) ...[
                  const SizedBox(height: 9),
                  Align(
                    alignment: Alignment.centerLeft,
                    child: Text(status!),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: 12),
          SectionCard(
            title: 'Connectors',
            icon: Icons.cable_outlined,
            color: Colors.teal,
            child: FutureBuilder<List<dynamic>>(
              future: connectors,
              builder: (context, snapshot) {
                if (connectors == null) {
                  return const Text('Connect to the Nexus server to view connectors.');
                }
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Padding(
                    padding: EdgeInsets.all(12),
                    child: CircularProgressIndicator(),
                  );
                }
                if (snapshot.hasError) return Text(snapshot.error.toString());

                final items = snapshot.data ?? const [];
                if (items.isEmpty) {
                  return const Text('No mailbox connectors configured.');
                }

                return Column(
                  children: items.whereType<Map>().map((raw) {
                    final item = Map<String, dynamic>.from(raw);
                    return ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading: const CircleAvatar(
                        child: Icon(Icons.mail_outline),
                      ),
                      title: Text(
                        item['label']?.toString() ??
                            item['username']?.toString() ??
                            'Mailbox',
                        style: const TextStyle(fontWeight: FontWeight.w800),
                      ),
                      subtitle: Text(
                        [
                          item['username'],
                          item['space_name'] ?? 'Not assigned',
                        ].where((e) => e != null).join(' · '),
                      ),
                      trailing: Icon(
                        item['last_scan_at'] != null
                            ? Icons.check_circle
                            : Icons.pending_outlined,
                        color: item['last_scan_at'] != null
                            ? Colors.green
                            : Colors.orange,
                      ),
                    );
                  }).toList(),
                );
              },
            ),
          ),
          const SizedBox(height: 12),
          const SectionCard(
            title: 'Intelligence controls',
            icon: Icons.psychology_alt_outlined,
            color: Colors.deepPurple,
            child: Text(
              'Corrections made from alerts, notices and evidence will remain above learned intelligence. Detailed controls will be added in the next release.',
            ),
          ),
        ],
      ),
    );
  }
}

class FirstConnectionView extends StatelessWidget {
  const FirstConnectionView({super.key});

  @override
  Widget build(BuildContext context) {
    return const SettingsScreen();
  }
}

class ConnectionErrorPage extends StatelessWidget {
  const ConnectionErrorPage({
    required this.message,
    required this.onRetry,
    super.key,
  });

  final String message;
  final Future<void> Function() onRetry;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(22),
      children: [
        const SizedBox(height: 80),
        const Icon(Icons.cloud_off_outlined, size: 58),
        const SizedBox(height: 14),
        Text(
          'Nexus could not reach the server',
          textAlign: TextAlign.center,
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w900,
              ),
        ),
        const SizedBox(height: 8),
        const Text(
          'Check the backend address in Settings and confirm that both devices are on the same network.',
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 16),
        FilledButton.icon(
          onPressed: onRetry,
          icon: const Icon(Icons.refresh),
          label: const Text('Retry'),
        ),
        const SizedBox(height: 12),
        ExpansionTile(
          title: const Text('Technical details'),
          children: [Padding(
            padding: const EdgeInsets.all(12),
            child: SelectableText(message),
          )],
        ),
      ],
    );
  }
}

class LoadingPage extends StatelessWidget {
  const LoadingPage({super.key});

  @override
  Widget build(BuildContext context) {
    return ListView(
      children: const [
        SizedBox(height: 240),
        Center(child: CircularProgressIndicator()),
      ],
    );
  }
}

class PageFrame extends StatelessWidget {
  const PageFrame({
    required this.title,
    required this.subtitle,
    required this.child,
    this.top,
    super.key,
  });

  final String title;
  final String subtitle;
  final Widget child;
  final Widget? top;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(14, 14, 14, 28),
      children: [
        Text(
          title,
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.w900,
              ),
        ),
        const SizedBox(height: 3),
        Text(subtitle),
        if (top != null) ...[
          const SizedBox(height: 12),
          top!,
        ],
        const SizedBox(height: 14),
        child,
      ],
    );
  }
}

class SectionCard extends StatelessWidget {
  const SectionCard({
    required this.title,
    required this.icon,
    required this.color,
    required this.child,
    super.key,
  });

  final String title;
  final IconData icon;
  final Color color;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(15, 14, 15, 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: color, size: 21),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    title,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.w900,
                        ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            child,
          ],
        ),
      ),
    );
  }
}

class EmptyMessage extends StatelessWidget {
  const EmptyMessage({
    required this.icon,
    required this.title,
    required this.text,
    super.key,
  });

  final IconData icon;
  final String title;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 60),
      child: Column(
        children: [
          Icon(icon, size: 55, color: Colors.green),
          const SizedBox(height: 12),
          Text(title, style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 5),
          Text(text, textAlign: TextAlign.center),
        ],
      ),
    );
  }
}
