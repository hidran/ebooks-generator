# Capítulo 23. Deploy en AWS con CloudFormation

::: {.chapter-goals}
[Qué aprenderás]{.callout-title}

Cómo diseñar con Claude una infraestructura AWS para la Photogallery (ECS Fargate, RDS, S3, SQS, CloudFront), cómo generar y revisar la plantilla de CloudFormation, cómo llevar a producción el backend Laravel y el frontend React sin meter secretos en la imagen, y qué revisar cuando el primer deploy sale mal.

[Requisitos previos]{.callout-title}

Una cuenta de AWS con la AWS CLI configurada (`aws configure`) y Docker en local. Un dominio ayuda, pero no es obligatorio.

:::

A estas alturas la Photogallery está terminada y revisada: las oleadas están cerradas, las correcciones de la revisión del capítulo 22 tienen su commit, los tests pasan. En `docs/TASKS.md` sigue abierta la Fase 8, "AWS migration" (`T086`, `T087`, `T088`). El código, eso sí, está listo: `DESIGN.md` §12.5 dice que en producción solo cambian las variables de entorno, con SQS en lugar de la cola en base de datos y dos buckets S3 en lugar del disco local. Este capítulo construye la infraestructura que esas variables esperan.

Para este capítulo el repo companion todavía no tiene rama: `BOOK-COMPANION.md` anuncia `book/cap-16-aws-deploy` como próxima, pero hoy no existe. La plantilla, el Dockerfile y el entrypoint de estas páginas salen de mi sesión, y tú los regeneras con los prompts del capítulo, en una rama tuya.

El flujo de trabajo es el de los capítulos anteriores: Claude genera, tú lees, y cada paso termina con una comprobación de verdad, aquí un health check que responde 200. La diferencia es que estos comandos crean recursos de pago, y más adelante decidimos quién los ejecuta.

## 23.1 La arquitectura AWS de la Photogallery

Desde la raíz del repo le pedí a Claude que preparara el deploy en AWS. Antes de escribir ningún archivo leyó el proyecto, vio que no había ninguna configuración de deploy y me hizo algunas preguntas: qué enfoque prefería, si ya tenía recursos en la cuenta (VPC, RDS, buckets) y cuánto quería gastar al mes.

![Claude propone cuatro estrategias de deploy en AWS: ECS Fargate, Elastic Beanstalk, EC2 con scripts de deploy, Laravel Forge o Vapor](figures/cap-23/fig-01.png)

Las cuatro aguantan una app como esta. Elegí ECS Fargate por dos motivos. La misma imagen Docker ejecuta la API y el worker que procesa las fotos; solo cambia el comando de arranque. Y la infraestructura vive en un archivo YAML dentro del repo, versionado como el resto del código: un archivo que Claude escribe bien y que tú puedes leer en un PR.

### Los componentes

| Componente | Qué hace para la Photogallery |
| :---- | :---- |
| ECS Fargate | Dos servicios a partir de la misma imagen: `api` (Laravel y Filament detrás del ALB) y `worker` (`queue:work` sobre SQS). Sin instancias EC2 que gestionar; pagas el tiempo en que los contenedores están corriendo. |
| RDS MariaDB | La base de datos, en subnets privadas, accesible solo desde las tareas de ECS. Backups diarios automáticos. MariaDB porque es el mismo motor que usas en local con Sail. |
| SQS | La cola de los jobs `ProcessPhoto` (redimensionado y EXIF), con una dead letter queue. |
| S3 | Tres buckets: originales privados (Block Public Access activado, solo URL firmadas de 5 minutos), variantes públicas servidas por la CDN y los archivos estáticos del frontend. |
| CloudFront | Sirve la SPA de React y las variantes de las fotos por HTTPS desde las edge locations, y reenvía `/api/*` al ALB. |
| ALB | Recibe las peticiones para la API y para `/admin`, las reparte entre las tareas y comprueba `/api/v1/health`. |
| Route 53 y ACM | DNS del dominio y certificados TLS gratuitos con renovación automática. |
| Secrets Manager | La contraseña de la base de datos y la `APP_KEY` de Laravel, inyectadas en el contenedor al arrancar. |
| CloudWatch | Logs de los contenedores, métricas de ECS, RDS, ALB y SQS, alarmas. |

La separación entre bucket privado y público viene de `DESIGN.md` §12.1: el disco `photos_private` contiene solo los originales y el disco `photos` solo las variantes redimensionadas, que salen del redimensionado sin datos EXIF. Un original nunca tiene una URL pública.

### La topología de red

La VPC tiene cuatro subnets en dos availability zones. En las dos subnets públicas vive el ALB, con salida a internet a través de un Internet Gateway. En las dos privadas viven las tareas de Fargate y la instancia RDS, sin acceso directo desde fuera. Para las llamadas salientes (el pull de la imagen desde ECR, las llamadas a S3, SQS y Secrets Manager) las tareas pasan por un NAT Gateway en la subnet pública. Así la base de datos solo responde a los contenedores de la app. Es la misma estructura que encontrarás en casi todos los proyectos de AWS.

