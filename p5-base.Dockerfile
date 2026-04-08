FROM ubuntu:24.04

# Install required packages
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    openjdk-17-jdk \
    python3-pip \
    net-tools \
    lsof \
    nano \
    sudo


# Install Python dependencies
RUN pip3 install jupyterlab==4.3.5 pandas==2.2.3 pyspark==4.1.1 matplotlib==3.10.1 google-genai==0.2.2 --break-system-packages

# Download and extract Hadoop
RUN wget https://dlcdn.apache.org/hadoop/common/hadoop-3.4.3/hadoop-3.4.3.tar.gz && \
    tar -xf hadoop-3.4.3.tar.gz && \
    rm hadoop-3.4.3.tar.gz

# Download and extract Spark
RUN wget https://dlcdn.apache.org/spark/spark-4.1.1/spark-4.1.1-bin-hadoop3.tgz && \
    tar -xf spark-4.1.1-bin-hadoop3.tgz && \
    rm spark-4.1.1-bin-hadoop3.tgz


# Set environment variables
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="${PATH}:/hadoop-3.4.3/bin"
ENV HADOOP_HOME=/hadoop-3.4.3
