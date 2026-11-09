# Lezione 43. Configurazione esterna e profili

## Punti chiave

### Configurazione fuori dal codice

- Una sola build per ogni ambiente: sviluppo, test, produzione
- Twelve factor: la configurazione sta nell'ambiente
- Cambiare un valore senza ricompilare
- Nessun segreto nel codice

> Percorso: una build, poi profilo dev, poi profilo prod.

### File di proprietà e @Value

- src/main/resources/shop.properties: chiave=valore
- @PropertySource("classpath:shop.properties") sulla configurazione
- @Value("${shop.currency}") sul parametro del costruttore
- ${chiave:predefinito}: il valore se la chiave manca
- Spring Boot aggiunge @ConfigurationProperties e application.yml

### Profili e valori da fuori

- @Profile("dev"), @Profile("prod"): il bean esiste solo nel suo profilo
- Nel codice: setActiveProfiles prima di refresh
- All'avvio: -Dspring.profiles.active=prod
- -Dshop.currency=USD o SHOP_CURRENCY vincono sul file
- Nessun profilo attivo: nessun gateway, errore all'avvio

## Codice della lezione

`src/main/resources/shop.properties`

~~~properties
# Shop configuration
shop.currency=EUR
~~~

`src/main/java/com/shop/checkout/CheckoutService.java`

~~~java
package com.shop.checkout;
import com.shop.payment.PaymentGateway;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
@Service
public class CheckoutService {
    private final PaymentGateway gateway;
    private final String currency;
    private final int minimumInCents;
    public CheckoutService(PaymentGateway gateway,
            @Value("${shop.currency}") String currency,
            @Value("${shop.minimum-order:1000}") int minimumInCents) {
        this.gateway = gateway;
        this.currency = currency;
        this.minimumInCents = minimumInCents;
    }
    public String checkout(int totalInCents) {
        if (totalInCents < minimumInCents) {
            return "Minimum order: " + minimumInCents + " cents";
        }
        return gateway.charge(totalInCents, currency);
    }
}
~~~

`src/main/java/com/shop/config/ShopConfig.java`

~~~java
package com.shop.config;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.PropertySource;
@Configuration
@ComponentScan("com.shop")
@PropertySource("classpath:shop.properties")
public class ShopConfig {
}
~~~

`src/main/java/com/shop/payment/FakePaymentGateway.java`

~~~java
package com.shop.payment;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;
@Component
@Profile("dev")
public class FakePaymentGateway implements PaymentGateway {
    @Override
    public String charge(int amountInCents, String currency) {
        return "Fake charge: " + amountInCents + " cents in " + currency;
    }
}
~~~

`src/main/java/com/shop/payment/BankPaymentGateway.java`

~~~java
package com.shop.payment;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;
@Component
@Profile("prod")
public class BankPaymentGateway implements PaymentGateway {
    @Override
    public String charge(int amountInCents, String currency) {
        return "Bank charge: " + amountInCents + " cents in " + currency;
    }
}
~~~

`src/main/java/com/shop/Main.java`, passaggio intermedio («dev»)

~~~java
package com.shop;
import com.shop.checkout.CheckoutService;
import com.shop.config.ShopConfig;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
public class Main {
    public static void main(String[] args) {
        try (var context = new AnnotationConfigApplicationContext()) {
            context.getEnvironment().setActiveProfiles("dev");
            context.register(ShopConfig.class);
            context.refresh();
            CheckoutService checkout = context.getBean(CheckoutService.class);
            System.out.println(checkout.checkout(4990));
            System.out.println(checkout.checkout(500));
        }
    }
}
~~~

`src/main/java/com/shop/Main.java`

~~~java
package com.shop;
import com.shop.checkout.CheckoutService;
import com.shop.config.ShopConfig;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
public class Main {
    public static void main(String[] args) {
        try (var context = new AnnotationConfigApplicationContext()) {
            context.getEnvironment().setActiveProfiles("prod");
            context.register(ShopConfig.class);
            context.refresh();
            CheckoutService checkout = context.getBean(CheckoutService.class);
            System.out.println(checkout.checkout(4990));
            System.out.println(checkout.checkout(500));
        }
    }
}
~~~

`src/main/java/com/shop/Main.java`, versione di partenza

~~~java
package com.shop;
import com.shop.checkout.CheckoutService;
import com.shop.config.ShopConfig;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
public class Main {
    public static void main(String[] args) {
        try (var context = new AnnotationConfigApplicationContext(ShopConfig.class)) {
            CheckoutService checkout = context.getBean(CheckoutService.class);
            System.out.println(checkout.checkout(4990));
            System.out.println(checkout.checkout(500));
        }
    }
}
~~~

`src/main/java/com/shop/payment/BankPaymentGateway.java`, versione di partenza

~~~java
package com.shop.payment;
import org.springframework.stereotype.Component;
@Component
public class BankPaymentGateway implements PaymentGateway {
    @Override
    public String charge(int amountInCents, String currency) {
        return "Bank charge: " + amountInCents + " cents in " + currency;
    }
}
~~~

`src/main/java/com/shop/payment/FakePaymentGateway.java`, versione di partenza

~~~java
package com.shop.payment;
import org.springframework.stereotype.Component;
@Component
public class FakePaymentGateway implements PaymentGateway {
    @Override
    public String charge(int amountInCents, String currency) {
        return "Fake charge: " + amountInCents + " cents in " + currency;
    }
}
~~~

`src/main/java/com/shop/payment/PaymentGateway.java`

~~~java
package com.shop.payment;
public interface PaymentGateway {
    String charge(int amountInCents, String currency);
}
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `pom.xml`: lezione 38
- `src/main/java/com/shop/config/ShopConfig.java`, versione di partenza: lezione 40, file `src/main/java/com/shop/config/ShopConfig.java`

## Riepilogo

- Configurazione esterna: una build, tanti ambienti
- @PropertySource carica il file, @Value inietta i valori
- ${chiave:predefinito} per il valore di riserva
- @Profile sceglie i bean per ambiente
