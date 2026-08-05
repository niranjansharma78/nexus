import 'package:flutter_test/flutter_test.dart';
import 'package:nexus_mobile/main.dart';

void main() {
  testWidgets('Nexus opens with settings when server is not configured',
      (tester) async {
    await tester.pumpWidget(const NexusApp());
    expect(find.text('Settings'), findsWidgets);
    expect(find.text('Nexus server'), findsOneWidget);
  });
}
