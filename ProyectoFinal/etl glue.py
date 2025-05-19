import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, collect_list, udf, desc
from bs4 import BeautifulSoup
from pyspark.sql.types import StringType


def extract_text(html):
    if html is None:
        return None
    return BeautifulSoup(html, "html.parser").get_text()


def read_s3(path_s3, delimiter,spark):
    df = (spark.read
          .option("header", "true")
          .option("inferSchema", "true")
          .option("delimiter", delimiter)
          .csv(path_s3)
          )
    return df


def tags_transforms(df_tags):
    df_tags = (df_tags.withColumn("Tag", col("Tag").cast("string"))
               .na.drop(subset=["Tag"]))

    tag_counts = df_tags.groupBy("Tag").count()

    top_tags_df = tag_counts.orderBy(desc("count")).limit(100).select("Tag")

    df_tags_filtered = df_tags.join(top_tags_df, on="Tag", how="inner")

    grouped_tags = (df_tags_filtered.groupBy("Id")
                    .agg(collect_list("Tag").alias("Tags")))

    return grouped_tags


def questions_transforms(df_questions):
    df_questions = df_questions.drop("OwnerUserId", "CreationDate", "ClosedDate", "Score")

    extract_text_udf = udf(extract_text, StringType())
    df_questions = df_questions.withColumn("Body", extract_text_udf(col("Body")))

    return df_questions


def merge_data(df_left, df_rigth):
    df_merged = df_left.join(df_rigth, on="Id", how="inner")
    return df_merged


def save_data(data, output_path):
    data.write.mode("overwrite").parquet(output_path)

s3_path_questions = "s3://prueba-tecnica-nequi-camilo-herrera-target/raw_questions/Questions.csv"
s3_path_tags = "s3://prueba-tecnica-nequi-camilo-herrera-target/raw_tags/Tags.csv"
s3_path_output = "s3://amazon-sagemaker-275533505486-us-east-1-4220b263a050/dzd_3zt82x5cpk5i07/4qvwjvukwiuduv/data/"

spark = SparkSession.builder.getOrCreate()

df_tags = read_s3(s3_path_tags,",",spark)
df_questions = read_s3(s3_path_questions,",",spark)

df_tags = tags_transforms(df_tags)
df_questions = questions_transforms(df_questions)

data_merged = merge_data(df_questions, df_tags)
save_data(data_merged, s3_path_output)



--python-modules-installer-option -r

s3://prueba-tecnica-nequi-camilo-herrera/librerias/requirements.txt