### Coste estimado

Con mil usuarios activos al mes y 100 GB de fotos, en `eu-west-1` (Irlanda), el orden de magnitud es este:

<!-- VERIFY: prezzi AWS eu-west-1 di ottobre 2026 (Fargate, RDS db.t4g.micro, ALB, NAT Gateway, free tier CloudFront). Le cifre sono stime arrotondate. -->

| Componente | Estimación mensual (USD) |
| :---- | :---- |
| ECS Fargate (2 tareas de 0,25 vCPU y 0,5 GB) | ~18 |
| RDS MariaDB db.t4g.micro y 20 GB de almacenamiento | ~15 |
| ALB | ~20 |
| NAT Gateway | ~35 |
| S3 (100 GB y peticiones) | ~4 |
| CloudFront (100 GB de tráfico) | 0-9 |
| Route 53, ACM, Secrets Manager | ~2 |
| CloudWatch Logs y métricas básicas | ~5 |
| Total | unos 100 |

El NAT Gateway es la partida que sorprende: más de un tercio del total, fijo, más una cuota por cada GB que pasa por él. En un entorno de pruebas puedes prescindir de él poniendo las tareas de Fargate en las subnets públicas con una IP pública. Es menos seguro, pero para experimentar te ahorras bastante.

## 23.2 La plantilla de CloudFormation generada con Claude

CloudFormation es el Infrastructure as Code nativo de AWS: describes los recursos en YAML y AWS los crea, actualiza o elimina en el orden correcto, resolviendo las dependencias. La plantilla de la Photogallery pasa de las 500 líneas. Escribirla a mano es largo y tedioso, así que es justo el tipo de trabajo que conviene delegar, siempre que luego la leas.

### El prompt

Después de responder a las preguntas de la figura anterior, le di a Claude las especificaciones de la infraestructura:

```text
Genera una plantilla de CloudFormation en YAML para el deploy de Photogallery en AWS.
Lee docs/DESIGN.md (§12.5 env switching, §12.6 workers) y backend/config/
para los nombres de las variables de entorno. La plantilla debe incluir:

- VPC con 2 subnets públicas y 2 privadas (eu-west-1a, eu-west-1b)
- RDS MariaDB en subnets privadas (db.t4g.micro en staging, db.t4g.small en production), cifrada
- Cluster ECS Fargate con 2 servicios a partir de la misma imagen: api y worker
- Repositorio ECR para la imagen Docker del backend
- Application Load Balancer en subnets públicas, listener HTTPS, health check en /api/v1/health
- Cola SQS photogallery-pro para los jobs ProcessPhoto
- 3 buckets S3: originales privados, variantes públicas, frontend
- CloudFront para la SPA (con routing de SPA), las variantes de las fotos y /api/* hacia el ALB
- Secrets Manager para la contraseña de la BD y la APP_KEY de Laravel
- Log groups de CloudWatch para api y worker
- Security groups con mínimo privilegio

Parameters: Environment (staging/production), DBPassword (NoEcho), AppKey (NoEcho).
Conditions: IsProd para las instancias más grandes.
Outputs: ALBDnsName, CloudFrontDomainName, CloudFrontDistributionId,
EcrRepositoryUri, FrontendBucketName.

Salida: un solo archivo, infra/cloudformation.yaml. Comenta las decisiones que no sean obvias.
```

Claude escribió `infra/cloudformation.yaml` con todos los recursos, las referencias cruzadas mediante `!Ref` y `!GetAtt` y las etiquetas por entorno. El principio del archivo:

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

![La plantilla de CloudFormation parametrizada: Environment, DBPassword y AppKey](figures/cap-23/fig-02.png)

Mi plantilla tiene también un cuarto parámetro `NoEcho`, para la contraseña del usuario admin de Filament, que `AdminUserSeeder` lee de `ADMIN_PASSWORD`. Si tú también lo añades, pásalo en `--parameter-overrides` junto con los demás. `NoEcho: true` hace que el valor no aparezca en la consola de CloudFormation ni en la salida de `describe-stacks`.

### Qué revisar en la plantilla

Antes del deploy, unos veinte minutos de lectura. No hace falta entender cada línea, pero hay cinco cosas que revisar.

