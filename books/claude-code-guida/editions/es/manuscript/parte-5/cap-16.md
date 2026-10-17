# Capítulo 16. Una landing page de la idea al deploy en Firebase

::: {.chapter-goals}
[Qué aprenderás]{.callout-title}

- Usar el visual companion de Superpowers para decidir el diseño sobre mockups HTML antes de escribir una línea de React.
- Convertir los mockups aprobados en una spec y en un plan de tareas atómicas, y ejecutarlo tarea por tarea con review y commit.
- Replicar un diseño existente, por ejemplo una página hecha con Lovable, a partir de una captura de pantalla.
- Publicar la landing en Firebase Hosting, pasando por un preview channel antes de producción.

[Requisitos previos]{.callout-title}

Node.js 20 o posterior, una cuenta de Google para la consola de Firebase y el plugin Superpowers instalado (capítulo 8). La Firebase CLI la instalamos sobre la marcha.

:::

Una landing page es el proyecto adecuado para juntar por primera vez todo lo que has visto hasta ahora. Es solo frontend: sin backend, sin base de datos, sin autenticación. El deploy es sencillo. La estructura es previsible (hero, features, pricing, testimonios, FAQ, footer), pero tiene suficientes piezas como para pedir un plan, una división en componentes y algunas vueltas de iteración sobre el diseño.

El producto se llama FluentAiPro: una app imaginaria para aprender idiomas con un tutor de IA, con conversaciones en más de 50 idiomas, feedback sobre la pronunciación y rutas adaptativas. El producto sigue siendo imaginario: lo que construimos es la página que lo presenta y lleva al usuario al registro, en React, Vite y Tailwind CSS, con deploy en Firebase Hosting.

El código está en el repo companion `github.com/hidran/fluentaipro-claude-landingpage`. Cada rama es una foto del proyecto al final de una sección: `book/cap-10-1-mockups`, `book/cap-10-2-spec`, `book/cap-10-3-execution`, `book/cap-10-5-deploy-ready`. El 10 viene de la primera edición, donde este era el capítulo 10. Las ramas conservaron el nombre para no romper los enlaces que ya circulan. El stack real del repo es React 19, Vite 6, Tailwind CSS 4.2 y Vitest 4.

El capítulo es largo porque cubre todo el recorrido, de la idea a la URL pública. Léelo con la terminal abierta.

## 16.1 El visual companion, del "quiero una landing" al mockup

### Por qué los mockups antes del código

El visual companion forma parte de la skill `brainstorming` de Superpowers. Genera borradores en HTML y CSS, los sirve desde un pequeño servidor local y te los muestra en el navegador. Tú comentas en lenguaje natural, Claude actualiza el borrador y recargas la página.

El problema que resuelve ya lo conoces. Le describes a Claude una interfaz ("un hero oscuro, título grande, dos botones, una imagen a la derecha") y obtienes código que cumple la descripción al pie de la letra. El resultado puede ser correcto y feo. Para arreglarlo tienes que leer los componentes, entender qué hizo Claude, corregir y esperar al HMR. Cada vuelta cuesta tiempo y tokens.

Con el visual companion esa vuelta ocurre antes, sobre archivos HTML estáticos: nada de dependencias que instalar, ningún proyecto React que arrancar. Cuando el mockup te convence, pasas al código. Es la misma separación entre decidir y construir que encontrarás en el Spec Driven Development de los capítulos 17-19, aplicada al diseño.

### Setup

Crea una carpeta vacía y arranca Claude Code dentro:

```bash
mkdir fluent-ai-landing && cd fluent-ai-landing
git init
claude
```

El `git init` de entrada sirve más adelante: cada tarea del plan se convertirá en un commit. Comprueba con `/status` que estás en la cuenta correcta.

Después entra en Plan Mode: pulsa `Shift+Tab` hasta que la barra de estado muestre `plan mode on`, o usa `/plan`. En Plan Mode Claude explora y propone, pero no modifica archivos hasta que apruebas.

### El prompt inicial

```text
Quiero construir una landing page para FluentAiPro,
una web app para aprender idiomas con ayuda de la IA.
Los usuarios pueden:
- practicar conversación con un tutor de IA en más de 50 idiomas
- recibir feedback en tiempo real sobre pronunciación y gramática
- seguir rutas de aprendizaje adaptativas
- escuchar podcasts temáticos en otro idioma

Empieza explorando el proyecto y propónme un plan.
Quiero que uses el visual companion para enseñarme borradores
visuales antes de tocar el código.
```

Claude mira la carpeta (vacía), carga la skill `brainstorming` y te pregunta si quieres usar el companion en el navegador. Responde que sí. Entonces lanza el script `start-server.sh` de la skill: en auto mode suele pasar solo, en Manual mode te pide que lo apruebes.

El servidor escucha en `localhost` en un puerto elegido al azar, y Claude te da la dirección completa que debes abrir, clave de sesión incluida. Los borradores acaban en la carpeta del proyecto, bajo `.superpowers/brainstorm/<id-de-sesion>/`. En la rama `book/cap-10-1-mockups` están los de mi sesión: `sections.html`, `approaches.html`, `hero-design.html` y `hero-design-v2.html`, `features-design.html` y `features-design-v2.html`, `social-pricing.html`, `pricing-v2.html`. Se abren con doble clic, sin build. El servidor se apaga solo tras cuatro horas de inactividad. Si retomas el trabajo al día siguiente, Claude lo vuelve a arrancar en el mismo puerto.

