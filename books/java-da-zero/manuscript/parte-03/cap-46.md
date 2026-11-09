# Lezione 28b. Git per lavorare in team

## Punti chiave

### Tre zone, una storia

- Un commit è una fotografia del progetto: autore, messaggio, codice
- git add porta le modifiche nello stage
- git commit scatta la fotografia
- status, log --oneline e diff dicono dove siamo

> Percorso: cartella di lavoro, poi stage, poi repository.

### Branch e merge

- main resta stabile: le novità nascono su un branch
- git switch -c crea il branch e ci porta sopra
- git merge riporta la novità su main
- Stesso punto cambiato da due parti: conflitto

> Percorso: main, poi feature/free-shipping, poi merge su main.

### Il merge tool di IntelliJ

- La finestra Conflicts: Accept Yours, Accept Theirs, Resolve Manually
- Tre colonne: la nostra versione, il risultato, quella che arriva
- Il centro è un editor: frecce per i blocchi, poi Apply Changes
- A mano o con lo strumento: leggere le due versioni e decidere

### Pull request e code review

- push del branch sul remote, poi una pull request verso main
- I colleghi leggono il diff, commentano, approvano
- Un server di integrazione continua compila e lancia i test
- Il merge su main solo con review approvata e test verdi

> Percorso: branch, poi push, poi pull request, poi review, poi merge.

## Codice della lezione

Il progetto parte dal modello Maven del corso: questi sono il suo `pom.xml` e il wrapper.

`pom.xml`: uguale a quello della lezione 27.

`.mvn/wrapper/maven-wrapper.properties`: uguale a quello della lezione 27.

`README.md`

~~~markdown
# Shop
Price calculator of the shop, built with Maven.
Weekend sale: 20 percent off.
Free shipping from 50 euros.
Payments by card or cash.
~~~

`src/main/java/PriceCalculator.java`

~~~java
public class PriceCalculator {
    public static int total(int priceInCents, int quantity) {
        return priceInCents * quantity;
    }
    public static int applyDiscount(int amountInCents, int percent) {
        return amountInCents - amountInCents * percent / 100;
    }
    public static void main(String[] args) {
        int total = applyDiscount(total(1200, 3), 20);
        System.out.println("Total with discount: " + total + " cents");
    }
}
~~~

`start/README.md`

~~~markdown
# Shop
Price calculator of the shop, built with Maven.
~~~

Gli altri file del progetto sono uguali a quelli di una lezione precedente:

- `src/test/java/PriceCalculatorTest.java`: lezione 28
- `start/PriceCalculator.java`: lezione 28, file `src/main/java/PriceCalculator.java`

## Comandi della lezione

I comandi che scriviamo nel terminale durante il video, nell'ordine.

~~~bash
ls -a
git --version
git init -b main
git status
printf 'target/\n.idea/\n.env\n' > .gitignore
cat .gitignore
git add .
git commit -m "Add the Maven project of the shop"
git log --oneline
sed -i '' 's/, 10);/, 20);/' src/main/java/PriceCalculator.java
git diff
git commit -m "Raise the discount to 20 percent"
git switch -c feature/free-shipping
echo "Free shipping from 50 euros." >> README.md
git commit -m "Mention free shipping in the README"
git switch main
cat README.md
echo "Weekend sale: 20 percent off." >> README.md
git commit -m "Announce the weekend sale in the README"
git merge feature/free-shipping
cat -n README.md
sed -i '' '3d;5d;7d' README.md
git add README.md
git commit -m "Merge the free shipping branch"
git log --oneline --graph
git branch -d feature/free-shipping
ls ..
git remote add origin ../remote/shop.git
git remote -v
git push -u origin main
cd ..
git clone remote/shop.git teammate
cd teammate
echo "Payments by card or cash." >> README.md
git commit -m "Describe the payment methods"
git push
cd ../shop
git pull
~~~

## Riepilogo

- .gitignore: fuori build, impostazioni dell'IDE e segreti
- add e commit; status, log --oneline e diff per orientarsi
- Branch con switch -c, merge, conflitto risolto a mano
- Remote origin: push manda, pull riceve
- In squadra il merge passa da pull request e code review
