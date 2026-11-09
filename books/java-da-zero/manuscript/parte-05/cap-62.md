# Lezione 42. Scope e ciclo di vita dei bean

## Punti chiave

### Singleton e prototype

- Singleton, lo scope predefinito: un oggetto solo
- Creato all'avvio del contesto, condiviso da tutti
- Quindi niente stato del singolo cliente
- @Scope("prototype"): un oggetto nuovo a ogni getBean

### Il ciclo di vita di un bean

- Costruttore, poi iniezione delle dipendenze
- @PostConstruct: il bean è completo, si prepara
- @PreDestroy: alla chiusura del contesto, libera le risorse
- Prototype: Spring non chiama il suo @PreDestroy

> Percorso: costruttore, poi @PostConstruct, poi uso, poi @PreDestroy.

### Quale scope?

- Singleton: servizi, repository, cache (quasi sempre)
- Prototype: un oggetto con il suo stato per ogni utilizzatore
- La pulizia di un prototype tocca a noi
- Web: scope request e session, più avanti
- Prototype dentro un singleton: creato una volta sola

## Codice della lezione

`src/main/java/com/shop/Main.java`

~~~java
package com.shop;
import com.shop.cart.ShoppingCart;
import com.shop.config.ShopConfig;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
public class Main {
    public static void main(String[] args) {
        try (var context = new AnnotationConfigApplicationContext(ShopConfig.class)) {
            System.out.println("Context ready");
            ShoppingCart anna = context.getBean(ShoppingCart.class);
            ShoppingCart marco = context.getBean(ShoppingCart.class);
            System.out.println("Same cart: " + (anna == marco));
            anna.add("Keyboard");
            System.out.println("Marco sees: " + marco.items());
            System.out.println("Closing the context");
        }
        System.out.println("End of main");
    }
}
~~~

`src/main/java/com/shop/cart/ShoppingCart.java`

~~~java
package com.shop.cart;
import java.util.ArrayList;
import java.util.List;
import org.springframework.stereotype.Component;
import org.springframework.context.annotation.Scope;
@Component
@Scope("prototype")
public class ShoppingCart {
    private final List<String> items = new ArrayList<>();
    public ShoppingCart() {
        System.out.println("Cart created");
    }
    public void add(String productName) {
        items.add(productName);
    }
    public List<String> items() {
        return List.copyOf(items);
    }
}
~~~

`src/main/java/com/shop/catalog/ProductCache.java`

~~~java
package com.shop.catalog;
import java.util.HashMap;
import java.util.Map;
import org.springframework.stereotype.Component;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
@Component
public class ProductCache {
    private final Map<String, Integer> prices = new HashMap<>();
    public ProductCache() {
        System.out.println("Cache created");
    }
    @PostConstruct
    public void load() {
        prices.put("Keyboard", 4990);
        prices.put("Mouse", 1990);
        System.out.println("Cache loaded: " + prices.size() + " products");
    }
    @PreDestroy
    public void clear() {
        prices.clear();
        System.out.println("Cache cleared");
    }
    public int priceOf(String name) {
        return prices.getOrDefault(name, 0);
    }
}
~~~

`src/main/java/com/shop/cart/ShoppingCart.java`, versione di partenza

~~~java
package com.shop.cart;
import java.util.ArrayList;
import java.util.List;
import org.springframework.stereotype.Component;
@Component
public class ShoppingCart {
    private final List<String> items = new ArrayList<>();
    public ShoppingCart() {
        System.out.println("Cart created");
    }
    public void add(String productName) {
        items.add(productName);
    }
    public List<String> items() {
        return List.copyOf(items);
    }
}
~~~

`src/main/java/com/shop/catalog/ProductCache.java`, versione di partenza

~~~java
package com.shop.catalog;
import java.util.HashMap;
import java.util.Map;
import org.springframework.stereotype.Component;
@Component
public class ProductCache {
    private final Map<String, Integer> prices = new HashMap<>();
    public ProductCache() {
        System.out.println("Cache created");
    }
    public int priceOf(String name) {
        return prices.getOrDefault(name, 0);
    }
}
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `pom.xml`: lezione 38
- `src/main/java/com/shop/config/ShopConfig.java`: lezione 40

## Riepilogo

- Singleton: un oggetto, creato all'avvio, condiviso
- @Scope("prototype"): un oggetto nuovo a ogni getBean
- @PostConstruct dopo l'iniezione, @PreDestroy alla chiusura
- try con risorse: chiude il contesto, parte @PreDestroy
