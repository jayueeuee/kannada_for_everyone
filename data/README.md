# Kannada for Everyone — Seed Data

This directory contains curated, authentic seed data for the **Kannada for Everyone** learning platform:

1. `situations.json`: 9 realistic, situation-based role-play scenarios:
   - Grocery shopping (ಕಿರಾಣಿ ಅಂಗಡಿ)
   - Local market (ತರಕಾರಿ ಮಾರುಕಟ್ಟೆ)
   - Darshini / Restaurant (ಹೋಟೆಲ್ / ಉಪಹಾರ ಗೃಹ)
   - Hotel stay (ಹೋಟೆಲ್ ವಾಸ್ತವ್ಯ)
   - Bus & Metro travel (ಬಸ್ ಮತ್ತು ಮೆಟ್ರೋ ಪ್ರಯಾಣ)
   - Asking for directions (ದಾರಿ ಕೇಳುವುದು)
   - Talking to neighbours (ನೆರೆಹೊರೆಯವರೊಂದಿಗೆ ಮಾತುಕತೆ)
   - College & workplace (ಕಾಲೇಜು ಮತ್ತು ಕಚೇರಿ)
   - Daily greetings & courtesy (ದೈನಂದಿನ ನಮಸ್ಕಾರಗಳು)

2. `seed_lessons.json`: Structured interactive lessons across Level 1 to Level 5.
   - Includes vocabulary, grammar rules adapted for Hindi, Marathi, and English speakers, and four exercise types:
     - Matching exercises
     - Fill-in-the-blank
     - Translation quizzes
     - Role-play / spoken application

3. `seed_vocabulary.json`: Core vocabulary items with Kannada script, Roman transliteration, and tri-lingual translations (English, Hindi, Marathi).

Seed data is loaded idempotently into MySQL via `python init_db.py`.
