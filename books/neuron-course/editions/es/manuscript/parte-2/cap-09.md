# Capítulo 9 — MCP: el Model Context Protocol

## 9.1 Qué es MCP y por qué importa

### La definición

MCP es un estándar abierto, diseñado por Anthropic, para conectar agentes con proveedores de servicios externos: la base de datos de tu aplicación, APIs externas, plataformas de terceros.

En la práctica: permite que un servidor exponga un conjunto de tools sobre un protocolo definido, y que cualquier cliente capaz de MCP las consuma.

### El problema que resuelve

Antes de MCP, cada integración era a medida. ¿Quieres que tu agente use Slack? Lee la documentación de la API de Slack, escribe las clases de tool, gestiona la autenticación, mantenlo. Luego haz lo mismo para Jira. Luego para GitHub. Luego para tu CRM. Y todos los demás frameworks en todos los demás lenguajes rehacen el mismo trabajo.

MCP invierte esto. El **proveedor** publica un servidor. Todos los clientes —NeuronAI, LangChain, un asistente de escritorio, un IDE— lo consumen.

Para ti como integrador, el cambio es: *«dos días de trabajo por integración»* se convierte en *«una línea de configuración, si existe un servidor»*.

### En NeuronAI

```php
use NeuronAI\MCP\McpConnector;

class MyAgent extends Agent
{
    protected function tools(): array
    {
        return [
            ...McpConnector::make([
                'command' => 'php',
                'args' => ['/home/code/mcp_server.php'],
            ])->tools(),
        ];
    }
}
```

Tres detalles en los que conviene detenerse:

**El operador de expansión.** `...McpConnector::make(...)->tools()`: `tools()` devuelve un array, y la expansión lo funde en tu lista. Olvida el `...` y anidarás un array dentro del array de tools, cosa que falla de una forma que el error no deja clara.

**Un conector por servidor.** Crea una instancia de `McpConnector` separada para cada servidor al que te conectes.

**El descubrimiento es automático.** NeuronAI descubre las tools que expone el servidor. Tú no las enumeras. Cuando el agente decide ejecutar una, NeuronAI genera la petición apropiada, la llama en el servidor y devuelve el resultado al modelo.

El resumen del propio framework: *se siente exactamente como tus propias tools definidas, pero puedes acceder a un enorme archivo de acciones predefinidas con una línea de código.*

### Dónde encontrar servidores

- GitHub oficial de MCP: `github.com/modelcontextprotocol/servers`
- Registro MCP-GET: `mcp-get.com`

### La valoración honesta

**Lo que MCP te da genuinamente:** un catálogo enorme de integraciones que no escribiste tú, un ecosistema que crece sin tu intervención y un estándar que se está adoptando ampliamente y no por un solo proveedor.

**Lo que te cuesta:** todas y cada una de las garantías de la Sección 5.1. Esas tools no las escribiste tú. No las revisaste. No controlas sus descripciones, su comportamiento, su gestión de errores ni qué hacen con los argumentos que envía el modelo. La Sección 9.4 se lo toma en serio.

La posición equilibrada: MCP es excelente para conectar con servicios en los que ya confías, y requiere diligencia real para cualquier otra cosa.

### Puntos clave

- Un estándar abierto: los servidores exponen tools, cualquier cliente las consume.
- Una línea de configuración sustituye a una integración a medida.
- Expande el resultado; un conector por servidor; el descubrimiento es automático.
- Heredas código que no escribiste, que es todo el objetivo y todo el riesgo.

## 9.2 Servidores locales

### Configuración estilo comando

Para un servidor instalado localmente en tu máquina o máquina virtual:

```php
use NeuronAI\MCP\McpConnector;

class MyAgent extends Agent
{
    protected function tools(): array
    {
        return [
            ...McpConnector::make([
                'command' => 'php',
                'args' => ['/home/code/mcp_server.php'],
            ])->tools(),
        ];
    }
}
```

