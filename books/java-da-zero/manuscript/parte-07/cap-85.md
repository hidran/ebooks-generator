# Lezione 63. Pagine server con Thymeleaf

## Punti chiave

### Pagine generate dal server

- @Controller restituisce il nome di una vista
- I dati passano nel Model
- Thymeleaf legge i template in resources/templates
- Il browser riceve HTML completo

### Form e Post, Redirect, Get

- th:object e th:field collegano il form
- @Valid e BindingResult raccolgono gli errori
- Con errori: di nuovo la vista del form
- Dopo il salvataggio: redirect all'elenco

### Cosa non serve

- Un framework JavaScript per un form semplice
- Un'API separata per le pagine
- Validazione scritta a mano nel controller

## Codice della lezione

`src/main/java/com/shop/web/ProductPageController.java`

~~~java
package com.shop.web;

import com.shop.catalog.ProductService;
import jakarta.validation.Valid;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;

@Controller
@RequestMapping("/products")
public class ProductPageController {
    private final ProductService service;

    public ProductPageController(ProductService service) {
        this.service = service;
    }

    @GetMapping
    public String list(Model model) {
        model.addAttribute("products",
                service.list().stream().map(ProductResponse::from).toList());
        return "products/list";
    }

    @GetMapping("/new")
    public String form(Model model) {
        model.addAttribute("product", ProductForm.empty());
        return "products/form";
    }

    @PostMapping
    public String create(
            @Valid @ModelAttribute("product") ProductForm form, BindingResult result) {
        if (result.hasErrors()) {
            return "products/form";
        }
        service.create(form.name(), form.priceInCents());
        return "redirect:/products";
    }
}
~~~

`src/main/resources/templates/products/list.html`

~~~html
<!DOCTYPE html>
<html xmlns:th="http://www.thymeleaf.org" lang="en">
<head>
    <meta charset="UTF-8">
    <title>Products</title>
    <link rel="stylesheet" th:href="@{/shop.css}">
</head>
<body>
<h1>Products</h1>
<table>
    <tr><th>Id</th><th>Name</th><th>Price in cents</th></tr>
    <tr th:each="product : ${products}">
        <td th:text="${product.id}">1</td>
        <td th:text="${product.name}">Keyboard</td>
        <td th:text="${product.priceInCents}">4900</td>
    </tr>
</table>
<p><a th:href="@{/products/new}">New product</a></p>
</body>
</html>
~~~

`src/main/resources/templates/products/form.html`

~~~html
<!DOCTYPE html>
<html xmlns:th="http://www.thymeleaf.org" lang="en">
<head>
    <meta charset="UTF-8">
    <title>New product</title>
    <link rel="stylesheet" th:href="@{/shop.css}">
</head>
<body>
<h1>New product</h1>
<form th:action="@{/products}" th:object="${product}" method="post">
    <label>Name <input type="text" th:field="*{name}"></label>
    <p class="error" th:if="${#fields.hasErrors('name')}" th:errors="*{name}">Name error</p>
    <label>Price in cents <input type="number" th:field="*{priceInCents}"></label>
    <p class="error" th:if="${#fields.hasErrors('priceInCents')}" th:errors="*{priceInCents}">Price error</p>
    <button type="submit">Save</button>
</form>
<p><a th:href="@{/products}">Back to the list</a></p>
</body>
</html>
~~~

`src/main/java/com/shop/web/ProductForm.java`

~~~java
package com.shop.web;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

public record ProductForm(@NotBlank String name, @NotNull @Positive Integer priceInCents) {
    public static ProductForm empty() {
        return new ProductForm("", null);
    }
}
~~~

`src/test/java/com/shop/web/ProductPageTests.java`

~~~java
package com.shop.web;

import com.shop.catalog.Product;
import com.shop.catalog.ProductService;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.assertj.MockMvcTester;
import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.BDDMockito.given;
import static org.mockito.BDDMockito.then;
import static org.mockito.Mockito.verifyNoInteractions;

