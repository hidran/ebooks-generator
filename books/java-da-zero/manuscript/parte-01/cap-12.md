# Lezione 8b. Debug con IntelliJ

## Punti chiave

### Il debugger

- Bug: il programma gira, ma il risultato è sbagliato
- Punto di interruzione: il programma si ferma prima di quella riga
- Variables: il valore di ogni variabile in quel momento
- Si avanza una riga alla volta e si guarda che cosa cambia

> Percorso: Punto di interruzione, poi Pausa, poi Variables, poi Riga successiva.

### I comandi in IntelliJ

- Cmd+F8: punto di interruzione; Ctrl+D: avvia il debug
- F8, Step Over: esegue la riga e passa alla successiva
- F7, Step Into: entra nel metodo chiamato
- Cmd+Option+R, Resume: riprende; Cmd+F2, Stop: ferma

### Due strumenti in più

- Punto di interruzione condizionale: clic destro sul cerchio rosso
- Una condizione, per esempio i == 2: si ferma solo quando è vera
- Evaluate Expression (Option+F8): calcola un'espressione a programma fermo
- Per esempio prices[0], senza cambiare il codice

## Codice della lezione

`Checkout.java`, prima del refactoring

~~~java
public class Checkout {
    public static void main(String[] args) {
        int[] pricesInCents = {1500, 2000, 1400};
        int totalInCents = sum(pricesInCents);
        System.out.println("Items: " + pricesInCents.length);
        System.out.println("Total in cents: " + totalInCents);
    }
    static int sum(int[] prices) {
        int total = 0;
        for (int i = 1; i < prices.length; i++) {
            total += prices[i];
        }
        return total;
    }
}
~~~

`Checkout.java`

~~~java
public class Checkout {
    public static void main(String[] args) {
        int[] pricesInCents = {1500, 2000, 1400};
        int totalInCents = sum(pricesInCents);
        System.out.println("Items: " + pricesInCents.length);
        System.out.println("Total in cents: " + totalInCents);
    }
    static int sum(int[] prices) {
        int total = 0;
        for (int i = 0; i < prices.length; i++) {
            total += prices[i];
        }
        return total;
    }
}
~~~

## Riepilogo

- Risultato sbagliato? Non si tira a indovinare: si usa il debugger
- Punto di interruzione, Ctrl+D, valori nella vista Variables
- F8 avanza, F7 entra, Cmd+Option+R riprende, Cmd+F2 ferma
- Si corregge solo la riga sbagliata, poi si esegue di nuovo
