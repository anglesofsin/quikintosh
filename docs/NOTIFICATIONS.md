# Notifications and panel behavior

In **Settings → Notifications → Banner Location**, choose **Dynamic Island** or **Upper Right**. This applies to subsequent banners without restarting the shell. If the island or its notification source is disabled, delivery falls back to the upper-right corner. Incoming-call controls remain a separate call activity.

There is one banner destination per delivery; notification history, unread state, app permissions and notification sounds continue to use the same service. Do Not Disturb suppresses presentation unless the existing critical-notification exception is enabled, and never plays notification sounds. The superseded island “consume popups” switch is hidden to avoid contradictory settings.

Upper-right banners have a shared glass backdrop, a rounded neutral surface, application identity, preview/title/body and supported notification action buttons. Each banner has its own lifetime, paused while hovered. Newest banners appear first; dismissal and default/action invocation animate out before the banner is removed. Automatic hiding keeps the notification in Notification Center; explicit dismissal closes it. Content respects the existing preview policy.

Notification Center uses a keyed application-group model. New messages update an existing group rather than reconstructing its delegate, preserving expansion state and avoiding replaying every arrival animation. Opening the center marks notifications read and hides outstanding banners. Panel motion uses spatial/fade durations rather than the previous 140/180ms caps, and respects Reduce Motion.

Control Center uses the same opening/closing motion approach. Its privacy header centers the highest-priority category and shows the applications responsible below it, using the real active PipeWire capture inventory. It does not guess which app is capturing from window focus. Clicking the header opens privacy settings.

The widget editor can be moved by dragging its title area. The card stays inside the display bounds. Double-clicking the title recenters it; its controls and native-file-dialog ownership are unchanged.

## References

- [Apple: notifications and actions](https://support.apple.com/guide/mac-help/get-notifications-mchl2fb1258f/mac)
- [Apple: notification preferences](https://support.apple.com/en-ca/guide/mac-help/-mh40583/mac)
- [Apple: Tahoe design and Control Center](https://www.apple.com/os/pdf/All_New_Features_macOS_Tahoe_Sept_2025.pdf)

## Validation

An isolated D-Bus session and private Wayland compositor received real `notify-send` notifications, checked both destinations without duplication, verified DND/history/unread behavior and opening Notification Center. Offscreen tests cover keyed grouping, routing fallback and animated-removal requests. A Qt Quick Test pointer press/move/release moved the real editor header, and separate panel tests verified Control Center opening and closure plus a centered privacy card showing the prioritized capture app. No test notification or pointer input was sent to the user's desktop.

Optional regression test, using the built source and a compatible Quickshell binary:

```sh
QUICKINTOSH_TEST_SOURCE=/path/to/built/source \
QUICKINTOSH_TEST_QS=/path/to/qs \
python3 -m unittest discover -s tests -p test_notification_delivery.py
```
