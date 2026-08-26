# Free character asset research

## Initial findings

### DiceBear / Avataaars
- Official style page: https://www.dicebear.com/styles/avataaars/
- Official repository: https://github.com/dicebear/dicebear
- Avataaars is a customizable cartoon vector half-body style with options for hairstyles, clothing, accessories and facial expressions.
- The official DiceBear page states that the Avataaars style is a remix of Avataaars by Pablo Stanley and is free for personal and commercial use; the style has creator-specific licensing details.
- DiceBear core code is MIT licensed, including commercial use. Individual avatar styles can have their own licenses, so the project must retain the relevant attribution/license notes.
- The official style page exposes an HTTP SVG API and an npm/CDN definition URL. For Knowly, vendoring SVG/definition assets or using a pinned package is safer than making the production UI depend on a remote third-party API at runtime.

## Integration direction

Use the current Knowly pair model and renderer as the primary implementation so the reference glossy pink/magenta/violet mascot identity is preserved. Use vetted open-source avatar libraries as an asset/reference source, not as an unreviewed remote runtime dependency. Candidate implementation options are:

1. Adapt selected open vector components under their verified license into a local Knowly-specific renderer.
2. Keep the existing SVG mascot silhouettes and expand their local layers (hair, accessories, clothing), adding attribution documentation for any reused source components.
3. Avoid copying third-party assets until the exact asset-level license and attribution requirement are verified.

Research is ongoing; this file will be updated after checking additional official repositories and licenses.


### Open Peeps
- Official source: https://www.openpeeps.com/
- The official page states that Open Peeps by Pablo Stanley is free for commercial and personal use under the CC0 license.
- The library is modular and offers PNG/SVG assets in bust, standing and sitting categories, which is useful for composable character scenes but has a hand-drawn illustration style rather than Knowly's glossy 3D mascot style.

### Open Peeps generator repository
- Repository inspected: https://github.com/hello-efficiency-inc/openpeeps-generator
- It is a public archived Vue generator for Open Peeps, with an MIT repository license, but the upstream illustration assets remain governed by Open Peeps/CC0 terms.
- The repository is archived/read-only since 2021, so it is better treated as a reference for composition and asset extraction than as a runtime dependency.

## Current conclusion

DiceBear/Avataaars provides the strongest ready-made customization breadth (hair, clothes, accessories, facial options), while Open Peeps is the clearest permissive source for modular SVG illustrations. Neither matches the supplied glossy Knowly mascot reference exactly. The safest product direction is to keep a local Knowly renderer with the reference-matched mascot identity, borrow only verified permissive component ideas/assets when needed, and document each source and license in this file.


### CC0 3D avatar registry
- Registry source: https://github.com/madjin/awesome-cc0
- It lists The Base Mesh, 300 CC0 Avatars, Polyhaven, Kenney and Quaternius among public-domain/free resources.
- The linked 100Avatars repository (https://github.com/madjin/100avatars) contains around 100 open-source avatars in FBX/VRM-oriented files. Its README allows use as a base for projects and monetization but asks users not to sell the avatars directly without major modification. The repository is suited to a separate 3D pipeline, not a lightweight Telegram SVG Mini App dependency.

### DiceBear Clay
- Official style page: https://www.dicebear.com/styles/clay/
- Clay is a soft rounded vector avatar style with simple faces and small horns/curls; the official page lists body, eyes, mouth, pattern and top options and states the style is CC0 1.0.
- Clay is closer to a soft mascot silhouette than Avataaars, but still does not match the supplied glossy Knowly mascot identity. It is a viable permissive source for visual exploration or secondary avatar mode, but not ideal as the primary pair.

## Decision

For the first production integration, retain local Knowly mascot identity and use the open-source findings to expand its component vocabulary. Do not hotlink third-party APIs in the production game flow. Keep source URLs and license notes in this document; if external SVG/3D files are vendored later, copy their exact license/attribution alongside the assets.
