# Lezione 1c. Java e IntelliJ IDEA su Windows

## Punti chiave

### Che cosa installiamo

- Lo stesso ambiente della lezione 1, su Windows 10 o 11 a 64 bit
- JDK: Eclipse Temurin 25 LTS, da adoptium.net
- IDE: IntelliJ IDEA, da jetbrains.com
- Le verifiche: in PowerShell

### Scaricare Temurin 25

- adoptium.net: Temurin 25 LTS, Windows, x64, pacchetto .msi
- Oppure in PowerShell: winget install EclipseAdoptium.Temurin.25.JDK
- Con winget l'installer attiva tutte le opzioni, JAVA_HOME compreso
- Cartella predefinita: C:\Program Files\Eclipse Adoptium

### Le opzioni dell'installer

- Custom Setup: Modify PATH variable è già attiva
- Set or override JAVA_HOME variable è spenta: attivatela
- Clic sull'icona, poi Will be installed on local hard drive
- Alla fine aprite una nuova finestra di PowerShell

### Verifica in PowerShell

- java -version: openjdk version "25...
- javac -version: javac 25...
- where.exe java: il primo percorso è quello usato
- $env:JAVA_HOME: la cartella di Temurin 25
- In PowerShell where da solo è un filtro: scrivete where.exe

### IntelliJ IDEA su Windows

- jetbrains.com/idea/download, scheda Windows, file .exe
- Opzioni: Create Desktop Shortcut, Add "bin" folder to the PATH
- Oppure: winget install JetBrains.IntelliJIDEA
- Al primo avvio parte in modalità gratuita, come su macOS

### Il JDK nel progetto

- Menu principale, File, Project Structure: Ctrl+Alt+Shift+S
- Project, SDK: il JDK 25 di Temurin
- Se non compare: Add JDK from Disk, cartella di Temurin
- Oppure Download JDK: versione 25, Eclipse Temurin

### Scorciatoie: macOS e Windows

- In generale Cmd diventa Ctrl: Cmd+S diventa Ctrl+S
- Nuovo file: Alt+Insert (su Mac Cmd+N)
- Esegui il file: Ctrl+Shift+F10; ripeti: Shift+F10 (su Mac Ctrl+R)
- Settings: Ctrl+Alt+S; vai alla riga: Ctrl+G
- Ricerca delle azioni: due volte Shift

### Il Maven wrapper su Windows

- Su macOS: ./mvnw test
- PowerShell: .\mvnw.cmd test
- Prompt dei comandi: mvnw.cmd test
- Primo avvio: scarica Maven in .m2\wrapper, nella cartella utente
- Trova Java con JAVA_HOME o con il PATH

## Codice della lezione

`README.md`

~~~markdown
# Lesson 1c: Java and IntelliJ IDEA on Windows

The same setup as lesson 1, on Windows 10 or 11 (64 bit).

## JDK: Eclipse Temurin 25 LTS

- Download from adoptium.net: Temurin 25, Windows, x64, `.msi` package.
- In the Custom Setup screen keep "Modify PATH variable" and turn on "Set or override JAVA_HOME variable"
  ("Will be installed on local hard drive"). Default folder: `C:\Program Files\Eclipse Adoptium`.
- Alternative: `winget install EclipseAdoptium.Temurin.25.JDK` (installs every feature, JAVA_HOME included).

## Check, in a NEW PowerShell window

```powershell
java -version
javac -version
where.exe java
$env:JAVA_HOME
```

In PowerShell `where` alone is an alias of `Where-Object`: use `where.exe`. The script
`verifica-ambiente.ps1` runs the same checks:
`powershell -ExecutionPolicy Bypass -File .\verifica-ambiente.ps1`.

## IntelliJ IDEA

- Download the Windows `.exe` from jetbrains.com/idea/download (alternative: `winget install JetBrains.IntelliJIDEA`).
- Installer options: "Create Desktop Shortcut", optionally "Add "bin" folder to the PATH" (restart needed).
- JDK of the project: File > Project Structure (Ctrl+Alt+Shift+S) > Project > SDK; "Add JDK from Disk" or "Download JDK".

## Shortcuts that change (macOS > Windows)

| Action | macOS | Windows |
| --- | --- | --- |
| Save | Cmd+S | Ctrl+S |
| New file | Cmd+N | Alt+Insert |
| Run the current file | Ctrl+R (in the course) | Ctrl+Shift+F10 (Shift+F10 reruns) |
| Settings | Cmd+, | Ctrl+Alt+S |
| Project Structure | Cmd+; | Ctrl+Alt+Shift+S |
| Go to line | Cmd+L | Ctrl+G |

## Maven wrapper

```powershell
.\mvnw.cmd test
```

In the Command Prompt: `mvnw.cmd test`. In Git Bash or WSL: `./mvnw test`, as on macOS.
~~~

`verifica-ambiente.ps1`

~~~powershell
# Java environment check for the course "Java da zero" (Windows, PowerShell).
# Run it in a NEW PowerShell window, after installing Eclipse Temurin 25:
#   powershell -ExecutionPolicy Bypass -File .\verifica-ambiente.ps1
# It only reads: it changes nothing on the computer.

Write-Host '--- java -version (expected: openjdk version "25...)'
java -version

Write-Host '--- javac -version (expected: javac 25...)'
javac -version

Write-Host '--- where.exe java (the first path is the java that runs)'
where.exe java

Write-Host "--- JAVA_HOME = $env:JAVA_HOME"
if ($env:JAVA_HOME -and (Test-Path (Join-Path $env:JAVA_HOME 'bin\javac.exe'))) {
    Write-Host 'JAVA_HOME points to a JDK: ok'
} else {
    Write-Host 'JAVA_HOME is missing or does not point to a JDK: set it in the Temurin installer'
}
~~~

## Riepilogo

- Temurin 25 da adoptium.net, con PATH e JAVA_HOME
- Verifica in un PowerShell nuovo: java, javac, where.exe
- IntelliJ IDEA: JDK in File, Project Structure, SDK
- Cmd diventa Ctrl, con poche eccezioni
- Maven wrapper: .\mvnw.cmd in PowerShell
