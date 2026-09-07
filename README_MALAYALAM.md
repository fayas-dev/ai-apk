# JARVIS AI Assistant - APK Build & Download Guide

## 📱 APK Build ചെയ്ത് Download ചെയ്യാൻ എളുപ്പ വഴി

### 🚀 Step 1: Code GitHub-ലേക്ക് Push ചെയ്യുക

**Option A: Batch File ഉപയോഗിച്ച് (ഏറ്റവും എളുപ്പം)**

1. `push_to_github.bat` file double-click ചെയ്യുക
2. Enter അമർത്തുക

**Option B: Commands ഉപയോഗിച്ച്**

PowerShell തുറന്ന് ഈ commands run ചെയ്യുക:

```bash
cd "c:\Users\fayas_1ewqckb\Downloads\ai-agend-main"
git add .
git commit -m "Build APK"
git push origin main
```

---

### ⏳ Step 2: Build Complete ആകുന്നത് വരെ കാത്തിരിക്കുക

1. ഈ link തുറക്കുക: **https://github.com/fayas-dev/ai-apk/actions**
2. Latest workflow run കാണും (yellow dot 🟡 = running)
3. 5-10 minutes കാത്തിരിക്കുക
4. Green checkmark (✅) വന്നാൽ build complete!

---

### 📥 Step 3: APK Download ചെയ്യുക

**Option A: Automatic Download (GitHub CLI ഉണ്ടെങ്കിൽ)**

1. `download_apk.bat` file double-click ചെയ്യുക
2. Option 1 തിരഞ്ഞെടുക്കുക
3. APK automatically ഈ folder-ലേക്ക് download ആകും:
   - `C:\Users\fayas_1ewqckb\Downloads\Jarvis_APK\`

**Option B: Manual Download**

1. `download_apk.bat` file double-click ചെയ്യുക
2. Option 2 തിരഞ്ഞെടുക്കുക
3. Browser-ൽ GitHub Actions page തുറക്കും
4. Latest successful workflow click ചെയ്യുക
5. "Artifacts" section-ൽ നിന്ന് `jarvis-release-apk` download ചെയ്യുക
6. ZIP extract ചെയ്ത് `app-release.apk` എടുക്കുക
7. ഈ folder-ലേക്ക് copy ചെയ്യുക: `C:\Users\fayas_1ewqckb\Downloads\Jarvis_APK\`

---

### 📲 Step 4: Android Phone-ൽ Install ചെയ്യുക

1. `app-release.apk` file phone-ലേക്ക് transfer ചെയ്യുക:
   - USB cable വഴി, അല്ലെങ്കിൽ
   - WhatsApp/Telegram വഴി, അല്ലെങ്കിൽ
   - Google Drive/Cloud വഴി

2. Phone-ൽ Settings → Security → "Install from Unknown Sources" enable ചെയ്യുക

3. APK file tap ചെയ്ത് install ചെയ്യുക

4. App-ന് permissions നൽകുക:
   - Microphone (voice commands-ന്)
   - Contacts (contact-കൾ access ചെയ്യാൻ)
   - Storage (files access ചെയ്യാൻ)

---

## 📁 Important Files & Folders

- **`push_to_github.bat`** - Code GitHub-ലേക്ക് push ചെയ്യാൻ
- **`download_apk.bat`** - APK download ചെയ്യാൻ
- **`C:\Users\fayas_1ewqckb\Downloads\Jarvis_APK\`** - APK download folder

---

## 🛠️ Troubleshooting

### Build fail ആയാൽ:
1. https://github.com/fayas-dev/ai-apk/actions പോയി error logs check ചെയ്യുക
2. Code push ചെയ്ത് വീണ്ടും try ചെയ്യുക

### APK install ആകുന്നില്ല എങ്കിൽ:
1. "Install from Unknown Sources" enabled ആണോ എന്ന് check ചെയ്യുക
2. Phone-ൽ പഴയ version uninstall ചെയ്ത് വീണ്ടും try ചെയ്യുക

### App crash ആകുന്നു എങ്കിൽ:
1. എല്ലാ permissions നൽകിയിട്ടുണ്ടോ എന്ന് check ചെയ്യുക
2. Backend server running ആണോ എന്ന് confirm ചെയ്യുക

---

## 🎯 Quick Summary

1. **Push code**: `push_to_github.bat` double-click
2. **Wait**: 5-10 minutes build-ന്
3. **Download**: `download_apk.bat` double-click
4. **Install**: APK phone-ലേക്ക് transfer ചെയ്ത് install ചെയ്യുക

**APK Location**: `C:\Users\fayas_1ewqckb\Downloads\Jarvis_APK\app-release.apk`

---

## 📞 Need Help?

GitHub Actions page: https://github.com/fayas-dev/ai-apk/actions

Happy Building! 🚀