1. Que estén todos los componentes. Recorre `Resources` y marca VPC, subnets, security groups, RDS, el cluster, los dos servicios, ECR, el ALB, SQS, los tres buckets, CloudFront y los secretos. Un componente que falta lo descubres en el deploy, con suerte.
2. Los security groups. El de RDS debe aceptar el puerto 3306 solo desde el security group de las tareas de ECS, nunca desde `0.0.0.0/0`. Claude suele escribirlos bien, pero es el punto donde un error sale más caro.
3. Las políticas IAM. Hay dos roles y hay que mantenerlos separados. ECS usa la execution role para arrancar el contenedor: pull desde ECR, lectura de los secretos, escritura de los logs. La task role es la que usa Laravel en tiempo de ejecución: lectura y escritura en los dos buckets de fotos, envío y recepción en SQS. Ninguno de los dos debe tener `"*"` como recurso. Revisa los `PolicyDocument` de los recursos `AWS::IAM::Role`.
4. El visibility timeout de la cola. El worker corre con `--timeout=180` (DESIGN.md §12.6). Si la cola SQS tiene el visibility timeout por defecto, 30 segundos, un job largo vuelve a ser visible mientras todavía se está procesando y un segundo worker lo recoge. El valor tiene que superar los 180 segundos.
5. Los nombres. Un esquema único (`photogallery-staging-api-sg`, `photogallery-staging-db`) hace legible la consola.

### Iterar sobre la plantilla

La primera plantilla nunca está completa. A la mía le faltaba el NAT Gateway, y las tareas de las subnets privadas no conseguían descargar la imagen:

```text
La plantilla no tiene NAT Gateway para las subnets privadas. Las tareas de Fargate
en las subnets privadas lo necesitan para hacer el pull de la imagen desde ECR. Añade:
- un NAT Gateway en la subnet pública 1a, con Elastic IP
- una route table para las subnets privadas con la ruta por defecto hacia el NAT Gateway
```

Después, la dead letter queue:

```text
Añade una dead letter queue de SQS a la cola photogallery-pro, con retención
de 14 días y maxReceiveCount 3, alineado con el --tries=3 del worker.
```

Los fallos normales ya los gestiona Laravel: después de tres intentos el job termina en `failed_jobs`, visible en el widget `QueueMonitor` de Filament. A la DLQ llegan los mensajes que el worker no consiguió cerrar, por ejemplo porque el contenedor murió por falta de memoria en mitad de un redimensionado. Tras tres o cuatro vueltas así, la plantilla está completa.

### El primer deploy

Antes de lanzar el comando, una aclaración sobre quién lo lanza.

::: {.callout .callout-warning}
[Atención]{.callout-title}

En auto mode el clasificador bloquea los deploys en producción: es uno de los casos previstos (capítulo 11). En un stack de staging, en cambio, podría dejar pasar el comando, y no quieres depender de esa valoración. Escribe una regla explícita en el `.claude/settings.json` del proyecto:

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

Las reglas `ask` valen también en auto mode y se evalúan antes que el clasificador: cada deploy te pide confirmación, mientras que los comandos de solo lectura para depurar pasan. Una regla de Bash compara el texto del comando, así que `aws --region eu-west-1 cloudformation deploy` se escapa del patrón. La alternativa más sencilla es lanzar tú los deploys en tu terminal y pegarle la salida a Claude. Las acciones bloqueadas por el clasificador quedan en `/permissions`, pestaña Recently denied.
:::

Luego está el tema de los secretos. Si escribes la contraseña de la base de datos en el prompt, o haces que Claude la genere dentro del comando, acaba en la conversación y en el historial de la shell. Prepárala tú, en tu terminal:

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

`read -rs` lee la contraseña sin mostrarla y sin guardarla en el historial. `key:generate --show` imprime una clave nueva sin tocar tu `.env`. `--capabilities CAPABILITY_NAMED_IAM` es obligatorio cuando la plantilla crea recursos IAM con un nombre explícito.

El primer deploy tarda entre 10 y 18 minutos. El cuello de botella es RDS, que se lleva 6-10 por sí solo; CloudFront necesita unos minutos más para propagarse. Al terminar, obtienes las salidas de la plantilla con `aws cloudformation describe-stacks --stack-name photogallery-staging`:

```text
ALBDnsName:               photogallery-staging-alb-1234567890.eu-west-1.elb.amazonaws.com
CloudFrontDomainName:     d1234567890abc.cloudfront.net
CloudFrontDistributionId: E1A2B3C4D5E6F7
EcrRepositoryUri:         123456789012.dkr.ecr.eu-west-1.amazonaws.com/photogallery
FrontendBucketName:       photogallery-staging-frontend
```

Pero ECR está vacío, así que los servicios de ECS todavía no tienen nada que ejecutar.

### Los change sets antes de cada actualización

`aws cloudformation deploy` crea o actualiza el stack directamente. En un stack que ya tiene datos, y en producción siempre, crea antes un change set:

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

El change set enumera lo que se añadiría, modificaría o eliminaría, sin aplicar nada. Después lo ejecutas con `execute-change-set` o lo descartas. Fíjate en el campo `Replacement`: si para la instancia RDS vale `True`, AWS borraría la base de datos para crear una nueva, y sin snapshot pierdes los datos. Basta con cambiar el nombre de la instancia para llegar ahí.

::: {.callout .callout-prompt}
[Prompt reutilizable]{.callout-title}

Para otro proyecto, parte de esta versión genérica y adapta el nombre, el stack, la base de datos y la región:

