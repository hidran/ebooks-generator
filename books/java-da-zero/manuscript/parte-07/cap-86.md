# Lezione 63b. Upload e download di file con Spring MVC

## Punti chiave

### File in arrivo: MultipartFile

- multipart/form-data: testo e file nella stessa richiesta
- @RequestParam MultipartFile: nome, tipo e byte
- max-file-size: limite per ogni file
- max-request-size: limite per tutta la richiesta
- Oltre il limite: 413 Content Too Large

### Dove salvare i file

- Fuori dal Jar: il Jar cambia a ogni versione
- Una cartella configurabile: shop.images.dir
- ${SHOP_IMAGES_DIR:data/images}: ambiente o default
- Stesso Jar, ambienti diversi (12-factor)

### Path traversal

- Il nome del file lo sceglie il client
- ../../escaped.png esce dalla cartella
- Principio: mai fidarsi dell'input del client
- normalize(), poi controllo della cartella di arrivo
- Alternativa: un nome generato da noi

### Cosa non serve

- Uno storage cloud per un solo server
- Immagini come BLOB nel database
- Una libreria per gli upload: bastano MultipartFile e java.nio.file

## Codice della lezione

`src/main/resources/application.yml`

~~~yaml
spring:
  application:
    name: shop
  servlet:
    multipart:
      max-file-size: 512KB
      max-request-size: 1MB
server:
  address: 127.0.0.1
  port: 18193
shop:
  images:
    dir: ${SHOP_IMAGES_DIR:data/images}
~~~

`src/main/java/com/shop/image/ProductImageStorage.java`

~~~java
package com.shop.image;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Optional;
import java.util.stream.Stream;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.util.FileSystemUtils;
import org.springframework.web.multipart.MultipartFile;

@Component
public class ProductImageStorage {
    private final Path root;

    public ProductImageStorage(@Value("${shop.images.dir}") Path root) {
        this.root = root.toAbsolutePath().normalize();
    }

    public void store(long productId, MultipartFile file) throws IOException {
        if (!MediaType.IMAGE_PNG_VALUE.equals(file.getContentType())) {
            throw new InvalidImageException("Only PNG images are accepted.");
        }
        Path folder = root.resolve(String.valueOf(productId));
        Path target = folder.resolve(file.getOriginalFilename()).normalize();
        if (!folder.equals(target.getParent())) {
            throw new InvalidImageException("File name outside the image folder.");
        }
        FileSystemUtils.deleteRecursively(folder);
        Files.createDirectories(folder);
        file.transferTo(target);
    }

    public Optional<Path> find(long productId) throws IOException {
        Path folder = root.resolve(String.valueOf(productId));
        if (!Files.isDirectory(folder)) {
            return Optional.empty();
        }
        try (Stream<Path> files = Files.list(folder)) {
            return files.findFirst();
        }
    }
}
~~~

`src/main/java/com/shop/web/ProductImageController.java`

~~~java
package com.shop.web;

import com.shop.catalog.Product;
import com.shop.catalog.ProductService;
import com.shop.image.ProductImageStorage;
import java.io.IOException;
import java.net.URI;
import java.nio.file.Path;
import java.util.Optional;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.http.ContentDisposition;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/products/{id}/image")
public class ProductImageController {
    private final ProductService products;
    private final ProductImageStorage images;

    public ProductImageController(ProductService products, ProductImageStorage images) {
        this.products = products;
        this.images = images;
    }

    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<Void> upload(@PathVariable long id,
            @RequestParam("file") MultipartFile file) throws IOException {
        Product product = products.find(id);
        images.store(product.id(), file);
        URI location = URI.create("/api/products/" + id + "/image");
        return ResponseEntity.created(location).build();
    }

    @GetMapping
    public ResponseEntity<Resource> download(@PathVariable long id) throws IOException {
        Optional<Path> image = images.find(id);
        if (image.isEmpty()) {
            return ResponseEntity.notFound().build();
        }
        ContentDisposition disposition = ContentDisposition.inline()
                .filename(image.get().getFileName().toString()).build();
        return ResponseEntity.ok()
                .contentType(MediaType.IMAGE_PNG)
                .header(HttpHeaders.CONTENT_DISPOSITION, disposition.toString())
                .body(new FileSystemResource(image.get()));
    }
}
~~~

`src/test/java/com/shop/web/ProductImageTests.java`

~~~java
package com.shop.web;

import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class ProductImageTests {
    static final byte[] PNG = {(byte) 0x89, 'P', 'N', 'G', 13, 10, 26, 10};
    @TempDir static Path tempDir;
    @Autowired MockMvc mvc;

    @DynamicPropertySource
    static void imagesFolder(DynamicPropertyRegistry registry) {
        registry.add("shop.images.dir", () -> tempDir.resolve("images").toString());
    }

    @Test
    void uploadedImageCanBeDownloaded() throws Exception {
        var image = new MockMultipartFile("file", "keyboard.png", "image/png", PNG);
        mvc.perform(multipart("/api/products/1/image").file(image))
                .andExpect(status().isCreated());
        mvc.perform(get("/api/products/1/image"))
                .andExpect(status().isOk())
                .andExpect(content().contentType("image/png"))
                .andExpect(header().string("Content-Disposition",
                        "inline; filename=\"keyboard.png\""))
                .andExpect(content().bytes(PNG));
    }

    @Test
    void fileNameCannotLeaveTheImageFolder() throws Exception {
        var image = new MockMultipartFile("file", "../../escaped.png", "image/png", PNG);
        var upload = mvc.perform(multipart("/api/products/1/image").file(image));
        assertThat(tempDir.resolve("escaped.png")).doesNotExist();
        upload.andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.title").value("Invalid image"));
    }

    @Test
    void onlyPngImagesAreAccepted() throws Exception {
        var notes = new MockMultipartFile("file", "notes.txt", "text/plain", new byte[1]);
        mvc.perform(multipart("/api/products/1/image").file(notes))
                .andExpect(status().isBadRequest());
    }
}
~~~

