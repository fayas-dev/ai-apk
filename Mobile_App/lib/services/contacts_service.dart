import 'package:flutter_contacts/flutter_contacts.dart';

/// Resolves a spoken name ("mom", "rajan") to a real phone number using the
/// device's contacts, so voice commands like "call mom" or "message dad"
/// can actually reach someone instead of trying to dial the literal word.
class JarvisContactsService {
  static List<Contact>? _cache;
  static bool _permissionGranted = false;

  /// Requests read-only contacts permission. Safe to call repeatedly.
  static Future<bool> ensurePermission() async {
    if (_permissionGranted) return true;
    _permissionGranted = await FlutterContacts.requestPermission(readonly: true);
    return _permissionGranted;
  }

  /// Clears the in-memory contact cache (e.g. after permission is newly granted).
  static void invalidateCache() {
    _cache = null;
  }

  static Future<List<Contact>> _loadContacts() async {
    if (_cache != null) return _cache!;
    final granted = await ensurePermission();
    if (!granted) return [];
    _cache = await FlutterContacts.getContacts(withProperties: true);
    return _cache!;
  }

  /// Returns true if [text] already looks like a phone number rather than a name.
  static bool looksLikePhoneNumber(String text) {
    final digits = text.replaceAll(RegExp(r'[^0-9+]'), '');
    // A real number has meaningfully more digits than stray punctuation removed.
    return digits.length >= 6 && digits.length >= text.trim().length - 3;
  }

  /// Resolves [spokenTarget] to a dialable phone number.
  /// Returns the cleaned number if [spokenTarget] is already numeric,
  /// the best-matching contact's number if a name is recognized,
  /// or null if nothing could be resolved (e.g. no permission, no match).
  static Future<String?> resolveNumber(String spokenTarget) async {
    final target = spokenTarget.trim();
    if (target.isEmpty) return null;

    if (looksLikePhoneNumber(target)) {
      return target.replaceAll(RegExp(r'[^0-9+]'), '');
    }

    final name = target.toLowerCase();
    final contacts = await _loadContacts();
    if (contacts.isEmpty) return null;

    Contact? best;

    // 1. Exact full-name match
    for (final c in contacts) {
      if (c.displayName.toLowerCase() == name && c.phones.isNotEmpty) {
        best = c;
        break;
      }
    }

    // 2. First-name-only match (e.g. "call fayas" matching "Fayas Muhammad")
    best ??= contacts.cast<Contact?>().firstWhere(
          (c) =>
              c != null &&
              c.phones.isNotEmpty &&
              c.displayName.toLowerCase().split(RegExp(r'\s+')).first == name,
          orElse: () => null,
        );

    // 3. Partial / contains match as a last resort
    best ??= contacts.cast<Contact?>().firstWhere(
          (c) => c != null && c.phones.isNotEmpty && c.displayName.toLowerCase().contains(name),
          orElse: () => null,
        );

    if (best == null || best.phones.isEmpty) return null;
    return best.phones.first.number.replaceAll(RegExp(r'[^0-9+]'), '');
  }
}
