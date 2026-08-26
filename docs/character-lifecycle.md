# Knowly Personal Character Lifecycle

Knowly follows a simple ownership rule: **one Telegram user owns one personal companion**. The companion is not a shared pair, not a public avatar and not a collection of personas. It is the visual identity that follows the user through the Mini App, quizzes, results, progression and bot entry points.

## First entry

After Telegram authentication, the profile endpoint returns `onboarding_required: true` when the existing JSON profile does not contain a valid `CharacterConfig`. The Mini App keeps the user on the onboarding screen and opens the creator automatically. The user chooses the character presentation and customizes appearance, hair, color, eyes, outfit, accessories and palette before entering the main home experience.

The onboarding save sends one `character` object to `PUT /api/v1/profile`. The server validates every enum and stores the configuration in the existing `profiles.character_config` JSON column. No client-side value is trusted as an authorization or entitlement decision.

## Returning users

A returning user receives `onboarding_required: false` and their personal character. The same editor can be opened from the home profile section or through the Telegram `/characters` command. Updates replace only that user's character configuration and do not affect other users or historical quiz results.

## Compatibility migration

Older Knowly versions stored a pair object with `feminine` and `masculine` fields. The profile adapter accepts this legacy shape, selects the feminine side as the deterministic migration default, and writes back a single character on the next profile read/write. A legacy single masculine character is preserved. Empty or invalid JSON is converted to the onboarding sentinel `{ "onboarding_required": true }` so the user can create a valid personal companion instead of receiving a broken profile.

## Bot entry

The bot exposes `/characters`, which returns a Web App button pointing to `?startapp=characters`. The Mini App recognizes that start parameter and opens the editor. For a first-time user, the mandatory onboarding flow takes precedence so a quiz deep link cannot bypass character creation.

## Acceptance criteria

| Area | Expected behavior |
| --- | --- |
| Ownership | Exactly one personal character is stored per profile |
| Onboarding | New profile cannot proceed without creating a character |
| Editing | Existing user can change the character at any time |
| Validation | Server allowlists gender and all customization fields |
| Migration | Legacy pair data does not crash or remain as pair storage |
| Bot | `/characters` opens the personal character editor |
| Privacy | Character configuration is private profile data, not a public URL payload |


## Live verification

After commit `286218e`, Render served the updated Mini App bundle with HTTP 200 and the API health endpoint returned `{"status":"ok"}` with HTTP 200. The production home screen visually shows one personal character card and no pair selector. The profile editor shows one save action, the gender/appearance controls, and the copy that the character belongs to the user.
