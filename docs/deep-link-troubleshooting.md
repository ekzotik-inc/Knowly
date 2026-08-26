# Knowly Telegram deep-link troubleshooting

## Live diagnosis

The user-provided link is `https://t.me/I_KNOWUbot?startapp=_mheKp_IOGaK_R_W`. Telegram resolves the username correctly and exposes an `Open App` action. The public Mini App is live at `https://knowly-mini-app.onrender.com`; its frontend code reads `initDataUnsafe.start_param` and falls back to the browser `startapp` query parameter. The bot/share code generates the same `?startapp=<opaque public token>` format.

The Bot API check confirmed that the configured bot is `I_KNOWUbot`, the webhook is `https://knowly-api.onrender.com/telegram/webhook`, there are no pending updates, and the bot command list is installed. Crucially, `getMe` currently reports `has_main_web_app: false`.

## Root cause

The application link format is correct, but Telegram has not yet registered Knowly as the bot's **Main Mini App**. Telegram's official Mini Apps documentation states that a bot's Main Mini App can be opened from a profile button or direct link, and that direct-link Mini Apps use the bot username plus a start parameter. Until the Main Mini App is enabled for this bot in BotFather, a `t.me/<bot>?startapp=...` link may only resolve to the bot profile/chat and will not launch the app with the payload.

## Required BotFather setup

In `@BotFather`, use `/mybots`, select `@I_KNOWUbot`, open `Bot Settings`, choose `Configure Mini App`, enable the Main Mini App and set its URL to `https://knowly-mini-app.onrender.com`. Then retest the exact shared URL. A successful setup should make `getMe.has_main_web_app` true and open the Mini App directly with the opaque token available as `initDataUnsafe.start_param`.

Source: https://core.telegram.org/bots/webapps


## Public token verification

The opaque public token `_mheKp_IOGaK_R_W` is valid: `GET https://knowly-api.onrender.com/api/v1/public/tests/_mheKp_IOGaK_R_W` returned HTTP 200 after the Render cold start. Therefore the shared quiz itself exists; the failure is specifically at Telegram's direct Mini App launch configuration, not at the quiz token or API route.
