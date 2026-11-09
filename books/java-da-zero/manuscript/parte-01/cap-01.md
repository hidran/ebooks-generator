# Lezione 1. Installare Java e IntelliJ, il primo programma

## Punti chiave

### Il JDK

- JDK: Java Development Kit
- Il pacchetto ufficiale per sviluppare in Java
- Contiene compilatore, JVM e librerie standard

### Il compilatore

- javac legge il sorgente .java
- Lo traduce in bytecode, in un file .class
- Se trova errori, si ferma e li segnala

### La JVM

- La Java Virtual Machine esegue il bytecode
- Lo stesso bytecode gira su Mac, Windows e Linux

> Percorso: Sorgente .java, poi javac, poi Bytecode .class, poi JVM.

### L'IDE

- IDE: ambiente di sviluppo integrato
- Editor, compilatore, esecuzione e suggerimenti in una sola finestra
- Useremo IntelliJ IDEA

### Installare IntelliJ IDEA

- Homebrew: il gestore di pacchetti per macOS
- brew install --cask intellij-idea
- In alternativa: il download dal sito di JetBrains

### Un JDK nel sistema

- Eclipse Temurin, distribuito da Adoptium: gratuito
- brew install --cask temurin@25
- Serve per usare java e javac dal terminale
- IntelliJ può scaricarne uno da solo

## Codice della lezione

`HelloWorld.java`

~~~java
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, world!");
    }
}
~~~

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
brew --version
brew install --cask intellij-idea
cd hello-java/src
java -version
javac HelloWorld.java
java HelloWorld
~~~

## Riepilogo

- JDK: compilatore, JVM e librerie
- IntelliJ IDEA: parte in modalità gratuita
- Sorgente .java, compilazione, esecuzione, output
