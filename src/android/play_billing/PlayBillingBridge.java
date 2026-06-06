package de.alltagshelfer.billing;

/**
 * Stub fuer Google Play Billing (Phase 1).
 * Wird per pyjnius aus services/play_billing_android.py angesprochen,
 * sobald buildozer.spec gradle_dependencies aktiviert.
 */
public class PlayBillingBridge {

    public static boolean isBillingAvailable() {
        return false;
    }

    public static String getStatusMessage() {
        return "Play Billing bridge not wired in build yet.";
    }
}
