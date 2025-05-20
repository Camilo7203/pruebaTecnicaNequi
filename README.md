# Paso 1: Alcance del proyecto y captura de datos
1. Identificar y recopilar los datos que usaras para tu proyecto.
El DataSet seleccionado es StackSample: 10% of Stack Overflow Q&A Data, que contiene preguntas y respuestas de Stack Overflow. Este conjunto de datos es ideal para el análisis de texto y la clasificación de preguntas y respuestas.
2. Limpiar los datos para dejarlos disponibles para entrenar un modelo de Machine learning que me prediga las tags de la pregunta con base en su texto.
3. Entrenar el modelo de machine learning del punto anterior.
4. Evaluar este model
5. Desplegar el modelo en un entorno de producción.
6. Realizar una propuesta de monitoreo y seguridad del modelo.
# Paso 2: Explorar y evaluar los datos, el EDA.
En el notebook llamado "Paso2.ipynb" realizado en google colab se llevaron a cabo los siguientes pasos:
1. Definicion de funciones
2. Lectura de los datos
3. Exploracion de los datos
4. Revision de la calidad de los datos

Estos pasos los explico a detalle dentro del archivo "Paso2.ipynb"
# Paso 3: Definir el modelo de datos
1. Trazar el modelo de datos conceptual y explicar por qué se eligió ese modelo.
![img_1.png](Imagenes/img_1.png)
Se eligió este modelo conceptual porque tiene una estructura clara y comprensible definiendo las entidades principales, que en este caso son las preguntas, las tags y las respuestas, adicionalmente nos facilita la comprensión respecto a las relaciones entre las entidades y como se pueden consultar y analizar.

2. Diseñar la arquitectura y los recursos utilizados.
![img_14.png](Imagenes/img_14.png)
3. Elegí herramientas como python porque es el lenguaje recomendado por el documento de la prueba técnica y porque es un lenguaje que manejo bastante bien, el uso de notebooks es debido a que me parece una herramienta sencilla de usar, que estoy acostumbrado a ella y me da la facilidad de tener un entorno aislado sin mucho esfuerzo.
Por otro lado respecto a las tecnologías y herramientas utilizadas
   - Amazon S3: Almacenamiento de datos en la nube.
   - Amazon SageMaker: Plataforma de machine learning para entrenar y desplegar modelos.
   - Amazon Glue: Servicio de ETL (Extracción, Transformación y Carga) para preparar los datos.
   - Amazon StepFunctions: Orquestación de flujos de trabajo.
   - Amazon EventBridge: Servicio de mensajería y eventos.

   Todas estas tecnologias se complementan bien para generar un flujo de ML simple


4. Esta implementacion nos permite entrenar un modelo de ML siempre que se tengan nuevos datos en el bucket de raw_data, mientras que cuando se necesite realziar alguna inferencia se puede cargar los datos a el bucket de inference

# Paso 4: Ejecutar la ETL
Para la ejecución del ETL guarde los datos en un bucket S3.
![img_3.png](Imagenes/img_3.png)
Luego hice un trabajo de glue en spark para que este limpiara los datos y los deje listos para el entrenamiento del modelo.
![img_4.png](Imagenes/img_4.png)

# Paso 5: Entrenar, evaluar y desplegar el modelo
Utilizamos un notebook de sagemaker para realizar todo el entrenamiento, evaluacion y despliegue del modelo

El codigo esta en el archivo train.ipynb, en el cual se entrena un modelo de clasificacion de texto. El modelo se entrena con los datos de preguntas y etiquetas extraídos del conjunto de datos de Stack Overflow. Se utiliza la biblioteca scikit-learn para dividir los datos en conjuntos de entrenamiento y prueba.

![img_7.png](Imagenes/img_7.png)
Guardamos los artefactos del modelo en s3
![img_8.png](Imagenes/img_8.png)

Realizamos un pipeline con la ejecucion del notebook de entrenamiento para que este se ejecute cada vez que se necesite.
![img_9.png](Imagenes/img_9.png)
Utilizamos una stepfunction para orquestar el flujo de trabajo y que este se ejecute cada vez que se necesite realizar un entrenamiento.
![img_10.png](Imagenes/img_10.png)
![img_11.png](Imagenes/img_11.png)
Utilizamos una stepfunction para orquestar el flujo de trabajo y que este se ejecute cada vez que se necesite realizar una inferencia en batch.
![img_12.png](Imagenes/img_12.png)

