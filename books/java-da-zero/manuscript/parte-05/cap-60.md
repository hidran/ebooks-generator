# Lezione 40. Scansione dei componenti e stereotipi

## Punti chiave

### Dalla configurazione alla scansione

- Lezione 39: un metodo @Bean per ogni classe
- Tante classi: tanti metodi uguali, solo new
- @ComponentScan: Spring cerca le classi annotate
- Ogni classe annotata diventa un bean

> Percorso: @ComponentScan("com.shop"), poi classi annotate, poi bean.

### Gli stereotipi

- @Component: componente generico
- @Service: un caso d'uso, la logica applicativa
- @Repository: accesso ai dati, traduce le eccezioni
- Per Spring sono tutti @Component: il nome dice il ruolo
- Nome del bean: la classe con l'iniziale minuscola

### Scansione o metodi @Bean?

- Classi nostre: stereotipo e scansione (KISS)
- Classi non nostre (JDK, librerie): metodo @Bean
- Le due strade convivono nella stessa configurazione
- Prezzo: le classi importano annotazioni di Spring
- Per ogni porta, una sola implementazione annotata

## Codice della lezione

`src/main/java/com/shop/config/ShopConfig.java`

~~~java
package com.shop.config;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
@Configuration
@ComponentScan("com.shop")
public class ShopConfig {
}
~~~

`src/main/java/com/shop/infrastructure/InMemoryProductRepository.java`

~~~java
package com.shop.infrastructure;
import com.shop.application.ProductRepository;
import com.shop.domain.Product;
import java.util.ArrayList;
import java.util.List;
import org.springframework.stereotype.Repository;
@Repository
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

`src/main/java/com/shop/application/CatalogService.java`

~~~java
package com.shop.application;
import com.shop.domain.Product;
import java.util.List;
import org.springframework.stereotype.Service;
@Service
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
            Object repository = context.getBean("inMemoryProductRepository");
            System.out.println("Scanned bean: " + repository.getClass().getSimpleName());
        }
    }
}
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `pom.xml`: lezione 38
- `src/main/java/com/shop/Main.java`, versione di partenza: lezione 39, file `src/main/java/com/shop/Main.java`
- `src/main/java/com/shop/application/CatalogService.java`, versione di partenza: lezione 39, file `src/main/java/com/shop/application/CatalogService.java`
- `src/main/java/com/shop/application/ProductRepository.java`: lezione 39
- `src/main/java/com/shop/domain/Product.java`: lezione 39
- `src/main/java/com/shop/infrastructure/InMemoryProductRepository.java`, versione di partenza: lezione 39, file `src/main/java/com/shop/infrastructure/InMemoryProductRepository.java`

## Riepilogo

- @Component, @Service, @Repository segnano i bean
- @ComponentScan cerca nel package e nei sotto package
- Un solo costruttore: Spring inietta, senza @Autowired
- Classi nostre: scansione; classi non nostre: @Bean
