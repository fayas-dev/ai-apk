# JARVIS release files

- `Jarvis-Mobile.apk` — Android app. Install it on Android after allowing installs from this source.
- `Jarvis-Desktop.exe` — Windows desktop companion. Run it on the PC you want to control.

Both applications connect to the configured JARVIS relay. Install the desktop companion first, then use the mobile app's settings to confirm the same relay address.

## Integrity checks

| File | SHA-256 |
| --- | --- |
| `Jarvis-Mobile.apk` | `53E4EE9FC3980D843DB369D74C6012B7EE99AA8F5349E39CB466EA19B5CF2CF3` |
| `Jarvis-Desktop.exe` | `1D414CA92C08C3442CF6196A2CB1CB9C55B357481B12BC3CE3FDC23BD4FD5CC8` |

The GitHub workflow rebuilds both deliverables from source whenever changes are pushed to the main branch.
