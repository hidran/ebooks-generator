# Lezione 44. Eventi applicativi

## Punti chiave

### Un servizio che sa troppo

- OrderService chiama email, magazzino e fattura
- Troppe responsabilità: SRP, lezione 30
- Ogni nuova reazione modifica il servizio: OCP, lezione 31

> Percorso: OrderService, poi email, magazzino, fattura.

### Eventi e listener

- Evento: un record al passato, OrderPlaced
- ApplicationEventPublisher nel costruttore: publishEvent
- Listener: un bean con un metodo @EventListener
- Il tipo del parametro sceglie l'evento

> Percorso: OrderService, poi OrderPlaced, poi listener.

### Sincroni, di base

- I listener girano nello stesso thread, dentro publishEvent
- Listener lento: l'ordine aspetta
- Eccezione nel listener: arriva a chi pubblica
- Esistono anche @Async e gli eventi transazionali
- @Order fissa la sequenza tra i listener

## Codice della lezione

`src/main/java/com/shop/order/OrderPlaced.java`

~~~java
package com.shop.order;
public record OrderPlaced(String orderId, int totalInCents) {
}
~~~

`src/main/java/com/shop/order/OrderService.java`

~~~java
package com.shop.order;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;
@Service
public class OrderService {
    private final ApplicationEventPublisher events;
    public OrderService(ApplicationEventPublisher events) {
        this.events = events;
    }
    public void placeOrder(String orderId, int totalInCents) {
        System.out.println("Order " + orderId + " saved");
        events.publishEvent(new OrderPlaced(orderId, totalInCents));
        System.out.println("Order " + orderId + " completed");
    }
}
~~~

`src/main/java/com/shop/notification/EmailListener.java`

~~~java
package com.shop.notification;
import com.shop.order.OrderPlaced;
import org.springframework.context.event.EventListener;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
@Component
public class EmailListener {
    @EventListener
    @Order(1)
    public void onOrderPlaced(OrderPlaced event) {
        System.out.println("Email: order " + event.orderId() + ", total " + event.totalInCents() + " cents");
    }
}
~~~

`src/main/java/com/shop/stock/StockListener.java`

~~~java
package com.shop.stock;
import com.shop.order.OrderPlaced;
import org.springframework.stereotype.Component;
import org.springframework.context.event.EventListener;
import org.springframework.core.annotation.Order;
@Component
public class StockListener {
    @EventListener
    @Order(2)
    public void onOrderPlaced(OrderPlaced event) {
        System.out.println("Stock: items of order " + event.orderId() + " reserved");
    }
}
~~~

`src/main/java/com/shop/Main.java`

~~~java
package com.shop;
import com.shop.config.ShopConfig;
import com.shop.order.OrderService;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
public class Main {
    public static void main(String[] args) {
        try (var context = new AnnotationConfigApplicationContext(ShopConfig.class)) {
            OrderService orders = context.getBean(OrderService.class);
            orders.placeOrder("A-100", 4990);
        }
    }
}
~~~

`src/main/java/com/shop/stock/StockListener.java`, versione di partenza

~~~java
package com.shop.stock;
import com.shop.order.OrderPlaced;
import org.springframework.stereotype.Component;
@Component
public class StockListener {
    public void onOrderPlaced(OrderPlaced event) {
        System.out.println("Stock: items of order " + event.orderId() + " reserved");
    }
}
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `pom.xml`: lezione 38
- `src/main/java/com/shop/config/ShopConfig.java`: lezione 40

## Riepilogo

- Il servizio pubblica un fatto, non chiama i destinatari
- ApplicationEventPublisher nel costruttore, publishEvent
- @EventListener su un metodo di un bean, @Order per la sequenza
- Nuovo listener: il servizio non cambia (OCP)
