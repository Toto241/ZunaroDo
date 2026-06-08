package de.alltagshelfer.billing;

import android.app.Activity;
import android.content.Context;

import com.android.billingclient.api.AcknowledgePurchaseParams;
import com.android.billingclient.api.BillingClient;
import com.android.billingclient.api.BillingClientStateListener;
import com.android.billingclient.api.BillingFlowParams;
import com.android.billingclient.api.BillingResult;
import com.android.billingclient.api.ProductDetails;
import com.android.billingclient.api.Purchase;
import com.android.billingclient.api.PurchasesUpdatedListener;
import com.android.billingclient.api.QueryProductDetailsParams;

import org.json.JSONArray;
import org.json.JSONObject;
import org.kivy.android.PythonActivity;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Google Play Billing (Billing Library 6.x) als pyjnius-Bruecke.
 *
 * Die BillingClient-API ist asynchron (Listener/Callbacks); pyjnius
 * erwartet aber synchrone Rueckgabewerte. Deshalb haelt diese Klasse
 * den Zustand in Feldern und die Python-Seite (services/play_billing_android.py)
 * pollt:
 *   1. startConnection()           -> Verbindung aufbauen
 *   2. queryProductsBlockingJson() -> SKUs + Preise (wartet kurz)
 *   3. launchPurchase(productId)   -> Kauf-Dialog
 *   4. getLastPurchaseToken()      -> nach Rueckkehr pollen
 *   5. getLastProductId()
 *   6. acknowledge(token)          -> Kauf bestaetigen (Pflicht < 3 Tage)
 *
 * !!! GERAETE-VERIFIKATION AUSSTEHEND !!!
 * In der Entwicklungsumgebung (Windows, kein Buildozer) NICHT baubar/
 * testbar. Vor Release auf einem Geraet mit Lizenz-Tester-Konto pruefen.
 * Gradle-Dep: com.android.billingclient:billing:6.2.1 (buildozer.spec).
 */
public final class PlayBillingBridge {

    private static PlayBillingBridge INSTANCE;

    private final BillingClient billingClient;
    private final Map<String, ProductDetails> productCache = new HashMap<>();

    private volatile boolean connected = false;
    private volatile String statusMessage = "nicht verbunden";
    private volatile String lastPurchaseToken = "";
    private volatile String lastProductId = "";
    private volatile int lastResponseCode = -1;

    private final PurchasesUpdatedListener purchasesUpdatedListener =
            new PurchasesUpdatedListener() {
                @Override
                public void onPurchasesUpdated(BillingResult result,
                                               List<Purchase> purchases) {
                    lastResponseCode = result.getResponseCode();
                    if (result.getResponseCode()
                            == BillingClient.BillingResponseCode.OK
                            && purchases != null) {
                        for (Purchase p : purchases) {
                            lastPurchaseToken = p.getPurchaseToken();
                            if (!p.getProducts().isEmpty()) {
                                lastProductId = p.getProducts().get(0);
                            }
                        }
                    }
                }
            };

    private PlayBillingBridge(Context context) {
        billingClient = BillingClient.newBuilder(context)
                .setListener(purchasesUpdatedListener)
                .enablePendingPurchases()
                .build();
    }

    private static synchronized PlayBillingBridge instance() {
        if (INSTANCE == null) {
            Context ctx = PythonActivity.mActivity.getApplicationContext();
            INSTANCE = new PlayBillingBridge(ctx);
        }
        return INSTANCE;
    }

    // ---- Von pyjnius aufgerufene, statische Einstiegspunkte ----------

    public static boolean isBillingAvailable() {
        try {
            return instance().billingClient != null;
        } catch (Throwable t) {
            return false;
        }
    }

    public static String getStatusMessage() {
        try {
            return instance().statusMessage;
        } catch (Throwable t) {
            return "Bridge nicht geladen: " + t.getMessage();
        }
    }

    public static void startConnection() {
        instance().connect();
    }

    public static boolean isConnected() {
        return instance().connected;
    }

    public static int getLastResponseCode() {
        return instance().lastResponseCode;
    }

    public static String getLastPurchaseToken() {
        return instance().lastPurchaseToken;
    }

    public static String getLastProductId() {
        return instance().lastProductId;
    }

    public static void clearLastPurchase() {
        PlayBillingBridge b = instance();
        b.lastPurchaseToken = "";
        b.lastProductId = "";
        b.lastResponseCode = -1;
    }

