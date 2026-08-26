# Per-question answer options

Each question now owns its own options array. The creator starts with two options, supports adding a third and fourth option, and allows removal only while at least two remain. The correct-answer radio selection stays attached to the question; removing the selected option clears the selection rather than silently choosing a different answer. The publish gate requires 2–4 non-empty, unique options and a selected correct option included in that same question.

Local visual verification showed independent controls on all three default question cards. The first card accepted a third option and updated its counter from `2/4` to `3/4` without changing the other cards. Production Render served the updated Mini App bundle with HTTP 200 after commit `62521b7`; API health remained HTTP 200.
