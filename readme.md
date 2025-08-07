# Nextplore - LLM-powered SQL ORM Context Creator

Nextplore is a multi-tenant microservice SaaS designed to leverage Large Language Models (LLMs) and advanced metaprogramming to enable general users or developers to interact with range of databases easily without knowing SQL language. It enables natual language querying across variety of database systems including Snowflake, MySQL, MSSQL, PostgreSQL. Nextplore supports different LLMs integrations including Deepseek, Qwen, meta-Llama and GPT-4o.

## Overview

Nextplore aims to enable developers or general users to interact with a variety of relational databases without the need to write any SQL queries. Under the hood it uses [`sqlalchemy`](https://docs.sqlalchemy.org/en/20/intro.html) to dynamically generate and query Object Relational Mapping ([ORMs](https://docs.sqlalchemy.org/en/20/orm/)) models. Due to abstraction of [DBAPI](https://peps.python.org/pep-0249/) the interaction with range of databases becomes possible regardless of the internals of particular database dialects. Nextplore creates ORMs by leveraging [factory pattern](https://refactoring.guru/design-patterns/factory-method) applied together with [metaprogramming](https://www.geeksforgeeks.org/python/metaprogramming-metaclasses-python/). This is achieved by converting natural language responses into structured JSON output schema which serve as arguments for a variety of metafactories responsible for generating new ORMs. Since databases may grow very large consisting of hundreds of schemas and tables, the metadata of tables are embedded and stored at [QDrant](https://qdrant.tech/). Respective metadata (i.e. integration, database, tables, schemas) is stored in PostgreSQL together with QDrant ID. This allows nextplore to apply [RAG](https://aws.amazon.com/what-is/retrieval-augmented-generation/) where only most relevant tables are used as basis for structured LLMs responses. The user natural language prompt is converted into vector, then cosine similarity is calculated between and top N vectors are matched as future knowledge source for chosen LLM.

## Features

## Architecture

![architecture](docs/Entity%20Relationship%20Diagram.jpg)

## Configuration

## License
