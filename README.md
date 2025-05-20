# Paso 1: Alcance del proyecto y captura de datos  
1. Identificar y recopilar los datos que usarás para tu proyecto.  
   El DataSet seleccionado es StackSample: 10% of Stack Overflow Q&A Data, que contiene preguntas y respuestas de Stack Overflow. Este conjunto de datos es ideal para el análisis de texto y la clasificación de preguntas y respuestas.  
2. Limpiar los datos para dejarlos disponibles para entrenar un modelo de Machine learning que prediga las tags de la pregunta con base en su contenido.  
3. Entrenar el modelo de machine learning del punto anterior.  
4. Evaluar este modelo.  
5. Desplegar el modelo en un entorno de producción.  
6. Realizar una propuesta de monitoreo y seguridad del modelo.  

# Paso 2: Explorar y evaluar los datos, el EDA  
En el notebook llamado “EDA/EDAStackOverFlow.ipynb” se llevaron a cabo los siguientes pasos:  
1. Definición de funciones.  
2. Lectura de los datos.  
3. Exploración de los datos.  
4. Revisión de la calidad de los datos.  

Estos pasos los explico a detalle dentro del archivo “EDA/EDAStackOverFlow.ipynb”.  

# Paso 3: Definir el modelo de datos  
1. Trazar el modelo de datos conceptual y explicar por qué se eligió ese modelo.  
   ![img_1.png](Imagenes/img_1.png)  
   Se eligió este modelo conceptual porque tiene una estructura clara y comprensible, definiendo las entidades principales (preguntas, tags y respuestas); adicionalmente, nos facilita la comprensión respecto a las relaciones entre las entidades y cómo se pueden consultar y analizar.  

2. Diseñar la arquitectura y los recursos utilizados.  
   ![img_14.png](Imagenes/img_14.png)  

3. Elegí herramientas como Python porque es el lenguaje recomendado por el documento de la prueba técnica y porque es un lenguaje que manejo bastante bien. El uso de notebooks se debe a que me parece una herramienta sencilla de usar, a la que estoy acostumbrado y que me da la facilidad de tener un entorno aislado sin mucho esfuerzo.  

   Por otro lado, respecto a las tecnologías y herramientas utilizadas:  
   - Amazon S3: Almacenamiento de datos en la nube.  
   - Amazon SageMaker: Plataforma de machine learning para entrenar y desplegar modelos.  
   - Amazon Glue: Servicio de ETL (Extracción, Transformación y Carga) para preparar los datos.  
   - Amazon StepFunctions: Orquestación de flujos de trabajo.  
   - Amazon EventBridge: Servicio de mensajería y eventos.  

   Todas estas tecnologías se complementan bien para generar un flujo de ML simple.  

4. Esta implementación nos permite entrenar un modelo de ML siempre que se tengan nuevos datos en el bucket de raw_data, mientras que, cuando se necesite realizar alguna inferencia, se puede cargar los datos al bucket de inference.  

# Paso 4: Ejecutar la ETL  
Para la ejecución del ETL, guardé los datos en un bucket S3.  
![img_3.png](Imagenes/img_3.png)  
Luego hice un job en Spark para que éste limpiara los datos y los dejara listos para el entrenamiento del modelo.  
![img_4.png](Imagenes/img_4.png)  
El codigo del GlueJob está en el archivo glue/etlGlue.py
# Paso 5: Entrenar, evaluar y desplegar el modelo  
Utilizamos un notebook de SageMaker para realizar todo el entrenamiento, evaluación y despliegue del modelo.  

El código está en el archivo "sageMakerTraining/train.ipynb", en el cual se entrena un modelo de clasificación de texto. El modelo se entrena con los datos de preguntas y etiquetas extraídos del conjunto de datos de Stack Overflow. Se utiliza la biblioteca scikit-learn para dividir los datos en conjuntos de entrenamiento y prueba.  
![img_7.png](Imagenes/img_7.png)  

Guardamos los artefactos del modelo en S3.  
![img_8.png](Imagenes/img_8.png)  

Realizamos un pipeline con la ejecución del notebook de entrenamiento para que éste se ejecute cada vez que se necesite.  
![img_9.png](Imagenes/img_9.png)  

Utilizamos una StepFunction para orquestar el flujo de trabajo y que éste se ejecute cada vez que se necesite realizar un entrenamiento.  
![img_10.png](Imagenes/img_10.png)  
![img_11.png](Imagenes/img_11.png)  

Utilizamos una StepFunction para orquestar el flujo de trabajo y que éste se ejecute cada vez que se necesite realizar una inferencia en batch.  
![img_12.png](Imagenes/img_12.png)  

Para el versionamiento del código del notebook se utiliza Git y GitHub directamente desde el notebook. Adicionalmente, los buckets de S3 están totalmente versionados, por lo que siempre se podrá acceder a la versión de los datos que se usaron para entrenar el modelo.  
![img_16.png](Imagenes/img_16.png)  
![img_17.png](Imagenes/img_17.png)  

# Paso 6: Monitoreo y seguridad  
Como propuesta de monitoreo y seguridad del modelo, se recomienda implementar las siguientes medidas:  

1. **Monitoreo operativo:**  
   - Ingesta (S3 Raw_data):  
     - Nº de archivos recibidos.  
     - % de objetos rechazados por formato o tamaño.  
   - ETL (AWS Glue/StepFunctions):  
     - Jobs completados vs. fallidos.  
     - Tiempo medio de ejecución.  
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

2. **Alertas y acciones correctivas automatizables:**  
   - Nueva ingesta > umbral de tamaño:  
     - Alarma: S3.PutObjectSize > X MB → SNS (e-mail / Slack).  
   - Fallo en ETL:  
     - Alarma: GlueJobFailed > 0 → SNS + PagerDuty.  
     - Acción automática: StepFunction reintenta job.  
   - Training Job FAIL o muy lento:  
     - Alarma: SageMakerTrainingJobFailed o duración > 2× baseline → SNS.  
   - Data drift detectado (Model Monitor):  
     - Alarma: DataQualityMonitorDetectionAlert → SNS.  
     - Acción automática: Step Functions lanza pipeline de reentrenamiento.  

3. **Controles y buenas prácticas de seguridad:**  
   - IAM & separación de entornos:  
     - Roles con principio de mínimo privilegio para Glue, SageMaker, StepFunction.  
     - Cuentas/roles distintos para dev, test y prod, gestionados vía AWS Organizations.  
   - Red y comunicaciones seguras:  
     - Comunicaciones cifradas.  
   - Cifrado de datos:  
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

**Resumen de logros:**  
- Ingesta y limpieza automática de datos de Stack Overflow.  
- Entrenamiento y despliegue continuo de un clasificador de tags con SageMaker.  
- Orquestación completa (EventBridge → Step Functions → Glue/SageMaker).  

**Impacto esperado:**  
- Reducción de esfuerzo manual en preparación e inferencia.  
- Mayor fiabilidad gracias a métricas, alarmas y rollbacks automáticos.  
- Trazabilidad total de datos, modelos y versiones.  

**Próximos pasos:**  
- Añadir tests automáticos de performance y robustez.  
- Incluir un dashboard de detección de sesgos.  
- Con esto, el flujo de ML queda cerrado, seguro y fácilmente mantenible y escalable.  
