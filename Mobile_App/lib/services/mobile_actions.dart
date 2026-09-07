import 'package:url_launcher/url_launcher.dart';

class MobileActionsService {
  /// Opens WhatsApp to chat or sends a prefilled message
  static Future<bool> openWhatsApp({String? phone, String? message}) async {
    try {
      final cleanPhone = (phone ?? '').replaceAll(RegExp(r'[^0-9+]'), '');
      final text = Uri.encodeComponent(message ?? '');
      
      final Uri whatsappUri;
      if (cleanPhone.isNotEmpty) {
        whatsappUri = Uri.parse("whatsapp://send?phone=$cleanPhone&text=$text");
      } else if (text.isNotEmpty) {
        whatsappUri = Uri.parse("whatsapp://send?text=$text");
      } else {
        whatsappUri = Uri.parse("whatsapp://app");
      }

      if (await canLaunchUrl(whatsappUri)) {
        return await launchUrl(whatsappUri, mode: LaunchMode.externalApplication);
      } else {
        // Web fallback
        final webUri = Uri.parse("https://wa.me/$cleanPhone?text=$text");
        return await launchUrl(webUri, mode: LaunchMode.externalApplication);
      }
    } catch (_) {
      return false;
    }
  }

  /// Initiates a phone call dialer with the given phone number
  static Future<bool> makePhoneCall(String phoneNumber) async {
    try {
      final clean = phoneNumber.replaceAll(RegExp(r'[^0-9+]'), '');
      final uri = Uri.parse("tel:$clean");
      if (await canLaunchUrl(uri)) {
        return await launchUrl(uri);
      }
      return false;
    } catch (_) {
      return false;
    }
  }

  /// Opens an external URL or web search
  static Future<bool> openUrl(String url) async {
    try {
      var target = url.trim();
      if (!target.startsWith('http://') && !target.startsWith('https://')) {
        target = 'https://$target';
      }
      final uri = Uri.parse(target);
      return await launchUrl(uri, mode: LaunchMode.externalApplication);
    } catch (_) {
      return false;
    }
  }

  /// Opens Google Chrome browser
  static Future<bool> openChrome() async {
    return await openUrl("https://www.google.com");
  }
}