```text
Genera una plantilla de CloudFormation en YAML para una aplicación [NOMBRE] con:
- Stack: [backend en Laravel/Node.js/Python] + [frontend en React/Vue/Angular]
- Base de datos: [MariaDB/MySQL/PostgreSQL] gestionada en RDS
- Región de AWS: [eu-west-1/us-east-1/...]
- Deployment target: ECS Fargate para el backend, S3 + CloudFront para el frontend
- Entornos: staging y production mediante Parameters

La plantilla debe incluir:
- VPC con 2 subnets públicas (ALB) y 2 privadas (ECS, RDS) en 2 AZ
- Security groups con mínimo privilegio (ECS hacia RDS solo en el puerto de la BD)
- IAM execution role para ECS (ECR, Secrets Manager, logs) y task role para la app
- Repositorio ECR para la imagen Docker
- Log group de CloudWatch para cada contenedor
- Outputs: ALBDnsName, CloudFrontDomainName, EcrRepositoryUri

Salida: infra/cloudformation.yaml. Añade comentarios inline en las secciones
que no sean obvias (p. ej., por qué ese DependsOn, por qué esa política IAM).
```

Pedir los comentarios inline importa: dentro de seis meses serás tú quien relea la plantilla, y sin comentarios no te acordarás de por qué está ese `DependsOn`.
:::

## 23.3 El backend en un contenedor

### El Dockerfile

El Dockerfile de producción es multi-stage: una etapa instala las dependencias de Composer sin las de desarrollo y la etapa final copia solo lo necesario. La imagen de Sail que usas en local está pensada para desarrollo y no va a producción. El prompt:

```text
Escribe un Dockerfile multi-stage para el backend/ de Photogallery (Laravel 13, PHP 8.4):
- stage vendor: composer install --no-dev --optimize-autoloader --no-interaction
- stage runtime: PHP 8.4 con las extensiones pdo_mysql, gd, exif, intl, opcache;
  sirve HTTP en el puerto 8080 (propón FrankenPHP o Nginx + PHP-FPM y justifica la elección)
- usuario no root, escritura permitida solo en storage/ y bootstrap/cache/
- ENTRYPOINT docker/entrypoint.sh: comprueba las variables obligatorias y ejecuta
  config:cache al arrancar el contenedor, no durante la build
- .dockerignore que excluya .env, node_modules, tests y storage/logs
La misma imagen tiene que poder arrancar también como worker sobrescribiendo el comando.
```

Dos detalles del prompt vienen de errores habituales. `config:cache` no debe ejecutarse durante la build: en ese momento las variables de producción no existen, porque ECS las inyecta al arrancar, y Laravel se quedaría con una configuración cacheada llena de valores vacíos. Y no hay `HEALTHCHECK` en el Dockerfile, porque ECS lo ignora: la comprobación la hace el ALB sobre `/api/v1/health`, configurado en la plantilla.

El entrypoint generado comprueba las variables antes que nada:

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

Un contenedor que sale con código 1 al arrancar y escribe en los logs qué variable falta se diagnostica en un minuto. Uno que arranca con valores vacíos y falla en la primera petición, con un error que parece no tener nada que ver, te hace perder una tarde.

### Build, tag y push a ECR

```bash
ECR_URI=$(aws cloudformation describe-stacks \
  --stack-name photogallery-staging \
  --query "Stacks[0].Outputs[?OutputKey=='EcrRepositoryUri'].OutputValue" \
  --output text)

# Autenticación en ECR
aws ecr get-login-password --region eu-west-1 | \
  docker login --username AWS --password-stdin "$ECR_URI"

# Build y tag
docker build --platform linux/amd64 -t photogallery-api:v1.0.0 backend/
docker tag photogallery-api:v1.0.0 "$ECR_URI:v1.0.0"
docker tag photogallery-api:v1.0.0 "$ECR_URI:latest"

# Push
docker push "$ECR_URI:v1.0.0"
docker push "$ECR_URI:latest"
```

`--platform linux/amd64` hace falta en un Mac con Apple Silicon: sin él construyes una imagen ARM, y Fargate, que por defecto corre en x86, la detiene con `exec format error`. Como alternativa, declaras `RuntimePlatform` con `CpuArchitecture: ARM64` en la task definition. Los push posteriores al primero solo suben las capas que cambiaron.

### Migraciones y usuario admin

La base de datos en RDS está vacía. Las migraciones se lanzan como una tarea puntual, con la misma task definition de la API y el comando sobrescrito:

```bash
aws ecs run-task \
  --cluster photogallery-staging \
  --launch-type FARGATE \
  --task-definition photogallery-api \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-0aaa,subnet-0bbb],securityGroups=[sg-0ccc],assignPublicIp=DISABLED}" \
  --overrides '{"containerOverrides":[{"name":"api","command":["php","artisan","migrate","--force"]}]}'
```

