# Lezione 36. Architettura a strati ed esagonale

## Punti chiave

### Tre responsabilità, tre strati

- Dominio: le regole del negozio
- Applicazione: i casi d'uso, come registrare un ordine
- Infrastruttura: database, web, pagamenti
- A strati classica: il dominio finisce per dipendere dal database

> Percorso: presentazione, poi applicazione, poi dominio, poi database.

### Esagonale: porte e adattatori

- Al centro dominio e applicazione, senza dettagli tecnici
- Porta: interfaccia decisa dall'applicazione (OrderRepository)
- Adattatore: la implementa nell'infrastruttura
- La D di SOLID applicata a tutta l'applicazione

> Percorso: infrastructure, poi application, poi domain.

### Quando non serve (KISS)

- Script piccolo: basta una classe
- Niente strati che passano i dati e basta
- Porte solo ai confini: database, pagamenti, email
- Conta la direzione delle dipendenze, non il nome dei package

## Codice della lezione

`com/shop/domain/Order.java`

~~~java
package com.shop.domain;
public record Order(String id, int totalInCents) {
    public Order {
        if (totalInCents <= 0) {
            throw new IllegalArgumentException("total must be positive");
        }
    }
}
~~~

`com/shop/infrastructure/InMemoryOrderRepository.java`

~~~java
package com.shop.infrastructure;
import com.shop.application.OrderRepository;
import com.shop.domain.Order;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
public class InMemoryOrderRepository implements OrderRepository {
    private final Map<String, Order> orders = new HashMap<>();
    @Override
    public void save(Order order) {
        orders.put(order.id(), order);
    }
    @Override
    public List<Order> findAll() {
        return List.copyOf(orders.values());
    }
}
~~~

`com/shop/Main.java`

~~~java
package com.shop;
import com.shop.application.OrderRepository;
import com.shop.application.PlaceOrderService;
import com.shop.infrastructure.InMemoryOrderRepository;
public class Main {
    public static void main(String[] args) {
        OrderRepository repository = new InMemoryOrderRepository();
        PlaceOrderService service = new PlaceOrderService(repository);
        System.out.println("Placed: " + service.place("A-1", 2500));
        try {
            service.place("A-2", 0);
        } catch (IllegalArgumentException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
        System.out.println("Stored: " + repository.findAll());
    }
}
~~~

`com/shop/application/OrderRepository.java`

~~~java
package com.shop.application;
import com.shop.domain.Order;
import java.util.List;
public interface OrderRepository {
    void save(Order order);
    List<Order> findAll();
}
~~~

`com/shop/application/PlaceOrderService.java`

~~~java
package com.shop.application;
import com.shop.domain.Order;
public class PlaceOrderService {
    private final OrderRepository repository;
    public PlaceOrderService(OrderRepository repository) {
        this.repository = repository;
    }
    public Order place(String id, int totalInCents) {
        Order order = new Order(id, totalInCents);
        repository.save(order);
        return order;
    }
}
~~~

## Esercizio 36: un caso d’uso dietro una porta

Obiettivo: Mantenere il servizio indipendente dall’adattatore di persistenza.

`OrderRepository` è la porta decisa dal caso d’uso.

**Completa `OrderService.place(customer, total)`**:

1. un cliente `null` o *blank* o totale non positivo causa `IllegalArgumentException` **prima di salvare**;
2. altrimenti crea `Order` con cliente ripulito da spazi esterni e totale ricevuto,
3. passalo a `repository.save` **una sola volta**,
4. restituisci l’identificativo prodotto dall’adattatore.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
public class Exercise {

    public record Order(String customer, int total) {}

    public interface OrderRepository {
        String save(Order order);
    }

    public static class OrderService {

        private final OrderRepository repository;

        public OrderService(OrderRepository repository) {
            this.repository = repository;
        }

        public String place(String customer, int total) {
            // TODO: completa questo blocco.
            // Suggerimento: Valida cliente e totale prima di chiamare il repository.
            // Crea un Order con new Order e il nome ripulito con trim().
            // Passa l’ordine a repository.save e restituisci l’identificativo ricevuto.
            return "";
        }
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
public class Exercise {

    public record Order(String customer, int total) {}

    public interface OrderRepository {
        String save(Order order);
    }

    public static class OrderService {

        private final OrderRepository repository;

        public OrderService(OrderRepository repository) {
            this.repository = repository;
        }

        public String place(String customer, int total) {
            if (customer == null || customer.isBlank() || total <= 0) {
                throw new IllegalArgumentException("Invalid order");
            }
            return repository.save(new Order(customer.trim(), total));
        }
    }
}
~~~

Vogliamo un caso d'uso che registra un ordine attraverso una porta, senza sapere quale adattatore lo salverà.

In `place` controlliamo tutto prima di salvare: cliente `null`, cliente fatto solo di spazi con `isBlank()`, oppure totale non positivo. In questi casi lanciamo `IllegalArgumentException`. L'ordine dei controlli conta: `customer == null` viene per primo, così `isBlank()` non viene mai chiamato su `null`. Poi creiamo `new Order(customer.trim(), total)`, lo passiamo a `repository.save` una sola volta e restituiamo l'identificativo che ci dà l'adattatore.

È l'architettura esagonale della lezione 36. `OrderRepository` è una porta: un'interfaccia decisa dall'applicazione, che dice solo "salva questo ordine e dammi un id". Database, file o memoria sono adattatori, e vivono nell'infrastruttura. Se il servizio usasse direttamente una classe di database, ogni cambio di tecnologia ci costringerebbe a modificare il caso d'uso, e ogni test avrebbe bisogno di un database acceso. Come dice la lezione, è la D di SOLID applicata all'intera applicazione.

Un errore tipico è dimenticare `trim()`: il test `passesDomainValueToPort` passa `" Ada "` e si aspetta che arrivi alla porta `new Order("Ada", 1200)`. Un altro è usare `isEmpty()` invece di `isBlank()`: la stringa `" "` non è vuota, quindi passerebbe la validazione. Il test `validatesBeforeSaving` la prova e controlla che il repository sia stato chiamato zero volte.

## Riepilogo

- Dominio, applicazione, infrastruttura: un package per strato
- La porta la decide l'applicazione, l'adattatore la implementa
- Dipendenze sempre verso il centro; Main collega tutto
