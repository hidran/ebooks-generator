# Lezione 31. O, aperto all'estensione, chiuso alla modifica

## Punti chiave

### Il problema: una catena di if

- Uno sconto per tipo di cliente: VIP 20%, STUDENT 10%
- Ogni caso nuovo è un ramo in più nello stesso metodo
- Si modifica codice che funziona già

> Percorso: Caso nuovo, poi Riapro DiscountCalculator, poi Nuovo else if, poi Rischio di rompere.

### Aperto e chiuso

- Aperto all'estensione: un caso nuovo è una classe nuova
- Chiuso alla modifica: il codice che funziona non si tocca
- Lo strumento: un'interfaccia, DiscountRule

> Percorso: DiscountCalculator, poi List&lt;DiscountRule&gt;, poi VipRule, StudentRule, BlackFridayRule.

### Non tutto va aperto

- Casi pochi, noti e stabili: enum o sealed interface
- switch come espressione, senza default
- Caso nuovo: il compilatore indica ogni switch da aggiornare
- KISS: niente interfacce per casi che non cambiano

## Codice della lezione

`before/DiscountCalculator.java`, prima del refactoring

~~~java
public class DiscountCalculator {
    public int discountInCents(CustomerType type, int totalInCents) {
        if (type == CustomerType.VIP) {
            return totalInCents * 20 / 100;
        } else if (type == CustomerType.STUDENT) {
            return totalInCents * 10 / 100;
        } else {
            return 0;
        }
    }
}
~~~

`DiscountCalculator.java`

~~~java
import java.util.List;
public class DiscountCalculator {
    private final List<DiscountRule> rules;
    public DiscountCalculator(List<DiscountRule> rules) {
        this.rules = rules;
    }
    public int discountInCents(CustomerType type, int totalInCents) {
        return rules.stream()
                .mapToInt(rule -> rule.discountInCents(type, totalInCents))
                .sum();
    }
}
~~~

`CustomerType.java`

~~~java
public enum CustomerType {
    STANDARD, VIP, STUDENT
}
~~~

`DiscountRule.java`

~~~java
public interface DiscountRule {
    int discountInCents(CustomerType type, int totalInCents);
}
~~~

`VipRule.java`

~~~java
public class VipRule implements DiscountRule {
    @Override
    public int discountInCents(CustomerType type, int totalInCents) {
        if (type != CustomerType.VIP) {
            return 0;
        }
        return totalInCents * 20 / 100;
    }
}
~~~

`StudentRule.java`

~~~java
public class StudentRule implements DiscountRule {
    @Override
    public int discountInCents(CustomerType type, int totalInCents) {
        if (type != CustomerType.STUDENT) {
            return 0;
        }
        return totalInCents * 10 / 100;
    }
}
~~~

`Main.java`

~~~java
import java.util.List;
public class Main {
    public static void main(String[] args) {
        var calculator = new DiscountCalculator(List.of(
                new VipRule(),
                new StudentRule()));
        for (CustomerType type : CustomerType.values()) {
            int discount = calculator.discountInCents(type, 10000);
            System.out.println(type + " discount: " + discount);
        }
    }
}
~~~

`BlackFridayRule.java`

~~~java
public class BlackFridayRule implements DiscountRule {
    @Override
    public int discountInCents(CustomerType type, int totalInCents) {
        return totalInCents * 10 / 100;
    }
}
~~~

`BlackFridayMain.java`

~~~java
import java.util.List;
public class BlackFridayMain {
    public static void main(String[] args) {
        var calculator = new DiscountCalculator(List.of(
                new VipRule(),
                new StudentRule(),
                new BlackFridayRule()));
        for (CustomerType type : CustomerType.values()) {
            int discount = calculator.discountInCents(type, 10000);
            System.out.println(type + " discount: " + discount);
        }
    }
}
~~~

`before/CustomerType.java`: uguale al listato `CustomerType.java` qui sopra.

## Esercizio 31: estendere le regole di sconto

Obiettivo: Applicare OCP delegando il calcolo a una strategia ricevuta.

`DiscountRule` definisce `discount(subtotal)`, cioè lo sconto in centesimi.

**Implementa `total(subtotal, rule)`**: applica la regola ricevuta e sottrai il risultato dal subtotale.

**Non distinguere** le implementazioni con `if` o `instanceof` e **non istanziare regole** nel metodo.

I test aggiungono una regola nuova *senza cambiare* `Exercise`.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
public class Exercise {

    public interface DiscountRule {
        int discount(int subtotal);
    }

    public int total(int subtotal, DiscountRule rule) {
        // TODO: completa questo blocco.
        // Suggerimento: rule è già la strategia scelta: chiamane discount(subtotal).
        // Il valore ottenuto è lo sconto, non il totale finale.
        return 0;
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
public class Exercise {

    public interface DiscountRule {
        int discount(int subtotal);
    }

    public int total(int subtotal, DiscountRule rule) {
        return subtotal - rule.discount(subtotal);
    }
}
~~~

Vogliamo un calcolo del totale che accetti qualunque regola di sconto, anche una inventata dopo.

Il metodo `total` fa una sola cosa: `subtotal - rule.discount(subtotal)`. Non sa quale regola gli arriva, e non gli importa. Chiama il metodo dell'interfaccia `DiscountRule` e sottrae il risultato.

È il principio aperto/chiuso, la O di SOLID della lezione 31. Il calcolatore è aperto all'estensione: una regola nuova è un'implementazione nuova, anche una semplice lambda. Ed è chiuso alla modifica: per aggiungerla non riapriamo `Exercise`. Pensa all'alternativa con una catena di `if` o di `instanceof` sul tipo di regola. Ogni sconto nuovo, come il Black Friday, ci costringerebbe a modificare un metodo che funziona già, con il rischio di rompere i casi vecchi. Infatti il test `acceptsNewRuleWithoutChangingCalculator` passa una regola `s -> 250` che `Exercise` non ha mai visto, e si aspetta `750`.

L'errore più comune è restituire direttamente `rule.discount(subtotal)`. Ma quello è lo sconto, non il totale: con la regola del 20% il test `appliesPercentageRule` si aspetta `800` e riceverebbe `200`. Il test `supportsNoDiscount` controlla anche che una regola che restituisce `0` lasci il subtotale `1000` intatto.

Come dice la lezione, se i casi fossero pochi e stabili andrebbero bene anche un enum o una sealed interface con uno `switch`.

## Riepilogo

- Una catena di if che cresce obbliga a modificare
- Interfaccia, una classe per regola, calcolatore con la lista
- Casi chiusi: enum, sealed e switch
