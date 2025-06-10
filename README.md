# pg-explain-optimize-dashboard

![pgdashmerged_cropped](https://github.com/user-attachments/assets/b6a6a156-fd4b-4169-9ccf-c1b7bad570a9)


Integrated application using Python, Grafana, Vector and Loki to store explain analyze query results
and display them for analyzation in a simple dashboard.

The motivation is to have many PostgreSQL explain analyze queries and databases and execute everything in one run, then analyze
the results interactively on the dashboard.

## Requirements

 - Python
 - PostgreSQL database running
 - [Grafana](https://grafana.com/docs/grafana/latest/)
 - [Vector](https://vector.dev/)
 - [Loki](https://grafana.com/docs/loki/latest/)
 - [Docker Engine or Docker Desktop]

## How it works

The python program uses the queries and databases saved to execute the explain queries. Results get logged using
Python logging and vector picks up the logs from the docker container running the Python program. Vector sends
it to Loki for storage, and Grafana queries Loki to display data in the dashboards.

## Notes

Keep in mind that this application only measures the elapsed time of SQL statements as they execute within the database engine itself. It does not account for any of the additional latencies and overhead you’ll encounter in a real‐world setting, including but not limited to:

- Network latency between your application server and the database host

- Client‐side processing, such as building and serializing the query or parsing and deserializing the result set

- Driver and ORM overhead, including marshalling parameters, mapping rows to objects, and any client‐side caching

- I/O contention on the database server (disk reads/writes, log flushing, buffer cache misses)

- Resource throttling or CPU scheduling enforced by container orchestrators or hypervisors

Because these factors can often dominate end‐to‐end response times, be sure to profile your full application stack—including the network path and client code—if you need an accurate measure of total latency.

## How to use

### Prerequisites

Please have [Docker Engine](https://docs.docker.com/engine/) or [Docker desktop](https://docs.docker.com/desktop/) installed.

### Add queries and databases

#### ⚠️ Important Warning
**Do not include `&` in any database or query fields.**
The system doesn't sanitize `&`, which causes hard-to-diagnose errors or silent failures.

#### Query Format Requirement
Only `EXPLAIN ANALYZE` queries in JSON format are supported. Always format SQL statements as:
```sql
EXPLAIN (ANALYZE, FORMAT JSON) SELECT ... ;
```


#### Setup instructions

1. Navigate to the project directory:

```bash
cd `root`/db-optimize-logger
```


**Option 1:** Using [uv](https://docs.astral.sh/uv/getting-started/installation/#installation-methods)


```bash
uv venv

uv run app/build_queries.py
```

**Option 2:** Using pip:

```bash
pip install dearpygui pandas pydantic

python app/build_queries.py`

```

After running either option:
Add databases and queries, then save them.


#### Run application and access the dashboard

After adding queries and databases, you can run the rest of the application.

The `start.sh` will delete any data from previous run and execute the queries, begin the pipeline and make the dashboard ready.


**Fresh start** (deletes previous data)

```bash
chmod +x start.sh

./start.sh
```

**Preserve Existing Data**

```bash
docker compose up -d
```


Note: Query execution time depends on complexity. The dashboard will be available after processing.


#### Access Dashboard
[http://localhost:3000/a/ivarehaugland-explaindbdashboard-app/home](http://localhost:3000/a/ivarehaugland-explaindbdashboard-app/home)




