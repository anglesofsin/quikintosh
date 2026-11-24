"""Independent engine reference and opt-in, headless Darwin API integration."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CXX = os.environ.get('QUICKINTOSH_TEST_CXX') or shutil.which('c++')
DARLING = os.environ.get('QUICKINTOSH_TEST_DARLING')


class RandomSource(unittest.TestCase):
    @unittest.skipUnless(CXX, 'Set QUICKINTOSH_TEST_CXX to a host C++ compiler')
    def test_matches_independent_standard_engine(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            header = ROOT / 'modules/lickintosh/mac-apps/mt19937-64.h'
            source = root / 'reference.cpp'
            source.write_text('#include <random>\n#include ' + json.dumps(str(header)) + '''
int main() {
 unsigned long long seeds[] = {0,1,5489,0xffffffffffffffffULL,0x8000000000000000ULL};
 for (auto seed : seeds) {
  QIMTState state; qi_mt_seed(&state,seed); std::mt19937_64 reference(seed);
  for (int i=0;i<10000;++i) if(qi_mt_next(&state)!=reference()) return 1;
 }
}
''')
            subprocess.run([CXX, '-std=c++11', str(source), '-o', str(root / 'reference')], check=True, capture_output=True)
            subprocess.run([str(root / 'reference')], check=True)

    @unittest.skipUnless(DARLING, 'Set QUICKINTOSH_TEST_DARLING to the experimental command')
    def test_guest_seed_copy_ranges_and_shuffle(self):
        root = Path(tempfile.mkdtemp(prefix='quickintosh-gameplay-'))
        environment = dict(os.environ, DPREFIX=str(root / 'prefix'))
        try:
            fixture = root / 'fixture.py'
            shutil.copyfile(ROOT / 'tests/fixtures/gameplay-runtime.py', fixture)
            result = subprocess.run([DARLING, 'shell', '/usr/bin/python2.7',
                                     '/Volumes/SystemRoot' + str(fixture)],
                                    env=environment, capture_output=True, text=True, timeout=90)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('GAMEPLAYKIT_DARWIN_SEED_COPY_BOUNDS_FLOAT_BOOL_OK', result.stdout,
                          result.stdout + result.stderr)
        finally:
            subprocess.run([DARLING, '--stop'], env=environment, capture_output=True, timeout=30, check=True)
            # OverlayFS workdirs belong to the mapped subordinate UID. Reuse
            # that user mapping to remove only our stopped temporary prefix;
            # neither host root nor the desktop's real prefix is involved.
            subprocess.run(['unshare', '--user', '--map-auto', '--map-current-user',
                            '--setuid=0', '--setgid=0', sys.executable, '-c',
                            'import shutil,sys;shutil.rmtree(sys.argv[1])', str(root)],
                           capture_output=True, check=True, timeout=30)


if __name__ == '__main__':
    unittest.main()
