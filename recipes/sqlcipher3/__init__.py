"""
python-for-android Recipe fuer 'sqlcipher3' (coleifer/sqlcipher3).

Zweck: stellt das Python-Modul 'sqlcipher3' im Android-Build bereit,
sodass database.py die SQLite-Datei mit SQLCipher verschluesseln kann
(siehe services/db_key.py + database.py).

ABHAENGIGKEIT: OpenSSL (libcrypto) - SQLCipher nutzt es fuer AES/PBKDF2.
Die p4a-eigene 'openssl'-Recipe liefert die Header und .so-Dateien.

!!! VERIFIKATIONS-HINWEIS !!!
Diese Recipe ist nach p4a-Konventionen geschrieben, konnte aber in der
aktuellen Umgebung (Windows, kein Buildozer) NICHT gebaut/getestet
werden. Vor dem ersten Release in WSL2/Linux verifizieren:

    buildozer android debug

Erfahrungsgemaess muessen ggf. angepasst werden:
  - 'version' / 'url' an die aktuelle sqlcipher3-sdist,
  - die SQLCIPHER-Compile-Defines,
  - der Pfad zu libcrypto aus der openssl-Recipe.

Referenzen:
  - p4a Recipe-API: https://python-for-android.readthedocs.io/en/latest/recipes/
  - SQLCipher Build-Defines: https://www.zetetic.net/sqlcipher/
"""
from os.path import join

from pythonforandroid.recipe import CompiledComponentsPythonRecipe


class Sqlcipher3Recipe(CompiledComponentsPythonRecipe):
    # sqlcipher3 (coleifer) bundelt die SQLCipher-Amalgamation in der
    # sdist und baut daraus eine C-Extension namens '_sqlite3'.
    version = "0.5.4"
    url = "https://files.pythonhosted.org/packages/source/s/sqlcipher3/sqlcipher3-{version}.tar.gz"

    # Modulname nach Installation -> 'import sqlcipher3'
    name = "sqlcipher3"

    # Braucht libcrypto fuer die SQLCipher-Krypto.
    depends = ["setuptools", "openssl"]

    call_hostpython_via_targetpython = False

    # SQLCipher wird nur aktiv, wenn diese Defines gesetzt sind. Ohne sie
    # baut sqlcipher3 ein normales (unverschluesseltes) SQLite.
    def get_recipe_env(self, arch, **kwargs):
        env = super().get_recipe_env(arch, **kwargs)

        openssl_recipe = self.get_recipe("openssl", self.ctx)
        env["CFLAGS"] += openssl_recipe.include_flags(arch)
        env["CFLAGS"] += (
            " -DSQLITE_HAS_CODEC"
            " -DSQLITE_TEMP_STORE=2"
            " -DSQLCIPHER_CRYPTO_OPENSSL"
        )

        # libcrypto aus der openssl-Recipe linken.
        env["LDFLAGS"] += openssl_recipe.link_dirs_flags(arch)
        env["LIBS"] = env.get("LIBS", "") + " -lcrypto"
        return env


recipe = Sqlcipher3Recipe()
