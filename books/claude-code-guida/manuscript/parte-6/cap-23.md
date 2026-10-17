# Capitolo 23. Deploy su AWS con CloudFormation

Cosa imparerai: come progettare con Claude un'infrastruttura AWS per Photogallery (ECS Fargate, RDS, S3, SQS, CloudFront), come generare e revisionare il template CloudFormation, come portare in produzione backend Laravel e frontend React senza mettere segreti nell'immagine, e cosa controllare quando il primo deploy va storto.

Prerequisiti: un account AWS con la AWS CLI configurata (`aws configure`) e Docker in locale. Un dominio è utile ma non obbligatorio.

Photogallery a questo punto è finita e revisionata: le wave sono chiuse, le fix della review del capitolo 22 sono committate, i test passano. In `docs/TASKS.md` resta aperta la Phase 8, "AWS migration" (`T086`, `T087`, `T088`). Il codice però è pronto: `DESIGN.md` §12.5 dice che in produzione cambiano solo le variabili d'ambiente, con SQS al posto della coda su database e due bucket S3 al posto del disco locale. Questo capitolo costruisce l'infrastruttura che quelle variabili si aspettano.

<!-- VERIFY: BOOK-COMPANION.md segna il branch `book/cap-16-aws-deploy` come "in arrivo". Se viene pubblicato prima dell'uscita del libro, citarlo qui e allineare template e comandi ai file reali (infra/, Dockerfile, entrypoint). -->

Il workflow è quello dei capitoli precedenti: Claude genera, tu leggi, ogni passo si chiude con una verifica vera, qui un health check che risponde 200. La differenza è che questi comandi creano risorse che costano soldi, e più avanti decidiamo chi li lancia.

## 23.1 Architettura AWS per Photogallery

Ho aperto la sessione nella root del repo e ho chiesto a Claude di preparare il deploy su AWS. Prima di scrivere qualsiasi file ha letto il progetto, ha notato che non esisteva ancora nessuna configurazione di deploy e mi ha fatto delle domande: quale approccio preferivo, se avevo già risorse nell'account (VPC, RDS, bucket), quanto ero disposto a spendere al mese.

![Claude propone quattro strategie di deploy su AWS: ECS Fargate, Elastic Beanstalk, EC2 con script di deploy, Laravel Forge o Vapor](figures/cap-23/fig-01.png)

Le quattro opzioni erano ECS Fargate con CloudFormation, Elastic Beanstalk, EC2 con script di deploy e le piattaforme Laravel (Forge, Vapor). Tutte reggono un'app come questa. Ho scelto ECS Fargate per due motivi concreti. Il primo: la stessa immagine Docker fa girare sia l'API sia il worker che elabora le foto, cambiando solo il comando di avvio. Il secondo: l'infrastruttura sta in un file YAML nel repo, versionata e revisionabile come il resto del codice, ed è il tipo di file che Claude scrive bene e tu puoi leggere in una PR.

### I componenti

