package de.alltagshelfer.ocr;

import android.content.Context;
import android.net.Uri;

import com.google.android.gms.tasks.Tasks;
import com.google.mlkit.vision.common.InputImage;
import com.google.mlkit.vision.text.Text;
import com.google.mlkit.vision.text.TextRecognition;
import com.google.mlkit.vision.text.TextRecognizer;
import com.google.mlkit.vision.text.latin.TextRecognizerOptions;

import org.kivy.android.PythonActivity;

import java.io.File;

/**
 * On-Device-OCR fuer Kassenbons via Google ML Kit Text Recognition.
 *
 * Laeuft komplett lokal (kein Cloud-Call) - passt damit zur
 * Datenschutz-Linie der App (siehe services/ocr.py). Angesprochen aus
 * services/ocr_android.py via pyjnius:
 *     autoclass("de.alltagshelfer.ocr.MlKitOcrBridge").recognize(path)
 *
 * ML Kit arbeitet asynchron (Task); hier wird mit Tasks.await blockierend
 * gewartet, weil pyjnius einen synchronen Rueckgabewert erwartet. Der
 * Aufruf erfolgt aus einem Python-Worker-Thread, nicht dem UI-Thread.
 *
 * Gradle-Abhaengigkeit (siehe buildozer.spec):
 *     com.google.mlkit:text-recognition:16.0.1
 */
public final class MlKitOcrBridge {

    private MlKitOcrBridge() {
    }

    /** Liefert den erkannten Text oder null bei Fehler. */
    public static String recognize(String imagePath) {
        try {
            Context context =
                    PythonActivity.mActivity.getApplicationContext();
            TextRecognizer recognizer = TextRecognition.getClient(
                    TextRecognizerOptions.DEFAULT_OPTIONS);
            InputImage image = InputImage.fromFilePath(
                    context, Uri.fromFile(new File(imagePath)));
            Text result = Tasks.await(recognizer.process(image));
            return result.getText();
        } catch (Exception e) {
            return null;
        }
    }

    /** Schneller Verfuegbarkeitstest fuer services/ocr_android.py. */
    public static boolean isAvailable() {
        try {
            TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS);
            return true;
        } catch (Throwable t) {
            return false;
        }
    }
}
