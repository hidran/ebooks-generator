# Lezione 45. Testare il container e i bean

## Punti chiave

### Spring Core in breve

- Il container crea e collega i bean (ApplicationContext)
- @Configuration e @Bean, scansione con gli stereotipi
- Costruttore, @Primary e @Qualifier; scope e ciclo di vita
- Proprietà, profili ed eventi

> Percorso: configurazione, poi container, poi bean collegati.

### Due modi di testare

- Test unitario: new e un finto della porta, senza Spring
- Veloce: verifica la logica del servizio
- Test del contesto: @SpringJUnitConfig(ShopConfig.class)
- Verifica il collegamento: bean giusti, chiamata vera

> Percorso: CheckoutServiceTest, poi new CheckoutService(fake).

### Quale test, quando

- Piramide: tanti test unitari, pochi test del contesto
- La logica si prova senza container
- Il contesto si prova una volta: bean, implementazioni, configurazione
- Spring riusa lo stesso contesto tra le classi di test
- Nel test, @Autowired sul costruttore: lo crea JUnit

## Codice della lezione

`src/test/java/com/shop/checkout/CheckoutServiceTest.java`

~~~java
package com.shop.checkout;
import com.shop.payment.PaymentGateway;
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;
class CheckoutServiceTest {
    private final PaymentGateway fake = amountInCents -> "Fake: " + amountInCents;
    private final CheckoutService service = new CheckoutService(fake);
    @Test
    void addsShippingUnderThreshold() {
        assertThat(service.checkout(2000)).isEqualTo("Fake: 2500");
    }
    @Test
    void shipsForFreeFromThreshold() {
        assertThat(service.checkout(3000)).isEqualTo("Fake: 3000");
    }
}
~~~

`src/test/java/com/shop/config/ShopConfigTest.java`

~~~java
package com.shop.config;
import com.shop.checkout.CheckoutService;
import com.shop.payment.BankPaymentGateway;
import com.shop.payment.PaymentGateway;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;
import static org.assertj.core.api.Assertions.assertThat;
@SpringJUnitConfig(ShopConfig.class)
class ShopConfigTest {
    private final PaymentGateway gateway;
    private final CheckoutService checkout;
    @Autowired
    ShopConfigTest(PaymentGateway gateway, CheckoutService checkout) {
        this.gateway = gateway;
        this.checkout = checkout;
    }
    @Test
    void wiresCheckoutToTheBankGateway() {
        assertThat(gateway).isInstanceOf(BankPaymentGateway.class);
        assertThat(checkout.checkout(2000)).isEqualTo("Bank charge: 2500 cents");
    }
}
~~~

`src/main/java/com/shop/checkout/CheckoutService.java`

~~~java
package com.shop.checkout;
import com.shop.payment.PaymentGateway;
import org.springframework.stereotype.Service;
@Service
public class CheckoutService {
    private final PaymentGateway gateway;
    public CheckoutService(PaymentGateway gateway) {
        this.gateway = gateway;
    }
    public String checkout(int totalInCents) {
        int shipping = totalInCents < 3000 ? 500 : 0;
        return gateway.charge(totalInCents + shipping);
    }
}
~~~

`src/main/java/com/shop/payment/BankPaymentGateway.java`

~~~java
package com.shop.payment;
import org.springframework.stereotype.Component;
@Component
public class BankPaymentGateway implements PaymentGateway {
    @Override
    public String charge(int amountInCents) {
        return "Bank charge: " + amountInCents + " cents";
    }
}
~~~

`src/main/java/com/shop/payment/PaymentGateway.java`

~~~java
package com.shop.payment;
public interface PaymentGateway {
    String charge(int amountInCents);
}
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `pom.xml`: lezione 38
- `src/main/java/com/shop/config/ShopConfig.java`: lezione 40

## Riepilogo

- Iniezione dal costruttore: test unitari con new e un finto
- @SpringJUnitConfig carica la configurazione vera
- Pochi test del contesto, tanti test unitari
