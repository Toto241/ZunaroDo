package de.alltagshelfer.dbkey;

import android.content.Context;
import android.content.SharedPreferences;

import androidx.security.crypto.EncryptedSharedPreferences;
import androidx.security.crypto.MasterKey;

import org.kivy.android.PythonActivity;

import java.security.SecureRandom;

/**
 * Liefert den SQLCipher-Datenbankschluessel, hardware-gestuetzt im
 * Android Keystore verankert.
 *
 * Beim ersten Aufruf wird ein zufaelliger 256-Bit-Schluessel erzeugt und
 * in EncryptedSharedPreferences abgelegt; der zugehoerige MasterKey liegt
 * im Android Keystore (AES256_GCM). Folgeaufrufe geben denselben
 * Schluessel als Hex-String zurueck.
 *
 * Angesprochen aus services/db_key.py via pyjnius:
 *     autoclass("de.alltagshelfer.dbkey.DbKeyProvider").getOrCreateKey()
 *
 * Gradle-Abhaengigkeit (siehe buildozer.spec):
 *     androidx.security:security-crypto:1.1.0-alpha06
 */
public final class DbKeyProvider {

    private static final String PREFS_FILE = "zunarodo_secure_prefs";
    private static final String KEY_NAME = "db_key_hex";

    private DbKeyProvider() {
    }

    public static String getOrCreateKey() {
        try {
            Context context =
                    PythonActivity.mActivity.getApplicationContext();

            MasterKey masterKey = new MasterKey.Builder(context)
                    .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
                    .build();

            SharedPreferences prefs = EncryptedSharedPreferences.create(
                    context,
                    PREFS_FILE,
                    masterKey,
                    EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
                    EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM);

            String existing = prefs.getString(KEY_NAME, null);
            if (existing != null && !existing.isEmpty()) {
                return existing;
            }

            byte[] raw = new byte[32];
            new SecureRandom().nextBytes(raw);
            String hex = toHex(raw);
            prefs.edit().putString(KEY_NAME, hex).apply();
            return hex;
        } catch (Exception e) {
            // Bei Fehler null -> services/db_key.py faellt auf
            // unverschluesselt zurueck statt die App abzuschiessen.
            return null;
        }
    }

    private static String toHex(byte[] bytes) {
        StringBuilder sb = new StringBuilder(bytes.length * 2);
        for (byte b : bytes) {
            sb.append(Character.forDigit((b >> 4) & 0xF, 16));
            sb.append(Character.forDigit(b & 0xF, 16));
        }
        return sb.toString();
    }
}