NeuronAI arranca el proceso y se comunica con él por entrada y salida estándar.

### El ecosistema de Node

La mayoría de los servidores publicados son paquetes de Node, ejecutados con `npx`:

```php
...McpConnector::make([
    'command' => 'npx',
    'args' => ['-y', '@modelcontextprotocol/server-everything'],
])->tools(),
```

`server-everything` es la implementación de referencia y lo indicado para experimentar: expone ejemplos de todas las funcionalidades de MCP y es la forma más rápida de ver el descubrimiento en acción.

::: {.callout .callout-warning}
[Requisito previo]{.callout-title}

Esto requiere Node en la máquina que ejecuta el agente. Un desarrollador de PHP sin Node instalado chocará con un fallo confuso y supondrá, razonablemente, que el framework está roto. Instálalo antes de trabajar esta sección.
:::

### El modelo de procesos, y sus consecuencias

El servidor es un **proceso hijo** de tu proceso PHP. De ahí se derivan tres cosas:

**Coste de arranque por ejecución.** Cada ejecución lanza el proceso, espera al descubrimiento y luego trabaja. En un script de CLI eso está bien. En una petición web es latencia en cada petición.

**Hereda tu entorno.** Acceso al sistema de archivos, variables de entorno, red. Un servidor MCP local se ejecuta con los privilegios de tu proceso. Trátalo exactamente como tratarías cualquier dependencia que ejecutas con `exec()`.

**No es para un despliegue web típico.** Lanzar `npx` por petición HTTP no es un patrón de producción. Para aplicaciones web, usa servidores remotos (Sección 9.3), o ejecuta el trabajo agéntico en un worker de cola donde el arranque del proceso se amortice en un trabajo más largo.

### El caso genuinamente interesante: tu propio servidor

Puedes escribir un servidor MCP en PHP:

```php
...McpConnector::make([
    'command' => 'php',
    'args' => ['/home/code/mcp_server.php'],
])->tools(),
```

¿Por qué lo harías? Porque convierte las capacidades de tu aplicación en algo que **cualquier** agente puede consumir: tu agente de NeuronAI, el agente en Python de un colega, un asistente de IDE, un cliente de escritorio.

En vez de construir tools para un agente, publicas una superficie de capacidades una sola vez. Para una empresa con un sistema interno valioso, eso es un movimiento estratégico más que un detalle de implementación.

### Puntos clave

- `command` + `args` para servidores locales; comunicación por stdio.
- La mayoría de los servidores son paquetes de Node: Node es un requisito previo.
- El servidor es un proceso hijo: coste de arranque, privilegios heredados, inadecuado para uso web por petición.
- Escribir tu propio servidor expone tu sistema a todos los ecosistemas de agentes a la vez.

## 9.3 Servidores remotos

### HTTP transmisible

El caso normal para servidores alojados:

```php
use NeuronAI\MCP\McpConnector;

class MyAgent extends Agent
{
    protected function tools(): array
    {
        return [
            ...McpConnector::make([
                'url' => 'https://mcp.example.com',
                'token' => 'BEARER_TOKEN',
                'timeout' => 30,
                'headers' => [
                    //'x-cutom-header' => 'value'
                ]
            ])->tools(),
        ];
    }
}
```

Cuatro claves:

- **`url`** — el endpoint del servidor
- **`token`** — se usa como token bearer de autorización
- **`timeout`** — segundos; fíjalo deliberadamente (ver abajo)
- **`headers`** — cualquier otra cosa que el servidor requiera

### Transporte SSE

Pon `async => true`:

```php
...McpConnector::make([
    'url' => 'https://mcp.example.com',
    'token' => 'BEARER_TOKEN',
    'timeout' => 30,
    'async' => true
])->tools(),
```

Los Server-Sent Events mantienen una única conexión HTTP de larga vida sobre la que el servidor empuja actualizaciones.

