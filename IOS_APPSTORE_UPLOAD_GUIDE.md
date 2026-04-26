# iOS Upload Guide (GoldPro FX)

This guide completes iPhone publishing from a Mac after the iOS project is prepared in `goldpro-mobile/ios`.

## 1) Prerequisites
- Apple Developer account (paid).
- App Store Connect access.
- A Mac with latest Xcode.
- The repository pulled on the Mac.

## 2) Open iOS Project
1. Open Terminal on Mac.
2. Go to project folder.
3. Run:

```bash
cd goldpro-mobile
npm install
npx cap sync ios
npx cap open ios
```

## 3) Configure App in Xcode
1. Select target: `App`.
2. In `Signing & Capabilities`:
- Set Team.
- Set unique Bundle Identifier (example: `com.goldprofx.app`).
- Enable `Automatically manage signing`.
3. In `General`:
- Set Version and Build.
- Set deployment target (recommended iOS 13+).

## 4) Notifications Permissions
Current project has local notifications plugin already integrated.

For local notifications:
- Keep permission request in app UI (already implemented).

For remote push notifications (APNs/FCM) later:
- Add capability: `Push Notifications`.
- Add capability: `Background Modes` -> `Remote notifications`.
- Configure APNs key in Apple Developer portal.
- If using Firebase, upload APNs key to Firebase and integrate FCM SDK.

## 5) Archive and Upload
1. In Xcode select `Any iOS Device (arm64)`.
2. Menu: `Product` -> `Archive`.
3. In Organizer: `Distribute App` -> `App Store Connect` -> `Upload`.

## 6) App Store Connect
1. Go to App Store Connect -> My Apps.
2. Create app record if new.
3. Wait for build processing (can take 10-30 mins).
4. Test via TestFlight first.
5. Submit for review.

## 7) iCloud Clarification
If by "iCloud" you mean cloud backup/data sync:
- Enable capability: `iCloud`.
- Choose needed services (`CloudKit` or `Key-value storage`).
- Add implementation in app code before submission.

If you only mean "upload to Apple ecosystem", App Store Connect/TestFlight steps above are enough.

## 8) Quick Handoff Checklist
- [ ] Project opens in Xcode without signing errors
- [ ] Bundle ID unique
- [ ] Team selected
- [ ] Archive succeeds
- [ ] Build uploaded to TestFlight
- [ ] Notification permission prompt appears on first enable action
