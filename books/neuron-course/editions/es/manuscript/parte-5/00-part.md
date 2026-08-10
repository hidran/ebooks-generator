# Parte V — Laravel

Todo lo anterior se ha ejecutado desde un script de CLI, por diseño. Ahora se traslada a una aplicación con usuarios, una base de datos, una cola, una capa HTTP y una factura.

El SDK de NeuronAI para Laravel aporta la fontanería —service provider, configuración, facades, bindings del contenedor, historial de chat respaldado por Eloquent— y los Capítulos 17 y 18 la cubren deprisa, porque los problemas interesantes no son la fontanería.

Los problemas interesantes son los que solo tiene la producción. Tools que tocan tus modelos reales y a los que no se debe engañar para que toquen los de otro tenant. Recuperación sobre datos que cambian constantemente y que hay que reindexar sin ventana de mantenimiento. Streaming de tokens hacia un navegador por SSE y Livewire mientras un worker de cola hace el trabajo de verdad. Workflows de aprobación que sobreviven a un despliegue ocurrido entre la petición y la decisión del responsable. Costes que escalan con el comportamiento de los usuarios y no con su número. Providers que te limitan la tasa en el peor momento posible. Prompt injection llegando a través de tu propia bandeja de soporte.

El Capítulo 23 termina con una lista de comprobación de despliegue y con la pregunta de la que va realmente este libro: ¿qué es lo peor que puede hacer tu agente, y qué lo detiene?
