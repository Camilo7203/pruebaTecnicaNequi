import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, collect_list, udf, desc
from bs4 import BeautifulSoup
from pyspark.sql.types import StringType


def extract_text(html):
    """
    Extrae texto plano del contenido HTML utilizando BeautifulSoup.

    Argumentos:
        html (str): Contenido HTML a analizar

    Retorna:
        str: Contenido de texto extraído o None si la entrada es None
    """
    if html is None:
        return None
    return BeautifulSoup(html, "html.parser").get_text()


def read_s3(path_s3, delimiter, spark):
    """
    Lee datos CSV desde una ruta S3 utilizando Spark.

    Argumentos:
        path_s3 (str): Ruta S3 al archivo CSV
        delimiter (str): Carácter delimitador de campos
        spark (SparkSession): Sesión de Spark activa

    Retorna:
        DataFrame: DataFrame de Spark que contiene los datos CSV
    """
    df = (spark.read
          .option("header", "true")
          .option("inferSchema", "true")
          .option("delimiter", delimiter)
          .csv(path_s3)
          )
    return df


def tags_transforms(df_tags):
    """
    Transforma los datos de etiquetas filtrando las 100 principales y agrupándolas por Id.

    Argumentos:
        df_tags (DataFrame): DataFrame que contiene datos de etiquetas

    Retorna:
        DataFrame: DataFrame con Id y lista de etiquetas agrupadas
    """
    df_tags = (df_tags.withColumn("Tag", col("Tag").cast("string"))
               .na.drop(subset=["Tag"]))
    tag_counts = df_tags.groupBy("Tag").count()
    top_tags_df = tag_counts.orderBy(desc("count")).limit(100).select("Tag")
    df_tags_filtered = df_tags.join(top_tags_df, on="Tag", how="inner")
    grouped_tags = (df_tags_filtered.groupBy("Id")
                    .agg(collect_list("Tag").alias("Tags")))
    return grouped_tags


def questions_transforms(df_questions):
    """
    Transforma los datos de preguntas eliminando columnas innecesarias y extrayendo texto del Body HTML.

    Argumentos:
        df_questions (DataFrame): DataFrame que contiene datos de preguntas

    Retorna:
        DataFrame: DataFrame de preguntas transformado
    """
    df_questions = df_questions.drop("OwnerUserId", "CreationDate", "ClosedDate", "Score")
    extract_text_udf = udf(extract_text, StringType())
    df_questions = df_questions.withColumn("Body", extract_text_udf(col("Body")))
    return df_questions


def merge_data(df_left, df_rigth):
    """
    Combina dos DataFrames en la columna 'Id' mediante un join interno.

    Argumentos:
        df_left (DataFrame): DataFrame izquierdo para unir
        df_rigth (DataFrame): DataFrame derecho para unir

    Retorna:
        DataFrame: DataFrame combinado
    """
    df_merged = df_left.join(df_rigth, on="Id", how="inner")
    return df_merged


def save_data_parquet(data, output_path):
    """
    Guarda DataFrame en S3 en formato Parquet.

    Argumentos:
        data (DataFrame): DataFrame a guardar
        output_path (str): Ruta de salida en S3

    Retorna:
        None
    """
    (data.write
     .mode("overwrite")
     .option("header", "true")
     .parquet(output_path))


s3_path_questions = "s3://prueba-tecnica-nequi-camilo/raw_data/questions/Questions.csv"
s3_path_tags = "s3://prueba-tecnica-nequi-camilo/raw_data/tags/Tags.csv"
s3_path_output_train = "s3://prueba-tecnica-nequi-camilo/data/train/"
s3_path_output_test = "s3://prueba-tecnica-nequi-camilo/data/test/"

spark = SparkSession.builder.getOrCreate()

df_tags = read_s3(s3_path_tags, ",", spark)
df_questions = read_s3(s3_path_questions, ",", spark)

df_tags = tags_transforms(df_tags)
df_questions = questions_transforms(df_questions)

data_merged = merge_data(df_questions, df_tags)

# Split into train (70%) and test (30%)
train_data, test_data = data_merged.randomSplit([0.7, 0.3], seed=42)

save_data_parquet(train_data, s3_path_output_train)
save_data_parquet(test_data, s3_path_output_test)