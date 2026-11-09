# Lezione 23. Date e orari con java.time

## Punti chiave

### Le classi di java.time

- LocalDate: solo la data, giorno, mese e anno
- LocalDateTime: data e ora, senza fuso orario
- ZonedDateTime: data, ora e fuso orario
- Period e Duration: quantità di tempo

> Percorso: LocalDate, poi LocalDateTime, poi ZonedDateTime.

### Perché non java.util.Date

- Modificabile: chi la riceve può cambiarla
- Piena di trappole: i mesi partono da 0
- Il nome inganna: è un istante, non una data
- java.time è immutabile: ogni operazione crea un oggetto nuovo

### Buone pratiche

- Scadenze e consegne: LocalDate
- Istanti reali: ZonedDateTime con ZoneId.of("Europe/Rome")
- Fusi con un nome, non scarti fissi: conoscono l'ora legale
- Niente now() nella logica: la data arriva come parametro

## Codice della lezione

`Main.java`, prima versione

~~~java
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
public class Main {
    public static void main(String[] args) {
        LocalDate placedOn = LocalDate.of(2026, 10, 28);
        Order order = new Order("A-17", placedOn);
        LocalDate delivery = order.deliveryDate();
        LocalDate deadline = order.paymentDeadline();
        var italian = DateTimeFormatter.ofPattern("dd/MM/yyyy");
        System.out.println("Delivery: " + delivery.format(italian));
        System.out.println("Day: " + delivery.getDayOfWeek());
        System.out.println("Pay by: " + deadline.format(italian));
        placedOn.plusDays(100);
        System.out.println("Placed: " + placedOn);
    }
}
~~~

`Main.java`

~~~java
import java.time.LocalDate;
import java.time.Period;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;
public class Main {
    public static void main(String[] args) {
        LocalDate placedOn = LocalDate.of(2026, 10, 28);
        Order order = new Order("A-17", placedOn);
        LocalDate delivery = order.deliveryDate();
        LocalDate deadline = order.paymentDeadline();
        var italian = DateTimeFormatter.ofPattern("dd/MM/yyyy");
        System.out.println("Delivery: " + delivery.format(italian));
        System.out.println("Day: " + delivery.getDayOfWeek());
        System.out.println("Pay by: " + deadline.format(italian));
        placedOn.plusDays(100);
        System.out.println("Placed: " + placedOn);
        LocalDate warrantyEnd = delivery.plusYears(2);
        Period warranty = Period.between(delivery, warrantyEnd);
        long days = ChronoUnit.DAYS.between(delivery, warrantyEnd);
        System.out.println("Warranty: " + warranty);
        System.out.println("Days: " + days);
    }
}
~~~

`Order.java`

~~~java
import java.time.LocalDate;
public record Order(String id, LocalDate placedOn) {
    public LocalDate paymentDeadline() {
        return placedOn.plusDays(14);
    }
    public LocalDate deliveryDate() {
        LocalDate date = placedOn.plusDays(3);
        return switch (date.getDayOfWeek()) {
            case SATURDAY -> date.plusDays(2);
            case SUNDAY -> date.plusDays(1);
            default -> date;
        };
    }
}
~~~

`ShippingTimes.java`

~~~java
import java.time.Duration;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
public class ShippingTimes {
    public static void main(String[] args) {
        var pickedUp = LocalDateTime.of(2026, 10, 24, 22, 0);
        var delivered = LocalDateTime.of(2026, 10, 25, 10, 0);
        Duration local = Duration.between(pickedUp, delivered);
        System.out.println("Local: " + local.toHours() + " hours");
        ZoneId rome = ZoneId.of("Europe/Rome");
        ZonedDateTime start = pickedUp.atZone(rome);
        ZonedDateTime end = delivered.atZone(rome);
        Duration zoned = Duration.between(start, end);
        System.out.println("Zoned: " + zoned.toHours() + " hours");
        System.out.println("From " + start);
        System.out.println("To " + end);
    }
}
~~~

## Esercizio 23: date senza dipendere da oggi

Obiettivo: Calcolare durate deterministiche e trattare correttamente i fusi orari.

