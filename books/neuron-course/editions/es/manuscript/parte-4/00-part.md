# Parte IV — Flujos de trabajo

Un agente decide su propio flujo de control. Ese es su poder, y en producción es también el problema: no puedes prometerle a un cliente que un bucle autónomo seguirá un proceso de cumplimiento normativo.

Los flujos de trabajo son la respuesta. Tú escribes el grafo; el modelo rellena los nodos. El resultado es determinista donde debe serlo e inteligente donde ayuda, que describe a la mayoría del software de negocio valioso.

El Capítulo 13 presenta el modelo guiado por eventos que usa NeuronAI. El Capítulo 14 añade bucles, ramas y estado tipado. El Capítulo 15 cubre la característica que hace que los flujos de trabajo sean genuinamente aptos para producción: la interrupción. Un flujo de trabajo puede detenerse a mitad de ejecución, persistir un punto de control, esperar lo que un humano necesite y reanudarse.

El Capítulo 15 contiene además la advertencia de corrección más importante de este libro. Un nodo reanudado se reejecuta desde el principio, así que una llamada al LLM sin punto de control producirá *contenido distinto del que el humano aprobó*. Es una corrección de una línea y un fallo de auditoría si se te pasa.

El Capítulo 16 pone varios agentes en un solo sistema y hace que se pasen el trabajo entre ellos.