### Las preguntas del brainstorming

Antes de dibujar, la skill hace preguntas, de una en una. Algunas llegan en la terminal, otras como página clicable en el navegador. Estas son las respuestas que di yo (adáptalas a tu gusto):

- Call to action principal: "Start for free". El objetivo es el registro directo, sin lista de espera.
- Audiencia: estudiantes y profesionales, con el mismo peso. El tono no debe dejar fuera a ninguno de los dos.
- Secciones: la página `sections.html` propone ocho (Hero, Features, Social proof, Pricing, Language showcase, App demo, FAQ, Footer con CTA final). Las seleccioné todas.

Justo después llega `approaches.html` con tres direcciones visuales: A, Glassmorphism (fondo oscuro, tarjetas de vidrio esmerilado, degradado del violeta al cian, un halo luminoso de fondo), la que recomendaba Claude; B, Deep Space + Gold (azul noche con acento dorado); C, Stark Minimal (casi negro, tipografía blanca, cero adornos). Para una app de IA elegí la A.

### Tres rondas de iteración

A partir de aquí Claude dibuja una sección cada vez, y cada borrador es un punto de partida. El sufijo `-v2` en los nombres de archivo corresponde a mis comentarios.

La primera ronda es para el hero y la navbar. La estructura era la buena, las proporciones no:

```text
Está bien, pero los enlaces del menú tienen que ser más grandes
y resaltarse cuando su sección está activa.
El título del hero tiene que ser más grande: es el mensaje principal.
```

Claude reescribe el HTML en pocos segundos, recargas y ves `hero-design-v2.html`. Son cambios de CSS: ningún componente, ningún bundle.

La segunda ronda toca features y pricing. Las tarjetas tenían texto pequeño y poco contraste, y los precios eran de relleno:

```text
Tarjetas de features: texto más grande y más contraste
entre título y descripción.
Pricing: usa estos planes reales:
- Free: 0 €/mes, 10 conversaciones con IA al mes, 1 idioma
- Silver: 12,99 €/mes, conversaciones ilimitadas, 3 idiomas
- Gold: 24,99 €/mes, los más de 50 idiomas, soporte prioritario
Añade un toggle mensual/anual con un 20% de descuento en el anual.
```

El toggle aparece enseguida, pero en el mockup es solo gráfico. La lógica llega con React.

La tercera ronda cierra los colores. Claude resume la paleta que salió de las rondas anteriores: fondo `#0a0a0f`, degradado de `#7c3aed` (violeta) a `#06b6d4` (cian), texto blanco, texto secundario en blanco al 65% de opacidad. La confirmas y Claude la registra como design tokens para la spec:

```text
La paleta está bien. Confírmala y guarda los design tokens.
```

En este punto tienes un mockup navegable con secciones, paleta y jerarquía decididas. Claude no ha creado `package.json`, no ha lanzado `npm install`, no ha escrito ni un archivo `.jsx`. Ha trabajado en una carpeta auxiliar separada del código, así que tirar un borrador no cuesta nada.

::: {.callout .callout-tip}
[Consejo]{.callout-title}

En el repo companion la carpeta `.superpowers/` está commiteada a propósito, para que puedas ver los mockups. En tus proyectos puedes añadirla al `.gitignore`: lo que importa del diseño acaba igualmente en la spec.
:::

## 16.2 Del mockup al plan de tareas atómicas

### Cerrar la fase de diseño

Cuando el mockup te convence, cierra la fase con un mensaje explícito:

```text
El mockup está aprobado. Ahora construyamos el proyecto de verdad
en React + Vite + Tailwind CSS (versión más reciente).
Genera primero las especificaciones completas y después el plan de
implementación con tareas atómicas.
```

A partir de aquí Claude planifica trabajo concreto: estructura del proyecto, componentes, dependencias, deploy. Todo lo que quieras en la página tiene que decirse ahora.

### La spec

Superpowers cierra el brainstorming escribiendo una spec. En el repo es `docs/superpowers/specs/2026-03-25-fluentaipro-landing-page-design.md`, en la rama `book/cap-10-2-spec`. Sin Superpowers la pides tú:

```text
Antes de escribir código, crea una carpeta docs/ y
escribe las especificaciones completas del proyecto: stack,
estructura, componentes, design tokens, accesibilidad.
```

La spec real recoge el stack (React 19 con Vite, Tailwind CSS v4 mediante el plugin `@tailwindcss/vite`, sin routing, Firebase Hosting, animaciones solo con CSS), los design tokens de la paleta, la escala tipográfica con la fuente Inter, el orden de las nueve secciones y, para cada una, textos, layout y comportamiento responsive. Cierran la spec una sección de accesibilidad (contrastes calculados, `aria-expanded` en la FAQ, `prefers-reduced-motion`) y una checklist de verificación final. Está en inglés, como los textos de la landing: el producto se dirige a un público internacional.

Dos detalles muestran cuánto trabajo posterior ahorra una spec bien escrita. La navbar se vuelve "de vidrio" cuando un `<div id="nav-sentinel">` colocado justo debajo sale del viewport, observado con `IntersectionObserver`. Los precios anuales están escritos tal cual (10,39 € Silver, 19,99 € Gold) en lugar de dejarle el cálculo al componente. Sin spec, Claude tomaría esas decisiones por su cuenta en mitad de la ejecución.

::: {.callout .callout-warning}
[Atención]{.callout-title}

