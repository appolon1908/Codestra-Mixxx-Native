"""Exercise owned scripts through isolated commands; never install or start services."""
import configparser
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class NativeSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.bin = self.directory / 'bin'
        self.bin.mkdir()
        self.log = self.directory / 'commands.jsonl'
        mock = f'''#!{sys.executable}
import json, os, pathlib, subprocess, sys
name = pathlib.Path(sys.argv[0]).name
with open(os.environ['COMMAND_LOG'], 'a') as stream:
 stream.write(json.dumps([name, *sys.argv[1:]]) + '\\n')
if name == 'install' and not pathlib.Path(sys.argv[-2]).is_file():
 print('missing checked-in install source', file=sys.stderr)
 raise SystemExit(2)
if name == 'sudo':
 raise SystemExit(subprocess.run(sys.argv[1:], check=False).returncode)
'''
        for name in ('install', 'systemctl', 'sudo'):
            p = self.bin / name
            p.write_text(mock)
            p.chmod(0o755)
        self.env = {**os.environ, 'PATH': str(self.bin) + os.pathsep + os.environ['PATH'], 'COMMAND_LOG': str(self.log)}

    def commands(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_installer_uses_all_checked_in_sources_from_any_working_directory(self):
        result = subprocess.run(['/bin/bash', str(ROOT / 'runtime/install-native-runtime.sh')], cwd=self.directory, env=self.env, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        installs = [row for row in self.commands() if row[0] == 'install']
        self.assertEqual(len(installs), 3)
        self.assertEqual([Path(row[-2]).resolve() for row in installs], [ROOT / 'runtime/start-native-mixxx.sh', ROOT / 'runtime/djone-mixxx.service', ROOT / 'runtime/djone-mixxx-relay.service'])
        self.assertEqual([row[-1] for row in installs], ['/home/codestra/DJONE-Mixxx/runtime/start-mixxx.sh', '/home/codestra/.config/systemd/user/djone-mixxx.service', '/etc/systemd/system/djone-mixxx-relay.service'])
        self.assertEqual([row[1] for row in installs], ['-Dm755', '-Dm644', '-Dm644'])

    def test_installer_preserves_existing_explicit_activation_commands_without_executing_them(self):
        result = subprocess.run(['/bin/bash', str(ROOT / 'runtime/install-native-runtime.sh')], cwd=ROOT, env=self.env, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = [row for row in self.commands() if row[0] == 'systemctl']
        self.assertEqual(calls, [['systemctl', '--user', 'daemon-reload'], ['systemctl', '--user', 'enable', '--now', 'djone-mixxx.service'], ['systemctl', 'daemon-reload'], ['systemctl', 'enable', '--now', 'djone-mixxx-relay.service']])

    def start(self, token, gui_pid=""):
        capture = self.directory / 'capture.py'
        capture.write_text('import json,os,sys; print(json.dumps({"args":sys.argv[1:],"token":os.environ.get("DJONE_MIXXX_TOKEN"),"home":os.environ.get("HOME"),"display":os.environ.get("DISPLAY")}))')
        bootstrap = self.directory / 'bash-env.sh'
        bootstrap.write_text('''sed() { printf '%s' "$FIXTURE_TOKEN"; }
pgrep() { if [ -n "$_TEST_GUI_PID" ]; then printf '%s' "$_TEST_GUI_PID"; else return 1; fi; }
exec() { "$_TEST_PYTHON" "$CAPTURE_SCRIPT" "$@"; exit $?; }
''')
        env = {**self.env, 'BASH_ENV': str(bootstrap), 'FIXTURE_TOKEN': token, '_TEST_PYTHON': sys.executable, 'CAPTURE_SCRIPT': str(capture), '_TEST_GUI_PID': gui_pid}
        return subprocess.run(['/bin/bash', str(ROOT / 'runtime/start-native-mixxx.sh')], cwd=self.directory, env=env, capture_output=True, text=True, timeout=5)

    def test_missing_credential_fails_before_native_execution(self):
        result = self.start('')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')

    def test_credential_remains_literal_and_only_canonical_native_binary_is_selected(self):
        marker = self.directory / 'must-not-exist'
        token = 'fixture;$(touch ' + str(marker) + ')'
        result = self.start(token)
        self.assertEqual(result.returncode, 0, result.stderr)
        observed = json.loads(result.stdout)
        self.assertEqual(observed['token'], token)
        self.assertEqual(observed['args'], ['/home/codestra/Desktop/DJONE-Mixxx/mixxx-2.5.6/build-djone/mixxx'])
        self.assertEqual(observed['home'], '/home/codestra')
        self.assertEqual(observed['display'], ':0')
        self.assertFalse(marker.exists())

    def test_unreadable_gui_environment_fails_before_native_execution(self):
        # A nonexistent synthetic PID cannot read any real process environment.
        result = self.start('fixture-token', gui_pid='999999999999')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')

    def test_native_service_matches_installed_launcher_and_user_session(self):
        unit = configparser.ConfigParser(interpolation=None)
        unit.read(ROOT / 'runtime/djone-mixxx.service')
        self.assertEqual(unit['Service']['ExecStart'], '/home/codestra/DJONE-Mixxx/runtime/start-mixxx.sh')
        self.assertEqual(unit['Service']['Type'], 'simple')
        self.assertEqual(unit['Unit']['PartOf'], 'graphical-session.target')
        self.assertEqual(unit['Install']['WantedBy'], 'default.target')

    def test_relay_contract_stays_on_private_bridge_to_loopback(self):
        unit = configparser.ConfigParser(interpolation=None)
        unit.read(ROOT / 'runtime/djone-mixxx-relay.service')
        self.assertEqual(unit['Service']['ExecStart'], '/usr/bin/socat TCP-LISTEN:18092,bind=172.21.0.1,reuseaddr,fork TCP:127.0.0.1:18092')
        self.assertEqual(unit['Service']['Restart'], 'always')
        self.assertNotIn('0.0.0.0', unit['Service']['ExecStart'])

if __name__ == '__main__':
    unittest.main()