**Cuál usar:** el que documente el servidor. Esta no es tu elección: es una propiedad del servidor al que te conectas.

### Fija el timeout deliberadamente

El valor por defecto puede ser generoso. Recuerda la aritmética de latencia de la Sección 1.4: un agente de varios pasos que hace varias llamadas MCP acumula todos los timeouts.

Si un servidor tarda habitualmente 25 segundos, o es inadecuado para uso interactivo o tu agente pertenece a una cola. No descubras esto en producción. Mídelo durante la integración y decide.

### Trata el token como una credencial

`'token' => 'BEARER_TOKEN'` en la documentación es un marcador de posición. En código real:

```php
...McpConnector::make([
    'url'     => env('CRM_MCP_URL'),
    'token'   => env('CRM_MCP_TOKEN'),
    'timeout' => 15,
])->tools(),
```

Todo lo de la Sección 3.7 aplica. Esta es una credencial de un sistema que probablemente puede leer o modificar datos de negocio.

### El descubrimiento ocurre en la construcción

Un detalle operativo que sorprende: **`tools()` se conecta al servidor.**

Eso significa que:

- Construir el agente requiere que el servidor sea alcanzable
- Un servidor lento ralentiza la construcción del agente, antes de cualquier llamada al modelo
- Un servidor caído significa que tu agente no se puede construir en absoluto

Si tu método `tools()` se conecta a tres servidores MCP remotos, tienes tres puntos de fallo entre la petición de un usuario y el primer token de la respuesta. Planifícalo: captura los fallos en la construcción, degrada a un conjunto reducido de tools y monitoriza la disponibilidad de los servidores como parte de tu propio tiempo de actividad y no del de otros.

### Puntos clave

- `url` + `token` + `timeout` + `headers` para HTTP transmisible; añade `async => true` para SSE.
- El transporte lo elige el servidor, no tú.
- El descubrimiento ocurre al construir el agente: los servidores remotos son dependencias de disponibilidad.
- Trata los tokens como credenciales; fija los timeouts explícitamente.

## 9.4 Filtrado y seguridad

### Filtrar por nombre de tool

```php
class MyAgent extends Agent
{
    protected function tools()
    {
        return [
            // EXCLUDE: discard certain tools
            ...McpConnector::make([
                'url' => 'https://mcp.example.com',
            ])->exclude([
                'tool_name_1',
                'tool_name_2',
            ])->tools(),

            // ONLY: select the tools you want to include
            ...McpConnector::make([
                'url' => 'https://mcp.example.com',
            ])->only([
                'tool_name_1',
                'tool_name_2',
            ])->tools(),
        ];
    }
}
```

**Diferencia importante respecto a la Sección 5.8.** Los filtros de toolkit reciben **nombres de clase** totalmente cualificados. Los filtros de MCP reciben **cadenas con el nombre de la tool**, porque las tools se definen remotamente y no tienen clases PHP de tu lado.

Esto tiene una consecuencia que conviene enunciar: no hay análisis estático, ni autocompletado del IDE, ni error en tiempo de compilación si un nombre cambia. Una errata en una lista de `only()` produce silenciosamente menos tools de las que esperabas. Registra el número resultante de tools durante el desarrollo.

### Usa `only()`. Siempre.

La Sección 5.8 argumentaba que las listas de permitidos ganan a las de denegación porque los toolkits ganan tools en las versiones del framework. Con MCP el argumento es muchísimo más fuerte:

**El servidor puede añadir tools en cualquier momento, sin que te enteres, sin un despliegue de tu parte.**

Escribiste `exclude(['delete_everything'])`. El mes que viene el mantenedor añade `purge_all`. Tu agente ya la tiene. No actualizaste una dependencia, no desplegaste, no revisaste un changelog. La capacidad llegó por la red.

