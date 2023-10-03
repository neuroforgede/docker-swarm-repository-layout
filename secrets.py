#!/usr/bin/env python3
from glob import glob
import os
from pathlib import Path
from platform import platform
import shutil
import sys
import subprocess
import filecmp
from datetime import datetime
from typing import Set, Any
import traceback
from tempfile import TemporaryDirectory
import platform

if len(sys.argv) != 3:
    print("you must specify either 'diff-current-encrypted-with-last-encrypted', 'diff-with-encrypted', 'diff-with-last-decrypted', 'encrypt' or 'decrypt' as the first parameter and the environment ('dev', 'test', 'prod') as the second parameter")
    exit(1)

if sys.argv[1] not in ('diff-current-encrypted-with-last-encrypted', 'diff-with-encrypted', 'diff-with-last-decrypted', 'encrypt', 'decrypt'):
    print("you must specify either 'diff-current-encrypted-with-last-encrypted', 'diff-with-last-decrypted', 'encrypt' or 'decrypt' as the only parameter and the environment ('dev', 'test', 'prod') as the second parameter")
    exit(1)

if sys.argv[2] not in ('dev', 'test', 'prod'):
    print("you must specify either 'diff-current-encrypted-with-last-encrypted', 'diff-with-encrypted', 'diff-with-last-decrypted', 'encrypt' or 'decrypt' as the only parameter and the environment ('dev', 'test', 'prod') as the second parameter")
    exit(1)

ENVIRONMENT = sys.argv[2]

BACKUP_BASE_DIR = "backup"
DIFF_TMP = ""

platform_machine = platform.machine()
if platform_machine == 'x86_64':
    AGE_BINARY = "./age/amd64/age"
elif platform_machine == 'arm64':
    AGE_BINARY = './age/arm64/age'
else:
    raise AssertionError(f'unrecognized platform.machine() == {platform_machine}')

BASE_ENCRYPTED_DIR = "environments_encrypted"
BASE_DECRYPTED_DIR = "environments"

AGE_DECRYPTION_KEY = os.getenv("AGE_DECRYPTION_KEY", f"{Path.home()}/.ssh/id_rsa")
if not os.path.exists(AGE_DECRYPTION_KEY):
    print(f"decryption key not found at: {AGE_DECRYPTION_KEY}")
    exit(1)

now = datetime.now()

ENCRYPTED_DIR = f'{BASE_ENCRYPTED_DIR}/{ENVIRONMENT}'
ENCRYPTED_DIR_BACKUP = f'{BACKUP_BASE_DIR}/encrypted/{now.strftime("%Y_%d_%m-%H_%M_%S")}/{BASE_ENCRYPTED_DIR}/{ENVIRONMENT}'
DECRYPTED_DIR = f'{BASE_DECRYPTED_DIR}/{ENVIRONMENT}'
DECRYPTED_DIR_BACKUP = f'{BACKUP_BASE_DIR}/decrypted/{now.strftime("%Y_%d_%m-%H_%M_%S")}/{BASE_DECRYPTED_DIR}/{ENVIRONMENT}'

SECRET_PATTERNS = [
    "./**/*secret*/**/*",
    "./**/*secret*",
    "./**/*-postgres-cluster/certs/**/*",
    "./**/ssh_keys/**/*",
    "./**/hcloud_token.yml",
    "./**/hetzner_dns_token.yml"
]

def matched_secrets(source_dir: str) -> Set[str]:
    ret = set()
    for pattern in SECRET_PATTERNS:
        secret_files = glob(f"{source_dir}/{pattern}", recursive=True)

        for secret_file in secret_files:
            abs_path = os.path.abspath(secret_file)
            if abs_path in ret:
                continue
            _path = Path(abs_path)
            if _path.is_file():
                ret.add(abs_path)

    return ret


def decrypt(source_dir: str, target_dir: str, secrets: Set[str]) -> None:
    def copy_decrypt(src, dest) -> None:
        if os.path.abspath(src) in secrets:
            decrypted = subprocess.check_output(
                args=[AGE_BINARY, "-d", "-i", AGE_DECRYPTION_KEY, "-o", "-", src]
            )
            def opener(path, flags):
                return os.open(path, flags, 0o600)
            with open(dest, 'wb', opener=opener) as file:
                file.write(decrypted)
            return dest
        else:
            return shutil.copy2(src, dest)

    shutil.copytree(
        src=source_dir,
        dst=target_dir,
        copy_function=copy_decrypt,
        dirs_exist_ok=True
    )


if sys.argv[1] == 'diff-with-last-decrypted':
    all_backup_decrypted = list(Path(f'{BACKUP_BASE_DIR}/decrypted').glob('*'))
    if len(all_backup_decrypted) == 0:
        print("no backed up decrypted found.")
        exit(1)
    last_decrypted = max(all_backup_decrypted, key=os.path.getmtime)

    exit(subprocess.call(
        args=["diff", "--color", "-r", f'{last_decrypted}/{DECRYPTED_DIR}', DECRYPTED_DIR]
    ))
