# Owned native source validation scope

This repository owns shell launch/installation sources and systemd configuration. The external patched Mixxx engine, desktop/audio session, DJONE controls and live installation are not built, started or certified by this gate.

Seven real isolated tests exercise the existing scripts through temporary command stubs: missing credentials fail before native execution, credential text remains literal, only the canonical binary is selected, all checked-in installation sources resolve from any working directory, original target modes/paths and explicit activation commands remain intact, unreadable synthetic GUI environment fails closed, and service/relay configuration preserves its user-session/private-bridge/loopback contract. No actual install, sudo, systemctl, native engine, desktop or audio command is executed.

The tests reproduced two genuine source defects before repair. The installer referenced absent `scripts/` and `infra/systemd/` files; it now resolves the same checked-in `runtime/` sources relative to its own directory while preserving every destination and activation command. `export VAR=$(...)` masked failed GUI environment reads; assignments now propagate failure before export, with the process path quoted. These are source fixes, not a live installation or authority change. Both shell files pass Bash syntax and strict checksum-pinned upstream ShellCheck 0.11.0; no warnings or excludes are suppressed.

Full tracked history/effective-tree Gitleaks uses explicit trusted embedded defaults, candidate native-ignore rejection and disabled inline allow comments. Generated private-key, inline, config/environment, exact-ignore and symlink regressions remain real and fatal. No source secrets or fixture exceptions are ignored.

The two new app-bound source/security checks replace only controller contexts; all other protections, reviews, refs, bypass/enforcement, force/deletion and deployment authority remain. CI is read-only, publishes/deploys nothing and never invokes a runtime operation. It grants no native engine, model, GPU, audio, custodian, provider or production certification/authorization.