Para la versionamiento del codigo del notebook se utiliza git y github directamente desde el notebook. adicionalmente que los buckets de s3 estan totalmente versionados por lo que siempre se podra acceder a la version de los datos que se usaron para entrenar el modelo.
![img_16.png](Imagenes/img_16.png)
![img_17.png](Imagenes/img_17.png)
# Paso 6: Monitoreo y seguridad
Como propuesta de monitoreo y seguridad del modelo, se recomienda implementar las siguientes medidas:
1. Monitoreo operativo:
    - Ingesta (S3 Raw_data):
      - Nº de archivos recibidos.
      - % de objetos rechazados por formato o tamaño.

   - ETL (AWS Glue/Lambda):
     - Jobs completados vs. fallidos. 
     - Tiempo medio de ejecución y variabilidad respecto al baseline.

   - Entrenamiento (SageMaker):
     - Estado de los Training Jobs (Completed/Failed). 
     - Uso de CPU/GPU y memoria.

   - Model Registry:
     - Nuevas versiones registradas. 
     - Promociones a “producción” vs. “staging”.

    - Inferencia Batch:
      - Jobs completados vs. fallidos. 
      - Tiempo total de procesamiento.

   - Herramienta central:
     - Un único CloudWatch Dashboard “ML-Pipeline” que consolide todas las métricas anteriores.


2. Alertas y acciones correctivas automatizables:

-   Nueva ingesta > umbral de tamaño:
    - Alarma: S3.PutObjectSize > X MB → SNS (e-mail / Slack).

- Fallo en ETL:

  - Alarma: GlueJobFailed > 0 → SNS + PagerDuty.

  - Acción automática: stepFunction reintenta job.

- Training Job FAIL o muy lento:

  - Alarma: SageMakerTrainingJobFailed o duración > 2× baseline → SNS.


- Data drift detectado (Model Monitor):

  - Alarma: DataQualityMonitorDetectionAlert → SNS.

  - Acción automática: Step Functions lanza pipeline de reentrenamiento.

3. Controles y buenas prácticas de seguridad:

- IAM & separación de entornos:

  - Roles con principio de mínimo privilegio para Glue, SageMaker, stepfunction.

  - Cuentas/roles distintos para dev, test y prod, gestionados vía AWS Organizations.

- Red y comunicaciones seguras:

  - Comunicaciones cifradas.

-   Cifrado de datos:

    - SSE-KMS en todos los buckets S3.

    - Cifrado en tránsito por defecto.

    - Credenciales y secretos en Secrets Manager o Parameter Store (KMS).
- Auditoría & detección de anomalías:

  - CloudTrail habilitado y logs enviados a un S3 de auditoría.

  - AWS Config + Security Hub para compliance continuo.

  - GuardDuty para detección de actividades sospechosas.

- Protección del ML:

  - Model Monitor para drift de datos y predicciones.

- Resiliencia y recuperación:
  - Orquestación con Step Functions usando retry y catch.

Versionado estricto de código y artefactos (CodeCommit/CodePipeline).
# Paso 7: Completar la redacción del proyecto

Como cierre del proyecto, se pueden destacar los siguientes puntos:

Resumen de logros:

- Ingesta y limpieza automática de datos de Stack Overflow.

- Entrenamiento y despliegue continuo de un clasificador de tags con SageMaker.

- Orquestación completa (EventBridge → Step Functions → Glue/SageMaker).
- 
Impacto esperado:
- Reducción de esfuerzo manual en preparación e inferencia.
- Mayor fiabilidad gracias a métricas, alarmas y rollbacks automáticos.
- Trazabilidad total de datos, modelos y versiones.

Próximos pasos:

- Añadir tests automáticos de performance y robustez.

- Incluir un dashboard de detección de sesgos.

- Con esto, el flujo de ML queda cerrado, seguro y fácilmente mantenible y escalable.
