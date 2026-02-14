# Direct Lake – Mental Model

| Situation | What Fabric Does | Why |
|--------|-----------------|-----|
| Query supported | Uses Direct Lake | Fastest path |
| Feature unsupported | Falls back to DirectQuery | Ensures correctness |
| Import not possible | Never used as fallback | Avoids data duplication |

Rule:
Direct Lake tries first, correctness beats speed.

