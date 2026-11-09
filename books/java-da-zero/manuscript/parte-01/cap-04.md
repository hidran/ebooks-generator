# Lezione 2. Compilare, eseguire e provare il codice

## Punti chiave

### Dal sorgente al risultato

- Scrivo un file sorgente, estensione .java
- javac lo controlla e lo traduce in bytecode
- java avvia la JVM, che esegue il bytecode

> Percorso: Greeting.java, poi javac, poi Greeting.class, poi java, poi Output.

### Tre modi per eseguire il codice

- javac e java: due passi, un file .class
- java Greeting.java: un solo passo, per un file singolo
- jshell: prove veloci, una riga alla volta

### Gli errori

- Errore di compilazione: il compilatore si ferma, il programma non parte
- Errore di esecuzione: il programma parte e poi si ferma
- IntelliJ segnala in rosso gli errori mentre scrivi

## Codice della lezione

`Greeting.java`

~~~java
public class Greeting {
    public static void main(String[] args) {
        System.out.println("Hello from the terminal!");
    }
}
~~~

`Welcome.java`

~~~java
public class Welcome {
    public static void main(String[] args) {
        System.out.println("Welcome to Java!");
    }
}
~~~

`Welcome.java`, versione con un errore voluto: non compila o il test fallisce, per leggere il messaggio

~~~java
public class Welcome {
    public static void main(String[] args) {
        System.out.println("Welcome to Java!");
    }
~~~

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
cd build-and-run/src
cat Greeting.java
javac Greeting.java
ls
java Greeting
java Greeting.java
javap -c Greeting
jshell
~~~

Dentro JShell scriviamo:

~~~text
2 + 3
"java".toUpperCase()
int year = 2026
year + 1
/exit
~~~

## Riepilogo

- Sorgente, compilazione, esecuzione sulla JVM
- javac e java, java File.java, jshell
- Gli errori di compilazione si vedono prima di eseguire
