#!/usr/bin/env python3
"""Translate the prose in code-block COMMENTS of the IT/ES editions.

Code is byte-identical across languages; only comment lines are touched. Each
line is matched by its whitespace-normalized text and rebuilt from the real
file line, so indentation, code, and the comment marker stay byte-exact — only
the human-language prose after the marker changes. Type annotations (@param,
@var), elision markers (// ...), the Dockerfile `# syntax=` directive, and
.gitignore globs are deliberately NOT in the table below.

Usage: translate_comments.py it|es
"""
import sys, re, glob

lang = sys.argv[1]
assert lang in ("it", "es")

# (english prose comment — single-spaced, without leading indent, it, es)
# The tuple's first field is normalized (collapse whitespace) for matching.
ENTRIES = [
 ("// subsequent values for the same header name must append",
  "// i valori successivi con lo stesso nome di header vanno aggiunti in coda",
  "// los valores siguientes con el mismo nombre de cabecera se añaden al final"),
 ("// <-- read that again", "// <-- rileggilo bene", "// <-- léelo otra vez"),
 ("// <-- wait, what?", "// <-- aspetta, cosa?", "// <-- espera, ¿qué?"),
 ("// copy-paste artifact: posts have no email",
  "// artefatto da copia-incolla: i post non hanno email",
  "// artefacto de copiar y pegar: los posts no tienen email"),
 ("// ... consult the cache, else delegate to $this->inner->all() ...",
  "// ... consulta la cache, altrimenti delega a $this->inner->all() ...",
  "// ... consulta la caché, si no delega en $this->inner->all() ..."),
 ("// ... delete(), clear(), has(), and the multi-key methods",
  "// ... delete(), clear(), has() e i metodi multi-chiave",
  "// ... delete(), clear(), has() y los métodos multiclave"),
 ("// Forgot: $this->id = (int) $this->conn->lastInsertId();",
  "// Dimenticato: $this->id = (int) $this->conn->lastInsertId();",
  "// Olvidado: $this->id = (int) $this->conn->lastInsertId();"),
 ("// Hard-enforce: security attributes are non-negotiable, no matter what the caller passes.",
  "// Imposizione forzata: gli attributi di sicurezza non sono negoziabili, qualunque cosa passi il chiamante.",
  "// Imposición estricta: los atributos de seguridad no son negociables, sin importar lo que pase el llamador."),
 ("// implemented the same way over $store ...",
  "// implementati allo stesso modo su $store ...",
  "// implementados de la misma forma sobre $store ..."),
 ("// Redis TTL handles expiry", "// il TTL di Redis gestisce la scadenza",
  "// el TTL de Redis gestiona la expiración"),
 ("// N queries", "// N query", "// N consultas"),
 ("// ... methods that actually use $this->conn ...",
  "// ... metodi che usano effettivamente $this->conn ...",
  "// ... métodos que realmente usan $this->conn ..."),
 ("// ... private methods shown below",
  "// ... metodi privati mostrati sotto", "// ... métodos privados mostrados abajo"),
 ("// ... verifySignup() and createUser() shown below ...",
  "// ... verifySignup() e createUser() mostrati sotto ...",
  "// ... verifySignup() y createUser() mostrados abajo ..."),
 ("// ... write methods shown below ...",
  "// ... metodi di scrittura mostrati sotto ...",
  "// ... métodos de escritura mostrados abajo ..."),
 ("// ...second test elided: it passes ATTR_EMULATE_PREPARES => true the same",
  "// ...secondo test omesso: passa ATTR_EMULATE_PREPARES => true nello stesso",
  "// ...segundo test omitido: pasa ATTR_EMULATE_PREPARES => true del mismo"),
 ("// deleteMultiple(), and has() delegate the same way ...",
  "// deleteMultiple() e has() delegano allo stesso modo ...",
  "// deleteMultiple() y has() delegan de la misma forma ..."),
 ("// way and verifies construction still yields a valid, hardened connection.",
  "// modo e verifica che la costruzione restituisca comunque una connessione valida e rinforzata.",
  "// modo y verifica que la construcción siga produciendo una conexión válida y reforzada."),
 ("// fatal error at runtime when findById returns null",
  "// errore fatale a runtime quando findById restituisce null",
  "// error fatal en tiempo de ejecución cuando findById devuelve null"),
 ("// regression: not the email field", "// regressione: non il campo email",
  "// regresión: no el campo email"),
 ("// 1 query", "// 1 query", "// 1 consulta"),
 ("// A bcrypt hash string, annotated:", "// Una stringa hash bcrypt, annotata:",
  "// Una cadena hash bcrypt, anotada:"),
 ("// A naive implementation — do not do this.",
  "// Un'implementazione ingenua — non farlo.", "// Una implementación ingenua — no hagas esto."),
 ("// DDL statements (CREATE TABLE, etc.) trigger an implicit commit in MySQL,",
  "// Le istruzioni DDL (CREATE TABLE, ecc.) provocano un commit implicito in MySQL,",
  "// Las sentencias DDL (CREATE TABLE, etc.) provocan un commit implícito en MySQL,"),
 ("// Global helpers — kept thin. Most logic lives in App\\Support typed classes.",
  "// Helper globali — mantenuti minimali. Quasi tutta la logica vive nelle classi tipizzate App\\Support.",
  "// Helpers globales — mantenidos ligeros. Casi toda la lógica vive en las clases tipadas App\\Support."),
 ('// Naive "health" endpoint: proves only that PHP can print a string.',
  '// Endpoint "health" ingenuo: dimostra solo che PHP sa stampare una stringa.',
  '// Endpoint "health" ingenuo: solo demuestra que PHP puede imprimir una cadena.'),
 ("// Naive controller — do not do this.",
  "// Controller ingenuo — non farlo.", "// Controlador ingenuo — no hagas esto."),
 ("// Naive counter-example — a user model as found in the wild.",
  "// Controesempio ingenuo — un modello utente come si trova in giro.",
  "// Contraejemplo ingenuo — un modelo de usuario como se ve en la práctica."),
 ("// Naive counter-example — do not write this.",
  "// Controesempio ingenuo — non scriverlo.",
  "// Contraejemplo ingenuo — no escribas esto."),
 ("// Naive counter-example — the N+1 pattern.",
  "// Controesempio ingenuo — il pattern N+1.",
  "// Contraejemplo ingenuo — el patrón N+1."),
 ("// Naive counter-example — the branching save().",
  "// Controesempio ingenuo — il save() pieno di diramazioni.",
  "// Contraejemplo ingenuo — el save() lleno de ramificaciones."),
 ("// Naive counter-example — the do-everything login controller.",
  "// Controesempio ingenuo — il controller di login che fa tutto.",
  "// Contraejemplo ingenuo — el controlador de login que lo hace todo."),
 ("// Naive helpers — do not do this.",
  "// Helper ingenui — non farlo.", "// Helpers ingenuos — no hagas esto."),
 ("// Naive implementation — for discussion, not for the repository.",
  "// Implementazione ingenua — per discussione, non per il repository.",
  "// Implementación ingenua — para la discusión, no para el repositorio."),
 ("// Naive preload: compiles files without resolving their dependencies.",
  "// Preload ingenuo: compila i file senza risolverne le dipendenze.",
  "// Preload ingenuo: compila los archivos sin resolver sus dependencias."),
 ("// Naive service-locator style — do not do this.",
  "// Stile service-locator ingenuo — non farlo.",
  "// Estilo service-locator ingenuo — no hagas esto."),
 ("// Naive: nothing stops the null case until production does.",
  "// Ingenuo: nulla ferma il caso null finché non lo fa la produzione.",
  "// Ingenuo: nada detiene el caso null hasta que lo hace producción."),
 ("// Naive: what does this accept? What does it return? Nobody knows.",
  "// Ingenuo: cosa accetta? Cosa restituisce? Nessuno lo sa.",
  "// Ingenuo: ¿qué acepta? ¿qué devuelve? Nadie lo sabe."),
 ("// PSR-16 reserves the characters {}()/\\@: in keys, so the segments are dot-separated.",
  "// PSR-16 riserva i caratteri {}()/\\@: nelle chiavi, quindi i segmenti sono separati da punti.",
  "// PSR-16 reserva los caracteres {}()/\\@: en las claves, por eso los segmentos se separan con puntos."),
 ("// Preload application classes through Composer's authoritative classmap so that",
  "// Precarica le classi dell'applicazione tramite la classmap autoritativa di Composer così che",
  "// Precarga las clases de la aplicación mediante la classmap autoritativa de Composer para que"),
 ("// Simplified mental model of the two render passes",
  "// Modello mentale semplificato dei due passaggi di rendering",
  "// Modelo mental simplificado de las dos pasadas de renderizado"),
 ("// The textbook shape — composition against an interface.",
  "// La forma da manuale — composizione contro un'interfaccia.",
  "// La forma de manual — composición contra una interfaz."),
 ("// each class is loaded *with* its dependencies (e.g. vendor PSR interfaces)",
  "// ogni classe è caricata *con* le sue dipendenze (es. le interfacce PSR di vendor)",
  "// cada clase se carga *con* sus dependencias (p. ej. las interfaces PSR de vendor)"),
 ("// inTransaction() so a DDL migration doesn't blow up on a missing transaction.",
  "// inTransaction() così una migrazione DDL non esplode per una transazione mancante.",
  "// inTransaction() para que una migración DDL no reviente por una transacción ausente."),
 ('// opcache_compile_file() avoids "Can\'t preload unlinked class" warnings.',
  '// opcache_compile_file() evita gli avvisi "Can\'t preload unlinked class".',
  '// opcache_compile_file() evita las advertencias "Can\'t preload unlinked class".'),
 ("// resolved in the correct order. Using the autoloader instead of bare",
  "// risolte nell'ordine corretto. Usare l'autoloader invece del semplice",
  "// resueltas en el orden correcto. Usar el autoloader en vez del simple"),
 ("// update() and delete() call parent, then $this->invalidate($id), the same way.",
  "// update() e delete() chiamano parent, poi $this->invalidate($id), allo stesso modo.",
  "// update() y delete() llaman a parent, luego $this->invalidate($id), de la misma forma."),
 ("// which ends the transaction begun here. Guard commit/rollBack with",
  "// che termina la transazione iniziata qui. Proteggi commit/rollBack con",
  "// que termina la transacción iniciada aquí. Protege commit/rollBack con"),
 # ---- Twig / HTML ----
 ("<!-- comment date and author email, escaped the same way -->",
  "<!-- data del commento ed email dell'autore, con escape allo stesso modo -->",
  "<!-- fecha del comentario y email del autor, con escape de la misma forma -->"),
 ("<!-- EDIT (GET form) and DELETE (POST form) buttons -->",
  "<!-- pulsanti EDIT (form GET) e DELETE (form POST) -->",
  "<!-- botones EDIT (formulario GET) y DELETE (formulario POST) -->"),
 ("<!-- Naive counter-example — an attacker's page, not ours. -->",
  "<!-- Controesempio ingenuo — la pagina di un attaccante, non la nostra. -->",
  "<!-- Contraejemplo ingenuo — la página de un atacante, no la nuestra. -->"),
 # ---- bash trailing ----
 ("# cache lookups in shared memory", "# lookup della cache in memoria condivisa",
  "# búsquedas de caché en memoria compartida"),
 ("# level 2: classmap misses fail immediately",
  "# livello 2: i miss nella classmap falliscono subito",
  "# nivel 2: los fallos de classmap fallan de inmediato"),
 ("# level 1: scan PSR-4 dirs into a classmap",
  "# livello 1: scansiona le directory PSR-4 in una classmap",
  "# nivel 1: escanea los directorios PSR-4 en una classmap"),
 ("# container engine functional", "# motore dei container funzionante",
  "# motor de contenedores funcional"),
 ("# the code at the end of Chapter 7", "# il codice alla fine del Capitolo 7",
  "# el código al final del Capítulo 7"),
 ("# back to the completed application", "# torna all'applicazione completata",
  "# vuelve a la aplicación completada"),
 ("# the full change", "# l'intera modifica", "# el cambio completo"),
 ("# files touched, at a glance", "# file toccati, a colpo d'occhio",
  "# archivos tocados, de un vistazo"),
 ("# PDO present for database work", "# PDO presente per il lavoro con il database",
  "# PDO presente para el trabajo con la base de datos"),
 # ---- dockerfile ----
 ("# ---- stage 1: composer ----", "# ---- fase 1: composer ----",
  "# ---- etapa 1: composer ----"),
 ("# ---- stage 2: runtime ----", "# ---- fase 2: runtime ----",
  "# ---- etapa 2: runtime ----"),
 ("# composer is needed in-container for the Makefile dev targets (make ci/test/stan/cs)",
  "# composer serve nel container per i target di sviluppo del Makefile (make ci/test/stan/cs)",
  "# composer es necesario en el contenedor para los targets de desarrollo del Makefile (make ci/test/stan/cs)"),
 ("# intl and redis need to be added.", "# intl e redis vanno aggiunti.",
  "# intl y redis deben añadirse."),
 ("# opcache and mbstring are already bundled in this base image; only pdo_mysql,",
  "# opcache e mbstring sono già inclusi in questa immagine base; solo pdo_mysql,",
  "# opcache y mbstring ya vienen incluidos en esta imagen base; solo pdo_mysql,"),
 # ---- TypeScript / Playwright ----
 ("// ...create a post, then:", "// ...crea un post, poi:", "// ...crea un post, luego:"),
 ("// Safety net: if the jQuery AJAX handler ever loads, it pops an alert.",
  "// Rete di sicurezza: se l'handler AJAX di jQuery viene caricato, mostra un alert.",
  "// Red de seguridad: si el handler AJAX de jQuery llega a cargarse, muestra un alert."),
 ('// Scope to <main> so we match a real post link, not the navbar "New post" (/posts/create).',
  '// Limita a <main> così intercettiamo un vero link a un post, non il "New post" della navbar (/posts/create).',
  '// Acota a <main> para que coincida un enlace real a un post, no el "New post" de la navbar (/posts/create).'),
 ("// Successful signup logs in and redirects home; the LOGOUT button proves the session.",
  "// Una registrazione riuscita effettua il login e reindirizza alla home; il pulsante LOGOUT prova la sessione.",
  "// Un registro correcto inicia sesión y redirige al inicio; el botón LOGOUT prueba la sesión."),
 ("// First draft — same caveat.", "// Prima bozza — stessa avvertenza.",
  "// Primer borrador — misma advertencia."),
 ("// First draft — written from memory, not from the page. It will not survive.",
  "// Prima bozza — scritta a memoria, non dalla pagina. Non sopravviverà.",
  "// Primer borrador — escrito de memoria, no desde la página. No sobrevivirá."),
 # ---- yaml (Helm) ----
 ("# set IRSA role ARN at install time via values.<env>.yaml",
  "# imposta l'ARN del ruolo IRSA all'installazione tramite values.<env>.yaml",
  "# define el ARN del rol IRSA en la instalación mediante values.<env>.yaml"),
 ("# overridden by --set in CI", "# sovrascritto con --set nella CI",
  "# sobrescritto con --set en la CI"),
]


