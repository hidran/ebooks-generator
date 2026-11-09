# Lezione 41. Iniezione dal costruttore, Qualifier e Primary

## Punti chiave

### Iniezione dal costruttore

- Campi final: le dipendenze non cambiano più
- L'oggetto nasce completo
- Nei test basta new, senza Spring
- Da evitare: @Autowired sopra un campo

> Percorso: Spring, poi costruttore, poi oggetto completo.

### Due implementazioni, un'interfaccia

- PaymentMethod: CardPayment e CashPayment, entrambe @Component
- CheckoutService chiede un PaymentMethod: quale?
- Nessuna scelta: errore all'avvio del contesto
- @Primary: la predefinita; @Qualifier("nome"): la scelta per nome

> Percorso: CheckoutService, poi PaymentMethod, poi CardPayment o CashPayment.

### Primary o Qualifier

- @Primary: una scelta normale, le altre sono eccezioni
- @Qualifier: un punto preciso chiede un bean per nome
- @Qualifier vince su @Primary
- Nome sbagliato: NoSuchBeanDefinitionException all'avvio
- Servono tutte? List&lt;PaymentMethod&gt; nel costruttore

## Codice della lezione

`src/main/java/com/shop/checkout/CheckoutService.java`

~~~java
package com.shop.checkout;
import com.shop.payment.PaymentMethod;
import org.springframework.stereotype.Service;
@Service
public class CheckoutService {
    private final PaymentMethod paymentMethod;
    public CheckoutService(PaymentMethod paymentMethod) {
        this.paymentMethod = paymentMethod;
    }
    public String checkout(int totalInCents) {
        return paymentMethod.pay(totalInCents);
    }
}
~~~

`src/main/java/com/shop/Main.java`, prima versione

~~~java
package com.shop;
import com.shop.checkout.CheckoutService;
import com.shop.config.ShopConfig;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
public class Main {
    public static void main(String[] args) {
        try (var context = new AnnotationConfigApplicationContext(ShopConfig.class)) {
            CheckoutService online = context.getBean(CheckoutService.class);
            System.out.println("Online: " + online.checkout(4990));
        }
    }
}
~~~

`src/main/java/com/shop/Main.java`

~~~java
package com.shop;
import com.shop.checkout.CheckoutService;
import com.shop.checkout.CounterCheckout;
import com.shop.config.ShopConfig;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
public class Main {
    public static void main(String[] args) {
        try (var context = new AnnotationConfigApplicationContext(ShopConfig.class)) {
            CheckoutService online = context.getBean(CheckoutService.class);
            System.out.println("Online: " + online.checkout(4990));
            CounterCheckout counter = context.getBean(CounterCheckout.class);
            System.out.println("Counter: " + counter.checkout(1500));
        }
    }
}
~~~

`src/main/java/com/shop/payment/CardPayment.java`

~~~java
package com.shop.payment;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Component;
@Component
@Primary
public class CardPayment implements PaymentMethod {
    @Override
    public String pay(int amountInCents) {
        return amountInCents + " cents by card";
    }
}
~~~

`src/main/java/com/shop/checkout/CounterCheckout.java`

~~~java
package com.shop.checkout;
import com.shop.payment.PaymentMethod;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;
@Service
public class CounterCheckout {
    private final PaymentMethod cash;
    public CounterCheckout(@Qualifier("cashPayment") PaymentMethod cash) {
        this.cash = cash;
    }
    public String checkout(int totalInCents) {
        return cash.pay(totalInCents);
    }
}
~~~

`src/main/java/com/shop/payment/CardPayment.java`, versione di partenza

~~~java
package com.shop.payment;
import org.springframework.stereotype.Component;
@Component
public class CardPayment implements PaymentMethod {
    @Override
    public String pay(int amountInCents) {
        return amountInCents + " cents by card";
    }
}
~~~

`src/main/java/com/shop/payment/CashPayment.java`

~~~java
package com.shop.payment;
import org.springframework.stereotype.Component;
@Component
public class CashPayment implements PaymentMethod {
    @Override
    public String pay(int amountInCents) {
        return amountInCents + " cents in cash";
    }
}
~~~

`src/main/java/com/shop/payment/PaymentMethod.java`

~~~java
package com.shop.payment;
public interface PaymentMethod {
    String pay(int amountInCents);
}
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `pom.xml`: lezione 38
- `src/main/java/com/shop/config/ShopConfig.java`: lezione 40

## Riepilogo

- Dipendenze dal costruttore: final, complete, testabili
- Più implementazioni: NoUniqueBeanDefinitionException
- @Primary per la predefinita, @Qualifier per scegliere