`only()` es la única opción defendible para cualquier servidor MCP que no controles. Este es uno de los pocos lugares de este libro donde hay una respuesta genuinamente correcta.

### La cuestión de la confianza, enunciada como es debido

Todos los argumentos de la Sección 5.1 sobre que la lista de tools es tu límite de seguridad asumían que escribiste tú las tools. Con MCP no las escribiste.

A qué le estás extendiendo confianza:

- **Descripciones de tools que no escribiste.** Y las descripciones son instrucciones que el modelo lee. Una descripción maliciosa o descuidada es un vector de prompt injection con un mecanismo de entrega de aspecto legítimo.
- **Comportamiento que no puedes inspeccionar.** La tool dice que lee un calendario. No puedes verificar que sea lo único que hace.
- **Una dependencia que cambia sin subir de versión.** Composer te da un archivo de lock. Un servidor MCP te da lo que esté ejecutando hoy.
- **Adondequiera que vayan tus argumentos.** Si el modelo pasa datos de un cliente a una tool remota, esos datos han salido de tu infraestructura. Eso es una cuestión de RGPD, no una preferencia técnica.

### Una política viable

**Nivel 1 — Servidores que ejecutas tú.** Tu propio servidor MCP, en tu infraestructura. La misma confianza que tu propio código. Úsalos con libertad.

**Nivel 2 — Servidores de proveedores en los que ya confías.** El servidor oficial de tu CRM, donde ya tienes un contrato, un acuerdo de tratamiento de datos y un canal de soporte. Úsalos con `only()`.

**Nivel 3 — Todo lo demás.** Servidores de la comunidad, entradas aleatorias de registros, cualquier cosa sin mantenimiento. Trátalos como código no fiable. Para producción: lee el código fuente, fija una versión, ejecútalo tú en lugar de conectarte a una instancia alojada y combina `only()` con aprobación de tools para cualquier cosa con efectos colaterales.

Prototipar es distinto: el Nivel 3 está bien para una prueba rápida. La distinción es entre «probarlo» y «publicarlo».

### Superpón las defensas

Las tools de MCP siguen siendo tools, así que todo lo del Capítulo 5 aplica:

```php
protected function tools(): array
{
    return [
        ...McpConnector::make([
            'url'   => env('CRM_MCP_URL'),
            'token' => env('CRM_MCP_TOKEN'),
        ])->only([
            'search_contacts',
            'get_contact',
        ])->tools(),
    ];
}
```

Nombres de tools de solo lectura en la lista de permitidos. Añade el middleware `ToolApproval` (Capítulo 15) para cualquier cosa que escriba. Y para una integración de verdad sensible, plantéate hacer de proxy: envuelve el servidor MCP en tu propia tool PHP que valide los argumentos antes de reenviarlos, para tener un sitio donde imponer tus propias reglas.

### Puntos clave

- Los filtros de MCP reciben cadenas con el nombre de la tool, no nombres de clase: sin análisis estático, así que registra el número de tools.
- `only()` es obligatorio para cualquier servidor que no controles; los servidores ganan tools sin que tú despliegues.
- Estás confiando en descripciones que no escribiste: una superficie de prompt injection.
- Tres niveles de confianza; ten claro en cuál estás.

## Ejercicios del capítulo

1. **Descubre.** Conéctate a `server-everything` y registra qué tools se descubren. Anota cuánto tarda la construcción: esa es latencia que pagarías en cada petición en un contexto web.

2. **Restringe.** Redúcelo con `only()` a dos tools y verifica que el agente no puede usar una tercera. Después mete una errata en la lista de permitidos y confirma que nada te avisa; ese silencio es la razón por la que la Sección 9.4 te pide que registres el número.

3. **Clasifica.** Para una integración que construirías de verdad, sitúa el servidor en un nivel de confianza y escribe qué exigirías antes de publicarla. Si la respuesta es «nada», contrástalo con los cuatro puntos de la sección sobre confianza.