def norm(s):
    return re.sub(r"\s+", " ", s.strip())


# map normalized-english -> translated prose (with marker, minus outer spacing)
tri = {norm(en): (it if lang == "it" else es) for (en, it, es) in ENTRIES}


def find_match(line):
    """Locate the comment marker whose comment text is a known key. Compares
    the portion from the marker onward, so trailing comments match and `//`
    inside a string is ignored (its text won't be in the table)."""
    for mk in ("<!--", "//", "#"):
        i = line.find(mk)
        if i != -1:
            key = norm(line[i:])
            if key in tri:
                return i, mk, tri[key]
    return None


def rebuild(line, i, mk, translated):
    """Keep line's real prefix (indent + code + marker); swap the prose."""
    if mk == "<!--":
        b = translated[translated.index("<!--") + 4:].strip()
        if b.endswith("-->"):
            b = b[:-3].strip()
        return line[:i] + "<!-- " + b + " -->"
    prose = translated[translated.index(mk) + len(mk):].strip()
    return line[:i] + mk + " " + prose


target = "book-it" if lang == "it" else "book-es"
total, per_file, seen = 0, {}, set()
for f in sorted(glob.glob(f"{target}/*.md")):
    lines = open(f, encoding="utf-8").read().split("\n")
    infence, changed = False, 0
    for idx, line in enumerate(lines):
        if re.match(r"^```", line):
            infence = not infence
            continue
        if infence:
            m = find_match(line)
            if m:
                i, mk, tr = m
                lines[idx] = rebuild(line, i, mk, tr)
                changed += 1
                seen.add(norm(line[i:]))
    if changed:
        open(f, "w", encoding="utf-8").write("\n".join(lines))
        per_file[f] = changed
        total += changed

print(f"{lang}: {total} comment lines translated across {len(per_file)} files")
missing = [k for k in tri if k not in seen]
if missing:
    print(f"WARNING: {len(missing)} table entries matched nothing:")
    for m in missing:
        print("   -", m[:80])