Las subnets y el security group son los privados de las tareas. El entrypoint se ejecuta igualmente, y después `exec "$@"` ejecuta el comando que le pasaste. Del mismo modo, con `["php","artisan","db:seed","--class=AdminUserSeeder","--force"]`, creas el usuario admin de Filament.

### Actualizar los servicios

Cuando hay una imagen nueva en ECR, fuerzas un nuevo despliegue de los dos servicios:

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

`--force-new-deployment` arranca tareas nuevas con la misma task definition, que, como apunta a `:latest`, descargan la imagen recién publicada. ECS hace un rolling update: arranca la tarea nueva, espera a que el ALB la considere sana y luego detiene la vieja. El usuario no nota ninguna interrupción. El worker no tiene un ALB delante: ECS lo considera sano mientras el proceso siga vivo, y si `queue:work` termina, lo reinicia. Es el trabajo que `DESIGN.md` §12.6 le asignaba a Supervisor, y en Fargate no hace falta nada más.

![La checklist del deploy completada: RDS, servicios de ECS, ALB, buckets S3, CloudFront, SQS, ECR, migraciones](figures/cap-23/fig-03.png)

### Las variables de entorno en el contenedor

Esta es la parte que más problemas da en el primer deploy. Las variables no van en el Dockerfile, no van en la imagen y no van en un `.env` copiado dentro del contenedor. Van en la task definition de ECS, y las sensibles llegan desde Secrets Manager. Los nombres son los que el código ya lee en `config/filesystems.php`, `config/queue.php` y `config/database.php`:

```yaml
ApiTaskDefinition:
  Type: AWS::ECS::TaskDefinition
  Properties:
    Family: photogallery-api
    # RequiresCompatibilities, NetworkMode, Cpu y Memory omitidos
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
        # LogConfiguration hacia ApiLogGroup omitida
```

En `Environment` van los valores no sensibles, visibles en la task definition y en la consola. En `Secrets` van solo referencias: ECS lee el valor de Secrets Manager al arrancar, y ese valor no aparece en la plantilla, en la consola ni en los logs. El contenedor lo ve como una variable de entorno normal.

Fíjate en lo que falta: `AWS_ACCESS_KEY_ID` y `AWS_SECRET_ACCESS_KEY`. El archivo `.env.production.example` previsto en `DESIGN.md` §12.5 las incluye, pero en ECS no hacen falta. Cuando `key` y `secret` de los discos S3 y de la conexión SQS están vacíos, el SDK de AWS que usa Laravel busca las credenciales de la task role, temporales y rotadas por AWS. Ninguna clave estática que custodiar o rotar a mano.

La task definition del worker es igual, con otro nombre, otro log group y, en `Command`, el comando de `DESIGN.md` §12.6: `php artisan queue:work sqs --queue=photogallery-pro --tries=3 --timeout=180 --sleep=3 --memory=512`.

## 23.4 El frontend en S3 y CloudFront

El frontend es más sencillo: la build produce archivos estáticos que van a S3, y CloudFront los sirve.

### La build

```bash
cd frontend
npm ci
npm run build
```

`npm run build` ejecuta `tsc -b && vite build` y escribe en `dist/`:

```text
dist/
  index.html
  assets/
    index-B7xk2Lq9.js
    index-D4fR8mWc.css
```

El cliente de la API (`src/api/client.ts`) usa `VITE_API_BASE_URL` o, si no está definida, `/api/v1`. Como CloudFront reenvía `/api/*` al ALB, frontend y API están en el mismo dominio: el valor por defecto funciona y no hace falta CORS. Con la API en un dominio aparte, la variable hay que definirla en el momento de la build, porque Vite la escribe en el bundle.

### Subida a S3, en el orden correcto

Si cambia el contenido de un bundle, cambia también su nombre: los archivos de `assets/` pueden quedarse en caché un año, mientras que `index.html`, que apunta a los bundles, no debe cachearse nunca. Y el orden importa: primero los assets nuevos, sin borrar los viejos, luego `index.html` y luego la invalidación. Quien todavía tenga el `index.html` viejo sigue encontrando los bundles viejos.

```bash
S3_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name photogallery-staging \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
  --output text)

# 1. Assets con hash: caché larga, sin borrado
aws s3 sync dist/assets/ "s3://$S3_BUCKET/assets/" \
  --cache-control "public, max-age=31536000, immutable"

# 2. index.html y los demás archivos: sin caché
aws s3 sync dist/ "s3://$S3_BUCKET/" \
  --exclude "assets/*" \
  --cache-control "no-cache, no-store, must-revalidate" \
  --delete
```

Con `--exclude "assets/*"` el segundo `sync` no toca los assets, ni siquiera con `--delete`. Los bundles viejos se quedan en S3: ocupan pocos KB y puedes limpiarlos de vez en cuando con una lifecycle rule o a mano.

### Routing de la SPA e invalidación