if sys.argv[1] == 'diff-current-encrypted-with-last-encrypted':
    all_backup_encrypted = list(Path(f'{BACKUP_BASE_DIR}/encrypted').glob('*'))
    if len(all_backup_encrypted) == 0:
        print("no backed up encrypted found.")
        exit(1)
    last_encrypted = max(all_backup_encrypted, key=os.path.getmtime)

    with TemporaryDirectory() as tempdir_current:
        with TemporaryDirectory() as tempdir_last:
            matched_secrets_current = matched_secrets(ENCRYPTED_DIR)
            decrypt(
                source_dir=ENCRYPTED_DIR,
                target_dir=tempdir_current,
                secrets=matched_secrets_current
            )
            matched_secrets_last = matched_secrets(f'{last_encrypted}/{ENCRYPTED_DIR}')
            decrypt(
                source_dir=f'{last_encrypted}/{ENCRYPTED_DIR}',
                target_dir=tempdir_last,
                secrets=matched_secrets_last
            )
            exit(subprocess.call(
                args=["diff", "--color", "-r", tempdir_current, tempdir_last]
            ))
elif sys.argv[1] == 'diff-with-encrypted':
    MATCHED_SECRETS = matched_secrets(ENCRYPTED_DIR)
    with TemporaryDirectory() as tempdir:
        decrypt(
            source_dir=ENCRYPTED_DIR,
            target_dir=tempdir,
            secrets=MATCHED_SECRETS
        )
        exit(subprocess.call(
            args=["diff", "--color", "-r", tempdir, DECRYPTED_DIR]
        ))
elif sys.argv[1] in ('encrypt', 'decrypt'):
    ENCRYPT = sys.argv[1] == "encrypt"
    if not ENCRYPT:
        # decrypt
        SOURCE_DIR = ENCRYPTED_DIR
        TARGET_DIR = DECRYPTED_DIR
        BACKUP_DIR = DECRYPTED_DIR_BACKUP
    else:
        # encrypt
        SOURCE_DIR = DECRYPTED_DIR
        TARGET_DIR = ENCRYPTED_DIR
        BACKUP_DIR = ENCRYPTED_DIR_BACKUP

    Path(TARGET_DIR).mkdir(parents=True, exist_ok=True)
    print(f"backing up {TARGET_DIR} to {BACKUP_DIR}")
    shutil.copytree(
        TARGET_DIR,
        BACKUP_DIR
    )

    EXTRA_FILES_TO_DELETE = set()
    all_files_in_source = set(os.path.relpath(elem, SOURCE_DIR) for elem in glob(f'{SOURCE_DIR}/**/*', recursive=True))
    all_files_in_target = set(os.path.relpath(elem, TARGET_DIR) for elem in glob(f'{TARGET_DIR}/**/*', recursive=True))
    EXTRA_FILES_TO_DELETE = all_files_in_target - all_files_in_source
    EXTRA_FILES_TO_DELETE_ABS = set(os.path.abspath(f'{TARGET_DIR}/{elem}') for elem in EXTRA_FILES_TO_DELETE)

    MATCHED_SECRETS = matched_secrets(SOURCE_DIR)

    if ENCRYPT:
        try:
            recipients_changed = not filecmp.cmp(f"{SOURCE_DIR}/age_recipients.txt", f"{TARGET_DIR}/age_recipients.txt")
        except:
            recipients_changed = True

        def copy_encrypt(src, dest) -> None:
            if os.path.abspath(src) in MATCHED_SECRETS:
                changed = True

                # check if the file exists already
                # if yes, decrypt the contents and only encrypt again if the data is different
                # as age is not stable in the encryption output
                if os.path.exists(dest):
                    with open(os.path.abspath(src), 'rb') as src_file:
                        src_contents = src_file.read()
                        try:
                            decrypted_dest = subprocess.check_output(
                                args=[AGE_BINARY, "-d", "-i", AGE_DECRYPTION_KEY, "-o", "-", dest]
                            )
                            if not recipients_changed:
                                if src_contents == decrypted_dest:
                                    changed = False
                                else:
                                    print(f"{src} and {dest} contents differ... re-encrypting.")
                        except:
                            changed = True

                if changed:
                    subprocess.check_call(
                        args=[AGE_BINARY, "-R", f"{SOURCE_DIR}/age_recipients.txt", "-o", dest, src]
                    )
                return dest
            else:
                return shutil.copy2(src, dest)

        try:
            shutil.copytree(
                src=SOURCE_DIR,
                dst=TARGET_DIR,
                copy_function=copy_encrypt,
                dirs_exist_ok=True
            )
            
            for elem in EXTRA_FILES_TO_DELETE_ABS:
                if os.path.isdir(elem):
                    shutil.rmtree(elem)
                elif os.path.exists(elem):
                    os.unlink(elem)
        except:
            traceback.print_exc()
            shutil.rmtree(TARGET_DIR)
            shutil.copytree(
                src=BACKUP_DIR,
                dst=TARGET_DIR
            )
    else:
        try:
            decrypt(
                source_dir=SOURCE_DIR,
                target_dir=TARGET_DIR,
                secrets=MATCHED_SECRETS
            )
            for elem in EXTRA_FILES_TO_DELETE_ABS:
                if os.path.isdir(elem):
                    shutil.rmtree(elem)
                elif os.path.exists(elem):
                    os.unlink(elem)
        except:
            traceback.print_exc()
            shutil.rmtree(TARGET_DIR)
            shutil.copytree(
                src=BACKUP_DIR,
                dst=TARGET_DIR
            )