`requests/download-image.http`

~~~http
### Download the keyboard image
GET http://127.0.0.1:18193/api/products/1/image
Accept: image/png
~~~

`requests/upload-image.http`

~~~http
### Upload the keyboard image
POST http://127.0.0.1:18193/api/products/1/image
Content-Type: multipart/form-data; boundary=ShopBoundary

--ShopBoundary
Content-Disposition: form-data; name="file"; filename="keyboard.png"
Content-Type: image/png

< ./keyboard.png
--ShopBoundary--
~~~

`requests/upload-too-big.http`

~~~http
### An image over the size limit
POST http://127.0.0.1:18193/api/products/1/image
Content-Type: multipart/form-data; boundary=ShopBoundary

--ShopBoundary
Content-Disposition: form-data; name="file"; filename="big-photo.png"
Content-Type: image/png

< ./big-photo.png
--ShopBoundary--
~~~

`requests/upload-traversal.http`

~~~http
### A file name that tries to leave the folder
POST http://127.0.0.1:18193/api/products/1/image
Content-Type: multipart/form-data; boundary=ShopBoundary

--ShopBoundary
Content-Disposition: form-data; name="file"; filename="../../escaped.png"
Content-Type: image/png

< ./keyboard.png
--ShopBoundary--
~~~

`src/main/java/com/shop/image/InvalidImageException.java`

~~~java
package com.shop.image;

public class InvalidImageException extends RuntimeException {
    public InvalidImageException(String message) {
        super(message);
    }
}
~~~

`src/main/java/com/shop/web/ApiErrorHandler.java`

~~~java
package com.shop.web;

import com.shop.catalog.ProductNotFoundException;
import com.shop.image.InvalidImageException;
import java.net.URI;
import java.util.Map;
import java.util.TreeMap;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.WebRequest;
import org.springframework.web.servlet.mvc.method.annotation.ResponseEntityExceptionHandler;

@RestControllerAdvice
public class ApiErrorHandler extends ResponseEntityExceptionHandler {
    @Override
    protected ResponseEntity<Object> handleMethodArgumentNotValid(
            MethodArgumentNotValidException exception,
            HttpHeaders headers,
            HttpStatusCode status,
            WebRequest request) {
        Map<String, String> errors = new TreeMap<>();
        exception.getBindingResult().getFieldErrors().forEach(error ->
                errors.putIfAbsent(error.getField(), error.getDefaultMessage()));

        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
                status, "One or more fields are invalid.");
        problem.setType(URI.create("https://api.shop.example/problems/validation-error"));
        problem.setTitle("Request validation failed");
        problem.setProperty("errors", errors);

        return handleExceptionInternal(exception, problem, headers, status, request);
    }

    @ExceptionHandler(ProductNotFoundException.class)
    public ProblemDetail handleProductNotFound(ProductNotFoundException exception) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
                HttpStatus.NOT_FOUND, exception.getMessage());
        problem.setType(URI.create("https://api.shop.example/problems/product-not-found"));
        problem.setTitle("Product not found");
        return problem;
    }

    @ExceptionHandler(InvalidImageException.class)
    public ProblemDetail handleInvalidImage(InvalidImageException exception) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
                HttpStatus.BAD_REQUEST, exception.getMessage());
        problem.setType(URI.create("https://api.shop.example/problems/invalid-image"));
        problem.setTitle("Invalid image");
        return problem;
    }
}
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `.mvn/wrapper/maven-wrapper.properties`: lezione 46
- `pom.xml`: lezione 55
- `src/main/java/com/shop/ShopApplication.java`: lezione 52
- `src/main/java/com/shop/catalog/InMemoryProductRepository.java`: lezione 57
- `src/main/java/com/shop/catalog/Product.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductNotFoundException.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductRepository.java`: lezione 57
- `src/main/java/com/shop/catalog/ProductService.java`: lezione 57
- `src/main/java/com/shop/web/CreateProductRequest.java`: lezione 57
- `src/main/java/com/shop/web/ProductController.java`: lezione 57
- `src/main/java/com/shop/web/ProductResponse.java`: lezione 57
- `src/test/java/com/shop/web/ProductApiTests.java`: lezione 57

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
./mvnw test
./mvnw package
java -jar target/shop-0.0.1-SNAPSHOT.jar
ls -R data
~~~

## Riepilogo

- MultipartFile e limiti in application.yml
- File in una cartella esterna e configurabile
- Il nome del client: normalizzato e controllato
- Download: ResponseEntity&lt;Resource&gt; e Content-Disposition
- multipart() di MockMvc prova upload, download e attacco