    /**
     * Fragt die uebergebenen Subscription-SKUs ab und liefert ein
     * JSON-Array [{productId, title, price}], sobald die Antwort da ist.
     * Leeres Array, wenn (noch) nichts geladen wurde.
     */
    public static String queryProductsBlockingJson(String[] productIds) {
        return instance().queryProducts(productIds);
    }

    public static void launchPurchase(String productId) {
        instance().launch(productId);
    }

    public static boolean acknowledge(String purchaseToken) {
        return instance().ack(purchaseToken);
    }

    // ---- Implementierung --------------------------------------------

    private void connect() {
        if (connected) {
            return;
        }
        billingClient.startConnection(new BillingClientStateListener() {
            @Override
            public void onBillingSetupFinished(BillingResult result) {
                if (result.getResponseCode()
                        == BillingClient.BillingResponseCode.OK) {
                    connected = true;
                    statusMessage = "verbunden";
                } else {
                    statusMessage = "Setup-Fehler: "
                            + result.getDebugMessage();
                }
            }

            @Override
            public void onBillingServiceDisconnected() {
                connected = false;
                statusMessage = "Verbindung getrennt";
            }
        });
    }

    private String queryProducts(String[] productIds) {
        List<QueryProductDetailsParams.Product> products = new ArrayList<>();
        for (String id : productIds) {
            products.add(QueryProductDetailsParams.Product.newBuilder()
                    .setProductId(id)
                    .setProductType(BillingClient.ProductType.SUBS)
                    .build());
        }
        QueryProductDetailsParams params =
                QueryProductDetailsParams.newBuilder()
                        .setProductList(products)
                        .build();

        billingClient.queryProductDetailsAsync(params, (result, list) -> {
            productCache.clear();
            if (list != null) {
                for (ProductDetails pd : list) {
                    productCache.put(pd.getProductId(), pd);
                }
            }
        });

        // Snapshot dessen, was bereits im Cache liegt (Python pollt erneut,
        // falls beim ersten Aufruf noch leer).
        JSONArray arr = new JSONArray();
        for (ProductDetails pd : productCache.values()) {
            try {
                JSONObject o = new JSONObject();
                o.put("productId", pd.getProductId());
                o.put("title", pd.getTitle());
                o.put("price", formattedPrice(pd));
                arr.put(o);
            } catch (Exception ignored) {
            }
        }
        return arr.toString();
    }

    private static String formattedPrice(ProductDetails pd) {
        List<ProductDetails.SubscriptionOfferDetails> offers =
                pd.getSubscriptionOfferDetails();
        if (offers != null && !offers.isEmpty()) {
            List<ProductDetails.PricingPhase> phases =
                    offers.get(0).getPricingPhases().getPricingPhaseList();
            if (!phases.isEmpty()) {
                return phases.get(0).getFormattedPrice();
            }
        }
        return "";
    }

    private void launch(String productId) {
        ProductDetails pd = productCache.get(productId);
        if (pd == null) {
            statusMessage = "Produkt nicht geladen: " + productId;
            return;
        }
        List<ProductDetails.SubscriptionOfferDetails> offers =
                pd.getSubscriptionOfferDetails();
        if (offers == null || offers.isEmpty()) {
            statusMessage = "Kein Angebot fuer " + productId;
            return;
        }
        String offerToken = offers.get(0).getOfferToken();

        List<BillingFlowParams.ProductDetailsParams> params = new ArrayList<>();
        params.add(BillingFlowParams.ProductDetailsParams.newBuilder()
                .setProductDetails(pd)
                .setOfferToken(offerToken)
                .build());
        BillingFlowParams flowParams = BillingFlowParams.newBuilder()
                .setProductDetailsParamsList(params)
                .build();

        Activity activity = PythonActivity.mActivity;
        billingClient.launchBillingFlow(activity, flowParams);
    }

    private boolean ack(String purchaseToken) {
        AcknowledgePurchaseParams params =
                AcknowledgePurchaseParams.newBuilder()
                        .setPurchaseToken(purchaseToken)
                        .build();
        final boolean[] ok = {false};
        billingClient.acknowledgePurchase(params, result ->
                ok[0] = result.getResponseCode()
                        == BillingClient.BillingResponseCode.OK);
        return ok[0];
    }
}
