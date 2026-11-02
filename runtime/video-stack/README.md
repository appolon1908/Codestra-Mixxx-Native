# Video stack Mixxx bridge authority

This repository remains the native Mixxx ControlObject authority at `127.0.0.1:18092`.

Do **not** add a second OSC/Telnet control engine. The canonical normalized API already exists in `appolon1908/DJONE/services/mixxx-bridge`, which talks to this native socket using the governed `DJONE_MIXXX_TOKEN`.

Controller flow:

```
Codestra Video Controller
  -> DJONE mixxx-bridge (/health, /v1/decks/{deck}/play, /v1/execute)
  -> Codestra-Mixxx-Native 127.0.0.1:18092
  -> Mixxx ControlObject engine
```

The existing DJONE safety state remains authoritative. Production execution stays fail-closed until certified and explicitly enabled.