La SPA usa `BrowserRouter`: un usuario que abre directamente `/albums/123` le pide a CloudFront un archivo que no existe en S3. La distribución tiene que responder a los errores 403 y 404 del bucket con `index.html` y estado 200 (las `CustomErrorResponses` de la plantilla), y a partir de ahí se encarga React Router.

Después de cada deploy del frontend, invalida `index.html` en la caché de CloudFront:

```bash
CLOUDFRONT_ID=$(aws cloudformation describe-stacks \
  --stack-name photogallery-staging \
  --query "Stacks[0].Outputs[?OutputKey=='CloudFrontDistributionId'].OutputValue" \
  --output text)

aws cloudfront create-invalidation \
  --distribution-id "$CLOUDFRONT_ID" \
  --paths "/index.html"
```

Los assets tienen nombres nuevos y no hace falta invalidarlos.

### Dominio propio con Route 53 y ACM

Para conectar `app.photogallery.example` a la distribución:

1. Solicita el certificado ACM en `us-east-1`. CloudFront lo exige, aunque el resto de la app esté en `eu-west-1`:

   ```bash
   aws acm request-certificate \
     --domain-name "*.photogallery.example" \
     --validation-method DNS \
     --region us-east-1
   ```

2. Añade en Route 53 el registro CNAME de validación que te muestra ACM.
3. Añade a la distribución de CloudFront `Aliases` y `ViewerCertificate` en la plantilla.
4. Crea en Route 53 un registro A de tipo alias de `app.photogallery.example` a la distribución. Para el panel de Filament haz lo mismo con `api.photogallery.example` hacia el ALB, con un certificado ACM en la región del ALB. Todo esto entra en la plantilla y pasa por el change set de siempre.

## 23.5 Troubleshooting del primer deploy

El primer deploy de una infraestructura así rara vez sale limpio: los recursos son muchos y los puntos de contacto entre ellos, todavía más. Aquí Claude ayuda mucho, si le das el error exacto y no un resumen. Con la regla `allow` sobre los comandos `describe-*` de §23.2 puede leer los eventos del stack por su cuenta y proponerte la corrección de la plantilla.

### Rollback de CloudFormation

El deploy se detiene y el stack queda en `ROLLBACK_COMPLETE` (primera creación) o `UPDATE_ROLLBACK_COMPLETE` (actualización). Los eventos dicen qué recurso falló y por qué:

```bash
aws cloudformation describe-stack-events \
  --stack-name photogallery-staging \
  --query "StackEvents[?ResourceStatus=='CREATE_FAILED' || ResourceStatus=='UPDATE_FAILED']" \
  --output table
```

Lee el campo `ResourceStatusReason`: suele ser muy preciso. Las causas que más he visto:

- Permisos IAM insuficientes para el usuario o el rol con el que lanzas el deploy. Si el mensaje es `InsufficientCapabilities`, en cambio, solo falta `--capabilities CAPABILITY_NAMED_IAM`.
- Límites de la cuenta alcanzados (VPC, Elastic IP, ALB). Los ves en Service Quotas, donde puedes pedir un aumento.
- Un nombre ya usado por otro recurso, quizá creado a mano desde la consola o que quedó de un stack anterior. Los nombres de los buckets S3 tienen que ser únicos en todo AWS, no solo en tu cuenta.
- Una dependencia que CloudFormation no ve. Si un recurso usa otro sin referenciarlo con `!Ref` o `!GetAtt`, CloudFormation los crea en paralelo y el segundo falla. Añade `DependsOn`.

Un stack en `ROLLBACK_COMPLETE` no se puede actualizar: hay que borrarlo con `aws cloudformation delete-stack` antes de volver a intentarlo.

### La tarea de ECS no arranca

El servicio muestra cero tareas en ejecución, o las tareas pasan en bucle de `PENDING` a `STOPPED`. El motivo y el exit code del contenedor los lees en la consola de ECS (tareas detenidas) o desde la CLI:

```bash
aws ecs describe-tasks \
  --cluster photogallery-staging \
  --tasks $(aws ecs list-tasks --cluster photogallery-staging --desired-status STOPPED --query 'taskArns[0]' --output text) \
  --query "tasks[0].{stoppedReason:stoppedReason, containers:containers[].{reason:reason, exitCode:exitCode}}"
```

Las causas típicas:

- Exit code 1 al arrancar: falta una variable. El log de CloudWatch de la tarea muestra la línea `FATAL: missing required env var` que escribe el entrypoint.
- Exit code 137: el contenedor se quedó sin memoria y lo mataron. En el worker pasa con fotos grandes, ya que `PHOTOS_MAX_DIMENSION` llega a 8000 píxeles. Sube `Memory` en la task definition.
- `CannotPullContainerError`: ECS no consigue descargar la imagen. Comprueba que la execution role tenga `ecr:GetAuthorizationToken` y `ecr:BatchGetImage`, que las subnets privadas salgan por el NAT Gateway y que en ECR exista de verdad el tag `latest`.
- `exec format error`: la imagen se construyó para la arquitectura equivocada (mira `--platform` en §23.3).
- La tarea arranca, luego el ALB la declara no sana y ECS la sustituye, sin fin. Mira la respuesta de `/api/v1/health`. El `HealthController` de la Photogallery escribe, vuelve a leer y borra un archivo de prueba en el disco `photos` y consulta la tabla `failed_jobs`: si la task role no puede escribir en el bucket público, o si la base de datos no responde, el endpoint devuelve 503 con `"storage": "error"` o `"queue": "error"`. El mensaje te dice por qué lado buscar.

