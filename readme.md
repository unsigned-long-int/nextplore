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
> All connections are secured using TLS with `TrustServerCertificate=false`, enforcing strict certificate validation. As a result, the server must present an SSL/TLS certificate issued by a publicly trusted Certificate Authority (CA). Certificates signed by private or internal CAs are not supported.
> **Note**: Nextplore also maintains region-specific [CA bundles](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.SSL.html#UsingWithRDS.SSL.CertificatesDownload) across all AWS regions to ensure compatibility and validation integrity.

| DB         | Native Authentication                       | Cloud IAM: Azure                                  | Cloud IAM: AWS                   | Cloud IAM: GCP | Key-Pair/JWT | Kerberos/Windows |
| ---------- | ------------------------------------------- | ------------------------------------------------- | -------------------------------- | -------------- | ------------ | ---------------- |
| SQL Server | ✅ (MSSQL's native auth with password)      | ✅ (AD Service Principal, oAuth 2.0 Access Token) | ❌                               | ❌             | ❌           | ❌               |
| MySQL      | ✅ (MySQL's native auth with password)      | ✅ (oAuth 2.0 Access Token)                       | ✅ (Assume Role with temp token) | ❌             | ❌           | ❌               |
| PostgreSQL | ✅ (PostgreSQL's native auth with password) | ✅ (oAuth 2.0 Access Token)                       | ❌                               | ❌             | ❌           | ❌               |

---

#### SQL Server

**Nextplore** supports multiple authentication methods for **SQL Server**:

- **SQL authentication** with username/password.
- For servers hosted on Azure, you can use **Microsoft Entra (Azure AD) Service Principal authentication** with **oAuth 2.0**

##### IAM Azure

Microsoft provides a very good [guide](https://learn.microsoft.com/en-gb/azure/azure-sql/database/authentication-aad-configure?view=azuresql&tabs=azure-portal) on how to connect with **oAuth 2.0** on Azure SQL.

Here is also a high-level **overview** how you may use **oAuth 2.0** that:

> ⚠️ **Note:**
> With minor syntatic sugar differences the configuration of oAuth 2.0 on Azure is very similar for SQL Server, MySQL and PostgreSQL. For non-native DBMS logging in as initial admin is enabled via token auth.

1. Under your running Azure Server Instance, set **Microsoft Entra Admin** (_it will be used for initial connection and creating users in SQL Server_)
2. Connect to your instance from **VSCode** or **ADS** with **Microsoft Entra Id - Universal with MFA Support** authentication type using your **Microsoft Entra Admin** account.
   - **ADS**:
     - left-bottom account corner
     - add linked accounts
     - log in via browser with MFA
   - **VSCode**
     - install mssql extension
     - go to SQL server
     - add connection
     - insert instance name of your SQL Server (your-instance.database.windows.net)
     - provide database name (optional)
     - choose authentication type **Microsoft Entra Id - Universal with MFA Support**
     - log in via browser with MFA
3. Register **Service Principal** (Application) in Azure.
   - Ensure your service principal has `Directory Readers` role in Azure.
4. Create Microsoft Entra Principals in SQL.
   - Ensure microsoft entra principal name in SQL matches exactly the one you just registered.
5. Then when creating integration on **Nextplore** just provide your client secret, tenant id, client id.
   - **Nextplore** will store them encrypted and will take care of [**oAuth 2.0**]
   - Note, that your client secrets will NOT be used in connection string and authentication will happen using temp byte token as described [here](https://learn.microsoft.com/en-us/sql/connect/odbc/using-azure-active-directory?view=sql-server-ver17#authenticating-with-an-access-token)

```sql
CREATE USER [<Microsoft_Entra_principal_name>] FROM EXTERNAL PROVIDER;
```

6. You may want to restrict rights of the user to **SELECT-ONLY** and to certain schemas/tables that you want to query with **Nextplore** in the future.

---

#### MySQL

**Nextplore** also supports different authentication methods for **MySQL**:

- **Native authentication** with username/password (e.g. `caching_sha2_password` or `mysql_native_password`).
- For **Azure Database** for MySQL, you can also enable **OAuth 2.0** authentication.
- For **Aurora and RDS** hosted on AWS, you can also enable **IAM** connection with temporary tokens through [Assume Role](https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html).

##### IAM Azure

To enable **oAuth 2.0** authentication for **MySQL** on Azure, follow these steps:

1. Create MySQL instance on Azure for **MySQL** flexible servers.
2. Create **user managed identity** ([UMI](https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/how-manage-user-assigned-managed-identities?pivots=identity-mi-methods-azp)).
3. Assign following privelleges to UMI:
   - User.Read.All
   - GroupMember.Read.All
   - Application.Read.ALL
4. Set Microsoft Entra Admin (same as by SQL Server)
5. Enable either **Microsoft Entra authentication only** or **MySQL and Microsoft Entra authentication** under Authentication in your MySQL instance on Azure.
6. Once enabled, Microsoft Entra admin may log in and create AAD users for connections. (in our case AAD user will be service principal)
7. Unlike SQL Server where connection was performed seamlessly through ADS or VSCODE, to log in you need to provide a valid access token as password yourself.
8. To do so get token in Azure CLI like this:
   - log in to azure via browser and choose/confirm your subscription:
     `az login`
   - once confirmed and logged in fetch the token into TOKEN variable:
     `TOKEN=$(az account get-access-token --resource-type oss-rdbms -o tsv --query accessToken)`
   - now you may go to **MySQL Workbench** and set obtained token as password and you username as Entra Admin you set on MySQL instance in Azure (for other connections, check the [guide](https://learn.microsoft.com/en-us/azure/mysql/flexible-server/how-to-azure-ad)).
9. When you are inside, create the AAD user with this statement:

```sql
CREATE AADUSER '<service_principal_name>';
```

10. You may want to restrict rights of the user to **SELECT-ONLY** and to certain schemas/tables that you want to query with **Nextplore** in the future.

Here is also a microsoft [guide](https://learn.microsoft.com/en-us/azure/mysql/flexible-server/how-to-azure-ad) on the same.

##### IAM AWS

To enable **IAM** connection on AWS, follow these steps:

1. Create MySQL instance on AWS under:
2. Connect to MySQL (e.g. via MySQL Workbench) with your admin account (_you should have created this when making the instance_)
3. Create user for future connection:
   Here, again you may want to restrict what **Nextplore** service may access in your DB.

```sql
CREATE USER 'test_user'@'%' IDENTIFIED WITH AWSAuthenticationPlugin AS 'RDS';
GRANT SELECT, INSERT, UPDATE, DELETE ON your_database.* TO 'test_user'@'%';
```

4. Create IAM policy for `test_user`:

**Example: IAM Policy**

```
{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Effect": "Allow",
			"Action": "rds-db:connect",
			"Resource": "arn:aws:rds-db:<region>:<account_id>:dbuser:<resource-id-mysql>/test_user"
		}
	]
}
```

5. Since **Nextplore** uses **Assume Role** you need to create role to set up the trust relationship with AWS **Nextplore** account.

> ⚠️ **Note:**:
>
> - **Nextplore** uses AWS Service - `ec2.amazonaws.com` - under **`NextploreExecutionRole`** for accessing your DB instance. So you should name principal accordingly (see example below).
> - **Nextplore** also validates the role names it is allowed to assume. So please ensure arn follows this naming convention: **`arn:aws:iam::<YOUR_ACCOUNT_ID>:role/NextploreRdsAccessRole`**.

**Example: Trust Policy**

```
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "AWS": "arn:aws:iam::<NEXTPLORE_SAAS_AWS_ACCOUNT_ID>:role/NextploreExecutionRole" },
    "Action": "sts:AssumeRole",
    "Condition": {
      "StringEquals": {
        "sts:ExternalId": "<EXTERNAL_ID>"
      }
    }
  }]
}
```

**`NEXTPLORE_SAAS_AWS_ACCOUNT_ID`**: Nextplore AWS Account

- we will provide you with this when you create your integration

**`EXTERNAL_ID`**: Unique connection id for Nextplore

- we will provide you with the one during integration creation with **AWS IAM**

6. Attach **IAM policy** as permission from `test_user` (_created in Step 4_) to the role you just created.

### PostgreSQL

**Nextplore** provides multiple authentication methods for **PostgreSQL**:

- **Native authentication** with username/password.
- For **Azure Database** for PostgreSQL, you can also enable **OAuth 2.0** authentication.

To use **oAuth 2.0** flow with Microsoft Entra, please follow these steps:

1. Create **PostgreSQL** instance on Azure for flexible servers.
2. Set **Microsoft Entra Admin(s)** for initial authentication and AD users creation (unlike MySQL, multiple admins are possible here).
3. Obtain the login admin token the same way as described in **MySQL step 8** above.
4. Use this token in pgAdmin to connect.
5. For your registered application run the following statement:

```sql
SELECT * FROM pg_catalog.pgaadauth_create_principal_with_oid(
    'your-sp-name',
    'your-sp-object-id',
    'service', -- type 'user', 'group' or 'service'
    false, -- not external - since sp is native principal to your tenant
    false -- not federated - since bult in and no federated IDP
)
```

I highly recommend you to read much more detailed microsoft [guide](https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/security-entra-configure) on the same.

---

> ⚠️ **Note:**
> To enabled more robust integration experience, it is planned to add certificates (instead of secrets) authentication and gateway agent for Kerberos in the next releases.

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