| Componente | Cosa fa per Photogallery |
| :---- | :---- |
| ECS Fargate | Due servizi dalla stessa immagine: `api` (Laravel e Filament dietro l'ALB) e `worker` (`queue:work` su SQS). Niente EC2 da gestire, paghi il tempo in cui i container girano. |
| RDS MariaDB | Il database, in subnet private, raggiungibile solo dai task ECS. Backup giornalieri automatici. MariaDB perché è lo stesso motore che usi in locale con Sail. |
| SQS | La coda dei job `ProcessPhoto` (resize e EXIF), con una dead letter queue. |
| S3 | Tre bucket: originali privati (Block Public Access attivo, solo URL firmati da 5 minuti), varianti pubbliche servite via CDN, file statici del frontend. |
| CloudFront | Serve la SPA React e le varianti delle foto via HTTPS dalle edge location, e inoltra `/api/*` all'ALB. |
| ALB | Riceve le richieste per l'API e per `/admin`, le distribuisce ai task e controlla `/api/v1/health`. |
| Route 53 e ACM | DNS del dominio e certificati TLS gratuiti con rinnovo automatico. |
| Secrets Manager | Password del database e `APP_KEY` di Laravel, iniettati nel container all'avvio. |
| CloudWatch | Log dei container, metriche di ECS, RDS, ALB e SQS, allarmi. |

La separazione tra bucket privato e pubblico arriva da `DESIGN.md` §12.1: il disco `photos_private` contiene solo gli originali, il disco `photos` solo le varianti ridimensionate, che escono dal resize senza dati EXIF. Un originale non ha mai un URL pubblico.

### La topologia di rete

La VPC ha quattro subnet in due availability zone. Nelle due subnet pubbliche vive l'ALB, con accesso a internet tramite Internet Gateway. Nelle due private vivono i task Fargate e l'istanza RDS, senza accesso diretto da fuori. Per le chiamate in uscita (il pull dell'immagine da ECR, le chiamate a S3, SQS e Secrets Manager) i task passano da un NAT Gateway nella subnet pubblica. Così il database risponde solo ai container dell'app. È la stessa struttura che ritrovi in quasi tutti i progetti AWS.

### Costo stimato

Con un traffico piccolo, diciamo mille utenti attivi al mese e 100 GB di foto, in `eu-west-1` (Irlanda) l'ordine di grandezza è questo:

<!-- VERIFY: prezzi AWS eu-west-1 di ottobre 2026 (Fargate, RDS db.t4g.micro, ALB, NAT Gateway, free tier CloudFront). Le cifre sono stime arrotondate. -->

| Componente | Stima al mese (USD) |
| :---- | :---- |
| ECS Fargate (2 task da 0,25 vCPU e 0,5 GB) | ~18 |
| RDS MariaDB db.t4g.micro e 20 GB di storage | ~15 |
| ALB | ~20 |
| NAT Gateway | ~35 |
| S3 (100 GB e richieste) | ~4 |
| CloudFront (100 GB di traffico) | 0-9 |
| Route 53, ACM, Secrets Manager | ~2 |
| CloudWatch Logs e metriche di base | ~5 |
| Totale | circa 100 |

Il NAT Gateway è la voce che sorprende: da solo costa più di un terzo del totale, fisso, più una quota per ogni GB che lo attraversa. In un ambiente di prova puoi farne a meno mettendo i task Fargate nelle subnet pubbliche con un IP pubblico assegnato. È meno sicuro, ma per sperimentare risparmi parecchio. In produzione tienilo.

## 23.2 Il template CloudFormation generato con Claude

CloudFormation è l'Infrastructure as Code nativo di AWS: descrivi le risorse in YAML, AWS le crea, le aggiorna o le elimina nell'ordine giusto risolvendo le dipendenze tra loro. Il template di Photogallery supera facilmente le 500 righe. Scriverlo a mano da zero è un lavoro lungo e noioso, ed è esattamente il genere di cosa da delegare, a patto di rileggerlo.

### Il prompt

Dopo aver risposto alle domande della figura precedente, ho dato a Claude le specifiche dell'infrastruttura:

```text
Genera un template CloudFormation YAML per il deploy di Photogallery su AWS.
Leggi docs/DESIGN.md (§12.5 env switching, §12.6 workers) e backend/config/
per i nomi delle variabili d'ambiente. Il template deve includere:

- VPC con 2 subnet pubbliche e 2 private (eu-west-1a, eu-west-1b)
- RDS MariaDB su subnet private (db.t4g.micro in staging, db.t4g.small in production), cifrato
- Cluster ECS Fargate con 2 servizi dalla stessa immagine: api e worker
- ECR repository per l'immagine Docker del backend
- Application Load Balancer su subnet pubbliche, listener HTTPS, health check su /api/v1/health
- Coda SQS photogallery-pro per i job ProcessPhoto
- 3 bucket S3: originali privati, varianti pubbliche, frontend
- CloudFront per la SPA (con routing SPA), le varianti delle foto e /api/* verso l'ALB
- Secrets Manager per la password del DB e l'APP_KEY di Laravel
- CloudWatch log group per api e worker
- Security group con least privilege

Parameters: Environment (staging/production), DBPassword (NoEcho), AppKey (NoEcho).
Conditions: IsProd per le istanze più grandi.
Outputs: ALBDnsName, CloudFrontDomainName, CloudFrontDistributionId,
EcrRepositoryUri, FrontendBucketName.

Output: un solo file, infra/cloudformation.yaml. Commenta le scelte non ovvie.
```

Claude ha scritto `infra/cloudformation.yaml` con tutte le risorse, i riferimenti incrociati tramite `!Ref` e `!GetAtt` e i tag per ambiente. L'inizio del file:

```yaml
AWSTemplateFormatVersion: "2010-09-09"
Description: PhotoGallery Pro - ECS Fargate + RDS MariaDB + S3 + SQS + CloudFront

Parameters:
  Environment:
    Type: String
    Default: production
    AllowedValues: [production, staging]

  DBPassword:
    Type: String
    NoEcho: true
    MinLength: 12
    Description: DB master password (min 12 chars)

  AppKey:
    Type: String
    NoEcho: true
    Description: Laravel APP_KEY (base64:...)
```

![Il template CloudFormation parametrizzato: Environment, DBPassword e AppKey](figures/cap-23/fig-02.png)

Nel file reale c'è anche un quarto parametro `NoEcho`, la password dell'utente admin di Filament, che `AdminUserSeeder` legge da `ADMIN_PASSWORD`. `NoEcho: true` fa sì che il valore non compaia nella console di CloudFormation né nell'output di `describe-stacks`.

<!-- VERIFY: nome esatto del quarto parametro nella figura 2 (illeggibile a questa risoluzione; probabilmente AdminPassword). -->

### Cosa rivedere nel template

Prima del deploy, una ventina di minuti di lettura. Non serve capire ogni riga, ma alcune cose vanno controllate a una a una.

1. Che ci siano tutti i componenti. Scorri `Resources` e spunta VPC, subnet, security group, RDS, cluster, i due servizi, ECR, ALB, SQS, i tre bucket, CloudFront, i secret. Un componente mancante lo scopri al deploy, se va bene.
2. I security group. Quello di RDS deve accettare la porta 3306 solo dal security group dei task ECS, mai da `0.0.0.0/0`. Claude di solito li scrive giusti, ma è il punto dove un errore costa di più.
3. Le policy IAM. Ci sono due ruoli e vanno tenuti distinti. La execution role serve a ECS per avviare il container: pull da ECR, lettura dei secret, scrittura dei log. La task role è quella che usa Laravel a runtime: lettura e scrittura sui due bucket delle foto, invio e ricezione su SQS. Nessuno dei due deve avere `"*"` come risorsa. Controlla i `PolicyDocument` nelle risorse `AWS::IAM::Role`.
4. Il visibility timeout della coda. Il worker gira con `--timeout=180` (DESIGN.md §12.6): se la coda SQS ha il visibility timeout di default, 30 secondi, un job lungo torna visibile mentre è ancora in lavorazione e un secondo worker lo riprende. Il valore deve superare i 180 secondi.
5. I nomi. Uno schema coerente come `photogallery-staging-api-sg`, `photogallery-staging-db` rende leggibile la console. Verifica che tutte le risorse lo seguano.

### Iterare sul template

Il primo template non è mai completo. Nel mio mancava il NAT Gateway, e i task nelle subnet private non riuscivano a scaricare l'immagine:

```text
Il template non ha il NAT Gateway per le subnet private. I task Fargate nelle
subnet private ne hanno bisogno per fare il pull dell'immagine da ECR. Aggiungi:
- un NAT Gateway nella subnet pubblica 1a, con Elastic IP
- una route table per le subnet private con la default route verso il NAT Gateway
```

Poi la dead letter queue:

```text
Aggiungi una dead letter queue SQS alla coda photogallery-pro, con retention
di 14 giorni e maxReceiveCount 3, allineato a --tries=3 del worker.
```

I fallimenti normali dei job li gestisce già Laravel: dopo tre tentativi il job finisce in `failed_jobs` e lo vedi nel widget `QueueMonitor` di Filament. Nella DLQ arrivano i messaggi che il worker non è riuscito nemmeno a chiudere, per esempio perché il container è stato ucciso per memoria a metà di un resize. Dopo tre o quattro giri come questi il template è completo.

### Il primo deploy

Prima di lanciare il comando, una precisazione su chi lo lancia.

::: {.callout .callout-warning}
[Attenzione]{.callout-title}

In auto mode il classificatore blocca i deploy in produzione: è uno dei casi previsti (capitolo 11). Su uno stack di staging potrebbe invece lasciar passare il comando, e non vuoi dipendere da questa valutazione. Scrivi una regola esplicita nel `.claude/settings.json` del progetto:

```json
{
  "permissions": {
    "ask": [
      "Bash(aws cloudformation deploy *)",
      "Bash(aws cloudformation execute-change-set *)",
      "Bash(aws cloudformation delete-stack *)",
      "Bash(aws ecs update-service *)"
    ],
    "allow": [
      "Bash(aws cloudformation describe-stack-events *)",
      "Bash(aws cloudformation describe-change-set *)"
    ]
  }
}
```

Le regole `ask` valgono anche in auto mode e vengono prima del classificatore, quindi ogni deploy ti chiede conferma; i comandi di sola lettura che servono per il debug passano senza interruzioni. Ricorda che una regola Bash confronta il testo del comando: `aws --region eu-west-1 cloudformation deploy` non corrisponde al pattern. L'alternativa più semplice è lanciare tu i comandi di deploy nel tuo terminale e incollare a Claude solo l'output o l'errore. Le azioni bloccate dal classificatore le ritrovi in `/permissions`, scheda Recently denied.
:::

C'è anche la questione dei segreti. Se scrivi la password del database nel prompt, o se la fai generare a Claude dentro il comando, finisce nella conversazione e nella cronologia della shell. Preparala tu, nel tuo terminale:

```bash
read -rs DB_PASSWORD
APP_KEY=$(cd backend && php artisan key:generate --show)

aws cloudformation deploy \
  --stack-name photogallery-staging \
  --template-file infra/cloudformation.yaml \
  --parameter-overrides \
    Environment=staging \
    DBPassword="$DB_PASSWORD" \
    AppKey="$APP_KEY" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region eu-west-1
```

`read -rs` legge la password senza mostrarla e senza salvarla nella history. `key:generate --show` stampa una nuova chiave senza toccare il tuo `.env` locale. Il flag `--capabilities CAPABILITY_NAMED_IAM` è obbligatorio quando il template crea risorse IAM con un nome esplicito: CloudFormation ti chiede di dichiarare che sai di creare ruoli e policy.

Il primo deploy richiede 10-18 minuti. Il collo di bottiglia è RDS, che da solo ne prende 6-10; CloudFront impiega qualche minuto in più a propagarsi. Alla fine trovi gli output del template con `aws cloudformation describe-stacks --stack-name photogallery-staging`:

```text
ALBDnsName:               photogallery-staging-alb-1234567890.eu-west-1.elb.amazonaws.com
CloudFrontDomainName:     d1234567890abc.cloudfront.net
CloudFrontDistributionId: E1A2B3C4D5E6F7
EcrRepositoryUri:         123456789012.dkr.ecr.eu-west-1.amazonaws.com/photogallery
FrontendBucketName:       photogallery-staging-frontend
```

I servizi ECS a questo punto non hanno ancora un'immagine da far girare: ECR è vuoto. Ci arriviamo nella prossima sezione.

### I change set prima di ogni aggiornamento

`aws cloudformation deploy` crea o aggiorna lo stack direttamente. Su uno stack che ha già dati, e in produzione sempre, crea prima un change set:

```bash
aws cloudformation create-change-set \
  --stack-name photogallery-production \
  --template-body file://infra/cloudformation.yaml \
  --change-set-name update-v2 \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameters ParameterKey=Environment,ParameterValue=production \
    ParameterKey=DBPassword,UsePreviousValue=true \
    ParameterKey=AppKey,UsePreviousValue=true

aws cloudformation describe-change-set \
  --stack-name photogallery-production \
  --change-set-name update-v2
```

Il change set elenca cosa verrebbe aggiunto, modificato o rimosso, senza applicare niente. Poi lo esegui con `execute-change-set` o lo scarti. Guarda soprattutto la colonna `Replacement`: se per l'istanza RDS vale `True`, AWS cancellerebbe il database e ne creerebbe uno nuovo, e senza snapshot perdi i dati. Basta cambiare una proprietà come il nome dell'istanza per arrivarci.

::: {.callout .callout-prompt}
[Prompt riusabile]{.callout-title}

Per un altro progetto, parti da questa versione generica e adatta nome, stack, database e regione:

```text
Genera un template CloudFormation YAML per un'applicazione [NOME] con:
- Stack: [backend in Laravel/Node.js/Python] + [frontend in React/Vue/Angular]
- Database: [MariaDB/MySQL/PostgreSQL] gestito su RDS
- Regione AWS: [eu-west-1/us-east-1/...]
- Deployment target: ECS Fargate per il backend, S3 + CloudFront per il frontend
- Ambienti: staging e production tramite Parameters

Il template deve includere:
- VPC con 2 subnet pubbliche (ALB) e 2 private (ECS, RDS) in 2 AZ
- Security group con least privilege (ECS verso RDS solo sulla porta del DB)
- IAM execution role per ECS (ECR, Secrets Manager, log) e task role per l'app
- ECR repository per l'immagine Docker
- CloudWatch log group per ogni container
- Outputs: ALBDnsName, CloudFrontDomainName, EcrRepositoryUri

Output: infra/cloudformation.yaml. Aggiungi commenti inline per le sezioni
non ovvie (es. perché quel DependsOn, perché quella policy IAM).
```

La richiesta dei commenti inline conta: tra sei mesi il template lo rileggerai tu, e senza commenti non ricorderai perché c'è quel `DependsOn`.
:::

## 23.3 Il backend in container

Con l'infrastruttura in piedi, il passo successivo è costruire l'immagine del backend, pubblicarla su ECR e far partire i servizi.

### Il Dockerfile

Il Dockerfile di produzione è multi-stage: una fase installa le dipendenze Composer senza quelle di sviluppo, la fase finale copia solo il necessario. L'immagine di Sail che usi in locale è pensata per lo sviluppo e non va in produzione. Il prompt:

```text
Scrivi un Dockerfile multi-stage per backend/ di Photogallery (Laravel 13, PHP 8.4):
- stage vendor: composer install --no-dev --optimize-autoloader --no-interaction
- stage runtime: PHP 8.4 con le estensioni pdo_mysql, gd, exif, intl, opcache;
  serve HTTP sulla porta 8080 (proponi FrankenPHP oppure Nginx + PHP-FPM e motiva)
- utente non root, scrittura consentita solo su storage/ e bootstrap/cache/
- ENTRYPOINT docker/entrypoint.sh: controlla le variabili obbligatorie e lancia
  config:cache all'avvio del container, non durante la build
- .dockerignore che esclude .env, node_modules, tests e storage/logs
La stessa immagine deve partire anche come worker sovrascrivendo il comando.
```

Due dettagli di questo prompt vengono da errori che si fanno spesso. Il primo è `config:cache` durante la build: in quel momento le variabili d'ambiente di produzione non esistono ancora, ECS le inietta solo all'avvio, e Laravel si ritroverebbe una configurazione cachata con valori vuoti. Il secondo: non ho chiesto un `HEALTHCHECK` nel Dockerfile, perché ECS lo ignora. Il controllo di salute lo fa l'ALB su `/api/v1/health`, configurato nel template.

L'entrypoint generato fa il controllo delle variabili prima di tutto:

<!-- VERIFY: entrypoint scritto per il capitolo, non ancora presente nel repo companion. Sostituire con il file reale se arriva il branch book/cap-16-aws-deploy. -->

```sh
#!/bin/sh
# docker/entrypoint.sh
set -e

for var in APP_KEY DB_HOST DB_PASSWORD AWS_BUCKET_PUBLIC AWS_BUCKET_PRIVATE SQS_QUEUE; do
  eval "value=\${$var:-}"
  if [ -z "$value" ]; then
    echo "FATAL: missing required env var: $var" >&2
    exit 1
  fi
done

php artisan config:cache
php artisan route:cache

exec "$@"
```

Un container che esce con codice 1 al boot e scrive nei log quale variabile manca si diagnostica in un minuto. Uno che parte con valori vuoti e fallisce alla prima richiesta, con un errore che sembra non c'entrare niente, ti fa perdere un pomeriggio.

### Build, tag e push su ECR

```bash
ECR_URI=$(aws cloudformation describe-stacks \
  --stack-name photogallery-staging \
  --query "Stacks[0].Outputs[?OutputKey=='EcrRepositoryUri'].OutputValue" \
  --output text)

# Autenticazione su ECR
aws ecr get-login-password --region eu-west-1 | \
  docker login --username AWS --password-stdin "$ECR_URI"

# Build e tag
docker build --platform linux/amd64 -t photogallery-api:v1.0.0 backend/
docker tag photogallery-api:v1.0.0 "$ECR_URI:v1.0.0"
docker tag photogallery-api:v1.0.0 "$ECR_URI:latest"

# Push
docker push "$ECR_URI:v1.0.0"
docker push "$ECR_URI:latest"
```

`--platform linux/amd64` serve se lavori su un Mac con Apple Silicon: senza, costruisci un'immagine ARM e Fargate, che di default gira su x86, la ferma con `exec format error`. In alternativa dichiari `RuntimePlatform` con `CpuArchitecture: ARM64` nella task definition e costruisci per ARM. Il primo push richiede qualche minuto; i successivi sono più veloci perché Docker manda solo i layer cambiati.

### Migrazioni e utente admin

Il database su RDS è vuoto. Le migrazioni le lanci come task una tantum, con la stessa task definition dell'API e il comando sovrascritto:

```bash
aws ecs run-task \
  --cluster photogallery-staging \
  --launch-type FARGATE \
  --task-definition photogallery-api \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-0aaa,subnet-0bbb],securityGroups=[sg-0ccc],assignPublicIp=DISABLED}" \
  --overrides '{"containerOverrides":[{"name":"api","command":["php","artisan","migrate","--force"]}]}'
```

Subnet e security group sono quelli privati dei task ECS: li trovi negli output dello stack o li chiedi a Claude, che li legge dal template. L'entrypoint gira comunque, poi `exec "$@"` esegue il comando passato. Allo stesso modo, con `["php","artisan","db:seed","--class=AdminUserSeeder","--force"]`, crei l'utente admin di Filament.

### Aggiornare i servizi

Quando una nuova immagine è su ECR, forzi un nuovo deploy dei due servizi:

```bash
aws ecs update-service \
  --cluster photogallery-staging \
  --service photogallery-api \
  --force-new-deployment \
  --region eu-west-1

aws ecs update-service \
  --cluster photogallery-staging \
  --service photogallery-worker \
  --force-new-deployment \
  --region eu-west-1
```

`--force-new-deployment` avvia nuovi task con la stessa task definition, che puntando a `:latest` scaricano l'immagine appena pubblicata. ECS fa un rolling update: avvia il task nuovo, aspetta che l'ALB lo consideri sano, poi ferma il vecchio. L'utente non vede interruzioni. Il worker non ha un ALB davanti: ECS lo considera sano finché il processo resta vivo, e se `queue:work` esce lo riavvia. È il lavoro che `DESIGN.md` §12.6 assegnava a Supervisor, e su Fargate non serve altro.

![La checklist del deploy completata: RDS, servizi ECS, ALB, bucket S3, CloudFront, SQS, ECR, migrazioni](figures/cap-23/fig-03.png)

### Le variabili d'ambiente nel container

Questa è la parte che dà più problemi al primo deploy. Le variabili non vanno nel Dockerfile, non vanno nell'immagine e non vanno in un `.env` copiato dentro il container: vanno nella task definition ECS, e quelle sensibili arrivano da Secrets Manager. I nomi sono quelli che il codice già legge in `config/filesystems.php`, `config/queue.php` e `config/database.php`:

```yaml
ApiTaskDefinition:
  Type: AWS::ECS::TaskDefinition
  Properties:
    Family: photogallery-api
    RequiresCompatibilities: [FARGATE]
    NetworkMode: awsvpc
    Cpu: "256"
    Memory: "512"
    ExecutionRoleArn: !GetAtt TaskExecutionRole.Arn
    TaskRoleArn: !GetAtt TaskRole.Arn
    ContainerDefinitions:
      - Name: api
        Image: !Sub "${EcrRepository.RepositoryUri}:latest"
        PortMappings:
          - ContainerPort: 8080
        Environment:
          - Name: APP_ENV
            Value: production
          - Name: DB_CONNECTION
            Value: mariadb
          - Name: DB_HOST
            Value: !GetAtt Database.Endpoint.Address
          - Name: DB_DATABASE
            Value: photogallery
          - Name: DB_USERNAME
            Value: photogallery
          - Name: DB_PERSISTENT_CONNECTIONS
            Value: "false"
          - Name: QUEUE_CONNECTION
            Value: sqs
          - Name: SQS_PREFIX
            Value: !Sub "https://sqs.${AWS::Region}.amazonaws.com/${AWS::AccountId}"
          - Name: SQS_QUEUE
            Value: !GetAtt PhotoQueue.QueueName
          - Name: PHOTOS_DRIVER
            Value: s3
          - Name: AWS_DEFAULT_REGION
            Value: !Ref AWS::Region
          - Name: AWS_BUCKET_PUBLIC
            Value: !Ref PublicBucket
          - Name: AWS_BUCKET_PRIVATE
            Value: !Ref PrivateBucket
          - Name: AWS_URL
            Value: !Sub "https://${Cdn.DomainName}"
        Secrets:
          - Name: DB_PASSWORD
            ValueFrom: !Ref DbPasswordSecret
          - Name: APP_KEY
            ValueFrom: !Ref AppKeySecret
        LogConfiguration:
          LogDriver: awslogs
          Options:
            awslogs-group: !Ref ApiLogGroup
            awslogs-region: !Ref AWS::Region
            awslogs-stream-prefix: api
```

In `Environment` vanno i valori non sensibili: endpoint del database, nomi dei bucket, regione. Sono visibili nella task definition e nella console. In `Secrets` vanno solo riferimenti: ECS legge il valore da Secrets Manager quando avvia il container, e il valore non compare mai nel template, nella console ECS o nei log. Il container lo vede come una normale variabile d'ambiente.

Nota cosa manca: `AWS_ACCESS_KEY_ID` e `AWS_SECRET_ACCESS_KEY`. Il file `.env.production.example` previsto da `DESIGN.md` §12.5 le elenca, ma su ECS non servono. Quando `key` e `secret` dei dischi S3 e della connessione SQS sono vuoti, l'SDK AWS usato da Laravel cerca le credenziali della task role, temporanee e ruotate da AWS. Nessuna chiave statica da custodire o da ruotare a mano.

La task definition del worker è la stessa, con un nome diverso, un altro log group e il comando sovrascritto:

```yaml
        Command:
          - php
          - artisan
          - queue:work
          - sqs
          - --queue=photogallery-pro
          - --tries=3
          - --timeout=180
          - --sleep=3
          - --memory=512
```

## 23.4 Il frontend su S3 e CloudFront

Il frontend React è più semplice: niente container, niente processi. La build produce una cartella di file statici che va su S3 e viene servita da CloudFront.

### La build

```bash
cd frontend
npm ci
npm run build
```

`npm run build` esegue `tsc -b && vite build` e scrive in `dist/`:

```text
dist/
  index.html
  assets/
    index-B7xk2Lq9.js
    index-D4fR8mWc.css
```

Il client API usa `VITE_API_BASE_URL` e, se manca, il default `/api/v1` (`src/api/client.ts`). Siccome CloudFront inoltra `/api/*` all'ALB, frontend e API stanno sullo stesso dominio, il default funziona così com'è e non devi configurare CORS. Se invece servi l'API da un dominio separato, la variabile va impostata al momento della build, perché Vite la scrive nel bundle.

### Upload su S3, nell'ordine giusto

L'hash nel nome dei file è la base della strategia di cache. Se il contenuto di un bundle cambia, cambia anche il nome. Quindi i file in `assets/` possono stare in cache per un anno, mentre `index.html`, che punta ai bundle, non va mai messo in cache.

L'ordine conta. Prima carichi gli asset nuovi, senza cancellare i vecchi; poi `index.html`; poi invalidi la cache. Un utente che nel frattempo ha ancora il vecchio `index.html` trova ancora i vecchi bundle su S3.

```bash
S3_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name photogallery-staging \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
  --output text)

# 1. Asset con hash: cache lunga, nessuna cancellazione
aws s3 sync dist/assets/ "s3://$S3_BUCKET/assets/" \
  --cache-control "public, max-age=31536000, immutable"

# 2. index.html e gli altri file: niente cache
aws s3 sync dist/ "s3://$S3_BUCKET/" \
  --exclude "assets/*" \
  --cache-control "no-cache, no-store, must-revalidate" \
  --delete
```

Con `--exclude "assets/*"` il secondo `sync` non tocca gli asset, nemmeno con `--delete`. I bundle vecchi restano su S3: occupano pochi KB, e puoi ripulirli ogni tanto con una lifecycle rule o a mano.

### Routing della SPA e invalidazione

La SPA usa `BrowserRouter`: un utente che apre direttamente `/albums/123` chiede a CloudFront un file che su S3 non esiste. La distribuzione deve rispondere con `index.html` e stato 200 agli errori 403 e 404 del bucket (le `CustomErrorResponses` nel template), poi ci pensa React Router.

Dopo ogni deploy del frontend invalida `index.html` nella cache di CloudFront:

```bash
CLOUDFRONT_ID=$(aws cloudformation describe-stacks \
  --stack-name photogallery-staging \
  --query "Stacks[0].Outputs[?OutputKey=='CloudFrontDistributionId'].OutputValue" \
  --output text)

aws cloudfront create-invalidation \
  --distribution-id "$CLOUDFRONT_ID" \
  --paths "/index.html"
```

Gli asset non hanno bisogno di invalidazione, perché hanno nomi nuovi. L'invalidazione arriva alle edge location in pochi minuti.

### Dominio personalizzato con Route 53 e ACM

Per collegare `app.photogallery.example` alla distribuzione:

1. Richiedi il certificato ACM in `us-east-1`. Per CloudFront è obbligatorio, anche se il resto dell'app sta in `eu-west-1`:

   ```bash
   aws acm request-certificate \
     --domain-name "*.photogallery.example" \
     --validation-method DNS \
     --region us-east-1
   ```

2. Aggiungi in Route 53 il record CNAME di validazione che ACM ti mostra.
3. Aggiungi alla distribuzione CloudFront `Aliases` e `ViewerCertificate` nel template.
4. Crea in Route 53 un record A di tipo alias da `app.photogallery.example` alla distribuzione. Per il pannello Filament fai lo stesso con `api.photogallery.example` verso l'ALB, con un certificato ACM nella regione dell'ALB.

Tutto questo entra nel template e va in produzione con il normale ciclo change set, execute.

## 23.5 Troubleshooting del primo deploy

Il primo deploy di un'infrastruttura così raramente va liscio: le risorse sono tante e i punti di contatto tra loro ancora di più. Claude qui aiuta molto, se gli dai l'errore esatto e non un riassunto. Con la regola `allow` sui comandi `describe-*` vista in §23.2 può leggere gli eventi dello stack da solo e proporti la correzione del template.

### Rollback di CloudFormation

Il deploy si ferma e lo stack finisce in `ROLLBACK_COMPLETE` (prima creazione) o `UPDATE_ROLLBACK_COMPLETE` (aggiornamento). Gli eventi dicono quale risorsa ha fallito e perché:

```bash
aws cloudformation describe-stack-events \
  --stack-name photogallery-staging \
  --query "StackEvents[?ResourceStatus=='CREATE_FAILED' || ResourceStatus=='UPDATE_FAILED']" \
  --output table
```

Leggi il campo `ResourceStatusReason`: di solito è molto preciso. Le cause che ho visto più spesso:

- Permessi IAM insufficienti per l'utente o il ruolo con cui lanci il deploy. Se il messaggio è `InsufficientCapabilities`, invece, manca solo `--capabilities CAPABILITY_NAMED_IAM`.
- Limiti dell'account raggiunti (VPC, Elastic IP, ALB). Li vedi in Service Quotas, dove puoi chiedere un aumento.
- Un nome già usato da un'altra risorsa, magari creata a mano dalla console o rimasta da uno stack precedente. I nomi dei bucket S3 devono essere unici in tutto AWS, non solo nel tuo account.
- Una dipendenza che CloudFormation non vede. Se una risorsa usa l'altra senza referenziarla con `!Ref` o `!GetAtt`, le crea in parallelo e la seconda fallisce. Aggiungi `DependsOn`.

Uno stack in `ROLLBACK_COMPLETE` non si aggiorna: va cancellato con `aws cloudformation delete-stack` prima di riprovare.

### Il task ECS non parte

Il servizio mostra zero task in esecuzione, oppure i task passano in loop da `PENDING` a `STOPPED`. In console vai su Cluster, Service, scheda Tasks, filtro Stopped, apri il task e leggi `Stopped reason` ed exit code del container. Da CLI:

```bash
aws ecs describe-tasks \
  --cluster photogallery-staging \
  --tasks $(aws ecs list-tasks --cluster photogallery-staging --desired-status STOPPED --query 'taskArns[0]' --output text) \
  --query "tasks[0].{stoppedReason:stoppedReason, containers:containers[].{reason:reason, exitCode:exitCode}}"
```

Le cause tipiche:

- Exit code 1 al boot: una variabile mancante. Il log CloudWatch del task riporta la riga `FATAL: missing required env var` scritta dall'entrypoint.
- Exit code 137: il container ha finito la memoria ed è stato ucciso. Sul worker succede con foto grandi, visto che `PHOTOS_MAX_DIMENSION` arriva a 8000 pixel. Alza `Memory` nella task definition.
- `CannotPullContainerError`: ECS non riesce a scaricare l'immagine. Controlla che la execution role abbia `ecr:GetAuthorizationToken` ed `ecr:BatchGetImage`, che le subnet private passino dal NAT Gateway e che su ECR esista davvero il tag `latest`.
- `exec format error`: l'immagine è stata costruita per l'architettura sbagliata (vedi `--platform` in §23.3).
- Il task parte, poi l'ALB lo dichiara non sano e ECS lo sostituisce, all'infinito. Guarda la risposta di `/api/v1/health`. L'`HealthController` di Photogallery scrive, rilegge e cancella un file di prova sul disco `photos` e interroga la tabella `failed_jobs`: se la task role non può scrivere sul bucket pubblico, o se il database non risponde, l'endpoint restituisce 503 con `"storage": "error"` o `"queue": "error"`. Il messaggio ti dice da quale lato cercare.

### Security group tra ECS e RDS

È l'errore più frequente e il meno ovvio la prima volta: il task parte, ma la connessione al database va in timeout. Quasi sempre il security group di RDS non accetta il traffico dei task. La configurazione corretta:

```yaml
DatabaseSecurityGroup:
  Type: AWS::EC2::SecurityGroup
  Properties:
    GroupDescription: RDS access from ECS tasks only
    VpcId: !Ref VPC
    SecurityGroupIngress:
      - IpProtocol: tcp
        FromPort: 3306
        ToPort: 3306
        SourceSecurityGroupId: !Ref EcsTaskSecurityGroup  # solo dal SG dei task
```

Con `CidrIp: 10.0.0.0/16`, l'intero CIDR della VPC, funziona lo stesso, ma qualsiasi risorsa nella VPC raggiunge il database. Meglio il riferimento al security group.

### CloudFront risponde 502 o 504

Il frontend si carica, ma le chiamate a `/api/v1/...` tornano con 502 Bad Gateway o 504 Gateway Timeout. Isola il problema saltando CloudFront e interrogando direttamente l'ALB:

```bash
curl -v "https://<ALBDnsName>/api/v1/health"
```

Se l'ALB risponde bene, il problema è nel behavior `/api/*` di CloudFront: origine, protocollo, header inoltrati (`Authorization` deve arrivare a Laravel, altrimenti Sanctum non vede il token). Se anche l'ALB restituisce 5xx, guarda i log CloudWatch del container. Un 504 di solito vuol dire che il container ci mette troppo a rispondere: controlla CPU e memoria del servizio e la latenza di RDS.

### Asset 404 dopo un deploy

Il frontend si carica ma alcuni bundle tornano 404. Quasi sempre qualcuno ha lanciato `sync --delete` anche sulla cartella `assets/`, cancellando i bundle a cui punta ancora l'`index.html` in cache. Con l'ordine di §23.4 non succede; se è già successo, ricarica la build precedente o invalida subito `index.html`.

## 23.6 Dopo il primo deploy

Il primo deploy funzionante è l'inizio della parte operativa. Servono poche abitudini, fatte con regolarità.

### Una dashboard CloudWatch

Anche il JSON della dashboard lo può scrivere Claude:

```text
Genera una dashboard CloudWatch in JSON per Photogallery con questi widget:
- request count e risposte 5xx dell'ALB
- latenza dell'ALB (p50, p95, p99)
- CPU e memoria dei servizi ECS api e worker
- connessioni RDS e latenza di lettura e scrittura
- messaggi visibili ed età del messaggio più vecchio nella coda photogallery-pro
Intervallo di 3 ore, refresh ogni 60 secondi. Aggiungila al template.
```

In mezzo minuto vedi se arriva traffico, se il database regge e se il worker smaltisce la coda.

### Allarmi via SNS

Sulle metriche importanti definisci allarmi CloudWatch che notificano un topic SNS, a cui iscrivi la tua email:

```bash
# Allarme se l'ALB restituisce più di 50 risposte 5xx in 5 minuti
aws cloudwatch put-metric-alarm \
  --alarm-name "photogallery-production-5xx" \
  --metric-name HTTPCode_Target_5XX_Count \
  --namespace AWS/ApplicationELB \
  --statistic Sum \
  --period 300 \
  --threshold 50 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:eu-west-1:123456789012:photogallery-alerts \
  --dimensions Name=LoadBalancer,Value=app/photogallery-production-alb/abc123
```

Questo allarme conta le risposte, non la percentuale: per una soglia in percentuale serve una metric math expression, che Claude ti scrive nel template. Come punto di partenza ho usato queste soglie:

- risposte 5xx sopra il 5% delle richieste per 5 minuti;
- latenza p99 dell'ALB sopra i 2 secondi per 5 minuti;
- CPU di un servizio ECS sopra l'80% per 10 minuti;
- connessioni RDS sopra l'80% del massimo per 10 minuti;
- messaggio più vecchio in coda con più di 300 secondi: il worker è in ritardo;
- almeno un messaggio nella dead letter queue.

### Provare i backup

RDS fa uno snapshot automatico al giorno. Uno snapshot che non hai mai ripristinato, però, non sai se funziona. Una volta al mese fai un restore di prova in un'istanza separata:

```bash
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier photogallery-restore-test \
  --db-snapshot-identifier rds:photogallery-production-YYYY-MM-DD-HH-MM \
  --db-instance-class db.t4g.micro
```

Collegati, controlla che i dati ci siano, poi cancella l'istanza. Sono un quarto d'ora di lavoro, e il giorno in cui serve davvero sai già quanto ci mette un ripristino.

### Aggiornare l'immagine di base

L'immagine PHP di base riceve aggiornamenti di sicurezza anche quando il tuo codice non cambia. Ogni due-quattro settimane ricostruisci l'immagine e ripeti tag, push e `update-service` di §23.3:

```bash
docker build --pull --platform linux/amd64 -t photogallery-api:v1.1.0 backend/
```

È `--pull` che fa scaricare la versione aggiornata dell'immagine di base; senza, Docker usa quella in cache locale, magari vecchia di settimane. `--no-cache` in più riesegue anche tutti i layer.

### Tenere d'occhio i costi

Un budget con avviso via email:

```bash
aws budgets create-budget \
  --account-id 123456789012 \
  --budget '{
    "BudgetName": "photogallery-monthly",
    "BudgetLimit": {"Amount": "120", "Unit": "USD"},
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }' \
  --notifications-with-subscribers '[{
    "Notification": {
      "NotificationType": "ACTUAL",
      "ComparisonOperator": "GREATER_THAN",
      "Threshold": 80
    },
    "Subscribers": [{"SubscriptionType": "EMAIL", "Address": "tu@example.com"}]
  }]'
```

Ti scrive quando superi l'80% del budget mensile, in tempo per capire cosa sta crescendo. Una volta alla settimana apri Cost Explorer per cinque minuti: un NAT Gateway dimenticato in un account di prova costa più di 30 dollari al mese e nessuno se ne accorge.

### Dal deploy a mano alla routine

L'obiettivo è che un deploy diventi noioso quanto un `git push`. Il repo ha già `.github/workflows/ci.yml`, che a ogni push lancia Pint, Pest, ESLint, Vitest e la build del frontend. Un job in più che, su `main` e con i test verdi, costruisce l'immagine, la pubblica su ECR e aggiorna i servizi è un buon prompt per Claude; per l'accesso ad AWS fatti proporre OIDC invece di chiavi statiche nei secret di GitHub.

I comandi di questo capitolo stanno bene in `scripts/`, uno per ambiente, così l'ordine (asset, `index.html`, invalidazione) non dipende dalla memoria di nessuno. Il runbook va in `docs/DEPLOY.md`, il task `T087` ancora aperto: ogni problema risolto, con il comando che l'ha diagnosticato. Chiedi a Claude di aggiornarlo alla fine di ogni sessione di troubleshooting.

## 23.7 La fine del libro

Photogallery è partita da un prompt nel capitolo 17 ed è arrivata su AWS. In mezzo ci sono le specifiche, i 124 task di `TASKS.md`, le wave in parallelo, le review e le fix. È lo stesso metodo che hai usato, in piccolo, per la landing page del capitolo 16, e funziona anche con un altro stack: un brief di una pagina, le specifiche scritte e rilette prima del codice, task piccoli eseguiti a wave con un commit ciascuno, una review a ogni wave e una più seria prima del deploy, l'infrastruttura descritta in un file e il primo deploy su un ambiente di prova.

Claude Code, nel frattempo, sarà cambiato: mentre scrivevo la seconda edizione sono arrivati auto mode, `/goal`, l'agent view e `/code-review ultra`, e qualche comando di questo libro avrà un nome diverso quando lo leggi. Per le novità c'è il riepilogo settimanale su `code.claude.com/docs/en/whats-new`.

Il prossimo progetto è tuo. Comincia dal brief. Se trovi un errore nel libro o nel repo companion, apri una issue con label `errata` su GitHub: la leggo.

Grazie di essere arrivato fin qui. Hidran

### Cosa viene dopo

Le appendici sono materiale di consultazione, non da leggere in ordine:

- Appendice A, glossario dei termini usati nel libro.
- Appendice B, troubleshooting, che estende §23.5.
- Appendice C, tutti i prompt riusabili dei capitoli.
- Appendice D, risorse: documentazione ufficiale, community, strumenti.
- Appendice E, changelog del libro.

## Riepilogo

- L'infrastruttura di Photogallery su AWS: ECS Fargate (servizi `api` e `worker` dalla stessa immagine), RDS MariaDB in subnet private, SQS con dead letter queue, tre bucket S3, CloudFront, ALB, Secrets Manager.
- Claude genera il template CloudFormation; a te tocca rivedere security group, ruoli IAM, visibility timeout della coda e nomi prima del primo deploy, e leggere un change set prima di ogni aggiornamento.
- I comandi di deploy li lanci tu o passano da una regola `ask` in `.claude/settings.json`; le password non entrano mai nel prompt.
- Le variabili d'ambiente vanno nella task definition: `Environment` per i valori in chiaro, `Secrets` per i riferimenti a Secrets Manager, la task role al posto delle chiavi AWS. `config:cache` si lancia all'avvio, non durante la build.
- Il frontend si carica nell'ordine asset, `index.html`, invalidazione; `/api/v1/health` è il primo posto dove guardare quando un task non diventa sano.

## Esercizio

Fai il primo deploy AWS di un tuo progetto piccolo. Non serve Photogallery: va bene una API con un solo endpoint, un bot, uno strumento interno.

1. Crea un branch per il lavoro, per esempio `cap-16-aws-deploy`.
2. Descrivi l'architettura in una pagina. Un servizio ECS e un RDS piccolo bastano.
3. Aggiungi le regole `ask` e `allow` di §23.2 al `.claude/settings.json` del progetto.
4. Genera il template con il prompt riusabile di §23.2 e rivedilo con la lista dei cinque controlli.
5. Fai il deploy su uno stack di staging con `aws cloudformation deploy`.
6. Annota in `docs/DEPLOY.md` ogni problema incontrato e il comando che l'ha risolto.

L'esercizio è finito quando `curl` sull'URL dell'ALB restituisce 200 dall'health check del tuo servizio. Poi cancella lo stack con `aws cloudformation delete-stack`, così non paghi il NAT Gateway per un mese: prima svuota i bucket S3, altrimenti la cancellazione fallisce. Conta tre-quattro ore per il primo giro, troubleshooting compreso.