### Security groups entre ECS y RDS

Es el error más frecuente y el menos obvio la primera vez: la tarea arranca, pero la conexión a la base de datos da timeout. Casi siempre el security group de RDS no acepta el tráfico de las tareas. La configuración correcta:

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
        SourceSecurityGroupId: !Ref EcsTaskSecurityGroup  # solo desde el SG de las tareas
```

Con `CidrIp: 10.0.0.0/16`, todo el CIDR de la VPC, funciona igual, pero cualquier recurso de la VPC llega a la base de datos. Mejor la referencia al security group.

### CloudFront responde 502 o 504

El frontend carga, pero las llamadas a `/api/v1/...` devuelven 502 o 504. Sáltate CloudFront y consulta directamente el ALB:

```bash
curl -v "https://<ALBDnsName>/api/v1/health"
```

Si el ALB responde bien, el problema está en el behavior `/api/*` de CloudFront: el origen, el protocolo, las cabeceras reenviadas (`Authorization` tiene que llegar a Laravel, si no Sanctum no ve el token). Si el ALB también devuelve 5xx, mira los logs de CloudWatch del contenedor. Un 504 suele significar que el contenedor tarda demasiado en responder: revisa la CPU y la memoria del servicio y la latencia de RDS.

### Assets con 404 después de un deploy

Si algunos bundles devuelven 404, casi siempre alguien lanzó `sync --delete` también sobre `assets/` y borró los archivos a los que apunta el `index.html` que sigue en caché. Vuelve a subir los assets de la build anterior y retoma el orden de §23.4.

## 23.6 Después del primer deploy

Tras el primer deploy empieza la parte operativa: unos pocos hábitos, mantenidos con regularidad.

### Un dashboard de CloudWatch

El JSON del dashboard también lo puede escribir Claude:

```text
Genera un dashboard de CloudWatch en JSON para Photogallery con estos widgets:
- request count y respuestas 5xx del ALB
- latencia del ALB (p50, p95, p99)
- CPU y memoria de los servicios de ECS api y worker
- conexiones de RDS y latencia de lectura y escritura
- mensajes visibles y antigüedad del mensaje más antiguo en la cola photogallery-pro
Intervalo de 3 horas, refresco cada 60 segundos. Añádelo a la plantilla.
```

En medio minuto ves si llega tráfico, si la base de datos aguanta y si el worker va vaciando la cola.

### Alarmas con SNS

Sobre las métricas importantes define alarmas de CloudWatch que notifiquen a un topic de SNS, al que suscribes tu email:

```bash
# Alarma si el ALB devuelve más de 50 respuestas 5xx en 5 minutos
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

Esta alarma cuenta respuestas, no porcentajes. Para un umbral en porcentaje hace falta una metric math expression, que Claude te escribe en la plantilla. Como punto de partida usé estos umbrales:

- respuestas 5xx por encima del 5% de las peticiones durante 5 minutos;
- latencia p99 del ALB por encima de 2 segundos durante 5 minutos;
- CPU de un servicio de ECS por encima del 80% durante 10 minutos;
- conexiones de RDS por encima del 80% del máximo durante 10 minutos;
- mensaje más antiguo de la cola con más de 300 segundos: el worker va con retraso;
- al menos un mensaje en la dead letter queue.

### Probar los backups

RDS hace un snapshot automático al día. Pero de un snapshot que nunca has restaurado no sabes si funciona. Una vez al mes, haz una restauración de prueba en una instancia aparte:

```bash
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier photogallery-restore-test \
  --db-snapshot-identifier rds:photogallery-production-YYYY-MM-DD-HH-MM \
  --db-instance-class db.t4g.micro
```

Conéctate, revisa los datos y luego borra la instancia. El día que de verdad lo necesites ya sabrás cuánto tarda una restauración.

### Actualizar la imagen base

La imagen base de PHP recibe actualizaciones de seguridad aunque tu código no cambie. Cada dos a cuatro semanas, reconstruye la imagen y repite el tag, el push y el `update-service` de §23.3:

```bash
docker build --pull --platform linux/amd64 -t photogallery-api:v1.1.0 backend/
```

Es `--pull` lo que hace que se descargue la versión actualizada de la imagen base. Sin él, Docker usa la que tiene en la caché local, que puede tener semanas. Si añades `--no-cache`, además vuelve a ejecutar todas las capas.

### Vigilar los costes

Un presupuesto con aviso por email:

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

Te avisa al llegar al 80% del presupuesto mensual, a tiempo para entender qué está creciendo. Una vez por semana, échale un vistazo a Cost Explorer: un NAT Gateway olvidado en una cuenta de pruebas cuesta más de 30 dólares al mes.

### Del deploy a mano a la rutina

El objetivo es que un deploy sea tan aburrido como un `git push`. El repo ya tiene `.github/workflows/ci.yml`, que en cada push ejecuta Pint, Pest, ESLint, Vitest y la build del frontend. Un job más que, en `main` y con los tests en verde, construya la imagen, la publique en ECR y actualice los servicios es un buen prompt para Claude. Para el acceso a AWS, pídele que proponga OIDC en lugar de claves estáticas en los secrets de GitHub.

Los comandos de este capítulo encajan bien en `scripts/`, uno por entorno, para que el orden (assets, `index.html`, invalidación) no dependa de la memoria de nadie. El runbook va en `docs/DEPLOY.md`, la tarea `T087` que sigue abierta: cada problema resuelto, con el comando que lo diagnosticó. Pídele a Claude que lo actualice al final de cada sesión de troubleshooting.

## 23.7 El final del libro

La Photogallery empezó con un prompt en el capítulo 17 y ha llegado a AWS, pasando por las especificaciones, las 124 tareas de `TASKS.md`, las oleadas, las revisiones y las correcciones. Es el método que usaste a pequeña escala para la landing page del capítulo 16, y funciona con cualquier stack: un brief de una página, especificaciones revisadas antes del código, tareas pequeñas por oleadas con un commit cada una, una revisión en cada wave y otra más seria antes del deploy, la infraestructura en un archivo.

Claude Code habrá cambiado mientras tanto: mientras escribía la segunda edición llegaron auto mode, `/goal`, agent view y `/code-review ultra`, y algunos comandos de este libro tendrán otro nombre cuando lo leas. Para las novedades está el resumen semanal en `code.claude.com/docs/en/whats-new`.

El próximo proyecto es tuyo. Empieza por el brief. Si encuentras un error en el libro o en el repo companion, abre un issue con la etiqueta `errata` en GitHub: los leo.

Gracias por llegar hasta aquí. Hidran

### Lo que viene después

Los apéndices son material de consulta, no para leer en orden:

- Apéndice A, glosario de los términos usados en el libro.
- Apéndice B, troubleshooting de los problemas más comunes.
- Apéndice C, prompts listos para copiar.
- Apéndice D, recursos: la documentación oficial de Claude Code organizada por parte del libro, cómo mantenerse al día, los repositorios companion, plugins y marketplaces, y la documentación de las herramientas de los proyectos.
- Apéndice E, el changelog del libro y de Claude Code entre la primera y la segunda edición.

## Resumen {.unlisted}

- La infraestructura de la Photogallery en AWS: ECS Fargate (servicios `api` y `worker` a partir de la misma imagen), RDS MariaDB en subnets privadas, SQS con dead letter queue, tres buckets S3, CloudFront, ALB, Secrets Manager.
- Claude genera la plantilla de CloudFormation. A ti te toca revisar security groups, roles IAM, visibility timeout de la cola y nombres antes del primer deploy, y leer un change set antes de cada actualización.
- Los comandos de deploy los lanzas tú o pasan por una regla `ask` en `.claude/settings.json`. Las contraseñas nunca entran en el prompt.
- Las variables de entorno van en la task definition: `Environment` para los valores en claro, `Secrets` para las referencias a Secrets Manager y la task role en lugar de las claves de AWS. `config:cache` se ejecuta al arrancar, no durante la build.
- El frontend se sube en el orden assets, `index.html`, invalidación. `/api/v1/health` es el primer sitio donde mirar cuando una tarea no pasa a estar sana.

## Ejercicio {.unlisted}

Haz el primer deploy en AWS de un proyecto pequeño tuyo. No hace falta que sea la Photogallery: vale una API con un solo endpoint, un bot o una herramienta interna.

1. Crea una rama para el trabajo, por ejemplo `cap-16-aws-deploy`.
2. Describe la arquitectura en una página. Un servicio de ECS y una RDS pequeña bastan.
3. Añade las reglas `ask` y `allow` de §23.2 al `.claude/settings.json` del proyecto.
4. Genera la plantilla con el prompt reutilizable de §23.2 y revísala con la lista de los cinco controles.
5. Haz el deploy en un stack de staging con `aws cloudformation deploy`.
6. Anota en `docs/DEPLOY.md` cada problema que encuentres y el comando que lo resolvió.

El ejercicio está terminado cuando `curl` sobre la URL del ALB devuelve 200 desde el health check de tu servicio. Después borra el stack con `aws cloudformation delete-stack`, para no pagar el NAT Gateway durante un mes. Vacía antes los buckets S3, o el borrado falla. Cuenta con tres o cuatro horas para la primera vuelta, troubleshooting incluido.
