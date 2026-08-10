# Parte III — Recuperación

Un modelo sabe lo que había en sus datos de entrenamiento y lo que tú pusiste en el prompt. Nada más. No conoce tu catálogo de productos, tu wiki interna, tu histórico de tickets ni nada que ocurriera después de su fecha de corte.

La generación aumentada por recuperación es la respuesta estándar, y se malinterpreta ampliamente como «dale tus documentos al modelo». Lo que realmente es: un problema de búsqueda vestido de problema de generación. Casi todo sistema RAG decepcionante decepciona porque la recuperación es mala, no porque lo sea el modelo.

El Capítulo 11 cubre la teoría y, con igual importancia, lo que la recuperación no resuelve: las preguntas que siempre responderá mal y los casos en los que deberías estar consultando una base de datos.

El Capítulo 12 construye el pipeline de NeuronAI de principio a fin: cargadores, divisores, proveedores de incrustaciones, almacenes vectoriales, filtrado por metadatos, reindexación cuando cambian tus documentos, y los procesadores previos y posteriores que separan una demo de algo que dejarías usar a un cliente.

Ambos laboratorios se ejecutan a coste cero sobre incrustaciones locales.