Lee la spec antes de aprobarla. Es el último momento en que añadir un requisito, quitar una sección o cambiar un texto cuesta una línea de Markdown. Después, cada cambio es una tarea de fix sobre código ya escrito.
:::

### El plan

Con la spec aprobada, Superpowers pasa a la skill `writing-plans` y genera el plan de implementación: una lista numerada de tareas, cada una con los archivos que toca, las tareas de las que depende y un criterio de finalización verificable. En mi sesión eran diez tareas. Los títulos los ves en la figura; los archivos y los criterios de aquí abajo los reconstruí a partir de la spec, porque el archivo del plan no está en el repo.

```text
Task 1: Project Scaffolding
  Archivos: package.json, vite.config.js, vitest.config.js, index.html,
            src/main.jsx, src/App.jsx, src/index.css, tests/setup.js
  Depende de: ninguna
  Done: npm run dev arranca sin errores, npx vitest run está en verde

Task 2: Shared UI Components
  Archivos: src/components/ui/Badge.jsx, Button.jsx, GlassCard.jsx,
            GradientText.jsx, tests/ui/Button.test.jsx, GlassCard.test.jsx
  Depende de: Task 1
  Done: los componentes se renderizan con las props principales, tests en verde

Task 3: Navbar
  Archivos: src/components/sections/Navbar.jsx, tests/sections/Navbar.test.jsx
  Depende de: Task 2
  Done: navbar sticky, efecto vidrio tras el scroll mediante el sentinel

Task 4: Hero Section
  Archivos: src/components/sections/Hero.jsx, tests/sections/Hero.test.jsx
  Depende de: Task 2
  Done: título, subtítulo, dos CTA, barra de estadísticas; h1 a 40px en móvil

Task 5: Features Section
  Archivos: src/components/sections/Features.jsx
  Depende de: Task 2
  Done: tarjeta ancha con el mockup del chat más 4 tarjetas; una columna por debajo de 768px

Task 6: Demo, Languages, Testimonials
  Archivos: src/components/sections/Demo.jsx, Languages.jsx, Testimonials.jsx
  Depende de: Task 2
  Done: mockup animado (quieto con prefers-reduced-motion), 18 idiomas
        más el chip "+32 more", 3 testimonios

Task 7: Pricing Section
  Archivos: src/components/sections/Pricing.jsx, tests/sections/Pricing.test.jsx
  Depende de: Task 2
  Done: toggle mensual/anual, anual a 10.39 (Silver) y 19.99 (Gold)

Task 8: FAQ Section
  Archivos: src/components/sections/FAQ.jsx, tests/sections/FAQ.test.jsx
  Depende de: Task 2
  Done: accordion con aria-expanded, animación sobre maxHeight

Task 9: Footer + Full Assembly
  Archivos: src/components/sections/Footer.jsx, src/App.jsx, tests/App.test.jsx
  Depende de: Task 3-8
  Done: 9 secciones en el orden de la spec, layout correcto a 375, 768, 1280 px

Task 10: Firebase Deployment
  Archivos: firebase.json, .firebaserc
  Depende de: Task 9
  Done: npm run build limpio, firebase deploy --only hosting correcto
```

![El plan de diez tareas en la terminal de VS Code, junto al package.json recién generado](figures/cap-16/fig-01.png)

### Por qué tareas tan pequeñas

Una tarea atómica lleva el proyecto de un estado coherente al siguiente con el mínimo trabajo posible. "Crea la sección Hero" es atómica, "crea la landing" no.

La ventaja se nota en tres momentos de la ejecución. Si cada tarea es un commit, `git log` se convierte en el diario del proyecto y un bug se localiza en un commit concreto. Si la Task 7 rompe el pricing, haces `git revert` de ese commit sin perder el Hero ni las Features. Y una review de un componente de 60 líneas se hace con atención; una de 1.200 líneas nuevas, no.

Si no usas Superpowers, pide que guarde el plan en un archivo y haz commit de él primero:

```text
Guarda el plan en docs/PLAN.md y haz commit de él como primer
commit del proyecto.
```

Con el plan en disco puedes hacer `/clear` cuando quieras: Claude vuelve a leer el archivo y sabe por dónde ibais.

## 16.3 Ejecución, una tarea cada vez

### Subagent driven

Cuando dices "ejecuta el plan" tienes dos caminos. El primero es la ejecución en línea: Claude trabaja en el contexto principal y tú lo ves todo en la conversación, pero la ventana de contexto se llena deprisa. El segundo es el modo subagent driven de Superpowers (skill `subagent-driven-development`): para cada tarea arranca un subagente con un contexto limpio, que lee la tarea, escribe los archivos, lanza los comandos y devuelve solo el resultado. Los archivos leídos, la salida de la build y los logs de los tests se quedan en el contexto del subagente.

Para esta landing elige el segundo:

```text
Ahora ejecuta el plan en modo subagent driven.
Un subagente por cada tarea. Espera mi confirmación
después de cada tarea antes de pasar a la siguiente.
```

La petición de confirmación hay que escribirla: sin ella, la skill ejecuta todo el plan de un tirón y solo se detiene ante un bloqueo. Así el ritmo lo marcas tú: miras el diff, abres el navegador y luego das paso a la siguiente tarea. Aquí las tareas van en fila, una detrás de otra. En el capítulo 20 verás cómo ejecutar en paralelo las tareas independientes, cada una en su worktree, cuando el proyecto es lo bastante grande como para justificarlo.