1. **Implementa `overdueDays(dueDate, today)`**: giorni fra scadenza e oggi, *senza risultati negativi*.
2. **Implementa `elapsedMinutes(start, end)`**: minuti realmente trascorsi fra due `ZonedDateTime`.

`toMinutes()` sulla durata è come `toHours()` ma restituisce i minuti totali.

Usa **`Duration.between`** direttamente sui due `ZonedDateTime`: tiene conto del cambio dell’ora.

Le date non sono `null` e `end` non precede `start`.

Parti da questo codice. Completa i blocchi TODO e lascia com'è il resto: nomi, firme e tipi sono quelli che i test di Udemy si aspettano.

`Exercise.java`, codice di partenza

~~~java
import java.time.*;
import java.time.temporal.ChronoUnit;

public class Exercise {

    public long overdueDays(LocalDate dueDate, LocalDate today) {
        // TODO: completa questo blocco.
        // Suggerimento: ChronoUnit.DAYS.between misura la distanza dalla scadenza a oggi.
        // Salva il risultato in una variabile long: con un if, se è negativo restituisci zero.
        return 0;
    }

    public long elapsedMinutes(ZonedDateTime start, ZonedDateTime end) {
        // TODO: completa questo blocco.
        // Suggerimento: Duration.between accetta direttamente i due ZonedDateTime e conta il tempo realmente trascorso.
        // Poi chiama toMinutes() sulla durata: come toHours(), ma restituisce i minuti totali.
        return 0;
    }
}
~~~

### Soluzione

Prova da solo prima di leggere: anche un tentativo sbagliato ti insegna qualcosa.

`Exercise.java`, soluzione

~~~java
import java.time.*;
import java.time.temporal.ChronoUnit;

public class Exercise {

    public long overdueDays(LocalDate dueDate, LocalDate today) {
        long days = ChronoUnit.DAYS.between(dueDate, today);
        if (days < 0) return 0;
        return days;
    }

    public long elapsedMinutes(ZonedDateTime start, ZonedDateTime end) {
        return Duration.between(start, end).toMinutes();
    }
}
~~~

Dobbiamo calcolare due durate usando solo le date ricevute, senza mai chiedere al sistema che giorno è.

In `overdueDays` usiamo `ChronoUnit.DAYS.between(dueDate, today)`, che conta i giorni dalla scadenza a oggi. Come abbiamo visto nella lezione 23, `LocalDate` è la classe giusta per le scadenze, e il calcolo conosce il calendario: dal 28 febbraio al 1 marzo 2024 passano 2 giorni, perché il 2024 è bisestile. Se la scadenza è nel futuro il risultato è negativo. Lo salviamo in una variabile `long` e, con `if (days < 0) return 0;`, lo portiamo a zero. Altrimenti restituiamo `days`.

In `elapsedMinutes` misuriamo con `Duration.between(start, end).toMinutes()`, passando direttamente i due `ZonedDateTime`, come nella lezione. Un valore con fuso orario individua un punto preciso sulla linea del tempo, quindi la durata conta il tempo realmente trascorso. Il motivo è l'ora legale. Il 29 marzo 2026, a Roma, gli orologi saltano dalle 2:00 alle 3:00. Fra le 1:30 e le 3:30 l'orologio mostra due ore di differenza, ma ne passa una sola.

Il test `handlesDaylightSavingTime` controlla proprio questo e si aspetta `60` minuti. Un errore tipico è confrontare solo gli orari dell'orologio, per esempio passando da `toLocalDateTime()`: otterresti 120. L'altro è dimenticare il limite a zero: `calculatesDaysWithoutWallClock` ha la scadenza il 5 marzo e oggi il 4, e si aspetta `0`, non `-1`. `countsDaysAcrossMonths` va dal 31 gennaio al 1 marzo e vuole 29, il che esclude `until(...).getDays()`. `countsMinutesNotWholeHours` vuole 90 minuti, non un'ora.

## Riepilogo

- LocalDate, LocalDateTime, ZonedDateTime
- Tutto immutabile: plusDays restituisce una data nuova
- Period, ChronoUnit.DAYS e Duration; DateTimeFormatter per il formato
