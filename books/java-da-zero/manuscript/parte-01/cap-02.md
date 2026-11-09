# Lezione 1b. Visual Studio Code per Java

## Punti chiave

### Perché Visual Studio Code

- Editor gratuito, leggero, per ogni sistema operativo
- Con le estensioni diventa un ambiente completo per Java
- Stesso JDK e stesso codice: cambia solo lo strumento

### Che cosa serve

- JDK 25, già installato nella lezione 1
- Visual Studio Code, dal sito ufficiale
- Extension Pack for Java: un'estensione, tutto il necessario

## Codice della lezione

`Hello.java`

~~~java
public class Hello {
    public static void main(String[] args) {
        System.out.println("Hello from VS Code!");
    }
}
~~~

`Totals.java`

~~~java
public class Totals {
    public static void main(String[] args) {
        int total = 0;
        for (int i = 1; i <= 3; i++) {
            total += i;
        }
        System.out.println("Total: " + total);
    }
}
~~~

`Welcome.java`

~~~java
public class Welcome {
    public static void main(String[] args) {
        System.out.println("Java " + Runtime.version().feature());
    }
}
~~~

## Riepilogo

- Extension Pack for Java: linguaggio, debugger, test, Maven
- Nuovo file, Run e terminale integrato
- Gli errori compaiono nel pannello Problems
- Punto di interruzione con F9, debug con F5, passo con F10
- Nel resto del corso scegliete l'IDE che preferite