### Task 1, scaffolding

El subagente de la Task 1 crea el proyecto Vite y añade Tailwind y Vitest:

```bash
npx create-vite@latest . --template react
npm install
npm install -D tailwindcss @tailwindcss/vite
npm install -D vitest jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event
```

Tailwind v4 ya no tiene `tailwind.config.js`: se activa con el plugin de Vite y una línea de CSS. El `vite.config.js` del repo es este:

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
})
```

En `src/index.css` la primera línea es `@import "tailwindcss";`, seguida de los design tokens de la spec, declarados tanto en `:root` como en `@theme`. Al terminar, el subagente informa de los archivos creados, el resultado de `npm run dev` y el commit. Abre `http://localhost:5173`, comprueba que se ve la página de Vite y responde:

```text
Task 1 ok. Sigue con la Task 2.
```

### Task 2, componentes compartidos

La Task 2 crea en `src/components/ui/` los cuatro bloques que reutilizan todas las secciones: `Badge` (la etiqueta en forma de píldora), `Button` (variantes `primary` y `secondary`, enlace o botón según reciba o no `href`), `GlassCard` (el contenedor de vidrio) y `GradientText` (el texto con el degradado violeta-cian). Son componentes diminutos. `GlassCard` entero cabe en siete líneas:

```jsx
export default function GlassCard({ children, className = '', ...props }) {
  return (
    <div className={`glass-card ${className}`} {...props}>
      {children}
    </div>
  )
}
```

El estilo vive en clases BEM dentro de `index.css` (`.glass-card`, `.btn-primary`), y el `CLAUDE.md` que Claude escribió para el repo lo dice claramente: nada de utilidades de Tailwind inline para los estilos estructurales o de marca.

Junto con los componentes llegan los primeros tests con Vitest y React Testing Library, en `tests/` con la misma estructura que `src/`. No es TDD en sentido estricto, solo una red mínima que te avisa antes del deploy si un refactoring rompe el `Button`.

![El test App renders without crashing y la lista de tareas mientras avanza la ejecución](figures/cap-16/fig-02.png)

### Task 4, el Hero

El Hero es la tarea que más se ve. Ten el navegador abierto mientras se ejecuta: con el HMR de Vite la página se actualiza con cada archivo guardado. Este es el componente en la rama `book/cap-10-3-execution`:

```jsx
import React from 'react'
import Badge from '../ui/Badge'
import GradientText from '../ui/GradientText'
import Button from '../ui/Button'
import { APP_URL } from '../../constants.js'

const STATS = [
  { number: '50+', label: 'Languages' },
  { number: '10M+', label: 'Conversations' },
  { number: '98%', label: 'Accuracy Rate' },
  { number: '4.9★', label: 'User Rating' },
]

export default function Hero() {
  return (
    <section id="hero" className="hero">
      <div className="hero__glow hero__glow--violet" aria-hidden="true" />
      <div className="hero__glow hero__glow--cyan" aria-hidden="true" />

      <Badge>AI-Powered Language Learning</Badge>

      <h1 className="hero__title">
        Learn any language<br />
        with your <GradientText>AI tutor</GradientText>
      </h1>

      <p className="hero__subtitle">
        Practice real conversations in 50+ languages. Get instant pronunciation
        feedback and a learning path that adapts to you.
      </p>

      <div className="hero__actions">
        <Button href={APP_URL} variant="primary">Start for free →</Button>
        <Button href="#features" variant="secondary">▶ See how it works</Button>
      </div>

      <div className="hero__stats" role="list">
        {STATS.map(({ number, label }, i) => (
          <React.Fragment key={label}>
            {i > 0 && <div className="hero__stats-divider" aria-hidden="true" />}
            <div className="hero__stat" role="listitem">
              <span className="hero__stat-number gradient-text">{number}</span>
              <span className="hero__stat-label">{label}</span>
            </div>
          </React.Fragment>
        ))}
      </div>
    </section>
  )
}
```

El título, el subtítulo y las estadísticas son los de la spec, palabra por palabra. Los halos de color son dos `div` decorativos con `aria-hidden`, y la URL del CTA viene de `src/constants.js`, así que se cambia en un solo sitio. Las cifras de las estadísticas son relleno de marketing que hay que sustituir por datos reales antes del lanzamiento.

### No ejecutes todo el plan de golpe

El error más común con un plan aprobado es escribir "ejecútalo todo sin pedirme confirmación". Te encuentras con decenas de archivos nuevos de una sola oleada. Si el toggle del pricing está roto tienes que averiguar cuál de los treinta archivos es el culpable, la review se convierte en una lectura en diagonal y el historial de Git es un único bloque.

Una tarea cada vez parece más lento. En la práctica es más rápido, porque cada error lo ves recién nacido. Para cada tarea bastan un vistazo al diff y una comprobación en el navegador.

### Task 7, el pricing con el toggle

El pricing es la sección con más lógica. En el mockup el toggle solo cambiaba el aspecto; aquí se convierte en estado de React. Este es un extracto de `Pricing.jsx` (Silver y Gold tienen la misma forma que el plan Free):

