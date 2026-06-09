"""
python-for-android Recipe fuer 'sqlcipher3' (coleifer/sqlcipher3).

Zweck: stellt das Python-Modul 'sqlcipher3' im Android-Build bereit,
sodass database.py die SQLite-Datei mit SQLCipher verschluesseln kann
(siehe services/db_key.py + database.py).

Funktionsweise (wichtig, weil die sdist KEINE Amalgamation mitbringt):
  1. Die sqlcipher3-sdist enthaelt nur den C-Extension-Wrapper. Ihr
     setup.py kennt zwei Builder: 'build_ext' linkt gegen eine
     System-libsqlcipher (gibt es fuer Android nicht), 'build_static'
     kompiliert eine VOM NUTZER bereitgestellte SQLCipher-Amalgamation
     (sqlite3.c/sqlite3.h) direkt in die Extension.
  2. prebuild_arch laedt darum den SQLCipher-C-Quellcode, generiert die
     Amalgamation auf dem Host (./configure + make sqlite3.c, braucht
     'tcl') und legt sqlite3.c/sqlite3.h in den Recipe-Build-Ordner.
  3. setup.py wird so gepatcht, dass 'build_ext' auf den
     Amalgamation-Builder zeigt - dadurch nutzen auch die impliziten
     build-Schritte von 'setup.py install' den statischen Pfad.
  4. Der Amalgamation-Builder setzt selbst -DSQLITE_HAS_CODEC usw. und
     linkt -lcrypto; die OpenSSL-Pfade kommen aus der p4a-openssl-Recipe.

Host-Validierung (Linux x86_64, 2026-06-09): build_static gegen die so
erzeugte 4.6.1-Amalgamation kompiliert, PRAGMA cipher_version liefert
'4.6.1 community', falscher PRAGMA key wird abgewiesen, Datei-Header ist
verschluesselt. Auf dem GERAET weiterhin pruefen:
Database.encryption_mode == "sqlcipher" (siehe release/GO_LIVE_TODO.md).

Referenzen:
  - p4a Recipe-API: https://python-for-android.readthedocs.io/en/latest/recipes/
  - SQLCipher Build-Defines: https://www.zetetic.net/sqlcipher/
"""
import os
import shutil
from os.path import exists, join

import sh
from pythonforandroid.logger import info, shprint
from pythonforandroid.recipe import CompiledComponentsPythonRecipe
from pythonforandroid.util import current_directory

#: SQLCipher-C-Quelle fuer die Amalgamation. Bei Versionswechsel auch den
#: Hinweis in der Host-Validierung oben aktualisieren.
SQLCIPHER_C_VERSION = "4.6.1"
SQLCIPHER_C_URL = (
    "https://github.com/sqlcipher/sqlcipher/archive/refs/tags/"
    "v{version}.tar.gz".format(version=SQLCIPHER_C_VERSION)
)


class Sqlcipher3Recipe(CompiledComponentsPythonRecipe):
    version = "0.5.4"
    url = "https://files.pythonhosted.org/packages/source/s/sqlcipher3/sqlcipher3-{version}.tar.gz"

    # Modulname nach Installation -> 'import sqlcipher3'
    name = "sqlcipher3"

    # Braucht libcrypto fuer die SQLCipher-Krypto.
    depends = ["setuptools", "openssl"]

    call_hostpython_via_targetpython = False

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        build_dir = self.get_build_dir(arch.arch)
        self._provide_amalgamation(build_dir)
        self._patch_setup_py(build_dir)

    def _provide_amalgamation(self, build_dir):
        """Erzeugt sqlite3.c/sqlite3.h (SQLCipher-Amalgamation) im Build-Dir.

        Die Generierung laeuft bewusst mit Host-Toolchain/-Env: 'make
        sqlite3.c' erzeugt nur eine architekturunabhaengige C-Datei;
        cross-kompiliert wird sie erst spaeter von setup.py.
        """
        if exists(join(build_dir, "sqlite3.c")) and exists(join(build_dir, "sqlite3.h")):
            return
        tarball = join(build_dir, "sqlcipher-src-{}.tar.gz".format(SQLCIPHER_C_VERSION))
        if not exists(tarball):
            info("Lade SQLCipher-Quellcode fuer Amalgamation ({})".format(SQLCIPHER_C_VERSION))
            self.download_file(SQLCIPHER_C_URL, tarball)
        src_dir = join(build_dir, "sqlcipher-{}".format(SQLCIPHER_C_VERSION))
        if not exists(src_dir):
            shprint(sh.tar, "xzf", tarball, "-C", build_dir)
        host_env = os.environ.copy()
        host_env["CFLAGS"] = "-DSQLITE_HAS_CODEC"
        with current_directory(src_dir):
            if not exists(join(src_dir, "Makefile")):
                shprint(sh.Command("./configure"), "--with-tempstore=yes", _env=host_env)
            shprint(sh.make, "sqlite3.c", _env=host_env)
        shutil.copy(join(src_dir, "sqlite3.c"), build_dir)
        shutil.copy(join(src_dir, "sqlite3.h"), build_dir)

    def _patch_setup_py(self, build_dir):
        """Biegt 'build_ext' auf den Amalgamation-Builder um (s. Docstring)."""
        setup_py = join(build_dir, "setup.py")
        with open(setup_py, encoding="utf-8") as fh:
            text = fh.read()
        patched = text.replace(
            '"build_ext": SystemLibSqliteBuilder',
            '"build_ext": AmalgationLibSqliteBuilder',
        )
        if patched != text:
            with open(setup_py, "w", encoding="utf-8") as fh:
                fh.write(patched)

    def get_recipe_env(self, arch, **kwargs):
        env = super().get_recipe_env(arch, **kwargs)

        openssl_recipe = self.get_recipe("openssl", self.ctx)
        # CFLAGS/LDFLAGS sind im Env nicht garantiert vorhanden -> .get().
        # Die SQLITE_*-Defines setzt der Amalgamation-Builder selbst; hier
        # kommen nur die Android-OpenSSL-Pfade dazu.
        env["CFLAGS"] = env.get("CFLAGS", "") + openssl_recipe.include_flags(arch)
        # libcrypto aus der openssl-Recipe linken (-lcrypto haengt der
        # Builder an; wir liefern den Suchpfad).
        env["LDFLAGS"] = env.get("LDFLAGS", "") + openssl_recipe.link_dirs_flags(arch)
        env["LIBS"] = env.get("LIBS", "") + " -lcrypto"
        return env


recipe = Sqlcipher3Recipe()
