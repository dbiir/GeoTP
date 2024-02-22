# Source Code of GeoTP
The source code of paper: "GeoTP: Latency-aware Geo-Distributed Transaction Processing in Database Middlewares".

folder description:
    - geo-agent: deploy in the same machinen with data source
    - geo-middleware: act as middleware
    - script: the network configuartion and running script in EVALUATION(Section6).

> 1.the branch name of both geo-agent and geo-middleware are 'GeoTP'.

> 2.we use benchbase as a client, the configuration can be seen in Section6.

## 1. geo-middleware
The project is inherite from shardingsphere, compile and deploy in the same way as shardingsphere. The configuartion file can be found in `proxy/bootstrap/src/main/resources/conf`, key files are `server.yaml` and `config-sharding.yaml`. Replace url and password with the corresponding values for the target machine.

## 2. geo-agent
Geo-agent works as an agent or proxy for data sources. Similar to geo-middleware, the config file can be found in `bootstrap/src/main/resources/conf`.

### 2.1 Compilation

We compile this project with `maven` and copy the `.jar` into `target/lib`

```shell
./build.py
```

### 2.2 Run geo-agent
```shell
cd target
./start.sh
```

## 3. script

We run the script `run_benchabse.py` to conduct evaluations. Before this, we copy the config file for benchbase into `config/` and tarverse this folder.
For example, we use following command in Section 6.2.

```shell
./run_benchbase.py -s normal -a none aharp_lppa -f skew -w ycsb -e mysql
```
More detail parameters can be found in `run_benchbase.py` or run 
```shell
./run_benchbase.py -h
```