```jsx
import { useState } from 'react'
import GlassCard from '../ui/GlassCard'
import { APP_URL } from '../../constants.js'

const PLANS = [
  {
    icon: '🌱', name: 'Free',
    monthly: '0', yearly: '0', yearlyTotal: null,
    desc: 'Try it out, no strings attached',
    features: [
      { label: '1 language', included: true },
      { label: '10 AI conversations / month', included: true },
      { label: 'Basic pronunciation feedback', included: true },
      { label: 'Adaptive learning path', included: false },
      { label: 'Progress analytics', included: false },
      { label: 'Priority support', included: false },
    ],
    cta: 'Get started free', ctaVariant: 'outline',
  },
  // Silver: monthly '12.99', yearly '10.39', yearlyTotal '124.70', featured: true
  // Gold:   monthly '24.99', yearly '19.99', yearlyTotal '239.88'
]

export default function Pricing() {
  const [cycle, setCycle] = useState('monthly')
  const isYearly = cycle === 'yearly'

  return (
    <section id="pricing" className="section section--centered">
      {/* ... título y subtítulo ... */}
      <div className="pricing__toggle-row">
        <button
          className={`pricing__toggle-label${!isYearly ? ' pricing__toggle-label--active' : ''}`}
          onClick={() => setCycle('monthly')}
        >
          Monthly
        </button>
        <button
          className="pricing__toggle-track"
          onClick={() => setCycle(isYearly ? 'monthly' : 'yearly')}
          role="switch"
          aria-checked={isYearly}
          aria-label={isYearly ? 'Switch to monthly billing' : 'Switch to yearly billing'}
        >
          <span className={`pricing__toggle-knob${isYearly ? ' pricing__toggle-knob--right' : ''}`} />
        </button>
        <button
          className={`pricing__toggle-label${isYearly ? ' pricing__toggle-label--active' : ''}`}
          onClick={() => setCycle('yearly')}
        >
          Yearly
        </button>
        {isYearly && <span className="pricing__save-badge">Save 20%</span>}
      </div>
      {/* ... las tres GlassCard: price = isYearly ? yearly : monthly ... */}
    </section>
  )
}
```

Haces clic y los precios cambian. El estado es un string, `'monthly'` o `'yearly'`, como pedía la spec, y el toggle tiene `role="switch"` con `aria-checked`, así que un lector de pantalla lo anuncia como lo que es. Los precios anuales están escritos en los datos y no calculados, de modo que el test puede comprobarlos directamente:

```jsx
test('shows yearly prices after toggling to yearly', async () => {
  const user = userEvent.setup()
  render(<Pricing />)
  await user.click(screen.getByRole('button', { name: /yearly/i }))
  expect(screen.getByText('10.39')).toBeInTheDocument()
  expect(screen.getByText('19.99')).toBeInTheDocument()
})
```

### La code review

En modo subagent driven la review no espera al final. En mi sesión, en marzo de 2026, Superpowers hacía dos controles después de cada tarea: uno verificaba que el código cumpliera la spec y el otro (el subagente `superpowers:code-reviewer`) miraba la calidad. En la figura, la Task 2 está en review mientras arranca la Task 3. Desde la versión 6 del plugin los dos controles se han convertido en un único reviewer por tarea, más una review de toda la rama al final.

![El subagente code-reviewer de Superpowers revisa la Task 2 mientras arranca la Task 3](figures/cap-16/fig-03.png)

Cuando todas las secciones estén listas, antes del deploy, haz de todos modos una review de conjunto. Algunos problemas solo se ven mirando las secciones una al lado de otra:

```text
Ahora haz una code review de los componentes en src/components/sections/.
Revisa:
- colores hardcodeados que deberían pasar por los design tokens
- CSS duplicado entre secciones
- accesibilidad (aria-label, contrastes, focus states)
- naming conventions coherentes
- archivos que no deberían estar en Git (dist/, .env.local)
```

En un proyecto así, los hallazgos típicos son un color como `#7c3aed` escrito a mano en un componente en lugar de `var(--color-grad-from)`, el mismo padding repetido en siete secciones, `dist/` ausente del `.gitignore`, un botón sin nombre accesible. En el código final del repo ves el resultado de las correcciones: la clase compartida `.section` en `index.css`, `dist/` en el `.gitignore`, `aria-label` en el toggle. Pide a Claude que corrija los hallazgos y haz commit aparte, con un mensaje como `fix: code review, design token, gitignore, accessibilità`.

Hoy Claude Code también tiene un comando integrado, `/code-review`, que revisa los cambios sin hacer push buscando bugs de corrección: lo encontrarás en el capítulo 22. La checklist de arriba sigue siendo útil para tokens, duplicaciones y accesibilidad, y el capítulo 19 retoma la review en un proyecto más grande.

## 16.4 Replicar un diseño existente, el caso Lovable

### Cuando el diseño ya existe

Hasta ahora has partido de cero. A menudo pasa lo contrario: el diseño ya existe. Puede ser una landing hecha en Lovable, un mockup de Figma o la web de un competidor que te gusta, y quieres rehacerlo en tu stack.

Lovable (`lovable.dev`) genera interfaces React a partir de una descripción, dentro de un editor visual. El resultado es cuidado, pero el código vive en la plataforma y es incómodo de llevar a un flujo de desarrollo normal. La landing de FluentAiPro se había construido antes también en Lovable, y la comparación con la versión hecha en Claude Code es instructiva.

### Replicar a partir de una captura

Claude Code lee imágenes, así que puedes enseñarle una pantalla y pedirle que la rehaga.

Primer paso: captura la página. Si es larga, haz una captura por cada sección principal y guárdalas en el proyecto:

```bash
mkdir -p docs/design-reference
# copia aquí las capturas
```

