# pgexplaindash

Showcase video:

https://github.com/user-attachments/assets/7bedbe31-1c47-41b4-a729-3305459ea6b7



Integrated application using Python, Grafana, Vector and Loki to store explain analyze query results
and display them for analyzation in a simple dashboard.

The motivation is to have many PostgreSQL explain analyze queries and databases and execute everything in one run, then analyze
the results interactively on the dashboard.

Inspired by [pev2](https://github.com/dalibo/pev2). Please check out this amazing tool.

Also thanks to [https://nicegui.io/](https://nicegui.io/) for the easy-to-setup UI.

## Requirements

 - Python
 - PostgreSQL database running
 - [Grafana](https://grafana.com/docs/grafana/latest/)
 - [Vector](https://vector.dev/)
 - [Loki](https://grafana.com/docs/loki/latest/)
 - Docker Engine or Docker Desktop

## How it works

The python program uses the queries and databases saved to execute the explain queries. Results get logged using
Python logging and vector picks up the logs from the docker container running the Python program. Vector sends
it to Loki for storage, and Grafana queries Loki to display data in the dashboards.


## How to use

### Prerequisites

Please have [Docker Engine](https://docs.docker.com/engine/) or [Docker desktop](https://docs.docker.com/desktop/) installed.

### Setup database connections

Databases running in other docker containers running locally must be on the same Docker network as the program. To do this, each container running a PostgreSQL database must be started using the same docker network.

**Create network**

```bash
docker network create `name`
```

**Setup external network with PostgreSQL databaes in docker-compose**

```yaml
pg-container:
 networks:
   - `name`


networks:
  `name`:
    external: true
```

**Set env var `NETWORK` in `.env`**

```
NETWORK=`name`
```

### Add queries and databases

#### ⚠️ Important Warning
**Do not include `&` in any database or query fields.**
The system doesn't sanitize `&`, which causes hard-to-diagnose errors or silent failures.

#### Query Format Requirement
Only `EXPLAIN ANALYZE` queries in JSON format are supported. Always format SQL statements as:
```sql
EXPLAIN (ANALYZE, FORMAT JSON) SELECT ... ;
```


#### <a name="setup-instr"></a> Setup instructions

1. Navigate to the grafana plugin directory and execute:

```bash
cd `root`/ivarehaugland-explaindbdashboard-app

npm install

npm run dev
```

Just close the program after `npm run dev`.

2. Navigate to root, and run docker compose:

```bash
docker compose up -d
```

3. Go to [http://dol.localhost/](http://dol.localhost/) in your browser.

4. Add queries and databases, then save them.

5. Run `START LOGS`

6. If it ran successfully, go to [http://localhost:3000/a/ivarehaugland-explaindbdashboard-app/home](http://localhost:3000/a/ivarehaugland-explaindbdashboard-app/home)

7. View the EXPLAIN ANALYZE log metrics



#### Access URLs
- UI for adding queries and databases: [http://dol.localhost](http://dol.localhost)
- Grafana dashboard viewing log metrics: [http://localhost:3000/a/ivarehaugland-explaindbdashboard-app/home](http://localhost:3000/a/ivarehaugland-explaindbdashboard-app/home)

## Notes

Keep in mind that this application only measures the elapsed time of SQL statements as they execute within the database engine itself. It does not account for any of the additional latencies and overhead you’ll encounter in a real‐world setting, including but not limited to:

- Network latency between your application server and the database host

- Client‐side processing, such as building and serializing the query or parsing and deserializing the result set

- Driver and ORM overhead, including marshalling parameters, mapping rows to objects, and any client‐side caching

- I/O contention on the database server (disk reads/writes, log flushing, buffer cache misses)

- Resource throttling or CPU scheduling enforced by container orchestrators or hypervisors

Because these factors can often dominate end‐to‐end response times, be sure to profile your full application stack—including the network path and client code—if you need an accurate measure of total latency.


