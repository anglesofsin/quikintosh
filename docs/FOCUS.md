# Focus

Settings → Focus manages profiles, allowed/silenced apps and people, critical
and time-sensitive notifications, overnight schedules, weekdays and application
activation. Profiles and schedules are local and persist across shell restarts.
Settings → Dynamic Island also offers automatic Do Not Disturb during screen
sharing (off by default), and Album/System accent/Custom media colors.

Automatic Do Not Disturb restores only a state that it enabled itself. Turning
Focus off manually suppresses that automation until its current trigger ends.
Existing enabled Do Not Disturb remains enabled after a sharing session ends.
Notification sounds remain silent during Do Not Disturb.

App exceptions match the notification's app name, case-insensitively. People
exceptions require a sender hint (`sender` or `x-quickintosh-sender`) from the
app. Time-sensitive exceptions require `x-quickintosh-time-sensitive`; critical
alerts use the standard freedesktop urgency. The shell cannot infer missing
sender information. This does not implement Apple's iCloud Focus sync, mobile
location triggers, or filters inside Apple's Mail/Safari apps.

The organization follows Apple's Focus model:
https://support.apple.com/guide/mac-help/set-up-a-focus-to-stay-on-task-mchl613dc43f/mac
https://support.apple.com/guide/iphone/allow-or-silence-notifications-for-a-focus-iph21d43af5b/ios