Segundo paso: pásale la imagen a Claude. Puedes pegarla en el prompt con `Ctrl+V` (también en macOS, no `Cmd+V`), arrastrarla a la terminal o citarla con `@`:

```text
Mira @docs/design-reference/lovable-landing.png

Replica esta landing page en React + Vite + Tailwind CSS.
Especificaciones de estilo:
- Dark mode, fondo casi negro
- Color de acento violeta (#7c3aed)
- Tipografía bold condensada para los títulos
- Efectos glassmorphism en las tarjetas
- Animaciones sutiles (fade-in on scroll)
```

Tercer paso: Claude analiza la imagen. Deduce el layout, la paleta, la tipografía y el número de bloques, y luego genera los componentes. Los textos, precios y nombres de sección que no se leen bien en la captura se convierten en relleno que habrá que actualizar.

### Cuatro rondas de iteración visual

La primera réplica rara vez es perfecta. De una imagen estática no se sacan espaciados exactos, estados hover, animaciones ni breakpoints. Se itera con comentarios precisos, un tema por ronda.

Proporciones generales:

```text
La réplica está bien de estructura, pero:
- El padding vertical del hero es demasiado estrecho
- Las tarjetas de features son más altas en el original
- La fuente del título principal debería ser más gruesa
```

Detalles interactivos:

```text
Añade:
- Hover state en las tarjetas: un ligero glow violeta en el borde
- Transición suave en el toggle del pricing (0.3s ease)
- Scroll behaviour smooth en los enlaces ancla del menú
```

Animaciones:

```text
Añade animaciones fade-in on scroll a las secciones
features, testimonials y pricing. Usa IntersectionObserver
o una librería ligera como framer-motion.
Nada exagerado: solo opacity de 0 a 1 con un translate-y
pequeño (20px), duration 0.5s.
```

Móvil:

```text
Revisa la versión móvil (375px):
- La navbar debe colapsar en un menú hamburguesa
- La cuadrícula de features debe ser de 1 columna en móvil
- Los precios deben leerse sin scroll horizontal
```

Después de cuatro rondas tienes una réplica fiel en React y Tailwind estándar, en tu repo, que puedes mantener con cualquier herramienta.

### Replicar o partir de cero

La réplica compensa cuando el diseño ya está validado: lo probaste con usuarios en el prototipo de Lovable, el cliente lo aprobó o es el esquema clásico de las landings SaaS y reinventarlo no aporta nada. Parte de cero con el visual companion cuando no tienes una referencia, cuando la marca tiene una identidad por construir o cuando el cliente todavía no ha visto nada y tienes margen para proponer.

En muchas landings comerciales la réplica ahorra tiempo: la estructura, la jerarquía y los CTA ya funcionan, y tú personalizas los detalles. Las dos herramientas conviven bien: Lovable para enseñarle una idea al cliente en pocos minutos, Claude Code para llevarla a producción con código versionado y testeado.

## 16.5 Commits, deploy en Firebase y URL en vivo

### El historial antes del deploy

Si has seguido una tarea cada vez, ya tienes una serie de commits. Compruébalo antes del deploy:

```bash
git log --oneline
```

Deberías ver algo así, un commit por tarea más el de la review:

```text
a7b3c2d fix: code review, design token, gitignore, accessibilità
f1e9d8c feat: Footer e assemblaggio delle 9 sezioni
2d4e5f6 feat: FAQ accordion con aria-expanded
3f2e1d0 feat: Pricing con toggle mensile/annuale
9c8b7a0 feat: Demo, Languages, Testimonials
8a7b6c5 feat: Features con card larga e mockup chat
4d3c2b1 feat: Hero con statistiche e glow
7e6f5d4 feat: Navbar sticky con effetto vetro
b9a8c7d feat: componenti UI Badge, Button, GlassCard, GradientText
1f0e9d8 feat: scaffolding Vite + React + Tailwind + Vitest
0c1b2a3 docs: spec e piano di implementazione
```

Cada línea se puede leer, revisar y revertir por separado. Las ramas del repo companion son fotos con un solo commit cada una, así que este historial no lo encontrarás allí: lo construyes tú.

### El proyecto de Firebase

Si todavía no tienes un proyecto de Firebase:

1. Ve a `console.firebase.google.com` y crea un proyecto nuevo.
2. Ponle un nombre, por ejemplo `fluent-ai-pro-landing`. Firebase deriva de él el ID del proyecto, que puedes modificar ahora: después de crearlo ya no se puede cambiar.
3. Sáltate los pasos opcionales, la asistencia de IA y Google Analytics: para una landing estática no hacen falta.
4. Confirma con Create project.

Apunta el ID del proyecto. A menudo coincide con el nombre, a veces lleva un sufijo. Lo necesitas en la CLI.

### La Firebase CLI

Puedes instalarla de forma global:

```bash
npm install -g firebase-tools
firebase login
```

o usarla sobre la marcha con `npx firebase-tools`, como hizo Claude en mi sesión. Si eliges `npx`, pon `npx firebase-tools` en lugar de `firebase` en todos los comandos de esta sección. `firebase login` abre el navegador para la autenticación con Google. Después comprueba:

```bash
firebase projects:list
```

El proyecto que acabas de crear tiene que aparecer en la lista.

### firebase init hosting

Desde la carpeta del proyecto:

```bash
firebase init hosting
```

La CLI hace algunas preguntas:

