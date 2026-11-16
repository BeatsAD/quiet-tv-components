#!/usr/bin/env python3
"""Verify the exported client and compile its platform-independent transport."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / 'client/android'
DEPENDENCIES = {
    'org/json/json/20240303/json-20240303.jar':
        '3cf6cd6892e32e2b4c1c39e0f52f5248a2f5b37646fdfbb79a66b46b618414ed',
    'org/bouncycastle/bcprov-jdk15to18/1.86/bcprov-jdk15to18-1.86.jar':
        'fc50334d4d87b4272e72fa95ca748ead05bdef02ef760a5b13f64ffee317cd81',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((CLIENT / 'source.json').read_text())
    for name, expected in manifest['files'].items():
        assert hashlib.sha256((CLIENT / name).read_bytes()).hexdigest() == expected, name
    key = manifest['publicKey']
    assert hashlib.sha256((ROOT / key['path']).read_bytes()).hexdigest() == key['sha256']
    args.output.mkdir(parents=True, exist_ok=True)
    dependencies = args.output / 'dependencies'
    dependencies.mkdir(exist_ok=True)
    classpath = []
    for name, expected in DEPENDENCIES.items():
        target = dependencies / name.rsplit('/', 1)[1]
        if not target.is_file():
            with urllib.request.urlopen('https://repo.maven.apache.org/maven2/' + name, timeout=30) as reply:
                target.write_bytes(reply.read())
        assert hashlib.sha256(target.read_bytes()).hexdigest() == expected, target.name
        classpath.append(str(target))
    package = CLIENT / 'src/main/java/home/quiet/components'
    subprocess.run(['javac', '--release', '11', '-encoding', 'UTF-8',
                    '-cp', os.pathsep.join(classpath), '-d', str(args.output),
                    str(package / 'DownloadSources.java'), str(package / 'ComponentFiles.java'),
                    str(package / 'ComponentManifest.java'), str(package / 'ComponentTransfer.java')], check=True)
    print('PASS: five client source hashes, signing public key and transport compilation')


if __name__ == '__main__':
    main()
