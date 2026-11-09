# Lezione 49. Logging strutturato con SLF4J e Spring Boot

## Punti chiave

### Un evento interrogabile

- SLF4J: API usata dal codice
- Logback: implementazione predefinita degli starter
- Livello, messaggio e campi sono informazioni distinte
- Dati fittizi: ORD-1042 e totale 2990 centesimi

### Dal testo ai campi

- Prima: frase con orderId e totale incorporati
- Dopo: messaggio stabile checkout_completed
- addKeyValue conserva nomi e valori dell'evento
- I numeri rimangono numeri, non parti di una frase
- KISS: usare il supporto di Boot senza scrivere encoder manuali

### Formato strutturato

- logging.structured.format.console: logstash
- Un oggetto JSON per riga
- Il formato non cambia la regola di calcolo
- jq seleziona soltanto l'evento e i campi utili

### Scegliere cosa registrare

- INFO per eventi operativi utili
- DEBUG per dettagli diagnostici mirati
- Evitare credenziali, token e dati personali
- Non loggare indiscriminatamente oggetti o richieste

## Codice della lezione

`src/main/java/com/shop/CheckoutService.java`

~~~java
package com.shop;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class CheckoutService {
    private static final Logger LOGGER = LoggerFactory.getLogger(CheckoutService.class);

    public int checkout(String orderId, int subtotal, int shipping) {
        if (subtotal < 0 || shipping < 0) {
            throw new IllegalArgumentException("Amounts must be non-negative");
        }
        int total = subtotal + shipping;
        LOGGER.atInfo()
                .addKeyValue("orderId", orderId)
                .addKeyValue("totalInCents", total)
                .log("checkout_completed");
        return total;
    }
}
~~~

`src/main/resources/application.yml`

~~~yaml
spring:
  application:
    name: shop
  main:
    banner-mode: off
logging:
  structured:
    format:
      console: logstash
~~~

`src/main/java/com/shop/CheckoutDemo.java`

~~~java
package com.shop;

import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

@Component
public class CheckoutDemo implements CommandLineRunner {
    private final CheckoutService checkout;

    public CheckoutDemo(CheckoutService checkout) {
        this.checkout = checkout;
    }

    @Override
    public void run(String... args) {
        checkout.checkout("ORD-1042", 2500, 490);
    }
}
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
- `pom.xml`: lezione 48
- `src/main/java/com/shop/ShopApplication.java`: lezione 46
- `src/test/java/com/shop/ShopApplicationTests.java`: lezione 46

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw package
java -jar target/shop-0.0.1-SNAPSHOT.jar
java -jar target/shop-0.0.1-SNAPSHOT.jar > checkout.jsonl
jq 'select(.message=="checkout_completed") | {level,message,orderId,totalInCents}' checkout.jsonl
java -jar target/shop-0.0.1-SNAPSHOT.jar --logging.level.com.shop=WARN > warn.jsonl
jq -s '[.[] | select(.message=="checkout_completed")] | length' warn.jsonl
~~~

## Riepilogo

- SLF4J e campi nominati separano evento e presentazione
- Boot può formattare la console come JSON
- Formato, livello e contenuto vanno scelti consapevolmente