- Proyecto: usa el existente y selecciónalo de la lista.
- Public directory: `dist`, la carpeta que genera `npm run build`.
- Single-page app: sí. Todas las URL se reescriben a `index.html`, y te hará falta si algún día añades React Router.
- Builds y deploys automáticos con GitHub: no, por ahora.
- Si ya existe `dist/index.html` y la CLI pregunta si sobrescribirlo, responde que no.

El resultado es el `firebase.json` de la rama `book/cap-10-5-deploy-ready`:

```json
{
  "hosting": {
    "public": "dist",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [{ "source": "**", "destination": "/index.html" }]
  }
}
```

Y un `.firebaserc` que vincula la carpeta al proyecto. En el repo el ID es `fluentapipro`; tú verás el tuyo:

```json
{
  "projects": {
    "default": "fluentapipro"
  }
}
```

![Claude escribe firebase.json y .firebaserc durante la tarea de deploy](figures/cap-16/fig-04.png)

Haz commit de la configuración:

```bash
git add firebase.json .firebaserc
git commit -m "chore: Firebase Hosting configuration"
```

En la misma rama están también `.github/workflows/deploy.yml` y `docs/ci-cd-vercel.md`: un pipeline de GitHub Actions que ejecuta los tests y publica en Vercel, con un deploy de preview para cada PR. Es una alternativa a Firebase, y puedes ignorarla para seguir el capítulo.

### Preview channel, antes de salir en vivo

Firebase Hosting tiene los preview channels: URL temporales, válidas 7 días por defecto, para enseñar una versión a un cliente o a un compañero sin tocar el sitio de producción.

```bash
npm run build
firebase hosting:channel:deploy preview-v1
```

La salida termina con la URL del canal y la fecha de caducidad:

```text
✔  hosting:channel:deploy complete!

Channel URL (fluent-ai-pro-landing):
https://fluent-ai-pro-landing--preview-v1-xyz123.web.app

[expires 2026-05-23 14:32:10]
```

Abre la URL y compruébalo todo: navega con los enlaces del menú, prueba el toggle del pricing y revisa los precios anuales, abre y cierra las FAQ, estrecha la ventana a 375px, comprueba que los CTA apuntan a la URL correcta. Si hace falta un cambio, vuelve a hacer deploy en el canal: el sitio de producción no lo tocas.

### El deploy en producción

Cuando la preview está aprobada:

```bash
npm run build
firebase deploy --only hosting
```

Firebase lee `firebase.json`, sube el contenido de `dist/` a su CDN y publica la nueva versión:

```text
=== Deploying to 'fluent-ai-pro-landing-a1b2c'...

i  deploying hosting
i  hosting[fluent-ai-pro-landing]: beginning deploy...
i  hosting[fluent-ai-pro-landing]: found 18 files in dist
✔  hosting[fluent-ai-pro-landing]: file upload complete
i  hosting[fluent-ai-pro-landing]: finalizing version...
✔  hosting[fluent-ai-pro-landing]: version finalized
i  hosting[fluent-ai-pro-landing]: releasing new version...
✔  hosting[fluent-ai-pro-landing]: release complete

✔  Deploy complete!

Project Console: https://console.firebase.google.com/project/...
Hosting URL: https://fluent-ai-pro-landing-a1b2c.web.app
```

La landing está online, con HTTPS y CDN, sin haber configurado un servidor y sin pagar un hosting: el plan gratuito de Firebase basta para una página estática.

### Después del deploy

Para un dominio propio ve a la consola, sección Hosting, y añade el dominio. Firebase te da los registros DNS que debes introducir en tu registrador y emite por su cuenta el certificado HTTPS. La propagación DNS puede tardar desde unas horas hasta un día; mientras tanto el sitio sigue accesible en `.web.app`.

Firebase guarda el historial de versiones publicadas. Si un deploy introduce un problema, desde la consola de Hosting vuelves a poner en línea una versión anterior con un clic. Si en cambio la preview aprobada es exactamente lo que quieres en producción, puedes copiarla al canal live sin rehacer la build:

```bash
firebase hosting:clone fluent-ai-pro-landing:preview-v1 fluent-ai-pro-landing:live
```

Si algún día llevas la landing a Next.js, activa la exportación estática en `next.config.js`:

```javascript
const nextConfig = {
  output: 'export',
  trailingSlash: true,
};
```

`next build` genera HTML estático en la carpeta `out/` en lugar de `dist/`, sin necesidad de un servidor Node.js. Acuérdate de cambiar `public` en `firebase.json`.

Un último caso, muy habitual. Probando la preview puede que notes que la opción activa del menú no sigue el scroll. Se resuelve con un scrollspy:

```text
Añade un scrollspy a la Navbar: usa IntersectionObserver
para detectar qué sección es visible y aplicar la
clase active al enlace correspondiente del menú.
```

En el `Navbar.jsx` del repo lo encuentras en el segundo `useEffect`: un `IntersectionObserver` con umbral 0.3 sigue la sección visible más alta. Claude lo implementa, tú haces commit y vuelves a hacer deploy:

```bash
npm run build
firebase deploy --only hosting
```

Con el ciclo de deploy ya configurado, un cambio de este tipo está en línea en un par de minutos.

## 16.6 Lo que has hecho y lo que queda fuera

En este capítulo has puesto en fila casi todo lo que viste en las partes I-IV: Superpowers con el brainstorming y el visual companion, Plan Mode, una spec escrita antes del código, un plan de tareas atómicas, los subagentes, la review después de cada tarea, un commit por tarea y el deploy con preview.