@WebMvcTest(ProductPageController.class)
class ProductPageTests {
    @Autowired MockMvcTester mvc;
    @MockitoBean ProductService service;

    @Test
    void listPageShowsTheProducts() {
        given(service.list()).willReturn(List.of(new Product(1, "Keyboard", 4900)));
        assertThat(mvc.get().uri("/products"))
                .hasStatusOk().hasViewName("products/list")
                .bodyText().contains("Keyboard");
    }

    @Test
    void formPageStartsEmpty() {
        assertThat(mvc.get().uri("/products/new"))
                .hasStatusOk().hasViewName("products/form")
                .bodyText().contains("name=\"priceInCents\"");
    }

    @Test
    void validFormRedirectsToTheList() {
        given(service.create("Mouse", 2500)).willReturn(new Product(2, "Mouse", 2500));
        assertThat(mvc.post().uri("/products")
                .param("name", "Mouse").param("priceInCents", "2500"))
                .hasStatus3xxRedirection().hasRedirectedUrl("/products");
        then(service).should().create("Mouse", 2500);
    }

    @Test
    void invalidFormShowsTheErrors() {
        assertThat(mvc.post().uri("/products")
                .param("name", " ").param("priceInCents", "0"))
                .hasStatusOk().hasViewName("products/form")
                .bodyText().contains("must not be blank")
                .contains("must be greater than 0");
        verifyNoInteractions(service);
    }
}
~~~

`pom.xml`

~~~xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>4.1.1</version>
        <relativePath/>
    </parent>
    <groupId>com.shop</groupId>
    <artifactId>shop</artifactId>
    <version>0.0.1-SNAPSHOT</version>
    <properties>
        <java.version>25</java.version>
    </properties>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-webmvc</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-thymeleaf</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-webmvc-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
~~~

`requests/create-product.http`

~~~http
### Create product
POST http://127.0.0.1:18093/api/products
Accept: application/json
Content-Type: application/json

{"name":"Mouse","priceInCents":2500}
~~~

`src/main/resources/application.yml`

~~~yaml
spring:
  application:
    name: shop
server:
  address: 127.0.0.1
  port: 18093
~~~

`src/main/resources/static/shop.css`

~~~css
body { font-family: system-ui, sans-serif; font-size: 28px; margin: 40px 60px; background: #111827; color: #e5edf8; }
h1 { font-size: 44px; }
table { border-collapse: collapse; margin-bottom: 24px; }
th, td { border: 1px solid #34435b; padding: 10px 24px; text-align: left; }
label { display: block; margin: 18px 0 6px; }
input, button { font-size: 28px; padding: 8px 12px; }
button { margin-top: 24px; }
a { color: #8ab4f8; }
.error { color: #f28b82; margin: 4px 0; }
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
- `src/main/java/com/shop/ShopApplication.java`: lezione 52
- `src/main/java/com/shop/catalog/InMemoryProductRepository.java`: lezione 57
- `src/main/java/com/shop/catalog/Product.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductNotFoundException.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductRepository.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductService.java`: lezione 57
- `src/main/java/com/shop/web/ApiErrorHandler.java`: lezione 57
- `src/main/java/com/shop/web/CreateProductRequest.java`: lezione 57
- `src/main/java/com/shop/web/ProductController.java`: lezione 57
- `src/main/java/com/shop/web/ProductResponse.java`: lezione 57
- `src/test/java/com/shop/web/ProductApiTests.java`: lezione 57

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw package -DskipTests
java -jar target/shop-0.0.1-SNAPSHOT.jar
./mvnw test
./mvnw package
~~~

## Riepilogo

- @Controller, Model e nome della vista
- th:each, th:text, th:field e th:errors
- @Valid e BindingResult riportano gli errori nel form
- Post, Redirect, Get dopo il salvataggio
- Lo stesso servizio per API e pagine
