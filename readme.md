<p align="center">
  <img src="docs/nextplore-logo.png" alt="Nextplore Logo" width="200"/>
</p>

<h1 align="center">Nextplore</h1>

<p align="center">
  AI-powered insights • Secure • Instant • Beautiful.
</p>

---

> ⚠️ **Status: WIP**  
> Nextplore is under active development. Interfaces and features may change without notice.

# Nextplore - LLM-powered SQL ORM Context Creator

> Nextplore is a multi-tenant microservice SaaS designed to leverage Large Language Models (LLMs) and advanced metaprogramming to enable general users or developers to interact with range of databases easily without knowing SQL language. It enables natural language querying across variety of database systems including Snowflake, MySQL, MSSQL, PostgreSQL. Nextplore supports different LLMs integrations including Deepseek, Qwen, meta-Llama and GPT-4o.

<p align="center">
  <a href="./license.md">
    <img src="https://img.shields.io/badge/License-Proprietary-red.svg" alt="License: Proprietary">
  </a>
  <a href="./readme.md">
    <img src="https://img.shields.io/badge/docs-open-blue" alt="Docs">
  </a>
  <img src="https://img.shields.io/badge/Status-WIP-yellowgreen" alt="Status: WIP">
</p>

---

## Table Of Contents

- [Demo & Screenshots](#demo--screenshots)
- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Security & Compliance](#security--compliance)
- [Databases & Storage](#databases--storage)
- [APIs & SDKs](#apis--sdks)
- [CLI & Admin Tools](#cli--admin-tools)
- [Observability](#observability)
- [Running in Production](#running-in-production)
- [Tenancy at Scale – Gotchas](#tenancy-at-scale--gotchas)
- [Testing & Quality](#testing--quality)
- [Troubleshooting](#troubleshooting)
- [Upgrade & Migration Guide](#upgrade--migration-guide)
- [Roadmap & Changelog](#roadmap--changelog)
- [Contribution Guide](#contribution-guide)
- [Licensing & Notices](#licensing--notices)
- [Support](#support)
- [Appendices](#appendices)

---

## Demo & Screenshots

### Natual Language AI Query

Request any data across your integrations and get structured response.

![AI Query Use Case](./docs/ai-query-use-case.gif)

- **New Integrations Creation/Update/Delete**

![Integrations Use Case](./docs/integrations-use-case.gif)

- **Vectors Metadata Overview**

![Vectors Metadata Use Case](./docs/vectors-metadata-use-case.gif)

- **MFA Tenant Login**

![MFA Login](./docs/mfa-login.gif)

---

## Overview

Nextplore aims to enable developers or general users to interact with a variety of relational databases without the need to write any SQL queries. Under the hood it uses [`sqlalchemy`](https://docs.sqlalchemy.org/en/20/intro.html) to dynamically generate and query Object Relational Mapping ([ORMs](https://docs.sqlalchemy.org/en/20/orm/)) models.

Due to abstraction of [DBAPI](https://peps.python.org/pep-0249/) the interaction with range of databases becomes possible regardless of the internals of particular database dialects. Nextplore creates ORMs by leveraging [factory pattern](https://refactoring.guru/design-patterns/factory-method) applied together with [metaprogramming](https://www.geeksforgeeks.org/python/metaprogramming-metaclasses-python/). This is achieved by converting natural language responses into structured JSON output schema which serve as arguments for a variety of metafactories responsible for generating new ORMs.

Since databases may grow very large consisting of hundreds of schemas and tables, the metadata of tables are embedded and stored at [QDrant](https://qdrant.tech/). Respective metadata (i.e. integration, database, tables, schemas) is stored in PostgreSQL together with QDrant ID. This allows nextplore to apply [RAG](https://aws.amazon.com/what-is/retrieval-augmented-generation/) where only most relevant tables are used as basis for structured LLMs responses. The user natural language prompt is converted into vector, then cosine similarity is calculated between and **top N** vectors are matched as future knowledge source for chosen LLM.

---

## Features

### Natual Language Querying

**Nextplore** enables you to explore and interact with **any relational data** across multiple databases **without writing a single line of SQL**.

With AI-driven search, you can query **all available metadata** from your connected integrations using a **single, unified query**.

- Choose from a variety of powerful AI models:

  - **Moonshatai**
  - **DeepSeek**
  - **OpenAI**
  - **LlamA**

- **Unified Search Across Integrations**  
  Query data across all connected databases in one go.

- **Pivot Functions**  
  Built-in support for:

  - `AVG`, `SUM`, `COUNT`, `MAX`, `MIN`

- **Advanced Filtering**  
  Supported operators:

  - `==`, `!=`, `>`, `<`, `>=`, `<=`, `LIKE`, `NOT LIKE`, `IN`

- **SQL Transparency**  
  View the **exact SQL** generated for your request.

- **Data Export**  
  Export selected results directly for further analysis.

- **Model Flexibility**  
  Choose your preferred AI model for query processing.

---

### Integrations

**Nextplore** supports integrations with the range of different **DBMS** including [Snowflake](https://www.snowflake.com/en/), [MySQL](https://www.mysql.com/), [MSSQL](https://www.microsoft.com/en/sql-server), [PostgreSQL](https://www.postgresql.org/). You can explore data across all your integrations using natural language.

> ⚠️ **Authentication**  
> Currently, only the following authentication methods are supported. All connections use TLS with TrustServerCertificate=no, so the server's certificate must be issued by a publicly trusted Certificate Authority (CA). Certificates from private or internal CAs are not supported.

| DB         | Native Authentication                       | Cloud-hosted: Azure                               | Cloud-hosted: AWS | Cloud-hosted: GCP | Key-Pair/JWT | Kerberos/Windows |
| ---------- | ------------------------------------------- | ------------------------------------------------- | ----------------- | ----------------- | ------------ | ---------------- |
| SQL Server | ✅ (MSSQL's native auth with password)      | ✅ (AD Service Principal, oAuth 2.0 Access Token) | ❌                | ❌                | ❌           | ❌               |
| MySQL      | ✅ (MySQL's native auth with password)      | ✅ (oAuth 2.0 Access Token)                       | ❌                | ❌                | ❌           | ❌               |
| PostgreSQL | ✅ (PostgreSQL's native auth with password) | ✅ (oAuth 2.0 Access Token)                       | ❌                | ❌                | ❌           | ❌               |

#### SQL Server

**Nextplore** supports multiple authentication methods for **SQL Server**:

- **SQL authentication** with username/password.
- For servers hosted on Azure, you can use either:

  - **Microsoft Entra (Azure AD) Service Principal authentication**.
  - **OAuth 2.0** (Azure AD access token).

#### MySQL

**Nextplore** also supports different authentication methods for **MySQL**:

- **Native authentication** with username/password (e.g. `caching_sha2_password` or `mysql_native_password`).
- For **Azure Database** for MySQL, you can also enable **OAuth 2.0** authentication.

### PostgreSQL

**Nextplore** provides multiple authentication methods for **PostgreSQL**:

- **Native authentication** with username/password.
- For **Azure Database** for PostgreSQL, you can also enable **OAuth 2.0** authentication.

---

### Metadata Overview

**Nextplore** provides a comprehensive view of the metadata associated with each integration.  
It allows users to seamlessly inspect and validate active integrations, with a focus on the tables and columns most relevant for **Retrieval-Augmented Generation (RAG)** query resolution.

By exposing both system-defined and descriptive metadata (e.g., SQL Server _extended properties_, PostgreSQL `COMMENT` fields), the platform helps users identify where metadata should be refined or extended.

This refinement enables RAG pipelines to more accurately surface the correct datasets for user queries, ultimately improving both retrieval precision and interpretability of query results.

---

## Architecture

The image below provides the basic architecture of the application.

![architecture](docs/architecture-diagram.jpg)

---

### Tenant Isolation

- For tenant isolation [RLS](https://www.postgresql.org/docs/current/ddl-rowsecurity.html) approach in a single database has been implemented (enough for MVP and small number of vendors, per-tenant-db and automatic provision with Terraform should be implemented to avoid [noisy neighbour problem](https://learn.microsoft.com/en-us/azure/architecture/antipatterns/noisy-neighbor/noisy-neighbor) if bigger tenants are coming)
- To secure sensitive data (i.e. integration credentials) automatic provision of Hashi Vault Store for [secret envelope](https://medium.com/@tarangchikhalia/envelope-encryption-a-secure-approach-to-secrets-management-c8abce5b24d2) has been built.
- Tenant isolation is achieved also with redis key validation, where sha256 keys always take unique user UUID and tenant UUID generated by PostgreSQL.
- To ensure only authenticated users reach microservices endpoints, JWT validation (with caching) is performed through middleware where user credentials are validated and context is set per user identity.
- Each of event sent by kafka follows the interface requiring to contain reference to user identity. Kafka events contain headers which allow message bus to partition them by tenant.

---

### Services Isolation

- Each microservice is provisioned with a dedicated PostgreSQL role, scoped with the principle of least privilege. Access is strictly limited to the schemas relevant to the service's domain, ensuring data segregation, minimizing blast radius, and supporting multi-tenant security requirements.
- Inter-service communication follows an event-driven architecture implemented on Apache Kafka. To maintain strict, language-agnostic contract guarantees, producing services register and version AVRO schemas in the Confluent Schema Registry. This ensures schema evolution compatibility and prevents consumer-producer contract drift.
- Kafka messages are transmitted in a compact, byte-encoded format, minimizing payload size and network overhead. Serialization and deserialization are handled via the AVRO-based implementation of the Codec interface, enabling a modular serialization layer. This design allows for seamless substitution with alternative serialization mechanisms such as Protocol Buffers or JSON without impacting upstream or downstream service logic.
- Kafka messages are partitioned by tenant-id to guarantee ordered delivery and consistent event processing within each tenant's scope.

---

### Logging

---

## License
