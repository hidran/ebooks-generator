# Chapter 23. Deploying to AWS with CloudFormation

::: {.chapter-goals}
[What you'll learn]{.callout-title}

How to design an AWS infrastructure for the Photogallery with Claude (ECS Fargate, RDS, S3, SQS, CloudFront), how to generate and review the CloudFormation template, how to ship the Laravel backend and the React frontend to production without baking secrets into the image, and what to check when the first deploy goes wrong.

[Prerequisites]{.callout-title}

An AWS account with the AWS CLI configured (`aws configure`) and Docker installed locally. A domain helps but isn't required.

:::

At this point the Photogallery is finished and reviewed: the waves are closed, the fixes from the chapter 22 review are committed, the tests pass. `docs/TASKS.md` still has Phase 8 open, "AWS migration" (`T086`, `T087`, `T088`). The code is ready, though: `DESIGN.md` §12.5 says that in production only the environment variables change, with SQS replacing the database queue and two S3 buckets replacing the local disk. This chapter builds the infrastructure those variables expect.

The companion repo doesn't have a branch for this chapter yet: `BOOK-COMPANION.md` lists `book/cap-16-aws-deploy` as coming soon, but today it doesn't exist. The template, Dockerfile and entrypoint on these pages come from my session, and you regenerate them yourself with the chapter's prompts, on a branch of your own.

The workflow is the same as in the previous chapters: Claude generates, you read, and every step ends with a real check, here a health check that returns 200. The difference is that these commands create resources you pay for, and later on we decide who runs them.

## 23.1 The AWS architecture for the Photogallery

From the repo root, I asked Claude to prepare the AWS deploy. Before writing a single file it read the project, saw that there was no deploy configuration at all, and asked me some questions: which approach I preferred, whether I already had resources in the account (VPC, RDS, buckets), and how much I wanted to spend per month.

![Claude proposes four AWS deploy strategies: ECS Fargate, Elastic Beanstalk, EC2 with deploy scripts, Laravel Forge or Vapor](figures/cap-23/fig-01.png)

Any of the four can handle an app like this one. I picked ECS Fargate for two reasons. The same Docker image runs both the API and the worker that processes photos; only the startup command changes. And the infrastructure lives in a YAML file in the repo, versioned like the rest of the code: a file Claude writes well and that you can read in a PR.

### The components

| Component | What it does for the Photogallery |
| :---- | :---- |
| ECS Fargate | Two services from the same image: `api` (Laravel and Filament behind the ALB) and `worker` (`queue:work` on SQS). No EC2 instances to manage; you pay for the time the containers run. |
| RDS MariaDB | The database, in private subnets, reachable only from the ECS tasks. Automatic daily backups. MariaDB because it's the same engine you use locally with Sail. |
| SQS | The queue for the `ProcessPhoto` jobs (resize and EXIF), with a dead letter queue. |
| S3 | Three buckets: private originals (Block Public Access on, only 5-minute signed URLs), public variants served through the CDN, and the frontend's static files. |
| CloudFront | Serves the React SPA and the photo variants over HTTPS from edge locations, and forwards `/api/*` to the ALB. |
| ALB | Receives requests for the API and for `/admin`, spreads them across the tasks and checks `/api/v1/health`. |
| Route 53 and ACM | DNS for the domain and free TLS certificates with automatic renewal. |
| Secrets Manager | The database password and Laravel's `APP_KEY`, injected into the container at startup. |
| CloudWatch | Container logs, metrics for ECS, RDS, ALB and SQS, alarms. |

The split between the private and the public bucket comes from `DESIGN.md` §12.1: the `photos_private` disk holds only the originals, and the `photos` disk holds only the resized variants, which come out of the resize step without EXIF data. An original never gets a public URL.

### The network topology

The VPC has four subnets across two availability zones. The ALB lives in the two public subnets, with internet access through an Internet Gateway. The Fargate tasks and the RDS instance live in the two private ones, with no direct access from outside. For outbound calls (pulling the image from ECR, calling S3, SQS and Secrets Manager) the tasks go through a NAT Gateway in the public subnet. That way the database only answers the app's containers. It's the same layout you'll find in almost every AWS project.

### Estimated cost

With a thousand monthly active users and 100 GB of photos, in `eu-west-1` (Ireland), the ballpark looks like this:

<!-- VERIFY: prezzi AWS eu-west-1 di ottobre 2026 (Fargate, RDS db.t4g.micro, ALB, NAT Gateway, free tier CloudFront). Le cifre sono stime arrotondate. -->

| Component | Monthly estimate (USD) |
| :---- | :---- |
| ECS Fargate (2 tasks with 0.25 vCPU and 0.5 GB) | ~18 |
| RDS MariaDB db.t4g.micro and 20 GB of storage | ~15 |
| ALB | ~20 |
| NAT Gateway | ~35 |
| S3 (100 GB and requests) | ~4 |
| CloudFront (100 GB of traffic) | 0-9 |
| Route 53, ACM, Secrets Manager | ~2 |
| CloudWatch Logs and basic metrics | ~5 |
| Total | about 100 |

The NAT Gateway is the line item that catches people off guard: more than a third of the total, fixed, plus a charge for every GB that passes through it. In a test environment you can skip it by putting the Fargate tasks in the public subnets with a public IP. It's less secure, but for experimenting it saves you a fair amount.

## 23.2 The CloudFormation template, generated with Claude

CloudFormation is AWS's native Infrastructure as Code: you describe the resources in YAML and AWS creates, updates or deletes them in the right order, working out the dependencies. The Photogallery template runs past 500 lines. Writing it by hand is long and tedious, which makes it exactly the kind of work to hand off, as long as you read it afterward.

### The prompt

After answering the questions in the previous figure, I gave Claude the infrastructure spec:

```text
Generate a CloudFormation YAML template to deploy Photogallery on AWS.
Read docs/DESIGN.md (§12.5 env switching, §12.6 workers) and backend/config/
for the environment variable names. The template must include:

- VPC with 2 public and 2 private subnets (eu-west-1a, eu-west-1b)
- RDS MariaDB on private subnets (db.t4g.micro in staging, db.t4g.small in production), encrypted
- ECS Fargate cluster with 2 services from the same image: api and worker
- ECR repository for the backend Docker image
- Application Load Balancer on public subnets, HTTPS listener, health check on /api/v1/health
- SQS queue photogallery-pro for the ProcessPhoto jobs
- 3 S3 buckets: private originals, public variants, frontend
- CloudFront for the SPA (with SPA routing), the photo variants and /api/* to the ALB
- Secrets Manager for the DB password and the Laravel APP_KEY
- CloudWatch log groups for api and worker
- Least-privilege security groups

Parameters: Environment (staging/production), DBPassword (NoEcho), AppKey (NoEcho).
Conditions: IsProd for the larger instances.
Outputs: ALBDnsName, CloudFrontDomainName, CloudFrontDistributionId,
EcrRepositoryUri, FrontendBucketName.

Output: a single file, infra/cloudformation.yaml. Comment the non-obvious choices.
```

Claude wrote `infra/cloudformation.yaml` with all the resources, the cross-references through `!Ref` and `!GetAtt`, and per-environment tags. The top of the file:

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

![The parameterized CloudFormation template: Environment, DBPassword and AppKey](figures/cap-23/fig-02.png)

My template also has a fourth `NoEcho` parameter, for the password of the Filament admin user, which `AdminUserSeeder` reads from `ADMIN_PASSWORD`. If you add it too, pass it in `--parameter-overrides` along with the others. `NoEcho: true` keeps the value out of the CloudFormation console and out of the `describe-stacks` output.

### What to review in the template

Before the deploy, set aside about twenty minutes of reading. You don't need to understand every line, but five things need checking.

1. That every component is there. Scroll through `Resources` and tick off the VPC, subnets, security groups, RDS, the cluster, the two services, ECR, the ALB, SQS, the three buckets, CloudFront and the secrets. If a component is missing, you'll find out at deploy time, if you're lucky.
2. The security groups. The RDS one must accept port 3306 only from the ECS tasks' security group, never from `0.0.0.0/0`. Claude usually gets these right, but this is where a mistake costs the most.
3. The IAM policies. There are two roles and they must stay separate. ECS uses the execution role to start the container: pulling from ECR, reading the secrets, writing the logs. The task role is the one Laravel uses at runtime: read and write on the two photo buckets, send and receive on SQS. Neither should have `"*"` as a resource. Check the `PolicyDocument` blocks in the `AWS::IAM::Role` resources.
4. The queue's visibility timeout. The worker runs with `--timeout=180` (DESIGN.md §12.6). If the SQS queue keeps the default visibility timeout of 30 seconds, a long job becomes visible again while it's still being processed, and a second worker picks it up. The value has to be above 180 seconds.
5. The names. A single scheme (`photogallery-staging-api-sg`, `photogallery-staging-db`) keeps the console readable.

### Iterating on the template

The first template is never complete. Mine was missing the NAT Gateway, so the tasks in the private subnets couldn't pull the image:

```text
The template has no NAT Gateway for the private subnets. The Fargate tasks in
the private subnets need one to pull the image from ECR. Add:
- a NAT Gateway in public subnet 1a, with an Elastic IP
- a route table for the private subnets with the default route to the NAT Gateway
```

Then the dead letter queue:

```text
Add an SQS dead letter queue to the photogallery-pro queue, with 14-day
retention and maxReceiveCount 3, matching the worker's --tries=3.
```

Laravel already handles ordinary failures: after three attempts the job lands in `failed_jobs`, which you can see in Filament's `QueueMonitor` widget. The DLQ gets the messages the worker never managed to finish, for example because the container was killed for running out of memory in the middle of a resize. After three or four rounds like this the template is complete.

### The first deploy

Before running the command, a word about who runs it.

::: {.callout .callout-warning}
[Warning]{.callout-title}

In auto mode the classifier blocks production deploys: it's one of the cases it's built to catch (chapter 11). On a staging stack, though, it might let the command through, and you don't want to depend on that call. Write an explicit rule in the project's `.claude/settings.json`:

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

`ask` rules apply in auto mode too, and they're evaluated before the classifier: every deploy asks for your confirmation, while the read-only commands you need for debugging go through. A Bash rule matches the command text, so `aws --region eu-west-1 cloudformation deploy` slips past the pattern. The simpler alternative is to run the deploys yourself in your own terminal and paste the output to Claude. Actions blocked by the classifier stay listed in `/permissions`, under the Recently denied tab.
:::

Then there's the matter of secrets. If you type the database password into the prompt, or have Claude generate it inside the command, it ends up in the conversation and in the shell history. Set it up yourself, in your own terminal:

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

`read -rs` reads the password without echoing it and without saving it to the history. `key:generate --show` prints a fresh key without touching your `.env`. `--capabilities CAPABILITY_NAMED_IAM` is required when the template creates IAM resources with an explicit name.

The first deploy takes 10-18 minutes. The bottleneck is RDS, which alone takes 6-10 of them; CloudFront needs a few extra minutes to propagate. When it's done, you get the template outputs with `aws cloudformation describe-stacks --stack-name photogallery-staging`:

```text
ALBDnsName:               photogallery-staging-alb-1234567890.eu-west-1.elb.amazonaws.com
CloudFrontDomainName:     d1234567890abc.cloudfront.net
CloudFrontDistributionId: E1A2B3C4D5E6F7
EcrRepositoryUri:         123456789012.dkr.ecr.eu-west-1.amazonaws.com/photogallery
FrontendBucketName:       photogallery-staging-frontend
```

ECR is still empty, though, so the ECS services have nothing to run yet.

### Change sets before every update

`aws cloudformation deploy` creates or updates the stack directly. On a stack that already holds data, and always in production, create a change set first:

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

The change set lists what would be added, modified or removed, without applying anything. Then you run it with `execute-change-set` or throw it away. Look at the `Replacement` field: if it reads `True` for the RDS instance, AWS would delete the database to create a new one, and without a snapshot you lose the data. Renaming the instance is all it takes to get there.

::: {.callout .callout-prompt}
[Reusable prompt]{.callout-title}

For another project, start from this generic version and adjust the name, stack, database and region:

```text
Generate a CloudFormation YAML template for an application [NAME] with:
- Stack: [backend in Laravel/Node.js/Python] + [frontend in React/Vue/Angular]
- Database: managed [MariaDB/MySQL/PostgreSQL] on RDS
- AWS region: [eu-west-1/us-east-1/...]
- Deployment target: ECS Fargate for the backend, S3 + CloudFront for the frontend
- Environments: staging and production via Parameters

The template must include:
- VPC with 2 public (ALB) and 2 private (ECS, RDS) subnets across 2 AZs
- Least-privilege security groups (ECS to RDS only on the DB port)
- IAM execution role for ECS (ECR, Secrets Manager, logs) and task role for the app
- ECR repository for the Docker image
- CloudWatch log group for each container
- Outputs: ALBDnsName, CloudFrontDomainName, EcrRepositoryUri

Output: infra/cloudformation.yaml. Add inline comments for the non-obvious
sections (e.g. why that DependsOn, why that IAM policy).
```

Asking for inline comments matters: six months from now you'll be the one rereading the template, and without comments you won't remember why that `DependsOn` is there.
:::

## 23.3 The backend in a container

### The Dockerfile

The production Dockerfile is multi-stage: one stage installs the Composer dependencies without the dev ones, and the final stage copies only what's needed. The Sail image you use locally is built for development and doesn't belong in production. The prompt:

```text
Write a multi-stage Dockerfile for Photogallery's backend/ (Laravel 13, PHP 8.4):
- vendor stage: composer install --no-dev --optimize-autoloader --no-interaction
- runtime stage: PHP 8.4 with the pdo_mysql, gd, exif, intl, opcache extensions;
  serves HTTP on port 8080 (propose FrankenPHP or Nginx + PHP-FPM and justify the choice)
- non-root user, write access only to storage/ and bootstrap/cache/
- ENTRYPOINT docker/entrypoint.sh: checks the required variables and runs
  config:cache when the container starts, not during the build
- .dockerignore that excludes .env, node_modules, tests and storage/logs
The same image must also start as the worker by overriding the command.
```

Two details in the prompt come from common mistakes. `config:cache` must not run during the build: at that point the production variables don't exist yet, because ECS injects them at startup, and Laravel would end up with a cached configuration full of empty values. And there's no `HEALTHCHECK` in the Dockerfile, because ECS ignores it: the ALB does the checking on `/api/v1/health`, as configured in the template.

The generated entrypoint checks the variables before anything else:

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

A container that exits with code 1 at boot and logs which variable is missing takes a minute to diagnose. One that starts with empty values and fails on the first request, with an error that seems to have nothing to do with it, costs you an afternoon.

### Build, tag and push to ECR

```bash
ECR_URI=$(aws cloudformation describe-stacks \
  --stack-name photogallery-staging \
  --query "Stacks[0].Outputs[?OutputKey=='EcrRepositoryUri'].OutputValue" \
  --output text)

# Authenticate with ECR
aws ecr get-login-password --region eu-west-1 | \
  docker login --username AWS --password-stdin "$ECR_URI"

# Build and tag
docker build --platform linux/amd64 -t photogallery-api:v1.0.0 backend/
docker tag photogallery-api:v1.0.0 "$ECR_URI:v1.0.0"
docker tag photogallery-api:v1.0.0 "$ECR_URI:latest"

# Push
docker push "$ECR_URI:v1.0.0"
docker push "$ECR_URI:latest"
```

You need `--platform linux/amd64` on an Apple Silicon Mac: without it you build an ARM image, and Fargate, which runs on x86 by default, stops it with `exec format error`. Alternatively, declare `RuntimePlatform` with `CpuArchitecture: ARM64` in the task definition. After the first push, later pushes only upload the layers that changed.

### Migrations and the admin user

The database on RDS is empty. You run the migrations as a one-off task, with the same task definition as the API and the command overridden:

```bash
aws ecs run-task \
  --cluster photogallery-staging \
  --launch-type FARGATE \
  --task-definition photogallery-api \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-0aaa,subnet-0bbb],securityGroups=[sg-0ccc],assignPublicIp=DISABLED}" \
  --overrides '{"containerOverrides":[{"name":"api","command":["php","artisan","migrate","--force"]}]}'
```

The subnets and the security group are the tasks' private ones. The entrypoint still runs, and then `exec "$@"` executes the command you passed. In the same way, with `["php","artisan","db:seed","--class=AdminUserSeeder","--force"]`, you create the Filament admin user.

### Updating the services

Once a new image is on ECR, you force a new deployment of both services:

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

`--force-new-deployment` starts new tasks with the same task definition, and since it points to `:latest` they pull the image you just pushed. ECS does a rolling update: it starts the new task, waits for the ALB to mark it healthy, then stops the old one. Users don't see any downtime. The worker has no ALB in front of it: ECS considers it healthy as long as the process stays alive, and restarts it if `queue:work` exits. That's the job `DESIGN.md` §12.6 gave to Supervisor, and on Fargate you need nothing else.

![The completed deploy checklist: RDS, ECS services, ALB, S3 buckets, CloudFront, SQS, ECR, migrations](figures/cap-23/fig-03.png)

### Environment variables in the container

This is the part that causes the most trouble on a first deploy. The variables don't go in the Dockerfile, they don't go in the image, and they don't go in a `.env` copied into the container. They go in the ECS task definition, and the sensitive ones come from Secrets Manager. The names are the ones the code already reads in `config/filesystems.php`, `config/queue.php` and `config/database.php`:

```yaml
ApiTaskDefinition:
  Type: AWS::ECS::TaskDefinition
  Properties:
    Family: photogallery-api
    # RequiresCompatibilities, NetworkMode, Cpu and Memory omitted
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
        # LogConfiguration to ApiLogGroup omitted
```

`Environment` holds the non-sensitive values, which are visible in the task definition and in the console. `Secrets` holds only references: ECS reads the value from Secrets Manager at startup, and that value never shows up in the template, the console or the logs. The container sees it as an ordinary environment variable.

Notice what's missing: `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`. The `.env.production.example` file planned in `DESIGN.md` §12.5 lists them, but on ECS you don't need them. When the `key` and `secret` of the S3 disks and of the SQS connection are empty, the AWS SDK that Laravel uses falls back to the task role's credentials, which are temporary and rotated by AWS. No static keys to guard or rotate by hand.

The worker's task definition is the same, with a different name, a different log group, and in `Command` the command from `DESIGN.md` §12.6: `php artisan queue:work sqs --queue=photogallery-pro --tries=3 --timeout=180 --sleep=3 --memory=512`.

## 23.4 The frontend on S3 and CloudFront

The frontend is simpler: the build produces static files that go to S3, and CloudFront serves them.

### The build

```bash
cd frontend
npm ci
npm run build
```

`npm run build` runs `tsc -b && vite build` and writes to `dist/`:

```text
dist/
  index.html
  assets/
    index-B7xk2Lq9.js
    index-D4fR8mWc.css
```

The API client (`src/api/client.ts`) uses `VITE_API_BASE_URL` or, if it's not set, `/api/v1`. Since CloudFront forwards `/api/*` to the ALB, the frontend and the API sit on the same domain: the default works and you don't need CORS. With the API on a separate domain, you have to set the variable at build time, because Vite writes it into the bundle.

### Uploading to S3, in the right order

When a bundle's content changes, its name changes too, so the files in `assets/` can stay cached for a year, while `index.html`, which points to the bundles, must never be cached. And the order matters: first the new assets, without deleting the old ones, then `index.html`, then the invalidation. Anyone still holding the old `index.html` still finds the old bundles.

```bash
S3_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name photogallery-staging \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
  --output text)

# 1. Hashed assets: long cache, no deletion
aws s3 sync dist/assets/ "s3://$S3_BUCKET/assets/" \
  --cache-control "public, max-age=31536000, immutable"

# 2. index.html and the other files: no cache
aws s3 sync dist/ "s3://$S3_BUCKET/" \
  --exclude "assets/*" \
  --cache-control "no-cache, no-store, must-revalidate" \
  --delete
```

With `--exclude "assets/*"` the second `sync` leaves the assets alone, even with `--delete`. The old bundles stay on S3: they take up a few KB, and you can clean them up now and then with a lifecycle rule or by hand.

### SPA routing and invalidation

The SPA uses `BrowserRouter`: a user who opens `/albums/123` directly asks CloudFront for a file that doesn't exist on S3. The distribution has to answer the bucket's 403 and 404 errors with `index.html` and status 200 (the `CustomErrorResponses` in the template), and React Router takes it from there.

After every frontend deploy, invalidate `index.html` in the CloudFront cache:

```bash
CLOUDFRONT_ID=$(aws cloudformation describe-stacks \
  --stack-name photogallery-staging \
  --query "Stacks[0].Outputs[?OutputKey=='CloudFrontDistributionId'].OutputValue" \
  --output text)

aws cloudfront create-invalidation \
  --distribution-id "$CLOUDFRONT_ID" \
  --paths "/index.html"
```

The assets have new names, so there's no need to invalidate them.

### Custom domain with Route 53 and ACM

To point `app.photogallery.example` at the distribution:

1. Request the ACM certificate in `us-east-1`. CloudFront requires it, even if the rest of the app lives in `eu-west-1`:

   ```bash
   aws acm request-certificate \
     --domain-name "*.photogallery.example" \
     --validation-method DNS \
     --region us-east-1
   ```

2. Add the validation CNAME record that ACM shows you to Route 53.
3. Add `Aliases` and `ViewerCertificate` to the CloudFront distribution in the template.
4. In Route 53, create an alias A record from `app.photogallery.example` to the distribution. For the Filament panel, do the same with `api.photogallery.example` pointing to the ALB, with an ACM certificate in the ALB's region. All of this goes into the template and through the usual change set.

## 23.5 Troubleshooting the first deploy

The first deploy of an infrastructure like this rarely goes smoothly: there are a lot of resources and even more points where they touch. Claude helps a lot here, as long as you give it the exact error and not a summary. With the `allow` rule on the `describe-*` commands from §23.2, it can read the stack events on its own and propose a fix to the template.

### CloudFormation rollback

The deploy stops and the stack ends up in `ROLLBACK_COMPLETE` (first creation) or `UPDATE_ROLLBACK_COMPLETE` (update). The events tell you which resource failed and why:

```bash
aws cloudformation describe-stack-events \
  --stack-name photogallery-staging \
  --query "StackEvents[?ResourceStatus=='CREATE_FAILED' || ResourceStatus=='UPDATE_FAILED']" \
  --output table
```

Read the `ResourceStatusReason` field: it's usually very precise. The causes I've run into most often:

- Insufficient IAM permissions for the user or role running the deploy. If the message says `InsufficientCapabilities`, on the other hand, you're only missing `--capabilities CAPABILITY_NAMED_IAM`.
- Account limits reached (VPCs, Elastic IPs, ALBs). You'll find them in Service Quotas, where you can request an increase.
- A name already taken by another resource, maybe one created by hand in the console or left over from a previous stack. S3 bucket names must be unique across all of AWS, not just within your account.
- A dependency CloudFormation can't see. If one resource uses another without referencing it through `!Ref` or `!GetAtt`, CloudFormation creates them in parallel and the second one fails. Add `DependsOn`.

A stack in `ROLLBACK_COMPLETE` can't be updated: delete it with `aws cloudformation delete-stack` before trying again.

### The ECS task won't start

The service shows zero running tasks, or the tasks cycle from `PENDING` to `STOPPED` over and over. You'll find the reason and the container's exit code in the ECS console (stopped tasks) or from the CLI:

```bash
aws ecs describe-tasks \
  --cluster photogallery-staging \
  --tasks $(aws ecs list-tasks --cluster photogallery-staging --desired-status STOPPED --query 'taskArns[0]' --output text) \
  --query "tasks[0].{stoppedReason:stoppedReason, containers:containers[].{reason:reason, exitCode:exitCode}}"
```

The usual causes:

- Exit code 1 at boot: a missing variable. The task's CloudWatch log shows the `FATAL: missing required env var` line written by the entrypoint.
- Exit code 137: the container ran out of memory and was killed. On the worker this happens with large photos, since `PHOTOS_MAX_DIMENSION` goes up to 8000 pixels. Raise `Memory` in the task definition.
- `CannotPullContainerError`: ECS can't pull the image. Check that the execution role has `ecr:GetAuthorizationToken` and `ecr:BatchGetImage`, that the private subnets route through the NAT Gateway, and that the `latest` tag really exists on ECR.
- `exec format error`: the image was built for the wrong architecture (see `--platform` in §23.3).
- The task starts, then the ALB marks it unhealthy and ECS replaces it, forever. Look at the response from `/api/v1/health`. The Photogallery's `HealthController` writes, reads back and deletes a test file on the `photos` disk and queries the `failed_jobs` table: if the task role can't write to the public bucket, or if the database doesn't respond, the endpoint returns 503 with `"storage": "error"` or `"queue": "error"`. The message tells you which side to look at.

### Security groups between ECS and RDS

This is the most common error, and the least obvious the first time: the task starts, but the database connection times out. Almost always, the RDS security group isn't accepting traffic from the tasks. The correct configuration:

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
        SourceSecurityGroupId: !Ref EcsTaskSecurityGroup  # only from the tasks' SG
```

With `CidrIp: 10.0.0.0/16`, the VPC's whole CIDR, it works just the same, but then any resource in the VPC can reach the database. The security group reference is the better choice.

### CloudFront returns 502 or 504

The frontend loads, but the calls to `/api/v1/...` come back with 502 or 504. Skip CloudFront and query the ALB directly:

```bash
curl -v "https://<ALBDnsName>/api/v1/health"
```

If the ALB responds fine, the problem is in CloudFront's `/api/*` behavior: the origin, the protocol, the forwarded headers (`Authorization` has to reach Laravel, otherwise Sanctum doesn't see the token). If the ALB returns 5xx too, look at the container's CloudWatch logs. A 504 usually means the container is taking too long to respond: check the service's CPU and memory and the RDS latency.

### Asset 404s after a deploy

If some bundles come back 404, almost always someone ran `sync --delete` on `assets/` as well, deleting the files that the still-cached `index.html` points to. Re-upload the previous build's assets and go back to the order in §23.4.

## 23.6 After the first deploy

After the first deploy the operational part begins: a few habits, kept up regularly.

### A CloudWatch dashboard

Claude can write the dashboard JSON too:

```text
Generate a CloudWatch dashboard in JSON for Photogallery with these widgets:
- ALB request count and 5xx responses
- ALB latency (p50, p95, p99)
- CPU and memory for the ECS services api and worker
- RDS connections and read and write latency
- visible messages and age of the oldest message in the photogallery-pro queue
3-hour range, refresh every 60 seconds. Add it to the template.
```

In half a minute you can see whether traffic is coming in, whether the database is keeping up and whether the worker is draining the queue.

### Alarms through SNS

On the metrics that matter, set up CloudWatch alarms that notify an SNS topic, and subscribe your email to it:

```bash
# Alarm if the ALB returns more than 50 5xx responses in 5 minutes
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

This alarm counts responses, not a percentage. A percentage threshold needs a metric math expression, which Claude can write into the template for you. As a starting point I used these thresholds:

- 5xx responses above 5% of requests for 5 minutes;
- ALB p99 latency above 2 seconds for 5 minutes;
- CPU of an ECS service above 80% for 10 minutes;
- RDS connections above 80% of the maximum for 10 minutes;
- oldest message in the queue older than 300 seconds: the worker is falling behind;
- at least one message in the dead letter queue.

### Testing the backups

RDS takes an automatic snapshot every day. But a snapshot you've never restored is a snapshot you don't know works. Once a month, do a test restore into a separate instance:

```bash
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier photogallery-restore-test \
  --db-snapshot-identifier rds:photogallery-production-YYYY-MM-DD-HH-MM \
  --db-instance-class db.t4g.micro
```

Connect, check the data, then delete the instance. On the day you really need it, you'll already know how long a restore takes.

### Updating the base image

The PHP base image gets security updates even when your code doesn't change. Every two to four weeks, rebuild the image and repeat the tag, push and `update-service` steps from §23.3:

```bash
docker build --pull --platform linux/amd64 -t photogallery-api:v1.1.0 backend/
```

It's `--pull` that fetches the updated base image. Without it, Docker uses the one in its local cache, which might be weeks old. Adding `--no-cache` also reruns every layer.

### Keeping an eye on costs

A budget with an email alert:

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

It warns you at 80% of the monthly budget, in time to figure out what's growing. Once a week, take a look at Cost Explorer: a NAT Gateway forgotten in a test account costs more than 30 dollars a month.

### From manual deploys to routine

The goal is for a deploy to become as boring as a `git push`. The repo already has `.github/workflows/ci.yml`, which runs Pint, Pest, ESLint, Vitest and the frontend build on every push. One more job that, on `main` and with green tests, builds the image, pushes it to ECR and updates the services makes a good prompt for Claude. For AWS access, have it propose OIDC instead of static keys in the GitHub secrets.

The commands from this chapter fit nicely in `scripts/`, one per environment, so that the order (assets, `index.html`, invalidation) doesn't depend on anyone's memory. The runbook goes in `docs/DEPLOY.md`, which is task `T087`, still open: every problem you solved, with the command that diagnosed it. Ask Claude to update it at the end of every troubleshooting session.

## 23.7 The end of the book

The Photogallery started from a prompt in chapter 17 and made it to AWS, by way of the specs, the 124 tasks in `TASKS.md`, the waves, the reviews and the fixes. It's the same method you used on a small scale for the landing page in chapter 16, and it works with any stack: a one-page brief, specs reviewed before the code, small tasks in waves with one commit each, a review after every wave and a more serious one before the deploy, the infrastructure in a file.

Claude Code will have changed in the meantime: while I was writing the second edition, auto mode, `/goal`, agent view and `/code-review ultra` arrived, and some commands in this book will have a different name by the time you read it. For what's new, there's the weekly roundup at `code.claude.com/docs/en/whats-new`.

The next project is yours. Start with the brief. If you find a mistake in the book or in the companion repo, open an issue with the `errata` label on GitHub: I read them.

Thanks for making it this far. Hidran

### What comes next

The appendices are reference material, not meant to be read in order:

- Appendix A, a glossary of the terms used in the book.
- Appendix B, troubleshooting for the most common problems.
- Appendix C, ready-to-copy prompts.
- Appendix D, resources: the official Claude Code documentation organized by part of the book, how to stay up to date, the companion repositories, plugins and marketplaces, and the documentation for the tools used in the projects.
- Appendix E, the changelog of the book and of Claude Code between the first and the second edition.

## Summary {.unlisted}

- The Photogallery's AWS infrastructure: ECS Fargate (`api` and `worker` services from the same image), RDS MariaDB in private subnets, SQS with a dead letter queue, three S3 buckets, CloudFront, ALB, Secrets Manager.
- Claude generates the CloudFormation template. Your job is to review the security groups, IAM roles, queue visibility timeout and names before the first deploy, and to read a change set before every update.
- You run the deploy commands yourself, or they go through an `ask` rule in `.claude/settings.json`. Passwords never go into the prompt.
- Environment variables go in the task definition: `Environment` for plain values, `Secrets` for references to Secrets Manager, and the task role instead of AWS keys. `config:cache` runs at startup, not during the build.
- The frontend is uploaded in the order assets, `index.html`, invalidation. `/api/v1/health` is the first place to look when a task won't turn healthy.

## Exercise {.unlisted}

Do the first AWS deploy of a small project of your own. It doesn't have to be the Photogallery: an API with a single endpoint, a bot or an internal tool will do.

1. Create a branch for the work, for example `cap-16-aws-deploy`.
2. Describe the architecture on one page. One ECS service and a small RDS instance are enough.
3. Add the `ask` and `allow` rules from §23.2 to the project's `.claude/settings.json`.
4. Generate the template with the reusable prompt from §23.2 and review it against the list of five checks.
5. Deploy to a staging stack with `aws cloudformation deploy`.
6. Write down in `docs/DEPLOY.md` every problem you hit and the command that fixed it.

The exercise is done when `curl` on the ALB URL returns 200 from your service's health check. Then delete the stack with `aws cloudformation delete-stack`, so you don't pay for the NAT Gateway for a month. Empty the S3 buckets first, or the deletion fails. Plan on three to four hours for the first round, troubleshooting included.