Para ser honestos, una landing deja fuera mucho de lo que necesita un producto de verdad:

- ni backend ni API: la página no llama a ningún endpoint ni guarda datos;
- ninguna base de datos;
- ninguna autenticación: "Start for free" lleva a una app externa y el registro ocurre allí;
- ningún formulario serio: no hay un formulario de contacto con validación, CAPTCHA y envío de email;
- ningún estado compartido entre páginas, porque solo hay una página;
- ni analytics ni tests A/B, que en una landing real sirven para medir las conversiones;
- un solo idioma, el inglés.

Es a propósito: un proyecto pequeño te permite aprender el ritmo del workflow sin distracciones de infraestructura, y si algo sale mal no pasa nada.

| Proyecto | Stack | Tamaño |
|---|---|---|
| Landing (capítulo 16) | React 19, Vite 6, Tailwind CSS v4, Firebase Hosting | 1 página, 10 tareas |
| Photogallery (capítulos 17-23) | Laravel 13, Filament v5, React 19, Vite 6, Tailwind CSS v4, AWS | API REST y admin, 124 tareas en 14 fases |

La Parte VI construye la Photogallery: una API REST en Laravel 13 bajo `/api/v1`, un panel de administración en Filament v5, un frontend React con login mediante tokens de Sanctum, jobs en cola para redimensionar las fotos y extraer los datos EXIF, y el deploy en AWS con CloudFormation. El método es el mismo de este capítulo (spec, tareas atómicas, review, commit), con requisitos, diseño y tareas en tres documentos separados, la ejecución por waves y la review hecha también con otros modelos. Cambia la escala: aquí tenías 10 tareas, allí tendrás 124.

::: {.callout .callout-prompt}
[Prompt reutilizable]{.callout-title}

Para tu próxima landing, adapta esta plantilla:

```text
Quiero construir una landing page para [NOMBRE DEL PRODUCTO].

Descripción del producto:
[2-3 frases que describan el producto y su valor principal]

Audiencia:
[quiénes son los usuarios objetivo]

Call to action principal:
[p. ej. "Empieza gratis", "Reserva una demo", "Descarga la app"]

Secciones que incluir:
- Hero con título, subtítulo, CTA e imagen/vídeo
- Features (4-6 funcionalidades principales con iconos)
- [sección opcional, p. ej. "How it works" con 3 pasos]
- Social proof (testimonios o logos de clientes)
- Pricing (N planes, con toggle mensual/anual si lo hay)
- FAQ (6-8 preguntas más frecuentes)
- Footer con CTA final

Estilo:
[p. ej. "dark mode, acento violeta, tipografía bold, tech forward"
 o bien "claro, colores cálidos, cercano, startup de consumo"]

Stack:
React + Vite + Tailwind CSS (última versión)

Deploy target:
Firebase Hosting

Workflow:
1. Usa el visual companion para enseñarme 3 variantes de layout
2. Tras aprobar el layout, genera las especificaciones en docs/SPEC.md
3. Crea el plan en docs/PLAN.md con tareas atómicas y criterios de done
4. Ejecuta una tarea cada vez y espera mi confirmación
5. Code review después de todos los componentes, antes del deploy
6. Build + firebase deploy --only hosting

Empieza en Plan Mode. No escribas código hasta que se aprueben las especificaciones.
```

Con las confirmaciones manuales cuenta con 60-90 minutos de sesión, algo menos en modo subagent driven.
:::

## Resumen {.unlisted}

- Antes de escribir React, decide el diseño con el visual companion: los borradores HTML en `.superpowers/brainstorm/` cuestan poco y se tiran sin remordimientos.
- Relee la spec antes de aprobarla. Los textos, precios y comportamientos que se deciden ahí no se convierten después en tareas de fix.
- Ejecuta el plan una tarea cada vez, con confirmación, diff y comprobación en el navegador. Un commit por tarea hace que cada error sea fácil de encontrar y de revertir.
- Haz una review de conjunto de todas las secciones antes del deploy, aunque Superpowers ya haya revisado cada tarea.
- Para publicar bastan `firebase init hosting` con `dist` como public directory, y después `npm run build` y `firebase deploy --only hosting`. Pasa por un preview channel cuando alguien tenga que dar el visto bueno.
- Si el diseño ya existe, replícalo a partir de una captura e itera un tema cada vez.

## Ejercicio {.unlisted}

Construye tu propia landing, no la de FluentAiPro: un side project, tu portfolio, un proyecto open source que merece una página mejor.

1. Crea una carpeta nueva, haz `git init` y arranca Claude Code en Plan Mode.
2. Pide al visual companion que te proponga tres direcciones visuales, elige una e itera sobre las secciones.
3. Haz que genere la spec y el plan de tareas atómicas, y léelos antes de aprobarlos.
4. Ejecuta una tarea cada vez y haz commit después de cada una.
5. Haz una review de conjunto antes del deploy y haz commit de las correcciones aparte.
6. Publica en un preview channel y después en producción.

Empieza pequeño, con hero, features y footer, y añade secciones después. Es más fácil hacer crecer una estructura mínima que recortar una demasiado ambiciosa. Para comparar tu trabajo con el mío, el punto de llegada es la rama `book/cap-10-5-deploy-ready`.

El ejercicio está terminado cuando tu URL `.web.app` responde por HTTPS, `npx vitest run` está en verde y `git log --oneline` muestra un commit por cada tarea del plan.
