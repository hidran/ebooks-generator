# Lezione 39. Bean e configurazione Java

## Punti chiave

### Dalle classi alla configurazione Java

- Lezione 38: le classi passate al contesto, Spring chiama i costruttori
- Limiti: classi non nostre, scelta dell'implementazione
- @Configuration: una classe che descrive i bean
- @Bean: un metodo che costruisce un oggetto con new

> Percorso: ShopConfig, poi ApplicationContext, poi bean.

### Le regole di @Bean

- Nome del bean = nome del metodo: productRepository
- Tipo del bean = tipo restituito: ProductRepository
- Dipendenze = parametri del metodo, le passa Spring
- getBean(CatalogService.class): un oggetto solo, riusato

> Percorso: productRepository(), poi catalogService(productRepository).

### Quando usare la configurazione Java

- Classi non nostre: librerie e JDK (Clock, client HTTP)
- Costruzione che richiede delle scelte
- Implementazione decisa in un punto solo (DIP)
- Le classi del negozio restano senza Spring

## Codice della lezione

`src/main/java/com/shop/config/ShopConfig.java`

~~~java
package com.shop.config;
import com.shop.application.CatalogService;
import com.shop.application.ProductRepository;
import com.shop.infrastructure.InMemoryProductRepository;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
@Configuration
public class ShopConfig {
    @Bean
    public ProductRepository productRepository() {
        return new InMemoryProductRepository();
    }
    @Bean
    public CatalogService catalogService(ProductRepository productRepository) {
        return new CatalogService(productRepository);
    }
}
~~~

`src/main/java/com/shop/Main.java`

~~~java
package com.shop;
import com.shop.application.CatalogService;
import com.shop.config.ShopConfig;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
public class Main {
    public static void main(String[] args) {
        try (var context = new AnnotationConfigApplicationContext(ShopConfig.class)) {
            CatalogService catalog = context.getBean(CatalogService.class);
            catalog.add("Keyboard", 4990);
            System.out.println("Catalog: " + catalog.products());
            CatalogService again = context.getBean(CatalogService.class);
            System.out.println("Same service: " + (catalog == again));
            Object repository = context.getBean("productRepository");
            System.out.println("Bean productRepository: " + repository.getClass().getSimpleName());
        }
    }
}
~~~

`src/main/java/com/shop/application/CatalogService.java`

~~~java
package com.shop.application;
import com.shop.domain.Product;
import java.util.List;
public class CatalogService {
    private final ProductRepository repository;
    public CatalogService(ProductRepository repository) {
        this.repository = repository;
    }
    public void add(String name, int priceInCents) {
        repository.save(new Product(name, priceInCents));
    }
    public List<Product> products() {
        return repository.findAll();
    }
}
~~~

`src/main/java/com/shop/application/ProductRepository.java`

~~~java
package com.shop.application;
import com.shop.domain.Product;
import java.util.List;
public interface ProductRepository {
    void save(Product product);
    List<Product> findAll();
}
~~~

`src/main/java/com/shop/domain/Product.java`

~~~java
package com.shop.domain;
public record Product(String name, int priceInCents) {
}
~~~

`src/main/java/com/shop/infrastructure/InMemoryProductRepository.java`

~~~java
package com.shop.infrastructure;
import com.shop.application.ProductRepository;
import com.shop.domain.Product;
import java.util.ArrayList;
import java.util.List;
public class InMemoryProductRepository implements ProductRepository {
    private final List<Product> products = new ArrayList<>();
    @Override
    public void save(Product product) {
        products.add(product);
    }
    @Override
    public List<Product> findAll() {
        return List.copyOf(products);
    }
}
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `pom.xml`: lezione 38

## Riepilogo

- @Configuration descrive i bean, @Bean li costruisce con new
- Nome dal metodo, dipendenze dai parametri
- getBean per tipo o per nome; di base un oggetto solo
- Utile per classi non nostre e per scegliere l'implementazione
